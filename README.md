# Turd News Network Enhanced v4.0

## Quick Setup

1. **Install Dependencies:**
```bash
pip install -r requirements.txt --break-system-packages
```

2. **Configure:**
- Edit `config.py`
- Set your `WEBHOOK_URL`
- Set your `ALERT_ROLE_ID` (format: `<@&1234567890>`)

3. **Run:**
```bash
python main.py
```

## Features

- ✅ Compact Discord embeds (60% smaller)
- ✅ Momentum scoring & price alerts
- ✅ AI trading recommendations
- ✅ Role pings for actionable alerts
- ✅ 3-year backtesting
- ✅ Sector analysis
- ✅ Daily digest reports

## Files

- `main.py` - Main orchestrator
- `config.py` - Configuration
- `analysis.py` - Analysis & scoring
- `discord_embed.py` - Embed builder
- `stats_reporter.py` - Statistics
- `stock_data.py` - Data fetching
- `database.py` - Database ops
- `scraper.py` - Reddit scraping
- `sentiment.py` - NLP sentiment
- `performance.py` - Performance tracking
- `backtesting.py` - Historical analysis

## Support

Check config.py for all customization options.
