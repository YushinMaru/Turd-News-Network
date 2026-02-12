# Claude Code - Stonk Bot Project Context

## Environment

- **Runtime OS**: Windows 11, run via Command Prompt (`python main.py`)
- **Claude Code OS**: WSL (Ubuntu) on Windows 11
- **WSL project path**: `/mnt/c/Users/jzeitler/Desktop/Stonk Bot/`
- **Windows project path**: `C:\Users\jzeitler\Desktop\Stonk Bot\`
- **Python version**: 3.13+ (Windows native install)
- **Database**: SQLite (`wsb_tracker_enhanced.db`) in project root, WAL mode, timeout=30s
- **No virtual environment**: packages installed globally via `pip install`

## Rules

1. **ASK USER BEFORE EVERY ACTION.** At every single step, ask the user a multiple choice question before proceeding. No exceptions. Do not assume, do not proceed without confirmation.
2. **No mock data or placeholder code.** All data must come from real, free APIs. Never stub out functionality.
3. **No TODO/FIXME/HACK comments in code.** If something needs doing, do it or skip it. The `todo.md` file is the single source of truth for planned work.
3. **No paid APIs.** All data sources must have a usable free tier (yfinance, Finnhub free, Alpha Vantage free, SEC EDGAR, etc.).
4. **Preserve emoji encoding.** Files use UTF-8. Never let the Edit tool introduce mojibake. If replacing emoji-containing lines, verify the result. Past sessions required byte-level Python scripts to fix multi-level UTF-8/Windows-1252 mojibake.
5. **Test syntax after edits.** Run `python -c "import py_compile; py_compile.compile('filename.py', doraise=True)"` after editing any Python file.
6. **Discord embed limits.** Title: 256 chars, field name: 256, field value: 1024, description: 4096, total per embed: 6000, max 25 fields, max 10 embeds per message. Empty field values cause HTTP 400.
7. **Don't touch backup files.** Files ending in `.backup`, `_fixed.py`, `_restore.py`, and `fix_*.py` are historical artifacts. Never import them or modify them.
8. **Respect rate limits.** Reddit JSON API, yfinance, and Discord webhooks all have rate limits. Use the delay constants in config.py.
9. **Keep embeds compact.** The bot uses a horizontal/compact embed layout. Don't make embeds verbose or add unnecessary fields.
10. **Windows Command Prompt output.** Console prints must work in Windows cmd.exe. Emoji in print statements are fine (Windows Terminal supports them), but avoid ANSI escape codes unless wrapped in a compatibility check.

## Project Structure

### Active Source Files (imported and used)

| File | Class/Purpose |
|------|---------------|
| `main.py` | `TurdNewsNetworkEnhanced` - Main orchestrator. Entry point. Modes: `--test`, `--single`, scheduled. |
| `config.py` | All constants: webhook URL, thresholds, feature flags, colors, subreddit list, ignore tickers. |
| `scraper.py` | `RedditScraper` - Scrapes Reddit JSON API, extracts tickers via regex, deduplicates by content hash. |
| `stock_data.py` | `StockDataFetcher` - yfinance data, multi-exchange ticker validation, technical indicators, news. |
| `analysis.py` | `AnalysisEngine` - Risk assessment, valuation, technical summary, momentum score, price alerts, quality score. |
| `sentiment.py` | `SentimentAnalyzer` - VADER-based sentiment on post title+body and comments. |
| `ai_summary.py` | `AISummaryGenerator` - Rule-based trading recommendations (not actual AI/LLM). |
| `backtesting.py` | `EnhancedBacktester` - Historical backtesting with benchmark comparison. |
| `database.py` | `DatabaseManager` - All SQLite CRUD operations, retry logic for locked DB. |
| `database_init.py` | `DatabaseInitializer` - Schema creation for all tables. |
| `discord_embed.py` | `DiscordEmbedBuilder` - Builds compact horizontal embeds with sentiment banner. |
| `discord_sender.py` | `DiscordSender` - Webhook posting with embed sanitization and chunking. |
| `stats_reporter.py` | `StatsReporter` - Performance dashboard, leaderboards, sector analysis, daily digest. |
| `performance.py` | `PerformanceTracker` - Updates stock prices, tracks winners/losers, generates console reports. |
| `congress_tracker.py` | `CongressTracker` - Fetches Congressional stock trades via Finnhub API, caches in DB. |
| `ml_predictor.py` | `PricePredictor` - ML price direction predictions using Random Forest on technical indicators. |
| `console_formatter.py` | Console output formatting utilities. |

### Support Files

| File | Purpose |
|------|---------|
| `requirements.txt` | pip dependencies |
| `run_bot.bat` | Windows batch launcher |
| `wsb_tracker_enhanced.db` | SQLite database (auto-created) |
| `bot_output.log` | Runtime log |
| `single_scan.log` | Single scan mode log |

### Backup/Legacy Files (DO NOT MODIFY OR IMPORT)

- `discord_embed.py.backup`, `discord_embed_fixed.py`, `discord_embed_restore.py`
- `discord_sender.py.backup`, `discord_sender_fixed.py`
- `fix_all_emojis.py`, `fix_encoding.py`, `fix_encoding_final.py`, `fix_encoding_v2.py`

## Architecture / Data Flow

```
main.py: process_posts()
  |
  +-> scraper.py: scrape subreddits -> extract tickers -> content hash dedup
  |
  +-> sentiment.py: analyze post sentiment (VADER)
  |
  +-> analysis.py: quality score -> filter low quality
  |
  +-> For each ticker:
  |     +-> stock_data.py: validate ticker -> fetch price/fundamentals/technicals/news
  |     +-> backtesting.py: historical backtest vs SPY
  |     +-> congress_tracker.py: check for Congressional trades on ticker
  |     +-> analysis.py: momentum score, price alerts, risk/reward, signal summary, fibonacci
  |     +-> ml_predictor.py: ML price direction prediction (RF classifier)
  |     +-> discord_embed.py: build compact embed with signal summary, ML prediction, logo thumbnail
  |     +-> discord_sender.py: post to Discord webhook
  |     +-> database.py: save all data
  |     +-> performance.py: update tracking
  |
  +-> stats_reporter.py: performance dashboard (if enough data)
  +-> stats_reporter.py: daily digest (at scheduled time)
```

## Database Schema

**Tables**: `posted_submissions`, `stock_tracking`, `stock_metadata`, `price_history`, `technical_indicators`, `news_catalysts`, `alert_log`, `duplicate_posts`, `performance_benchmarks`, `performance_history`, `insider_transactions`, `congress_trades`, `ml_predictions`

**Key indexes**: `idx_ticker`, `idx_post_date`, `idx_ticker_date`, `idx_status`, `idx_performance`

See `database_init.py` for full schema definitions.

## Config Quick Reference

| Setting | Value | Notes |
|---------|-------|-------|
| `WINNER_THRESHOLD` | 20% | Stock is a "winner" |
| `LOSER_THRESHOLD` | -20% | Stock is a "loser" |
| `HIGH_VOLUME_THRESHOLD` | 1.5x | Unusual volume flag |
| `EXTREME_VOLUME_THRESHOLD` | 3.0x | Alert trigger |
| `NEAR_52W_HIGH_PCT` | 3% | 52-week high proximity alert |
| `NEAR_52W_LOW_PCT` | 3% | 52-week low proximity alert |
| `RISK_REWARD_MIN_RATIO` | 2.0 | Minimum R/R for alerts |
| `RUN_TIMES` | 06:00, 12:00, 18:00, 00:00 | Scheduled scan times |
| `DAILY_DIGEST_TIME` | 08:00 | Daily digest send time |
| `ENABLE_CONGRESS_TRACKER` | True | Cross-reference tickers with Congressional trades |
| `CONGRESS_LOOKBACK_DAYS` | 60 | Congress trade lookback window |
| `CONGRESS_CACHE_HOURS` | 12 | Cache TTL for Congress data fetches |
| `ENABLE_ENHANCED_TECHNICALS` | True | Calculate VWAP, ADX, Ichimoku, Fib and unified signal |
| `ADX_TRENDING_THRESHOLD` | 25 | ADX above this = trending market |
| `ADX_RANGING_THRESHOLD` | 20 | ADX below this = ranging/choppy market |
| `FIBONACCI_LOOKBACK_DAYS` | 60 | Swing high/low lookback for Fibonacci levels |
| `ENABLE_ML_PREDICTION` | True | ML-based price direction predictions |
| `ML_MIN_TRAINING_SAMPLES` | 30 | Min DB rows before training activates |
| `ML_PREDICTION_DAYS` | 5 | Predict price direction N trading days ahead |
| `ML_RETRAIN_DAYS` | 7 | Retrain model every N days |
| `ENABLE_CHARTS` | True | Attach candlestick chart PNGs to embeds |
| `ENABLE_CHART_BOLLINGER` | True | Overlay Bollinger Bands on charts |
| `ENABLE_FINBERT` | True | Use FinBERT for sentiment (falls back to VADER) |
| `ENABLE_OPTIONS_FLOW` | True | Fetch and display unusual options activity |
| `ENABLE_INSIDER_DATA` | True | Fetch insider transactions and institutional ownership |
| `DUPLICATE_DETECTION_HOURS` | 48 | Dedup window |

## Current Dependencies (requirements.txt)

```
requests>=2.31.0
yfinance>=0.2.36
beautifulsoup4>=4.12.0
vaderSentiment>=3.3.2
numpy>=1.24.0
pandas>=2.0.0
lxml>=4.9.0
transformers>=4.30.0
torch>=2.0.0
matplotlib>=3.7.0
mplfinance>=0.12.9b7
scikit-learn>=1.3.0
joblib>=1.3.0
```

## Known Patterns and Conventions

- **Feature flags**: All major features have `ENABLE_*` toggles in config.py. Check before adding new features.
- **Ticker validation**: `stock_data.py` tries 9 international exchange suffixes before giving up. Invalid tickers are cached to avoid repeat lookups.
- **Embed sanitization**: `discord_sender.py` strips empty fields and enforces Discord limits as a safety net. Always guard against empty field values at the source too.
- **Error printing**: Use emoji prefixes in console output: `[i]` info, warning uses the warning emoji, error uses the X emoji. These print to Windows cmd.
- **IGNORE_TICKERS**: Large set in config.py to filter Reddit abbreviations (DOJ, FAQ, YOLO, etc.) from being treated as stock symbols.
- **Compact embed layout**: Fields use `inline: True` for horizontal layout. The sentiment banner at the bottom uses `inline: False`.

## Past Issues and Fixes (Reference)

1. **Mojibake**: Multi-level UTF-8/Windows-1252 encoding corruption across 9 files. Fixed with byte-level Python scripts. If emoji look garbled again, use the same approach (open in binary mode, match hex patterns, replace).
2. **Discord 400 errors**: Caused by empty field values from `"\n".join([])`. Fixed with guards and sanitization layer.
3. **False positive tickers**: Common abbreviations extracted as tickers. Fixed by expanding IGNORE_TICKERS.
4. **HTTP 404 for invalid tickers**: Fixed with pre-validation and stderr suppression in stock_data.py.
5. **Duplicate dashboard posting**: `generate_daily_digest_embed()` was calling `generate_performance_embed()`. Fixed to only include header + most-mentioned.
6. **KeyError 'emoji' in momentum**: Early returns in `calculate_momentum_score()` were missing the `'emoji'` key. Fixed by adding it to all return paths.
