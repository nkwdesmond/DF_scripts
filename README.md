# 🔍  Scripts to Aid Digital Forensics Analysis

![Python](https://img.shields.io/badge/python-3.x-blue)
![Status](https://img.shields.io/badge/status-active-darkgreen)
![Use Case](https://img.shields.io/badge/use--case-DFIR-purple)

A collection of Python scripts for various purposes to aid digital forensics analysis.

## 🔮 Overview

| Script | Description / Input Type |
|--------|--------------------------|
| parse_webAccess.py | Web access logs (access.log) with optional browser history CSV |
| parse_ipCmdCount.py | Command-line history files (e.g. `.bash_history`) with IP address extraction |
| lookup_ipinfo_batch.py | CSV of IP addresses for batch enrichment using IPinfo API |
| query_url.py | CSV of URLs for HTTP status code queries |
| csv_filter_columnString.py | Filter CSV rows by substring match in a specified column |
| csv_merge_selectedFields.py | Merge multiple CSV files and retain only specified fields |
| csv_merge.py | Merge all CSV files in a directory into one CSV |

## 📜 Scripts

<details>
<summary><strong>parse_webAccess.py</strong></summary>

---

### 📌 Description
Parses web server access logs and optionally correlates them with browser history data to identify user web activity.  
Supports timestamp correlation, URL normalization, and efficient matching between logs and history records.

---

### ✨ Features
- Parses standard web access logs (Apache/Nginx-style)
- Correlates access logs with browser history CSV
- URL normalization (handles encoding and query strings)
- Time-based correlation with configurable delta
- Supports WebKit and ISO timestamp formats
- Efficient matching using indexed lookups (no full nested loops)
- Handles malformed log entries gracefully
- Outputs structured CSV for analysis

---

### 📂 File Parsed
- Web access logs (e.g., `access.log`, `access.log.1`, etc.)
- Browser history CSV (optional)

---

### 🤖 Auto Detect File Names in Directory
- Yes  
- Automatically processes files containing `"access"` in the filename

---

### 📝 Default Output File Name
- `<input_filename>.csv`

---

### 📍 Default Output File Location
- Same directory as the input file

---

### 🕒 Output Timezone
- Defaults to **log timezone**
- Option to convert logs to **UTC** using flag

---

### 🚩 Flags

- `-f, --file` → Specify a single log file  
- `-d, --directory` → Specify a directory containing logs  
- `-u, --urls` → Browser history CSV file  

- `--url-field` → Field name for URL in CSV (default: `url`)  
- `--time-field` → Field name for timestamp in CSV (default: `last_visit_time`)  
- `--time-delta` → Time difference in minutes for correlation (default: `10`)  

- `--force-utc` → Convert log timestamps to UTC  
- `--ignore-query` → Ignore query strings when matching URLs  

---

### 🚀 Usage

#### Parse single log file
```bash
python3 parse_webAccess.py -f access.log
```
#### Parse Directory of Logs
```bash
python3 parse_webAccess.py -d /path/to/logs
```
#### Correlate with Browser History
```bash
python3 parse_webAccess.py -f access.log -u history.csv
```
#### Advanced Example
```bash
python3 parse_webAccess.py -d logs/ -u history.csv --time-delta 5 --force-utc --ignore-query
```
---
</details>

<details>
<summary><strong>parse_ipCmdCount.py</strong></summary>

---

### 📌 Description
Parses command-line history files (e.g. `.bash_history`) to extract and analyze commands involving IP addresses.  
Generates counts of command usage per IP and supports structured CSV or Excel output with detailed breakdowns.

---

### ✨ Features
- Extracts and counts commands associated with IP addresses
- Supports both **per-command** and **combined per-IP** aggregation
- Detects and groups commands by script/binary name
- Plugin-based parsing system (e.g., `openfortivpn` credential extraction)
- Optional Excel output with:
  - Per-command sheets
  - Parsed command fields
  - Misc command grouping
- Detects and flags **dirty lines** (control characters, NULL bytes)
- Cleans unsafe characters for Excel compatibility
- Automatically generates unique Excel sheet names

---

### 📂 File Parsed
- Text-based command history files (e.g., `.bash_history`, logs, command dumps)

---

### 📝 Default Output File Name
- CSV: `<input_filename>_ipCmdCount.csv`  
- Excel (`-x`): `<input_filename>_processed.xlsx`

---

### 📍 Default Output File Location
- Same directory as the input file

---

### 🚩 Flags

- `-f, --file` → Input file (**required**)  
- `-o, --output` → Specify output file  

- `--combine` → Combine counts per IP (instead of per command)  
- `-x, --excel` → Output Excel workbook instead of CSV  

---

### 🚀 Usage

#### Basic CSV Output
```bash
python3 parse_ipCmdCount.py -f .bash_history
```
#### Combine Counts Per IP
```bash
python3 parse_ipCmdCount.py -f .bash_history --combine
```
#### Excel Output (Multi-Sheet)
```bash
python3 parse_ipCmdCount.py -f .bash_history -x
```
---
</details>

<details>
<summary><strong>lookup_ipinfo_batch.py</strong></summary>

---

### 📌 Description
Enriches IP addresses from a CSV file using the **IPinfo Lite Batch API**.  
Processes IPs in batches and outputs structured enrichment data (e.g., geo, ASN) into a new CSV file.

---

### ✨ Features
- Batch enrichment using IPinfo API (efficient for large datasets) via POST requests
- Automatically removes duplicate IPs while preserving order
- Handles API errors and missing data gracefully
- Extracts JSON fields from API response and dynamically builds output fields (expands nested dictionaries)
- Supports large datasets via chunking (default: 1000 IPs per batch)

---

### 📂 File Parsed
- CSV file containing IP addresses (expects IPs in the **first column**)

---

### 📝 Default Output File Name
- `<input_filename>_ipinfo.csv`

---

### 📍 Default Output File Location
- Same directory as the input file

---

### 🚩 Flags

- `-f, --file` → Input CSV file containing IPs (**required**)  
- `-t, --token` → IPinfo API token (**required**)  

---

### 🚀 Usage

#### Basic Usage
```bash
python3 lookup_ipinfo_batch.py -f ips.csv -t <YOUR_API_TOKEN>
```
---
</details>

<details>
<summary><strong>query_url.py</strong></summary>

---

### 📌 Description
Queries a list of URLs from a CSV file and records HTTP response codes and errors.  
Uses multithreading to efficiently process large numbers of URLs with progress tracking and ETA estimation.

---

### ✨ Features
- Parallel URL querying using configurable thread pool
- Captures HTTP response status codes
- Handles common network errors (timeout, SSL, connection issues)
- Displays real-time progress with elapsed time and ETA
- Lightweight and fast for bulk URL validation or triage

---

### 📂 File Parsed
- CSV file containing URLs (expects URLs in the **first column**)

---

### 📝 Default Output File Name
- `<input_filename>_queried.csv`

---

### 📍 Default Output File Location
- Same directory as the input file

---

### 🚩 Flags

- `-f, --file` → Input CSV file containing URLs (**required**)  
- `-t, --threads` → Number of parallel threads (default: `10`)  

---

### 🚀 Usage

#### Basic Usage
```bash
python3 query_url.py -f urls.csv
```
#### Custom Thread Count
```bash
python3 query_url.py -f urls.csv -t 25
```
---
</details>

<details>
<summary><strong>csv_filter_columnString.py</strong></summary>

---

### 📌 Description
Filters rows in a CSV file based on whether a specified column contains a given string.  
Outputs a new CSV file containing only matching rows.

---

### ✨ Features
- Filters CSV rows by substring match in a specific column
- Preserves original CSV structure and headers
- Simple and lightweight for quick data triage
- Provides match count after processing

---

### 📂 File Parsed
- CSV file with headers (uses column names for filtering)

---

### 📝 Default Output File Name
- None (must be specified by user)

---

### 📍 Default Output File Location
- Defined by user (via output file argument)

---

### 🚀 Usage

#### Basic Usage
```bash
python3 csv_filter_columnString.py <input_file> <output_file> <column_name> <search_string>
```
---
</details>

<details>
<summary><strong>merge_filter_csv_fields.py</strong></summary>

---

### 📌 Description
Merges multiple CSV files from a directory and retains only specified fields.  
Useful for consolidating datasets while extracting only relevant columns for analysis.

---

### ✨ Features
- Merges all CSV files in a directory into a single output file
- Filters columns based on a user-provided field list
- Preserves row data while standardizing output structure
- Handles missing fields gracefully (fills with empty values)
- Provides processing summary (files and total rows)

---

### 📂 File Parsed
- Multiple CSV files from a specified directory  
- Field list file (`.txt`) containing column names (one per line)

---

### 🤖 Auto Detect File Names in Directory
- Yes  
- Automatically processes all `.csv` files in the specified directory  

---

### 📝 Default Output File Name
- `filtered_merged_output.csv`

---

### 📍 Default Output File Location
- Same directory as the input CSV files  

---

### 🚩 Flags

- `-d, --directory` → Directory containing CSV files (**required**)  
- `-f, --fields` → Text file with fields to retain (**required**)  

---

### 🚀 Usage

#### Basic Usage
```bash
python csv_merge_selectedFields.py -d /path/to/csvs -f fields.txt
```
---
</details>

<details>
<summary><strong>merge_csv_files.py</strong></summary>

---

### 📌 Description
Merges all CSV files within a specified directory into a single consolidated CSV file.  
Useful for combining datasets with identical structures into one file for analysis.

---

### ✨ Features
- Automatically merges all CSV files in a directory
- Preserves original column structure (based on first valid file)
- Skips empty or invalid CSV files
- Simple and efficient for bulk data consolidation

---

### 📂 File Parsed
- Multiple CSV files from a specified directory  

---

### 🤖 Auto Detect File Names in Directory
- Yes  
- Automatically processes all `.csv` files in the specified directory  

---

### 📝 Default Output File Name
- `merged_output.csv`

---

### 📍 Default Output File Location
- Same directory as the input CSV files  

---

### 🚩 Flags

- `-d, --directory` → Directory containing CSV files (**required**)  

---

### 🚀 Usage

#### Basic Usage
```bash
python csv_merge.py -d /path/to/csvs
```
---
</details>
