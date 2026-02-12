# Turd News Network Enhanced - Windows Setup Guide

## Quick Start

### Option 1: Using Batch File (Recommended)
Simply double-click `run_bot.bat` to start the bot!

### Option 2: Using Command Prompt
1. Open Command Prompt (CMD)
2. Navigate to the bot directory:
   ```
   cd "C:\Users\jzeitler\Desktop\Stonk Bot"
   ```
3. Run the bot:
   ```
   python -W ignore main.py --single
   ```

## Console Output

The bot now has **clean, Windows-optimized console output** with:

- ✅ **No emoji rendering issues** - Uses ASCII symbols like `[OK]`, `[!]`, `[i]`
- ✅ **ANSI color support** - Beautiful colored output in Windows Command Prompt
- ✅ **Clean formatting** - No mojibake or weird characters
- ✅ **Suppressed warnings** - No yfinance spam

### Console Symbols Guide

| Symbol | Meaning |
|--------|---------|
| `[OK]` | Success / Completed |
| `[X]`  | Error / Failed |
| `[!]`  | Warning |
| `[i]`  | Information |
| `[*]`  | Highlight / Important |
| `[#]`  | Statistics / Data |
| `->` | Arrow / Direction |

## Running Modes

### Test Mode (Quick Check)
```
python main.py --test
```
Tests the embed structure without sending to Discord.

### Single Scan Mode
```
python main.py --single
```
Performs one scan and sends results to Discord.

### Continuous Mode
```
python main.py
```
Runs continuously according to the schedule in config.py.

## Troubleshooting

### Colors Not Showing
If colors don't display properly:
1. Use Windows Terminal instead of legacy CMD
2. Or run: `chcp 65001` before starting the bot (enables UTF-8)

### Python Not Found
Make sure Python is in your PATH:
```
python --version
```
Should show Python 3.8 or higher.

### Dependencies Missing
Install requirements:
```
pip install -r requirements.txt
```

## Tips for Best Experience

1. **Use Windows Terminal** (recommended over CMD)
   - Better font rendering
   - Full ANSI color support
   - Modern interface

2. **Resize Console** - Make it wide (100+ columns) for best formatting

3. **Check Discord Webhook** - Verify webhook URL in `config.py` is correct

## Need Help?

- Check the main `README.md` for general documentation
- Review `SETUP_GUIDE.md` for detailed configuration
- See `CHANGELOG.md` for recent updates
