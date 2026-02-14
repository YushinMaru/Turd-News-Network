#!/usr/bin/env python3
"""Fix the corrupted f-string in main.py"""

# Read the file with utf-8 encoding
with open('main.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# The corrupted section
corrupt = '''                embed.add_field(
                    name="📈 Summary",
                    value=f"**Total Posts:** {total}"
"
                          f"**Processed:** {processed}"
"
                          f"**Skipped (already sent):** {skipped_already_sent}"
"
                          f"**Skipped (no tickers):** {skipped_no_tickers}"
"
                          f"**Skipped (no stock data):** {skipped_no_stock_data}",
                    inline=False
                )'''

# The fixed version
fixed = '''                embed.add_field(
                    name="📈 Summary",
                    value=f"**Total Posts:** {total}\\n"
                          f"**Processed:** {processed}\\n"
                          f"**Skipped (already sent):** {skipped_already_sent}\\n"
                          f"**Skipped (no tickers):** {skipped_no_tickers}\\n"
                          f"**Skipped (no stock data):** {skipped_no_stock_data}",
                    inline=False
                )'''

if corrupt in content:
    content = content.replace(corrupt, fixed)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed corrupted f-string!")
else:
    print("ERROR: Could not find corrupted section")
    # Try simpler approach
    import re
    # Just fix any standalone " lines within the value= block
    pattern = r'(value=f"[^"]+)"\s*\n\s*f"'
    replacement = r'\1\\n"\n                          f"'
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: Fixed with regex!")
    else:
        print("Could not fix with regex either")
