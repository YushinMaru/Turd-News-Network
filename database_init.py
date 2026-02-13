"""
Database initialization and schema management
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from config import DB_PATH


class DatabaseInitializer:
    """Handles database schema initialization"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize comprehensive SQLite database with advanced tracking"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Table for tracking posted submissions
        c.execute('''CREATE TABLE IF NOT EXISTS posted_submissions
                     (post_id TEXT PRIMARY KEY,
                      subreddit TEXT,
                      title TEXT,
                      url TEXT,
                      author TEXT,
                      score INTEGER,
                      num_comments INTEGER,
                      upvote_ratio REAL,
                      posted_date TEXT,
                      scraped_date TEXT,
                      tickers TEXT,
                      post_length INTEGER,
                      flair TEXT,
                      quality_score REAL,
                      content_hash TEXT)''')
        
        # Enhanced stock tracking
        c.execute('''CREATE TABLE IF NOT EXISTS stock_tracking
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      post_id TEXT,
                      initial_price REAL,
                      initial_date TEXT,
                      current_price REAL,
                      last_updated TEXT,
                      price_change_pct REAL,
                      max_price REAL,
                      min_price REAL,
                      max_gain_pct REAL,
                      max_loss_pct REAL,
                      days_tracked INTEGER,
                      status TEXT,
                      alert_sent BOOLEAN DEFAULT 0,
                      reached_winner BOOLEAN DEFAULT 0,
                      reached_loser BOOLEAN DEFAULT 0,
                      time_to_peak_days INTEGER,
                      time_to_bottom_days INTEGER,
                      FOREIGN KEY(post_id) REFERENCES posted_submissions(post_id))''')
        
        # Stock metadata
        c.execute('''CREATE TABLE IF NOT EXISTS stock_metadata
                     (ticker TEXT PRIMARY KEY,
                      company_name TEXT,
                      sector TEXT,
                      industry TEXT,
                      market_cap REAL,
                      pe_ratio REAL,
                      forward_pe REAL,
                      peg_ratio REAL,
                      beta REAL,
                      dividend_yield REAL,
                      profit_margin REAL,
                      debt_to_equity REAL,
                      current_ratio REAL,
                      roe REAL,
                      revenue_growth REAL,
                      earnings_date TEXT,
                      analyst_rating TEXT,
                      price_target REAL,
                      short_interest REAL,
                      short_ratio REAL,
                      institutional_ownership REAL,
                      insider_ownership REAL,
                      last_updated TEXT)''')
        
        # Price history
        c.execute('''CREATE TABLE IF NOT EXISTS price_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      date TEXT,
                      open_price REAL,
                      high_price REAL,
                      low_price REAL,
                      close_price REAL,
                      volume INTEGER,
                      UNIQUE(ticker, date))''')
        
        # News and catalysts
        c.execute('''CREATE TABLE IF NOT EXISTS news_catalysts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      date TEXT,
                      headline TEXT,
                      source TEXT,
                      url TEXT,
                      sentiment TEXT,
                      importance INTEGER,
                      UNIQUE(ticker, headline, date))''')
        
        # Technical indicators
        c.execute('''CREATE TABLE IF NOT EXISTS technical_indicators
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      date TEXT,
                      rsi REAL,
                      macd REAL,
                      macd_signal REAL,
                      sma_20 REAL,
                      sma_50 REAL,
                      sma_200 REAL,
                      ema_12 REAL,
                      ema_26 REAL,
                      bollinger_upper REAL,
                      bollinger_lower REAL,
                      volume_ratio REAL,
                      UNIQUE(ticker, date))''')
        
        # Performance benchmarks
        c.execute('''CREATE TABLE IF NOT EXISTS performance_benchmarks
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      benchmark_date TEXT,
                      timeframe TEXT,
                      ticker_return REAL,
                      spy_return REAL,
                      sector_return REAL,
                      alpha REAL,
                      UNIQUE(ticker, benchmark_date, timeframe))''')
        
        # Duplicate detection
        c.execute('''CREATE TABLE IF NOT EXISTS duplicate_posts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      content_hash TEXT,
                      post_id TEXT,
                      ticker TEXT,
                      detected_date TEXT,
                      UNIQUE(content_hash, ticker))''')
        
        # Alert log - Enhanced with sentiment validation
        c.execute('''CREATE TABLE IF NOT EXISTS alert_log
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      alert_type TEXT,
                      alert_date TEXT,
                      trigger_value REAL,
                      price REAL,
                      confidence REAL,
                      sentiment_score REAL,
                      sentiment_confidence REAL,
                      news_count INTEGER DEFAULT 0,
                      reddit_count INTEGER DEFAULT 0,
                      validated BOOLEAN DEFAULT 0,
                      validation_method TEXT,
                      sent_to_discord BOOLEAN DEFAULT 0,
                      message TEXT,
                      details TEXT,
                      UNIQUE(ticker, alert_type, alert_date))''')
        
        # Performance history
        c.execute('''CREATE TABLE IF NOT EXISTS performance_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      post_id TEXT,
                      final_status TEXT,
                      peak_gain_pct REAL,
                      peak_loss_pct REAL,
                      days_to_peak INTEGER,
                      days_to_bottom INTEGER,
                      total_days_tracked INTEGER,
                      initial_price REAL,
                      final_price REAL,
                      quality_score REAL,
                      subreddit TEXT,
                      closed_date TEXT)''')
        
        # Insider transactions
        c.execute('''CREATE TABLE IF NOT EXISTS insider_transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      insider_name TEXT,
                      title TEXT,
                      transaction_type TEXT,
                      shares INTEGER,
                      value REAL,
                      transaction_date TEXT,
                      scraped_date TEXT,
                      UNIQUE(ticker, insider_name, transaction_date, transaction_type))''')

        # Congress trades
        c.execute('''CREATE TABLE IF NOT EXISTS congress_trades
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      politician_name TEXT,
                      party TEXT,
                      chamber TEXT,
                      transaction_type TEXT,
                      amount_range TEXT,
                      transaction_date TEXT,
                      disclosure_date TEXT,
                      scraped_date TEXT,
                      UNIQUE(ticker, politician_name, transaction_date, transaction_type))''')

        # ML predictions
        c.execute('''CREATE TABLE IF NOT EXISTS ml_predictions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      prediction_date TEXT,
                      predicted_direction TEXT,
                      confidence REAL,
                      features_used TEXT,
                      actual_direction TEXT,
                      actual_change_pct REAL,
                      resolved_date TEXT,
                      correct INTEGER,
                      UNIQUE(ticker, prediction_date))''')

        # Sentiment analysis - NEW TABLE
        c.execute('''CREATE TABLE IF NOT EXISTS sentiment_analysis
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      analysis_date TEXT,
                      sentiment TEXT,
                      confidence REAL,
                      score REAL,
                      model_used TEXT,
                      text_analyzed TEXT,
                      source TEXT,
                      UNIQUE(ticker, analysis_date))''')

        # Add enhanced technical indicator columns (safe for existing DBs)
        for col_def in [
            ('vwap', 'REAL'), ('adx', 'REAL'), ('plus_di', 'REAL'), ('minus_di', 'REAL'),
            ('ichimoku_tenkan', 'REAL'), ('ichimoku_kijun', 'REAL'),
            ('ichimoku_senkou_a', 'REAL'), ('ichimoku_senkou_b', 'REAL'),
            ('signal', 'TEXT'), ('signal_confidence', 'REAL'),
        ]:
            try:
                c.execute(f'ALTER TABLE technical_indicators ADD COLUMN {col_def[0]} {col_def[1]}')
            except sqlite3.OperationalError:
                pass  # Column already exists

        # Add enhanced alert log columns (safe for existing DBs)
        for col_def in [
            ('price', 'REAL'), ('confidence', 'REAL'), ('sentiment_score', 'REAL'),
            ('sentiment_confidence', 'REAL'), ('news_count', 'INTEGER DEFAULT 0'),
            ('reddit_count', 'INTEGER DEFAULT 0'), ('validated', 'BOOLEAN DEFAULT 0'),
            ('validation_method', 'TEXT'), ('sent_to_discord', 'BOOLEAN DEFAULT 0'),
            ('details', 'TEXT'),
        ]:
            try:
                c.execute(f'ALTER TABLE alert_log ADD COLUMN {col_def[0]} {col_def[1]}')
            except sqlite3.OperationalError:
                pass  # Column already exists

        # Discord Dashboard User Management
        c.execute('''CREATE TABLE IF NOT EXISTS dashboard_users
                     (user_id TEXT PRIMARY KEY,
                      username TEXT,
                      discriminator TEXT,
                      display_name TEXT,
                      is_admin BOOLEAN DEFAULT 0,
                      permissions TEXT,
                      created_date TEXT,
                      last_active TEXT,
                      settings TEXT)''')

        # Enhanced Watchlists with alert conditions
        c.execute('''CREATE TABLE IF NOT EXISTS user_watchlists
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id TEXT,
                      ticker TEXT,
                      added_date TEXT,
                      notes TEXT,
                      alert_enabled BOOLEAN DEFAULT 1,
                      alert_price_above REAL,
                      alert_price_below REAL,
                      alert_percent_change REAL,
                      alert_volume_spike BOOLEAN DEFAULT 0,
                      alert_congress_trades BOOLEAN DEFAULT 1,
                      alert_news BOOLEAN DEFAULT 1,
                      last_price REAL,
                      last_updated TEXT,
                      notification_count INTEGER DEFAULT 0,
                      FOREIGN KEY(user_id) REFERENCES dashboard_users(user_id),
                      UNIQUE(user_id, ticker))''')

        # Watchlist alert history
        c.execute('''CREATE TABLE IF NOT EXISTS watchlist_alerts
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id TEXT,
                      ticker TEXT,
                      alert_type TEXT,
                      alert_date TEXT,
                      trigger_price REAL,
                      trigger_condition TEXT,
                      message TEXT,
                      sent_to_discord BOOLEAN DEFAULT 0,
                      user_notified BOOLEAN DEFAULT 0,
                      acknowledged BOOLEAN DEFAULT 0,
                      FOREIGN KEY(user_id) REFERENCES dashboard_users(user_id))''')

        # User notification settings
        c.execute('''CREATE TABLE IF NOT EXISTS user_notification_settings
                     (user_id TEXT PRIMARY KEY,
                      dm_enabled BOOLEAN DEFAULT 1,
                      price_alerts BOOLEAN DEFAULT 1,
                      percent_change_alerts BOOLEAN DEFAULT 1,
                      volume_spike_alerts BOOLEAN DEFAULT 0,
                      congress_trade_alerts BOOLEAN DEFAULT 1,
                      news_alerts BOOLEAN DEFAULT 1,
                      alert_frequency TEXT DEFAULT 'immediate',
                      quiet_hours_start INTEGER DEFAULT 22,
                      quiet_hours_end INTEGER DEFAULT 7,
                      max_alerts_per_day INTEGER DEFAULT 50,
                      created_date TEXT,
                      updated_date TEXT,
                      FOREIGN KEY(user_id) REFERENCES dashboard_users(user_id))''')

        # Dashboard state
        c.execute('''CREATE TABLE IF NOT EXISTS dashboard_state
                     (channel_id TEXT PRIMARY KEY,
                      current_view TEXT DEFAULT 'overview',
                      current_ticker TEXT,
                      refresh_interval INTEGER DEFAULT 30,
                      last_refresh TEXT,
                      auto_refresh BOOLEAN DEFAULT 1,
                      pinned_message_id TEXT,
                      UNIQUE(channel_id))''')

        # Generated reports
        c.execute('''CREATE TABLE IF NOT EXISTS generated_reports
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      report_type TEXT,
                      ticker TEXT,
                      user_id TEXT,
                      channel_id TEXT,
                      file_path TEXT,
                      generated_date TEXT,
                      pages INTEGER,
                      file_size INTEGER,
                      FOREIGN KEY(user_id) REFERENCES dashboard_users(user_id))''')

        # Add watchlist columns (safe for existing DBs)
        for col_def in [
            ('alert_price_above', 'REAL'),
            ('alert_price_below', 'REAL'),
            ('alert_percent_change', 'REAL'),
            ('alert_volume_spike', 'BOOLEAN DEFAULT 0'),
            ('alert_congress_trades', 'BOOLEAN DEFAULT 1'),
            ('alert_news', 'BOOLEAN DEFAULT 1'),
            ('last_price', 'REAL'),
            ('last_updated', 'TEXT'),
            ('notification_count', 'INTEGER DEFAULT 0'),
        ]:
            try:
                c.execute(f'ALTER TABLE user_watchlists ADD COLUMN {col_def[0]} {col_def[1]}')
                print(f"[DB INIT] Added column {col_def[0]} to user_watchlists")
            except sqlite3.OperationalError:
                pass  # Column already exists

        # ML Prediction tracking - for learning from outcomes
        c.execute('''CREATE TABLE IF NOT EXISTS ml_prediction_outcomes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      prediction_date TEXT,
                      predicted_direction TEXT,
                      predicted_price REAL,
                      confidence REAL,
                      model_version TEXT,
                      features_used TEXT,
                      actual_direction TEXT,
                      actual_price REAL,
                      actual_return_pct REAL,
                      days_to_outcome INTEGER,
                      outcome_date TEXT,
                      accuracy_score REAL,
                      model_improved BOOLEAN DEFAULT 0,
                      UNIQUE(ticker, prediction_date, model_version))''')

        # A/B Testing for ML models
        c.execute('''CREATE TABLE IF NOT EXISTS ml_ab_tests
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      test_name TEXT,
                      model_a_version TEXT,
                      model_b_version TEXT,
                      start_date TEXT,
                      end_date TEXT,
                      total_predictions INTEGER DEFAULT 0,
                      model_a_correct INTEGER DEFAULT 0,
                      model_b_correct INTEGER DEFAULT 0,
                      winner TEXT,
                      status TEXT DEFAULT 'active')''')

        # Twitter/X sentiment data
        c.execute('''CREATE TABLE IF NOT EXISTS twitter_sentiment
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      tweet_date TEXT,
                      tweet_id TEXT,
                      tweet_text TEXT,
                      author TEXT,
                      followers INTEGER,
                      sentiment TEXT,
                      sentiment_score REAL,
                      confidence REAL,
                      likes INTEGER,
                      retweets INTEGER,
                      replies INTEGER,
                      is_verified BOOLEAN DEFAULT 0,
                      UNIQUE(ticker, tweet_id))''')

        # SEC EDGAR insider transactions (enhanced)
        c.execute('''CREATE TABLE IF NOT EXISTS sec_insider_filings
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      filing_date TEXT,
                      transaction_date TEXT,
                      insider_name TEXT,
                      insider_title TEXT,
                      transaction_type TEXT,
                      shares INTEGER,
                      price_per_share REAL,
                      total_value REAL,
                      shares_owned_after INTEGER,
                      form_type TEXT,
                      filing_url TEXT,
                      UNIQUE(ticker, insider_name, transaction_date, transaction_type))''')

        # Economic calendar events
        c.execute('''CREATE TABLE IF NOT EXISTS economic_calendar
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      event_date TEXT,
                      event_time TEXT,
                      country TEXT,
                      event_name TEXT,
                      impact_level TEXT,
                      forecast TEXT,
                      previous TEXT,
                      actual TEXT,
                      sentiment TEXT,
                      UNIQUE(event_date, event_name))''')

        # Options unusual activity tracking
        c.execute('''CREATE TABLE IF NOT EXISTS options_unusual_activity
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      detection_date TEXT,
                      expiry_date TEXT,
                      strike REAL,
                      option_type TEXT,
                      volume INTEGER,
                      open_interest INTEGER,
                      volume_oi_ratio REAL,
                      premium REAL,
                      sentiment TEXT,
                      alert_triggered BOOLEAN DEFAULT 0,
                      UNIQUE(ticker, detection_date, strike, option_type))''')

        # Price correlations between tickers
        c.execute('''CREATE TABLE IF NOT EXISTS ticker_correlations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker_a TEXT,
                      ticker_b TEXT,
                      correlation_coefficient REAL,
                      correlation_period TEXT,
                      calculation_date TEXT,
                      p_value REAL,
                      is_significant BOOLEAN DEFAULT 0,
                      UNIQUE(ticker_a, ticker_b, correlation_period))''')

        # Congress trading patterns
        c.execute('''CREATE TABLE IF NOT EXISTS congress_patterns
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      pattern_type TEXT,
                      pattern_description TEXT,
                      confidence_score REAL,
                      total_trades INTEGER,
                      avg_return_after INTEGER,
                      success_rate REAL,
                      detected_date TEXT,
                      last_updated TEXT)''')

        # ML Feature store - for technical indicators over time
        c.execute('''CREATE TABLE IF NOT EXISTS ml_feature_store
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      date TEXT,
                      rsi REAL,
                      macd REAL,
                      macd_signal REAL,
                      bollinger_upper REAL,
                      bollinger_lower REAL,
                      sma_20 REAL,
                      sma_50 REAL,
                      sma_200 REAL,
                      ema_12 REAL,
                      ema_26 REAL,
                      volume_ratio REAL,
                      adx REAL,
                      plus_di REAL,
                      minus_di REAL,
                      vwap REAL,
                      price_change_1d REAL,
                      price_change_5d REAL,
                      price_change_20d REAL,
                      target_direction TEXT,
                      target_return_5d REAL,
                      UNIQUE(ticker, date))''')

        # Invalid tickers cache - skip these in future scans
        c.execute('''CREATE TABLE IF NOT EXISTS invalid_tickers
                     (ticker TEXT PRIMARY KEY,
                      invalid_date TEXT,
                      reason TEXT)''')

        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON stock_tracking(ticker)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_post_date ON posted_submissions(posted_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ticker_date ON price_history(ticker, date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_status ON stock_tracking(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_performance ON performance_history(ticker, final_status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_user_watchlist ON user_watchlists(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_user_reports ON generated_reports(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ml_predictions ON ml_prediction_outcomes(ticker, prediction_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_twitter_sentiment ON twitter_sentiment(ticker, tweet_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_sec_insider ON sec_insider_filings(ticker, transaction_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_economic_calendar ON economic_calendar(event_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ml_features ON ml_feature_store(ticker, date)')
        
        conn.commit()
        conn.close()
