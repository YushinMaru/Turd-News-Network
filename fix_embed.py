import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the exception handler to print errors instead of calling fallback
old_code = "await self._send_simple_embed(stonks_channel, sd, post)"
new_code = "print(f\"[DD ERROR] Ticker report failed for {ticker}: {e}\")"

content = content.replace(old_code, new_code)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - replaced fallback with error print')
