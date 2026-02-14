#!/usr/bin/env python3
"""Fix the corrupted f-string - complete rewrite"""

# Read the file with utf-8 encoding
with open('main.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Find and replace lines 1244-1253 (0-indexed: 1243-1252)
# We need to replace the whole block

# Check what's currently there
for i in range(1243, min(1255, len(lines))):
    print(f"Line {i+1}: {repr(lines[i])}")

# Replace lines 1245-1250 (1-indexed) with proper f-string
new_lines = lines[:1244]  # Keep everything before line 1245

# Add the fixed embed.add_field section
new_content = '''                embed.add_field(
                    name="📈 Summary",
                    value=f"**Total Posts:** {total}\\n"
                          f"**Processed:** {processed}\\n"
                          f"**Skipped (already sent):** {skipped_already_sent}\\n"
                          f"**Skipped (no tickers):** {skipped_no_tickers}\\n"
                          f"**Skipped (no stock data):** {skipped_no_stock_data}",
                    inline=False
                )
'''
new_lines.append(new_content)

# Add everything from line 1254 onwards
new_lines.extend(lines[1253:])

# Write back
with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("DONE: Fixed the f-string!")
