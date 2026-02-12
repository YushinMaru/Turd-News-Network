# Stonk Bot - Implementation Roadmap

Each segment is designed to be completable in a single Claude Code session. Work top to bottom. Each segment lists the files it will touch and its dependencies.

---

## Segment 1: Sentiment Upgrade - FinBERT [COMPLETED]

**Goal**: Replace VADER with FinBERT (finance-tuned BERT) for dramatically better financial sentiment analysis.

**Files**: `sentiment.py`, `config.py`, `requirements.txt`

**Tasks**:
- [x] Add `transformers` and `torch` to requirements.txt
- [x] Add FinBERT model config to config.py (model name, device, batch size, fallback toggle)
- [x] Rewrite `SentimentAnalyzer` to load FinBERT (`ProsusAI/finbert`) on init
- [x] Keep VADER as fallback if FinBERT fails to load (e.g., insufficient RAM)
- [x] Add `ENABLE_FINBERT` toggle in config.py (default True, falls back to VADER if False or on error)
- [x] Update `analyze_post_sentiment()` to use FinBERT tokenizer+model
- [x] Update `analyze_comments_sentiment()` similarly
- [x] Ensure `get_sentiment_emoji()` still works with the same output format
- [x] Test that the rest of the pipeline (main.py, discord_embed.py) works without changes

**Notes**: FinBERT outputs `positive`, `negative`, `neutral` with confidence scores. Map these to the existing classification scheme (BULLISH, BEARISH, NEUTRAL, etc.). First run will download the model (~400MB).

**Setup required**: Run `pip install transformers torch` on the Windows machine. First run will auto-download the FinBERT model (~400MB). If torch is not installed or fails, VADER is used automatically.

---

## Segment 2: Chart Image Generation [COMPLETED]

**Goal**: Generate and attach price chart images to Discord embeds for visual context.

**Files**: `stock_data.py`, `discord_embed.py`, `discord_sender.py`, `config.py`, `requirements.txt`

**Tasks**:
- [x] Add `matplotlib` and `mplfinance` to requirements.txt
- [x] Add chart config to config.py (ENABLE_CHARTS, CHART_PERIOD, CHART_DIR, ENABLE_CHART_BOLLINGER)
- [x] Create `_generate_chart()` method in `stock_data.py` that:
  - Generates a candlestick chart with volume bars for the last 3 months
  - Overlays SMA 20/50/200 lines
  - Marks 52-week high (green) and low (red) as horizontal dashed lines
  - Saves to a temp PNG file in `charts/` subdirectory
  - Returns the file path
- [x] Update `discord_sender.py` to support sending embeds with file attachments
  - Added `send_embeds_with_files()` using multipart/form-data with `files[N]` keys
  - Embed references the image via `"image": {"url": "attachment://<filename>.png"}`
- [x] Update `discord_embed.py` to include the chart image reference in the embed
  - `send_discord_embed()` collects chart_path from stock_data, attaches to embed image field
  - Falls back to plain `send_embeds()` when no charts available
- [x] Clean up temp chart files after sending (deleted on success, stale files >1hr cleaned on generation)
- [x] Add Bollinger Bands overlay as optional (`ENABLE_CHART_BOLLINGER` config toggle)

**Notes**: Discord webhook file uploads have a 25MB limit. Charts will be ~50-200KB PNGs. Use `mplfinance` for clean financial charts with minimal code.

**Setup required**: Run `pip install matplotlib mplfinance` on the Windows machine. Charts are generated headlessly using the Agg backend (no GUI needed).

---

## Segment 3: Options Flow & Unusual Activity Detection [COMPLETED]

**Goal**: Detect unusual options activity and display it in embeds.

**Files**: `stock_data.py`, `discord_embed.py`, `analysis.py`, `config.py`, `main.py`

**Tasks**:
- [x] Add options data fetching to `stock_data.py` using yfinance `.options` and `.option_chain()`
  - Get current options chain (nearest expiry)
  - Calculate put/call ratio
  - Identify unusual volume strikes (volume > 5x open interest)
  - Get max pain price via `_calculate_max_pain()` method
- [x] Add `analyze_options_flow()` method to `analysis.py`
  - Classify as BULLISH_FLOW, BEARISH_FLOW, or NEUTRAL using point system
  - Detect large single-strike bets (volume > 1000 and ratio >= threshold)
  - Flag if put/call ratio is extreme (< 0.5 or > 1.5, configurable)
- [x] Add options summary field to `discord_embed.py`
  - `_build_options_compact()` with format: `P/C: 0.67 | Max Pain: $145 | Unusual: $150C 3.2x OI`
- [x] Add `ENABLE_OPTIONS_FLOW` toggle and threshold constants in config.py
- [x] Handle tickers that have no options data gracefully (returns None, skipped in embed)
- [x] Hooked into `main.py` process loop with console output

---

## Segment 4: Insider & Institutional Trading Data [COMPLETED]

**Goal**: Show recent insider buys/sells and institutional ownership changes.

**Files**: `stock_data.py`, `discord_embed.py`, `config.py`, `main.py`, `database.py`, `database_init.py`

**Tasks**:
- [x] Add insider data fetching to `stock_data.py` via `get_insider_data()`
  - Primary source: yfinance `insider_transactions` and `major_holders`
  - Parses transaction type (BUY/SELL/OTHER), filters by lookback window
  - Aggregates net insider buying/selling over configurable period (default 90 days)
- [x] Add Finnhub free tier integration for institutional ownership
  - Endpoint: `/stock/institutional-ownership` (optional, only if API key provided)
  - Used as supplement when yfinance doesn't have institutional % data
- [x] Add `FINNHUB_API_KEY` to config.py (empty string = disabled)
- [x] Add insider/institutional summary field to `discord_embed.py`
  - `_build_insider_compact()` format: `Insiders: 3 buys / 1 sell (90d)` + `Inst: 67.2% | Insider: 4.5%`
- [x] Add `ENABLE_INSIDER_DATA` toggle and `INSIDER_LOOKBACK_DAYS` to config.py
- [x] Store insider transaction data in new `insider_transactions` DB table
- [x] Added `save_insider_transactions()` to database.py
- [x] Hooked into main.py with console output and DB save

---

## Segment 5: Congress & Political Trading Tracker [COMPLETED]

**Goal**: Cross-reference mentioned tickers with recent Congressional stock trades.

**Files**: New `congress_tracker.py`, `discord_embed.py`, `config.py`, `database_init.py`, `database.py`, `main.py`

**Tasks**:
- [x] Create `congress_tracker.py` with `CongressTracker` class
  - Uses Finnhub free tier `/stock/congressional-trading` endpoint
  - Fetches recent Congress member trades (configurable lookback, default 60 days)
  - Caches results in DB to avoid repeated API calls (configurable cache TTL, default 12 hours)
  - Method: `check_congress_trades(ticker)` -> list of recent trades
  - Method: `format_for_embed(trades)` -> embed-ready dict with buy/sell counts
- [x] Add `congress_trades` table to `database_init.py`
  - Fields: politician_name, party, chamber, ticker, transaction_type, amount_range, transaction_date, disclosure_date, scraped_date
- [x] Add `save_congress_trades()`, `get_congress_trades()`, `get_congress_cache_age_hours()` to `database.py`
- [x] Add Congress trading field to `discord_embed.py`
  - `_build_congress_compact()` format: summary line + up to 2 individual trades
  - Only shows if there are matching trades
- [x] Add `ENABLE_CONGRESS_TRACKER`, `CONGRESS_LOOKBACK_DAYS`, `CONGRESS_CACHE_HOURS` to config.py
- [x] Integrated into `main.py` process_posts flow with console output

**Notes**: Uses Finnhub API (requires `FINNHUB_API_KEY` in config.py). Party information is not provided by Finnhub; chamber is inferred from position field when available. No additional pip dependencies required.

---

## Segment 6: Enhanced Technical Analysis & Signals [COMPLETED]

**Goal**: Add more technical indicators and generate clear buy/sell signals.

**Files**: `analysis.py`, `stock_data.py`, `discord_embed.py`, `config.py`, `database_init.py`, `database.py`, `main.py`

**Tasks**:
- [x] Add VWAP calculation to `stock_data.py`
  - 20-day rolling VWAP using typical price * volume
- [x] Add Fibonacci retracement levels to `analysis.py`
  - Uses 52-week high/low as swing points
  - Calculates 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100% levels
  - Identifies nearest level and distance percentage
- [x] Add ADX (Average Directional Index) to `stock_data.py` technical indicators
  - 14-period Wilder smoothing for +DI, -DI, and ADX
  - ADX > 25 = trending, ADX < 20 = ranging
- [x] Add Ichimoku Cloud components (Tenkan, Kijun, Senkou A/B)
  - Tenkan (9-period), Kijun (26-period), Senkou A (midpoint), Senkou B (52-period)
- [x] Create `generate_signal_summary()` in `analysis.py`
  - Combines RSI (weight 2), MACD (weight 2), MA alignment (weight 2), 200 SMA (weight 1), Bollinger (weight 1), ADX+DI (weight 2), Ichimoku (weight 2), VWAP (weight 1) into BUY/SELL/HOLD
  - Net score >= 3 = BUY, <= -3 = SELL, else HOLD
  - Confidence = abs(net) / max_possible as percentage
- [x] Add signal summary field to embed via `_build_signal_summary_compact()`
  - Shows signal + confidence + top 3 reasons + ADX/Cloud/VWAP/Fib summary
  - Appears between Risk/Technicals and Options Flow sections
- [x] Store signals in `technical_indicators` table
  - Added columns: vwap, adx, plus_di, minus_di, ichimoku_tenkan, ichimoku_kijun, ichimoku_senkou_a, ichimoku_senkou_b, signal, signal_confidence

**Notes**: All indicators are calculated from existing yfinance historical data. No additional API calls or dependencies required. Config toggle: `ENABLE_ENHANCED_TECHNICALS`.

---

## Segment 7: ML Price Prediction Model [COMPLETED]

**Goal**: Train a simple ML model to predict short-term price direction based on historical patterns.

**Files**: New `ml_predictor.py`, `config.py`, `requirements.txt`, `discord_embed.py`, `main.py`, `database_init.py`, `database.py`

**Tasks**:
- [x] Add `scikit-learn>=1.3.0` and `joblib>=1.3.0` to requirements.txt
- [x] Create `ml_predictor.py` with `PricePredictor` class
  - Feature engineering: RSI, MACD, volume ratio, ADX, price vs SMA 20/50/200 ratios, Bollinger Band position, price vs VWAP
  - Random Forest classifier (100 trees, max_depth=8): UP/DOWN/FLAT over 5 trading days
  - Training data from stock_tracking joined with technical_indicators (entries with 5+ days tracked)
  - Graceful fallback: disables if scikit-learn not installed
  - predict() returns {direction, confidence, features_used, prediction_days, probabilities}
- [x] Add `ENABLE_ML_PREDICTION` toggle and config constants in config.py
  - ML_MODEL_PATH, ML_MIN_TRAINING_SAMPLES (30), ML_PREDICTION_DAYS (5), ML_RETRAIN_DAYS (7)
  - ML_UP_THRESHOLD (3%), ML_DOWN_THRESHOLD (-3%)
- [x] Add training schedule: retrain model every 7 days (checks via DB prediction date)
- [x] Save trained model to disk via joblib (ml_model.joblib)
- [x] Add ML prediction field to `discord_embed.py`
  - _build_ml_prediction_compact() shows direction, confidence, class probabilities, features used
  - Includes "Experimental - not financial advice" disclaimer
- [x] Integrate into `main.py` flow (import, init, predict in process loop, console output)
- [x] Add `ml_predictions` table to track prediction accuracy over time
  - Columns: ticker, prediction_date, predicted_direction, confidence, features_used, actual_direction, actual_change_pct, resolved_date, correct

**Notes**: Model only activates after accumulating ML_MIN_TRAINING_SAMPLES (30) tracked stocks with 5+ days of data. Predictions appear in the embed between Signal Summary and Options Flow.

---

## Segment 8: Paper Trading Simulator

**Goal**: Simulate trades based on bot recommendations to track hypothetical P&L.

**Files**: New `paper_trader.py`, `discord_embed.py`, `stats_reporter.py`, `config.py`, `database_init.py`

**Tasks**:
- [ ] Create `paper_trader.py` with `PaperTrader` class
  - Virtual portfolio with configurable starting balance (default $100K)
  - Auto-enter positions when quality score >= PREMIUM_DD_SCORE and sentiment is BULLISH
  - Position sizing: equal weight or Kelly criterion
  - Auto-exit on: winner threshold hit, loser threshold hit, or 30-day timeout
  - Track: entry price, exit price, P&L, holding period, win rate
- [ ] Add `paper_trades` and `paper_portfolio` tables to `database_init.py`
- [ ] Add paper trading summary to `stats_reporter.py` dashboard
  - Portfolio value, total P&L, win rate, best/worst trade, Sharpe ratio
- [ ] Add `ENABLE_PAPER_TRADING` toggle and `PAPER_STARTING_BALANCE` to config.py
- [ ] Integrate into `main.py` and `performance.py`
- [ ] Add weekly paper trading report embed

---

## Segment 9: Multi-Source News Aggregation

**Goal**: Aggregate news from multiple free sources beyond Yahoo Finance.

**Files**: `stock_data.py`, `discord_embed.py`, `config.py`

**Tasks**:
- [ ] Add Finnhub news endpoint integration (free tier: 60 calls/min)
- [ ] Add Google News RSS scraping as backup source
- [ ] Add SEC EDGAR filing detection (10-K, 10-Q, 8-K filings)
  - Flag if a company filed something in the last 7 days
- [ ] Deduplicate news across sources (fuzzy title matching)
- [ ] Add news sentiment scoring per headline (using FinBERT from Segment 1)
- [ ] Improve news display in embed:
  - Show source credibility badge (Reuters > Bloomberg > CNBC > etc.)
  - Color-code by sentiment (green/red/yellow)
  - Format: `[Reuters] Company beats earnings +12% | Bullish`
- [ ] Add `ENABLE_MULTI_SOURCE_NEWS` toggle in config.py

**Dependencies**: Segment 1 (FinBERT) recommended but not required.

---

## Segment 10: Earnings Calendar & Event Detection

**Goal**: Show upcoming earnings dates, ex-dividend dates, and other catalysts.

**Files**: `stock_data.py`, `discord_embed.py`, `analysis.py`, `config.py`

**Tasks**:
- [ ] Extract earnings date from yfinance `.info['earningsDate']` (already partially in stock_metadata)
- [ ] Add earnings countdown to embed: `Earnings in 5 days (Feb 12 AMC)`
- [ ] Add ex-dividend date detection and display
- [ ] Add stock split detection
- [ ] Create `detect_upcoming_catalysts()` in `analysis.py`
  - Combine earnings, dividends, splits, FDA dates (biotech), known events
  - Return list of upcoming catalysts with dates
- [ ] Add catalyst countdown field to `discord_embed.py`
  - Format: `Catalysts: Earnings Feb 12 (5d) | Ex-Div Mar 1 (22d)`
- [ ] Flag high-risk earnings plays in the risk assessment
- [ ] Add `ENABLE_CATALYST_DETECTION` toggle in config.py

---

## Segment 11: Sector Rotation & Market Breadth

**Goal**: Track sector performance trends and market-wide breadth indicators.

**Files**: `stats_reporter.py`, `stock_data.py`, `config.py`, `database_init.py`

**Tasks**:
- [ ] Create sector ETF tracking (XLK, XLF, XLE, XLV, XLI, XLC, XLY, XLP, XLU, XLRE, XLB)
  - Fetch daily returns for all sector ETFs
  - Calculate 1W, 1M, 3M sector performance
  - Identify rotating sectors (money flowing in/out)
- [ ] Add market breadth indicators:
  - Advance/decline ratio (use SPY components or approximate)
  - % of S&P 500 above 200 SMA (approximate via sector ETFs)
  - VIX level and trend (fetch ^VIX via yfinance)
- [ ] Add sector rotation heatmap to stats dashboard embed
  - Use colored squares or bars to show sector performance
- [ ] Add market breadth summary to dashboard header
  - Format: `Market: VIX 15.2 (-3%) | Breadth: 67% > 200SMA | Sectors: Tech leading, Energy lagging`
- [ ] Store sector data in new `sector_performance` table
- [ ] Add `ENABLE_SECTOR_ROTATION` toggle in config.py

---

## Segment 12: Short Interest & Squeeze Detection

**Goal**: Track short interest data and identify potential squeeze setups.

**Files**: `stock_data.py`, `analysis.py`, `discord_embed.py`, `config.py`

**Tasks**:
- [ ] Enhance short interest data collection in `stock_data.py`
  - yfinance provides `shortRatio` and `shortPercentOfFloat`
  - Add Finnhub short interest endpoint as supplementary source
- [ ] Create `detect_squeeze_setup()` in `analysis.py`
  - Criteria: short interest > 20%, days to cover > 5, rising price, increasing volume
  - Score the squeeze probability (0-100)
  - Detect gamma squeeze potential (high call OI near current price)
- [ ] Add squeeze indicator to embed
  - Format: `Short: 34.2% float | DTC: 7.3 | Squeeze Score: 82/100`
- [ ] Add squeeze alert type to price alerts system
- [ ] Add `ENABLE_SQUEEZE_DETECTION` toggle in config.py

**Dependencies**: Segment 3 (Options Flow) recommended for gamma squeeze detection.

---

## Segment 13: Correlation & Portfolio Risk Analysis

**Goal**: Show how a mentioned stock correlates with what the bot has already tracked.

**Files**: `analysis.py`, `stats_reporter.py`, `discord_embed.py`, `config.py`

**Tasks**:
- [ ] Add `calculate_correlation()` to `analysis.py`
  - Calculate 90-day Pearson correlation between ticker and SPY, QQQ, and sector ETF
  - Calculate beta relative to S&P 500
- [ ] Add correlation matrix for tracked portfolio in `stats_reporter.py`
  - Show if tracked stocks are all highly correlated (concentrated risk)
  - Diversification score for the bot's tracked universe
- [ ] Add correlation info to individual stock embed
  - Format: `Correlation: SPY 0.82 | QQQ 0.91 | Sector 0.76 | Beta: 1.34`
- [ ] Add portfolio risk summary to dashboard
  - Overall portfolio beta, correlation clustering, sector concentration
- [ ] Add `ENABLE_CORRELATION_ANALYSIS` toggle in config.py

---

## Segment 14: Alert System Overhaul

**Goal**: More granular, configurable alerts with separate Discord channels/threads.

**Files**: `main.py`, `discord_sender.py`, `config.py`, `analysis.py`

**Tasks**:
- [ ] Add `ALERT_WEBHOOK_URL` to config.py (separate webhook for alerts vs regular posts)
- [ ] Create alert priority levels: INFO, WARNING, ACTIONABLE, CRITICAL
- [ ] Add alert deduplication: don't send the same alert type for the same ticker within 24h
- [ ] Add configurable alert rules in config.py:
  - Volume spike threshold
  - Price move threshold (% change in 1 day)
  - RSI extreme thresholds
  - Momentum reversal detection
- [ ] Add alert summary embed: batch all alerts from a scan into one embed
- [ ] Add Discord thread creation for high-priority alerts (using Discord API)
- [ ] Track alert accuracy over time (was the alert followed by a significant move?)

---

## Segment 15: Historical Accuracy Tracking & Leaderboard

**Goal**: Track the bot's prediction/alert accuracy over time and display it.

**Files**: `performance.py`, `stats_reporter.py`, `database_init.py`, `discord_embed.py`

**Tasks**:
- [ ] Add accuracy tracking to `performance.py`
  - For each posted stock: was it ultimately a winner or loser?
  - Track by source subreddit, quality score tier, sentiment classification
  - Calculate: overall accuracy, accuracy by subreddit, accuracy by quality tier
- [ ] Add `prediction_accuracy` table to database
- [ ] Add accuracy stats to the performance dashboard
  - Format: `Bot Accuracy: 62% winners | WSB: 58% | ValueInvesting: 71% | Premium DD: 74%`
- [ ] Add monthly accuracy report embed
- [ ] Add "Subreddit Leaderboard" to stats dashboard
  - Rank subreddits by their stock pick accuracy
- [ ] Use accuracy data to weight future quality scores (subreddits with better track records get score boosts)

---

## Segment 16: Discord Embed Polish & UX [COMPLETED]

**Goal**: Visual improvements to embeds for better readability.

**Files**: `discord_embed.py`

**Tasks**:
- [x] Add dynamic embed color based on overall analysis
  - _determine_embed_color() checks signal summary first (BUY/SELL + confidence threshold)
  - Falls back to sentiment (BULLISH/BEARISH)
  - Then quality tier (gold for premium, green for quality, blue for standard)
  - High-confidence BUY = dark green, high-confidence SELL = dark red
- [x] Add thumbnail images (Clearbit Logo API)
  - _get_logo_thumbnail() extracts domain from stock_data['website'] field
  - Sets embed thumbnail to `https://logo.clearbit.com/{domain}`
- [x] Add footer with timestamp and bot version
  - Already had timestamp + version; updated to v5.0
- [x] Improve field layout: Quick Stats replaces old stock header with dense one-liner
- [x] Add sparkline-style text charts for price trends (Unicode block characters)
  - _build_sparkline() uses Unicode blocks: \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588
  - Renders in Performance Timeline field below the percentage values
- [x] Add "Quick Stats" one-liner at top of each stock section
  - Format: `$AAPL Name | $182.50 +2.3% | MC: $2.8T | P/E: 28.4 | RSI: 62`
  - Replaces old separate stock header field; includes sector/industry on second line
- [x] Review and compress all field values to maximize information density
  - Quick Stats consolidates ticker, price, change, mcap, P/E, RSI into one field
  - Sparklines add visual density without extra embed fields

---

## Segment 17: Rate Limiting & Resilience

**Goal**: Proper rate limiting, retry logic, and graceful degradation.

**Files**: `stock_data.py`, `scraper.py`, `discord_sender.py`, `config.py`

**Tasks**:
- [ ] Add exponential backoff retry decorator for all API calls
- [ ] Add proper Discord rate limit handling (read `X-RateLimit-*` headers, sleep accordingly)
- [ ] Add circuit breaker pattern: if an API fails N times in a row, disable it for a cooldown period
- [ ] Add request timeout configuration for all HTTP calls
- [ ] Add graceful degradation: if yfinance is down, still post what we have (sentiment, Reddit data)
- [ ] Add health check endpoint logging (track API success rates over time)
- [ ] Handle yfinance "Too Many Requests" by implementing adaptive delay between calls

---

## Segment 18: Monte Carlo & Risk Projections

**Goal**: Run Monte Carlo simulations to project potential price ranges.

**Files**: New `monte_carlo.py`, `discord_embed.py`, `config.py`, `requirements.txt`

**Tasks**:
- [ ] Create `monte_carlo.py` with `MonteCarloSimulator` class
  - Use historical daily returns to model return distribution
  - Run 10,000 simulations for 30-day forward projection
  - Calculate: median price, 10th/90th percentile range, probability of profit
  - Use geometric Brownian motion with historical volatility
- [ ] Add Monte Carlo projection field to embed
  - Format: `30d Projection: $145-$172 (80% CI) | P(profit): 64% | Median: $158`
- [ ] Add `ENABLE_MONTE_CARLO` toggle in config.py
- [ ] Add configurable simulation parameters (num simulations, time horizon, confidence interval)
- [ ] Generate a simple text-based probability distribution for the embed

**Dependencies**: numpy (already in requirements.txt).

---

## Segment 19: Watchlist & User Interaction

**Goal**: Allow Discord users to add tickers to a watchlist for automatic monitoring.

**Files**: New `watchlist.py`, `discord_sender.py`, `main.py`, `config.py`, `database_init.py`

**Tasks**:
- [ ] Create `watchlist.py` with `WatchlistManager` class
  - Store watchlist tickers in a new `watchlist` DB table
  - Methods: `add_ticker()`, `remove_ticker()`, `get_watchlist()`, `check_alerts()`
- [ ] Add watchlist scanning to `main.py` run cycle
  - On each scan, also check watchlist tickers for significant moves
  - Send alerts for watchlist tickers that hit price targets or volume spikes
- [ ] Add a simple input mechanism:
  - Read from a `watchlist.txt` file in the project directory (one ticker per line)
  - Scan this file on each run cycle
- [ ] Add watchlist summary to the daily digest
- [ ] Add `ENABLE_WATCHLIST` toggle in config.py

**Notes**: Full Discord bot interaction (slash commands) would require migrating from webhooks to a Discord bot with `discord.py`. This segment uses a file-based approach to keep it simple. A future segment could add the bot migration.

---

## Segment 20: Performance & Optimization

**Goal**: Optimize the bot for speed and reduce API call waste.

**Files**: `main.py`, `stock_data.py`, `database.py`, `config.py`

**Tasks**:
- [ ] Add concurrent stock data fetching using `concurrent.futures.ThreadPoolExecutor`
  - Fetch multiple tickers in parallel (respect API rate limits with semaphore)
- [ ] Add database connection pooling
- [ ] Cache stock metadata in memory (refresh every 24h instead of every scan)
- [ ] Add scan duration logging and performance metrics
- [ ] Reduce redundant yfinance calls (batch where possible)
- [ ] Add incremental processing: skip tickers already processed in the last N hours
- [ ] Profile and optimize the slowest operations

---

## Segment 21: Logging & Monitoring Overhaul

**Goal**: Replace print statements with proper logging framework.

**Files**: All Python files, new `logging_config.py`

**Tasks**:
- [ ] Create `logging_config.py` with centralized logging setup
  - Console handler (with colors for Windows Terminal)
  - File handler (rotating log files, max 10MB, keep 5 backups)
  - Different log levels: DEBUG for detailed data, INFO for flow, WARNING for issues, ERROR for failures
- [ ] Replace all `print()` calls across the codebase with appropriate `logger.info/warning/error` calls
- [ ] Add structured logging for key events (JSON format for machine parsing)
- [ ] Add scan summary logging: tickers processed, embeds sent, errors encountered, duration
- [ ] Add Discord send logging with payload sizes
- [ ] Add `LOG_LEVEL` and `LOG_FILE` to config.py

---

## Segment 22: Discord Bot Migration (Advanced)

**Goal**: Migrate from webhook-only to a proper Discord bot with slash commands.

**Files**: New `bot.py`, `discord_sender.py`, `config.py`, `requirements.txt`

**Tasks**:
- [ ] Add `discord.py` to requirements.txt
- [ ] Create `bot.py` with Discord bot setup
  - Slash commands: `/watchlist add AAPL`, `/watchlist remove AAPL`, `/analyze AAPL`, `/stats`
  - `/scan` command to trigger an immediate scan
  - `/alert set AAPL > 150` for custom price alerts
- [ ] Migrate embed sending to use bot channels instead of webhooks
- [ ] Keep webhook as fallback option (config toggle)
- [ ] Add `DISCORD_BOT_TOKEN` to config.py
- [ ] Add role-based permissions (admin commands vs user commands)

**Notes**: This is a significant architectural change. The webhook approach still works and should be kept as an option. This segment is optional and only for users who want interactive features.
