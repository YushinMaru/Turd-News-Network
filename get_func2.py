with open('main.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

start = content.find('async def send_scan_summary')
if start != -1:
    next_func = content.find('\n    async def ', start + 1)
    if next_func == -1:
        print(content[start:start+2000])
    else:
        print(content[start:next_func])
