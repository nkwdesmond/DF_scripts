#!/bin/bash

DIR=""
SEARCH="123.123.123.123"
LIST_ONLY=false

usage() {
  echo "Usage: $0 -d <directory> [-s <comma_separated_keywords>] [-l]"
  exit 1
}

# Parse arguments
while getopts "d:s:l" opt; do
  case "$opt" in
    d) DIR="$OPTARG" ;;
    s) SEARCH="$OPTARG" ;;
    l) LIST_ONLY=true ;;
    *) usage ;;
  esac
done

# Validate input
[[ -z "$DIR" ]] && usage
[[ ! -d "$DIR" ]] && { echo "Error: invalid directory"; exit 1; }

# Build regex (OR matching)
IFS=',' read -ra SEARCHES <<< "$SEARCH"
pattern=$(printf "%s\n" "${SEARCHES[@]}" | paste -sd '|')

shopt -s nullglob

files=(
  "$DIR"/btmp
  "$DIR"/btmp-*
  "$DIR"/wtmp
  "$DIR"/wtmp-*
)

process_file() {
  local file="$1"

  [[ ! -e "$file" ]] && return

  # Determine command safely (no eval)
  if [[ "$file" == *.gz ]]; then
    if [[ "$file" == *btmp* ]]; then
      zcat -- "$file" | lastb -f -
    else
      zcat -- "$file" | last -f -
    fi
  else
    if [[ "$file" == *btmp* ]]; then
      lastb -f "$file"
    else
      last -f "$file"
    fi
  fi
}

for f in "${files[@]}"; do
  if $LIST_ONLY; then
    # Stop early on first match (efficient)
    if process_file "$f" | grep -Eq "$pattern"; then
      echo "$f"
    fi
  else
    # Stream matching lines directly
    process_file "$f" | grep -E "$pattern"
  fi
done