import argparse
import csv
import os
import sys
import requests

BATCH_SIZE = 1000

def chunk_list(data, size):
    """Split list into chunks of given size"""
    for i in range(0, len(data), size):
        yield data[i:i + size]


def query_batch(ip_chunk, token):
    url = f"https://api.ipinfo.io/batch/lite?token={token}"

    payload = "\n".join(ip_chunk).encode("utf-8")  # IMPORTANT: bytes

    headers = {
        "Content-Type": "text/plain"
    }

    try:
        response = requests.post(
            url,
            data=payload,
            headers=headers,
            timeout=60
        )

        if response.status_code != 200:
            print(f"[!] HTTP {response.status_code}")
            print(response.text)
            return {}

        return response.json()

    except Exception as e:
        print(f"[!] Request failed: {e}")
        return {}


def main():

    parser = argparse.ArgumentParser(description="IPinfo Lite batch enrichment")
    parser.add_argument("-f", "--file", required=True, help="Input CSV file with IPs")
    parser.add_argument("-t", "--token", required=True, help="IPinfo API token")

    args = parser.parse_args()

    input_file = args.file
    token = args.token

    if not os.path.isfile(input_file):
        print("Input file does not exist")
        sys.exit(1)

    # Read IPs from CSV (first column only)
    ips = []
    with open(input_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)

        # next(reader, None)  # skip header

        for row in reader:
            if row:
                ip = row[0].strip()
                if ip:
                    ips.append(ip)

    # Remove duplicates (preserve order)
    ips = list(dict.fromkeys(ips))

    print(f"[+] Loaded {len(ips)} unique IPs")

    chunks = list(chunk_list(ips, BATCH_SIZE))
    print(f"[+] Processing {len(chunks)} batch requests")

    results = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"[+] Batch {i}/{len(chunks)} ({len(chunk)} IPs)")

        batch_data = query_batch(chunk, token)

        for ip in chunk:
            data = batch_data.get(ip)

            if isinstance(data, dict):
                row = data.copy()
            else:
                # handle missing or error responses
                row = {"ip": ip, "error": str(data)}

            row["ip"] = ip
            results.append(row)

    # Dynamically determine all fields
    all_fields = set()
    for r in results:
        all_fields.update(r.keys())

    fieldnames = sorted(all_fields)

    # Prepare output file
    base = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(
        os.path.dirname(os.path.abspath(input_file)),
        f"{base}_ipinfo.csv"
    )

    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            writer.writerow(row)

    print(f"\n✅ Output written to: {output_file}")


if __name__ == "__main__":
    main()