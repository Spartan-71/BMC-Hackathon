#!/bin/bash

# Define directories to search for SUID/SGID files
SUID_DIR="/usr/bin"
SGID_DIR="/usr/sbin"

# Search for SUID files
l_output2=$(find "$SUID_DIR" -type f -perm 0755 -print)

# Check if any SUID files were found
if [ -n "$l_output2" ]; then
  echo "SUID executable files:"
  echo "$l_output2"
else
  echo "No SUID executable files found."
fi

# Search for SGID files
l_output=$(find "$SGID_DIR" -type f -perm 0755 -print)

# Check if any SGID files were found
if [ -n "$l_output" ]; then
  echo "\nSGID executable files:"
  echo "$l_output"
else
  echo "No SGID executable files found."
fi

# Action summary and audit result
echo "\nAction Summary:"
echo "Review these lists to ensure no rogue programs have been added."

if [ -n "$l_output2" ] || [ -n "$l_output" ]; then
  echo "\nAudit Result: Potential security risk detected. Review SUID/SGID files manually."
else
  echo "\nAudit Result: No potential security risks found."
fi

# Output list of files in a human-readable format
if [ -n "$l_output2" ]; then
  for file in $l_output2; do
    owner=$(stat -c "%U" "$file")
    group=$(stat -c "%G" "$file")
    type=$(stat -c "%a" "$file")
    echo "File: $file"
    echo "Owner: $owner"
    echo "Group: $group"
    echo "Type: $type"
    echo ""
  done
fi

if [ -n "$l_output" ]; then
  for file in $l_output; do
    owner=$(stat -c "%U" "$file")
    group=$(stat -c "%G" "$file")
    type=$(stat -c "%a" "$file")
    echo "File: $file"
    echo "Owner: $owner"
    echo "Group: $group"
    echo "Type: $type"
    echo ""
  done
fi
