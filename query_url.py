#!/usr/bin/env python3

import argparse
import csv
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---- Worker function ----
def fetch_url(url):
    url = url.strip()

    try:
        response = requests.get(url, timeout=(3, 7), allow_redirects=True)
        return (url, response.status_code, "")

    except requests.exceptions.Timeout as e:
        return (url, "timeout", str(e))

    except requests.exceptions.ConnectionError as e:
        return (url, "connection_error", str(e))

    except requests.exceptions.SSLError as e:
        return (url, "ssl_error", str(e))

    except requests.exceptions.RequestException as e:
        return (url, "other_error", str(e))


# ---- Main processing ----
def query_urls(input_file, threads):
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_queried.csv"

    urls = []

    # Read input CSV
    with open(input_file, newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        for row in reader:
            if row:
                urls.append(row[0])

    results = []

    # Start timer
    start_time = time.time()

    # Parallel execution
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(fetch_url, url): url for url in urls}

        total = len(futures)
        completed = 0

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            completed += 1

            # Time calculation
            elapsed = int(time.time() - start_time)
            hrs = elapsed // 3600
            mins = (elapsed % 3600) // 60
            secs = elapsed % 60

            # ETA calculation
            if completed > 0:
                avg_time = elapsed / completed
                remaining = int(avg_time * (total - completed))
            else:
                remaining = 0

            r_hrs = remaining // 3600
            r_mins = (remaining % 3600) // 60
            r_secs = remaining % 60

            print(
                f"[{completed}/{total}] completed. "
                f"Time: {hrs:02d}:{mins:02d}:{secs:02d} | "
                f"ETA: {r_hrs:02d}:{r_mins:02d}:{r_secs:02d}",
                end="\r",
                flush=True
            )

    print()  # move to next line after progress completes

    # Write output CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["url", "response_code", "error_detail"])

        for row in results:
            writer.writerow(row)

    print(f"[+] Output written to: {output_file}")


# ---- CLI ----
def main():
    parser = argparse.ArgumentParser(
        description="Query URLs from CSV (parallel) and log response codes"
    )
    parser.add_argument(
        "-f", "--file", required=True,
        help="Input CSV file with URLs"
    )
    parser.add_argument(
        "-t", "--threads", type=int, default=10,
        help="Number of parallel threads (default: 10)"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"[-] File not found: {args.file}")
        return

    query_urls(args.file, args.threads)


if __name__ == "__main__":
    main()