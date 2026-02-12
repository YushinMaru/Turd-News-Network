# Turd News Network Enhanced v4.0 - Setup Guide

## ðŸš€ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Configure Discord

#### Get Your Webhook URL:
1. Go to your Discord server
2. Server Settings â†’ Integrations â†’ Webhooks
3. Create New Webhook or edit existing
4. Copy the Webhook URL

#### Get Your Role ID:
1. Enable Developer Mode (User Settings â†’ Advanced â†’ Developer Mode)
2. Right-click the @Stonks role â†’ Copy ID
3. Format as: `<@&1234567890>` (replace with your role ID)

#### Update config.py:
```python
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE"
ALERT_ROLE_ID = "<@&YOUR_ROLE_ID_HERE>"
```

### 3. Run
```bash
python main.py
```

## âš™ï¸ Configuration

### Alert Settings
```python
# Only ping role for high-quality alerts
NEAR_52W_HIGH_PCT = 3.0  # Breakout alerts
EXTREME_VOLUME_THRESHOLD = 3.0  # Volume spike alerts
MIN_MOMENTUM_FOR_ALERT = 70  # Strong momentum only
RISK_REWARD_MIN_RATIO = 2.0  # Good R/R only
```

### Features
```python
ENABLE_AI_SUMMARY = True  # AI trading recommendations
ENABLE_DAILY_DIGEST = True  # Morning reports
ENABLE_ROLE_PING_ON_ALERTS = True  # @Stonks pings
```

## ðŸ“Š Features

### Compact Embeds
- 60% smaller than v3
- Horizontal layout
- Mobile-optimized

### Smart Alerts
- Only actionable alerts ping users
- Filtered for quality
- Types:
  - ðŸš¨ Breakout (within 3% of 52W high)
  - ðŸŽ¯ Bounce (within 3% of 52W low)
  - ðŸ“ 200 SMA test
  - ðŸ”¥ Extreme volume (3x+ average)

### AI Recommendations
After stats report, AI analyzes all stocks and gives:
- ðŸš€ STRONG BUYS (score 60+)
- âœ… BUYS (score 35-59)
- âš ï¸ AVOID (score < -40)

Scoring based on:
- Momentum (25%)
- Technical signals (20%)
- Risk/reward (20%)
- Backtest (15%)
- Risk profile (10%)
- Alerts (10%)
- Sentiment (10%)

## ðŸ”§ Troubleshooting

### No alerts pinging?
- Check `ENABLE_ROLE_PING_ON_ALERTS = True`
- Verify role ID format: `<@&1234567890>`
- Make sure bot has permissions

### Embeds too long?
```python
MAX_FIELDS_PER_STOCK = 10  # Reduce from 12
MAX_NEWS_ARTICLES = 2  # Reduce from 3
```

### Discord 400 errors?
- Reduce MAX_FIELDS_PER_STOCK
- Check total embed < 6000 chars

## ðŸ“ File Structure

```
wsb_monitor_clean/
â”œâ”€â”€ main.py                 # Main orchestrator
â”œâ”€â”€ config.py              # Configuration
â”œâ”€â”€ analysis.py            # Analysis & alerts
â”œâ”€â”€ discord_embed.py       # Embed builder
â”œâ”€â”€ stats_reporter.py      # Statistics
â”œâ”€â”€ ai_summary.py          # AI recommendations
â”œâ”€â”€ stock_data.py          # Data fetching
â”œâ”€â”€ database.py            # Database ops
â”œâ”€â”€ database_init.py       # Schema
â”œâ”€â”€ scraper.py             # Reddit scraping
â”œâ”€â”€ sentiment.py           # NLP analysis
â”œâ”€â”€ performance.py         # Tracking
â”œâ”€â”€ backtesting.py         # Historical analysis
â”œâ”€â”€ discord_sender.py      # Discord API
â”œâ”€â”€ requirements.txt       # Dependencies
â””â”€â”€ README.md              # Quick reference
```

## ðŸŽ¯ Testing

Test without spamming:
```python
# In config.py, temporarily set:
ENABLE_ROLE_PING_ON_ALERTS = False  # Test first!
RUN_TIMES = ["HH:MM"]  # Your current time + 1 min
```

Run once:
```bash
python main.py
```

Check Discord for output, then enable role pings.

## ðŸ’¡ Tips

1. **Start conservative** - Use default thresholds
2. **Monitor first week** - Adjust alert thresholds based on volume
3. **Mobile test** - Check Discord mobile app rendering
4. **Database backup** - Copy `wsb_tracker_enhanced.db` weekly

## ðŸ†˜ Support

- Check logs for errors
- Verify webhook URL is correct
- Test role ping manually in Discord first
- Ensure bot has "Mention Everyone" permission

---

**Version:** 4.0.0  
**Last Updated:** February 2026
