#!/usr/bin/env python3

# Quick and dirty method with Linux:
# cut -d',' -f2 history_urls.csv | sed 's|https\?://[^/]*||' | sort -u > paths.txt
# while read p; do grep "$p" web_access.log; done < paths.txt > matches.txt

#!/usr/bin/env python3

import argparse
import os
import csv
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, unquote

# -----------------------------
# LOG PARSING
# -----------------------------
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) (?P<identity>\S+) (?P<user>\S+) '
    r'\[(?P<timestamp>.*?)\] '
    r'"(?P<request>.*?)" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
    r'(?: "(?P<referrer>.*?)" "(?P<user_agent>.*?)")?'
)

TIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"

LOG_FIELDS = [
    "ip", "identity", "user", "timestamp",
    "method", "path", "protocol",
    "status", "size", "referrer", "user_agent",
    "is_malformed"
]

HISTORY_FIELDS = ["timestamp_in_tz_of_log", "history_url", "normalized_path"]

# -----------------------------
# LOG PARSING
# -----------------------------

def parse_log_line(line):
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    data = match.groupdict()

    try:
        data['timestamp'] = datetime.strptime(data['timestamp'], TIME_FORMAT)
    except Exception:
        return None

    request = data.get("request", "")
    parts = request.split()

    if len(parts) == 3:
        data["method"], data["path"], data["protocol"] = parts
        data["is_malformed"] = False
    else:
        data["method"] = None
        data["path"] = request
        data["protocol"] = None
        data["is_malformed"] = True

    return data

# -----------------------------
# NORMALIZATION
# -----------------------------

def normalize_url(url, ignore_query=False):
    parsed = urlparse(url)
    path = unquote(parsed.path)
    query = unquote(parsed.query)

    if query and not ignore_query:
        return f"{path}?{query}"
    return path


def normalize_path(path, ignore_query=False):
    if '?' in path and ignore_query:
        path = path.split('?', 1)[0]
    return unquote(path.strip())

# -----------------------------
# TIME HANDLING
# -----------------------------

def webkit_to_datetime(value):
    try:
        value = int(value)
        epoch_start = datetime(1601, 1, 1, tzinfo=timezone.utc)
        return epoch_start + timedelta(microseconds=value)
    except Exception:
        return None

# -----------------------------
# HISTORY INGESTION
# -----------------------------

def load_history(csv_file, url_field, time_field, ignore_query):
    history = []

    with open(csv_file, encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if url_field not in row:
                continue

            norm = normalize_url(row[url_field], ignore_query)

            ts = None
            if time_field and time_field in row:
                raw_time = row[time_field]
                try:
                    ts = datetime.fromisoformat(raw_time)
                except Exception:
                    ts = webkit_to_datetime(raw_time)

            history.append({
                "history_url": row[url_field],
                "normalized_path": norm,
                "_time": ts  # internal field
            })

    return history

# -----------------------------
# LOG INGESTION
# -----------------------------

def load_logs(filepath, ignore_query):
    entries = []

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parsed = parse_log_line(line)
            if not parsed:
                continue

            # internal matching field
            parsed['_norm_path'] = normalize_path(parsed['path'], ignore_query)

            entries.append(parsed)

    return entries

# -----------------------------
# CORRELATION
# -----------------------------

def correlate(history, logs, time_delta_seconds, force_utc):
    results = []

    # 🔥 Build index: path -> list of log entries
    log_index = {}
    for l in logs:
        key = l['_norm_path']
        if key not in log_index:
            log_index[key] = []
        log_index[key].append(l)

    # 🔥 Match using index (no full nested loop)
    for h in history:
        candidates = log_index.get(h['normalized_path'], [])

        for l in candidates:
            log_time = l['timestamp']

            if force_utc and log_time:
                log_time = log_time.astimezone(timezone.utc)

            if h['_time'] and log_time:
                delta = abs((h['_time'] - log_time).total_seconds())
                if delta > time_delta_seconds:
                    continue

                        # convert history timestamp to log timezone if possible
            hist_ts = h.get('_time')
            if hist_ts and l.get('timestamp'):
                log_tz = l['timestamp'].tzinfo
                if log_tz:
                    try:
                        hist_ts = hist_ts.astimezone(log_tz)
                    except Exception:
                        pass

            row = {
                "timestamp_in_tz_of_log": hist_ts,
                "history_url": h['history_url'],
                "normalized_path": h['normalized_path']
            }

            for field in LOG_FIELDS:
                row[field] = l.get(field)

            row['timestamp'] = log_time

            results.append(row)

    return results

# -----------------------------
# OUTPUT
# -----------------------------

def write_csv(filepath, rows, include_history):
    if not rows:
        print(f"[-] No output for {filepath}")
        return

    output_file = filepath + ".csv"

    if include_history:
        fieldnames = HISTORY_FIELDS + LOG_FIELDS
    else:
        fieldnames = LOG_FIELDS

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"[+] Written: {output_file}")

# -----------------------------
# FILE HANDLING
# -----------------------------

def is_foreman_log(filename):
    # Identify any access log generically
    return "access" in filename.lower()


def process_file(filepath, history, time_delta_seconds, force_utc, ignore_query):
    print(f"[+] Processing: {filepath}")

    logs = load_logs(filepath, ignore_query)

    if history:
        results = correlate(history, logs, time_delta_seconds, force_utc)
        write_csv(filepath, results, include_history=True)
    else:
        # strip internal fields before output
        cleaned = []
        for l in logs:
            row = {k: l.get(k) for k in LOG_FIELDS}
            cleaned.append(row)

        write_csv(filepath, cleaned, include_history=False)


def process_directory(directory, history, time_delta_seconds, force_utc, ignore_query):
    for root, _, files in os.walk(directory):
        for file in files:
            if is_foreman_log(file):
                process_file(os.path.join(root, file), history, time_delta_seconds, force_utc, ignore_query)

# -----------------------------
# MAIN
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Foreman DFIR Parser (Hardened)")

    parser.add_argument('-f', '--file', help='Single log file')
    parser.add_argument('-d', '--directory', help='Directory of logs')
    parser.add_argument('-u', '--urls', help='Browser history CSV')

    parser.add_argument('--url-field', default='url')
    parser.add_argument('--time-field', default='last_visit_time')
    parser.add_argument('--time-delta', type=int, default=10)

    parser.add_argument('--force-utc', action='store_true')
    parser.add_argument('--ignore-query', action='store_true')

    args = parser.parse_args()

    history = []
    if args.urls:
        history = load_history(args.urls, args.url_field, args.time_field, args.ignore_query)

    time_delta_seconds = args.time_delta * 60

    if args.file:
        process_file(args.file, history, time_delta_seconds, args.force_utc, args.ignore_query)
    elif args.directory:
        process_directory(args.directory, history, time_delta_seconds, args.force_utc, args.ignore_query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
