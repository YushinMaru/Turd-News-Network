"""
Database operations and queries
FIXED: Database locking issues with timeout and WAL mode
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import DB_PATH
from database_init import DatabaseInitializer


class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.initializer = DatabaseInitializer(db_path)
        self.initializer.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with timeout to prevent locking"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable Write-Ahead Logging
        return conn
    
    def is_post_already_sent(self, post_id: str) -> bool:
        """Check if post was already sent to Discord"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT post_id FROM posted_submissions WHERE post_id = ?", (post_id,))
        result = c.fetchone()
        conn.close()
        return result is not None
    
    def save_post(self, post: Dict, tickers: List[str], quality_score: float, content_hash: str):
        """Save posted submission to database"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''INSERT OR IGNORE INTO posted_submissions 
                     (post_id, subreddit, title, url, author, score, num_comments, 
                      upvote_ratio, posted_date, scraped_date, tickers, post_length, 
                      flair, quality_score, content_hash)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (post['id'], post['subreddit'], post['title'], post['url'],
                   post.get('author', 'Unknown'), post.get('score', 0),
                   post.get('num_comments', 0), post.get('upvote_ratio', 0),
                   post.get('created_utc', datetime.now().isoformat()),
                   datetime.now().isoformat(), ','.join(tickers),
                   post.get('post_length', 0), post.get('flair', ''),
                   quality_score, content_hash))
        
        conn.commit()
        conn.close()
    
    def save_stock_tracking(self, ticker: str, post_id: str, initial_price: float):
        """Save initial stock data for tracking"""
        # Validate initial_price to prevent division by zero later
        if not initial_price or initial_price == 0:
            print(f"   ⚠️  Skipping save_stock_tracking for {ticker}: invalid initial_price ({initial_price})")
            return
        
        conn = self.get_connection()
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        
        c.execute('''INSERT INTO stock_tracking 
                     (ticker, post_id, initial_price, initial_date, current_price, 
                      last_updated, price_change_pct, max_price, min_price, 
                      max_gain_pct, max_loss_pct, days_tracked, status, alert_sent,
                      reached_winner, reached_loser, time_to_peak_days, time_to_bottom_days)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (ticker, post_id, initial_price, now, initial_price, now, 
                   0.0, initial_price, initial_price, 0.0, 0.0, 0, 'TRACKED', 0,
                   0, 0, None, None))
        
        conn.commit()
        conn.close()
    
    def save_stock_metadata(self, ticker: str, data: Dict):
        """Save comprehensive stock metadata"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO stock_metadata 
                     (ticker, company_name, sector, industry, market_cap, pe_ratio,
                      forward_pe, peg_ratio, beta, dividend_yield, profit_margin,
                      debt_to_equity, current_ratio, roe, revenue_growth,
                      earnings_date, analyst_rating, price_target, short_interest,
                      short_ratio, institutional_ownership, insider_ownership, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (ticker, data.get('name'), data.get('sector'), data.get('industry'),
                   data.get('market_cap'), data.get('pe_ratio'), data.get('forward_pe'),
                   data.get('peg_ratio'), data.get('beta'), data.get('dividend_yield'),
                   data.get('profit_margin'), data.get('debt_to_equity'), data.get('current_ratio'),
                   data.get('roe'), data.get('revenue_growth'), data.get('earnings_date'),
                   data.get('analyst_rating'), data.get('price_target'), data.get('short_interest'),
                   data.get('short_ratio'), data.get('institutional_ownership'),
                   data.get('insider_ownership'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def save_price_history(self, ticker: str, hist_data):
        """Save historical price data"""
        conn = self.get_connection()
        c = conn.cursor()
        
        for date, row in hist_data.iterrows():
            c.execute('''INSERT OR IGNORE INTO price_history 
                         (ticker, date, open_price, high_price, low_price, close_price, volume)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (ticker, date.strftime('%Y-%m-%d'), row['Open'], row['High'],
                       row['Low'], row['Close'], row['Volume']))
        
        conn.commit()
        conn.close()
    
    def save_technical_indicators(self, ticker: str, indicators: Dict):
        """Save technical indicators"""
        if not indicators:
            return

        conn = self.get_connection()
        c = conn.cursor()

        c.execute('''INSERT OR REPLACE INTO technical_indicators
                     (ticker, date, rsi, macd, macd_signal, sma_20, sma_50, sma_200,
                      ema_12, ema_26, bollinger_upper, bollinger_lower, volume_ratio,
                      vwap, adx, plus_di, minus_di,
                      ichimoku_tenkan, ichimoku_kijun, ichimoku_senkou_a, ichimoku_senkou_b,
                      signal, signal_confidence)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (ticker, datetime.now().strftime('%Y-%m-%d'),
                   indicators.get('rsi'), indicators.get('macd'), None,
                   indicators.get('sma_20'), indicators.get('sma_50'), indicators.get('sma_200'),
                   indicators.get('ema_12'), indicators.get('ema_26'),
                   indicators.get('bollinger_upper'), indicators.get('bollinger_lower'),
                   indicators.get('volume_ratio'),
                   indicators.get('vwap'), indicators.get('adx'),
                   indicators.get('plus_di'), indicators.get('minus_di'),
                   indicators.get('ichimoku_tenkan'), indicators.get('ichimoku_kijun'),
                   indicators.get('ichimoku_senkou_a'), indicators.get('ichimoku_senkou_b'),
                   indicators.get('signal'), indicators.get('signal_confidence')))

        conn.commit()
        conn.close()
    
    def save_news_articles(self, ticker: str, articles: List[Dict]):
        """Save news articles"""
        if not articles:
            return
        
        conn = self.get_connection()
        c = conn.cursor()
        
        for article in articles:
            try:
                c.execute('''INSERT OR IGNORE INTO news_catalysts 
                             (ticker, date, headline, source, url, sentiment, importance)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (ticker, article['date'], article['title'], 
                           article['source'], article['url'], 'NEUTRAL', 5))
            except Exception:
                continue
        
        conn.commit()
        conn.close()
    
    def is_duplicate_post(self, content_hash: str, ticker: str, hours: int = 24) -> bool:
        """Check if similar post was already processed"""
        conn = self.get_connection()
        c = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        c.execute('''SELECT id FROM duplicate_posts 
                     WHERE content_hash = ? AND ticker = ? AND detected_date > ?''',
                  (content_hash, ticker, cutoff_date))
        
        result = c.fetchone()
        conn.close()
        return result is not None
    
    def save_duplicate_entry(self, content_hash: str, post_id: str, ticker: str):
        """Save duplicate detection entry"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''INSERT OR IGNORE INTO duplicate_posts 
                     (content_hash, post_id, ticker, detected_date)
                     VALUES (?, ?, ?, ?)''',
                  (content_hash, post_id, ticker, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def save_insider_transactions(self, ticker: str, transactions: List[Dict]):
        """Save insider transaction records"""
        if not transactions:
            return
        conn = self.get_connection()
        c = conn.cursor()
        for txn in transactions:
            try:
                c.execute('''INSERT OR IGNORE INTO insider_transactions
                             (ticker, insider_name, title, transaction_type,
                              shares, value, transaction_date, scraped_date)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (ticker,
                           txn.get('name', 'Unknown'),
                           txn.get('title', ''),
                           txn.get('type', ''),
                           txn.get('shares', 0),
                           txn.get('value', 0),
                           txn.get('date', ''),
                           datetime.now().isoformat()))
            except Exception:
                continue
        conn.commit()
        conn.close()

    def save_congress_trades(self, trades: List[Dict]):
        """Save Congress trade records"""
        if not trades:
            return
        conn = self.get_connection()
        c = conn.cursor()
        for trade in trades:
            try:
                c.execute('''INSERT OR IGNORE INTO congress_trades
                             (ticker, politician_name, party, chamber,
                              transaction_type, amount_range,
                              transaction_date, disclosure_date, scraped_date)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (trade.get('ticker', ''),
                           trade.get('politician_name', 'Unknown'),
                           trade.get('party', ''),
                           trade.get('chamber', ''),
                           trade.get('transaction_type', ''),
                           trade.get('amount_range', ''),
                           trade.get('transaction_date', ''),
                           trade.get('disclosure_date', ''),
                           datetime.now().isoformat()))
            except Exception:
                continue
        conn.commit()
        conn.close()

    def save_sentiment_analysis(self, ticker: str, sentiment: Dict):
        """Save sentiment analysis results"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''INSERT OR REPLACE INTO sentiment_analysis
                         (ticker, analysis_date, sentiment, confidence, score, model_used, text_analyzed, source)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (ticker, datetime.now().strftime('%Y-%m-%d'),
                       sentiment.get('sentiment', 'NEUTRAL'),
                       sentiment.get('confidence', 0),
                       sentiment.get('score', 0),
                       'FinBERT',
                       f"{ticker} stock analysis",
                       'HTML Report'))
            conn.commit()
        except Exception as e:
            print(f"[DB] Error saving sentiment: {e}")
        conn.close()

    def get_congress_trades(self, ticker: str, days: int = 60) -> List[Dict]:
        """Get recent Congress trades for a ticker from the DB cache"""
        conn = self.get_connection()
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        c.execute('''SELECT politician_name, party, chamber, transaction_type,
                            amount_range, transaction_date, disclosure_date
                     FROM congress_trades
                     WHERE ticker = ? AND transaction_date >= ?
                     ORDER BY transaction_date DESC''',
                  (ticker, cutoff))
        rows = c.fetchall()
        conn.close()
        return [
            {
                'politician_name': r[0],
                'party': r[1],
                'chamber': r[2],
                'transaction_type': r[3],
                'amount_range': r[4],
                'transaction_date': r[5],
                'disclosure_date': r[6]
            }
            for r in rows
        ]

    def get_congress_cache_age_hours(self) -> Optional[float]:
        """Get hours since the last Congress data fetch"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT MAX(scraped_date) FROM congress_trades')
        result = c.fetchone()
        conn.close()
        if result and result[0]:
            last_scraped = datetime.fromisoformat(result[0])
            delta = datetime.now() - last_scraped
            return delta.total_seconds() / 3600
        return None

    def save_ml_prediction(self, ticker: str, prediction: Dict):
        """Save an ML prediction for later accuracy tracking"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''INSERT OR REPLACE INTO ml_predictions
                         (ticker, prediction_date, predicted_direction, confidence, features_used)
                         VALUES (?, ?, ?, ?, ?)''',
                      (ticker, datetime.now().strftime('%Y-%m-%d'),
                       prediction.get('direction', 'FLAT'),
                       prediction.get('confidence', 0),
                       prediction.get('features_used', '')))
            conn.commit()
        except Exception:
            pass
        conn.close()

    def get_ml_training_data(self) -> List[Dict]:
        """Get historical stock tracking data with technical indicators for ML training"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT st.ticker, st.initial_price, st.current_price, st.price_change_pct,
                            st.days_tracked, st.initial_date,
                            ti.rsi, ti.macd, ti.sma_20, ti.sma_50, ti.sma_200,
                            ti.volume_ratio, ti.adx, ti.bollinger_upper, ti.bollinger_lower,
                            ti.vwap
                     FROM stock_tracking st
                     LEFT JOIN technical_indicators ti ON st.ticker = ti.ticker
                        AND ti.date = substr(st.initial_date, 1, 10)
                     WHERE st.days_tracked >= 5
                        AND st.initial_price > 0
                        AND st.current_price > 0''')
        rows = c.fetchall()
        conn.close()
        return [
            {
                'ticker': r[0], 'initial_price': r[1], 'current_price': r[2],
                'price_change_pct': r[3], 'days_tracked': r[4], 'initial_date': r[5],
                'rsi': r[6], 'macd': r[7], 'sma_20': r[8], 'sma_50': r[9],
                'sma_200': r[10], 'volume_ratio': r[11], 'adx': r[12],
                'bollinger_upper': r[13], 'bollinger_lower': r[14], 'vwap': r[15]
            }
            for r in rows
        ]

    def get_ml_model_age_days(self) -> Optional[float]:
        """Check when the ML model was last trained by checking latest prediction date"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT MAX(prediction_date) FROM ml_predictions')
        result = c.fetchone()
        conn.close()
        if result and result[0]:
            try:
                last = datetime.strptime(result[0], '%Y-%m-%d')
                return (datetime.now() - last).days
            except ValueError:
                pass
        return None

    def get_stock_stats(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive win/loss stats for a ticker"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'WINNER' OR reached_winner = 1 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN status = 'LOSER' OR reached_loser = 1 THEN 1 ELSE 0 END) as losses,
                        AVG(price_change_pct) as avg_change,
                        MAX(max_gain_pct) as best_gain,
                        MIN(max_loss_pct) as worst_loss,
                        AVG(days_tracked) as avg_days,
                        AVG(time_to_peak_days) as avg_time_to_peak,
                        AVG(time_to_bottom_days) as avg_time_to_bottom
                     FROM stock_tracking WHERE ticker = ?''', (ticker,))
        
        result = c.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            win_rate = (result[1] / result[0] * 100) if result[0] > 0 else 0
            return {
                'total_mentions': result[0],
                'wins': result[1],
                'losses': result[2],
                'avg_change': round(result[3], 2) if result[3] else 0,
                'best_gain': round(result[4], 2) if result[4] else 0,
                'worst_loss': round(result[5], 2) if result[5] else 0,
                'avg_days': round(result[6], 1) if result[6] else 0,
                'avg_time_to_peak': round(result[7], 1) if result[7] else None,
                'avg_time_to_bottom': round(result[8], 1) if result[8] else None,
                'win_rate': round(win_rate, 1)
            }
        return None
    
    def get_related_posts(self, ticker: str, limit: int = 3) -> List[Dict]:
        """Get recent related DD posts for the same ticker"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT title, url, subreddit, score, posted_date, quality_score
                     FROM posted_submissions 
                     WHERE tickers LIKE ? 
                     ORDER BY posted_date DESC, quality_score DESC
                     LIMIT ?''', (f'%{ticker}%', limit + 1))
        
        posts = []
        for row in c.fetchall():
            post_date = datetime.fromisoformat(row[4])
            days_ago = (datetime.now() - post_date).days
            
            posts.append({
                'title': row[0],
                'url': row[1],
                'subreddit': row[2],
                'score': row[3],
                'days_ago': days_ago,
                'quality_score': row[5]
            })
        
        conn.close()
        return posts[1:] if len(posts) > 1 else []

    # =========================================================================
    # WATCHLIST METHODS
    # =========================================================================

    def get_user_watchlist(self, user_id: str) -> List[Dict]:
        """Get all watchlist items for a user"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT ticker, added_date, notes, alert_enabled,
                            alert_price_above, alert_price_below, alert_percent_change,
                            alert_volume_spike, alert_congress_trades, alert_news,
                            last_price, last_updated, notification_count
                     FROM user_watchlists
                     WHERE user_id = ?
                     ORDER BY added_date DESC''', (user_id,))
        
        watchlist = []
        for row in c.fetchall():
            watchlist.append({
                'ticker': row[0],
                'added_date': row[1],
                'notes': row[2],
                'alert_enabled': bool(row[3]),
                'alert_price_above': row[4],
                'alert_price_below': row[5],
                'alert_percent_change': row[6],
                'alert_volume_spike': bool(row[7]),
                'alert_congress_trades': bool(row[8]),
                'alert_news': bool(row[9]),
                'last_price': row[10],
                'last_updated': row[11],
                'notification_count': row[12]
            })
        
        conn.close()
        return watchlist

    def add_to_watchlist(self, user_id: str, ticker: str, notes: str = '',
                         alert_price_above: float = None, alert_price_below: float = None,
                         alert_percent_change: float = None, alert_volume_spike: bool = False,
                         alert_congress_trades: bool = True, alert_news: bool = True) -> bool:
        """Add a stock to user's watchlist"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''INSERT OR REPLACE INTO user_watchlists
                         (user_id, ticker, added_date, notes, alert_enabled,
                          alert_price_above, alert_price_below, alert_percent_change,
                          alert_volume_spike, alert_congress_trades, alert_news,
                          last_price, last_updated)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, ticker.upper(), datetime.now().isoformat(), notes, True,
                       alert_price_above, alert_price_below, alert_percent_change,
                       alert_volume_spike, alert_congress_trades, alert_news,
                       None, None))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB] Error adding to watchlist: {e}")
            conn.close()
            return False

    def remove_from_watchlist(self, user_id: str, ticker: str) -> bool:
        """Remove a stock from user's watchlist"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('DELETE FROM user_watchlists WHERE user_id = ? AND ticker = ?',
                      (user_id, ticker.upper()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB] Error removing from watchlist: {e}")
            conn.close()
            return False

    def update_watchlist_alerts(self, user_id: str, ticker: str, **kwargs) -> bool:
        """Update alert settings for a watchlist item"""
        conn = self.get_connection()
        c = conn.cursor()
        
        allowed_fields = ['notes', 'alert_enabled', 'alert_price_above', 'alert_price_below',
                         'alert_percent_change', 'alert_volume_spike', 'alert_congress_trades', 'alert_news']
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            conn.close()
            return False
        
        values.extend([user_id, ticker.upper()])
        
        try:
            c.execute(f'''UPDATE user_watchlists SET {', '.join(updates)}
                        WHERE user_id = ? AND ticker = ?''', values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB] Error updating watchlist: {e}")
            conn.close()
            return False

    def update_watchlist_price(self, user_id: str, ticker: str, price: float):
        """Update the last known price for a watchlist item"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''UPDATE user_watchlists 
                        SET last_price = ?, last_updated = ?
                        WHERE user_id = ? AND ticker = ?''',
                      (price, datetime.now().isoformat(), user_id, ticker.upper()))
            conn.commit()
        except Exception as e:
            print(f"[DB] Error updating watchlist price: {e}")
        finally:
            conn.close()

    def is_in_watchlist(self, user_id: str, ticker: str) -> bool:
        """Check if a ticker is in user's watchlist"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('SELECT 1 FROM user_watchlists WHERE user_id = ? AND ticker = ?',
                  (user_id, ticker.upper()))
        result = c.fetchone()
        conn.close()
        return result is not None

    def get_all_watchlist_items(self) -> List[Dict]:
        """Get all watchlist items with user info for monitoring"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT w.user_id, w.ticker, w.alert_price_above, w.alert_price_below,
                            w.alert_percent_change, w.alert_volume_spike, w.alert_congress_trades,
                            w.alert_news, w.last_price, w.alert_enabled, u.username
                     FROM user_watchlists w
                     LEFT JOIN dashboard_users u ON w.user_id = u.user_id
                     WHERE w.alert_enabled = 1''')
        
        items = []
        for row in c.fetchall():
            items.append({
                'user_id': row[0],
                'ticker': row[1],
                'alert_price_above': row[2],
                'alert_price_below': row[3],
                'alert_percent_change': row[4],
                'alert_volume_spike': bool(row[5]),
                'alert_congress_trades': bool(row[6]),
                'alert_news': bool(row[7]),
                'last_price': row[8],
                'alert_enabled': bool(row[9]),
                'username': row[10]
            })
        
        conn.close()
        return items

    def log_watchlist_alert(self, user_id: str, ticker: str, alert_type: str,
                           trigger_price: float, trigger_condition: str, message: str):
        """Log a watchlist alert"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''INSERT INTO watchlist_alerts
                         (user_id, ticker, alert_type, alert_date, trigger_price,
                          trigger_condition, message, sent_to_discord, user_notified)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, ticker.upper(), alert_type, datetime.now().isoformat(),
                       trigger_price, trigger_condition, message, False, False))
            
            # Increment notification count
            c.execute('''UPDATE user_watchlists 
                        SET notification_count = notification_count + 1
                        WHERE user_id = ? AND ticker = ?''', (user_id, ticker.upper()))
            
            conn.commit()
        except Exception as e:
            print(f"[DB] Error logging watchlist alert: {e}")
        finally:
            conn.close()

    def get_recent_alerts(self, user_id: str, hours: int = 24) -> List[Dict]:
        """Get recent alerts for a user"""
        conn = self.get_connection()
        c = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        c.execute('''SELECT ticker, alert_type, alert_date, trigger_price,
                            trigger_condition, message, acknowledged
                     FROM watchlist_alerts
                     WHERE user_id = ? AND alert_date > ?
                     ORDER BY alert_date DESC''', (user_id, cutoff))
        
        alerts = []
        for row in c.fetchall():
            alerts.append({
                'ticker': row[0],
                'alert_type': row[1],
                'alert_date': row[2],
                'trigger_price': row[3],
                'trigger_condition': row[4],
                'message': row[5],
                'acknowledged': bool(row[6])
            })
        
        conn.close()
        return alerts

    def acknowledge_alert(self, alert_id: int):
        """Mark an alert as acknowledged"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('UPDATE watchlist_alerts SET acknowledged = 1 WHERE id = ?', (alert_id,))
            conn.commit()
        except Exception as e:
            print(f"[DB] Error acknowledging alert: {e}")
        finally:
            conn.close()

    # =========================================================================
    # NOTIFICATION SETTINGS METHODS
    # =========================================================================

    def get_notification_settings(self, user_id: str) -> Dict:
        """Get user's notification settings"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT dm_enabled, price_alerts, percent_change_alerts,
                            volume_spike_alerts, congress_trade_alerts, news_alerts,
                            alert_frequency, quiet_hours_start, quiet_hours_end,
                            max_alerts_per_day
                     FROM user_notification_settings WHERE user_id = ?''', (user_id,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return {
                'dm_enabled': bool(row[0]),
                'price_alerts': bool(row[1]),
                'percent_change_alerts': bool(row[2]),
                'volume_spike_alerts': bool(row[3]),
                'congress_trade_alerts': bool(row[4]),
                'news_alerts': bool(row[5]),
                'alert_frequency': row[6],
                'quiet_hours_start': row[7],
                'quiet_hours_end': row[8],
                'max_alerts_per_day': row[9]
            }
        
        # Return defaults if no settings found
        return {
            'dm_enabled': True,
            'price_alerts': True,
            'percent_change_alerts': True,
            'volume_spike_alerts': False,
            'congress_trade_alerts': True,
            'news_alerts': True,
            'alert_frequency': 'immediate',
            'quiet_hours_start': 22,
            'quiet_hours_end': 7,
            'max_alerts_per_day': 50
        }

    def save_notification_settings(self, user_id: str, settings: Dict) -> bool:
        """Save user's notification settings"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''INSERT OR REPLACE INTO user_notification_settings
                         (user_id, dm_enabled, price_alerts, percent_change_alerts,
                          volume_spike_alerts, congress_trade_alerts, news_alerts,
                          alert_frequency, quiet_hours_start, quiet_hours_end,
                          max_alerts_per_day, created_date, updated_date)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, 
                       settings.get('dm_enabled', True),
                       settings.get('price_alerts', True),
                       settings.get('percent_change_alerts', True),
                       settings.get('volume_spike_alerts', False),
                       settings.get('congress_trade_alerts', True),
                       settings.get('news_alerts', True),
                       settings.get('alert_frequency', 'immediate'),
                       settings.get('quiet_hours_start', 22),
                       settings.get('quiet_hours_end', 7),
                       settings.get('max_alerts_per_day', 50),
                       datetime.now().isoformat(),
                       datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[DB] Error saving notification settings: {e}")
            conn.close()
            return False

    def ensure_user_exists(self, user_id: str, username: str = None, 
                          discriminator: str = None, display_name: str = None):
        """Ensure user exists in dashboard_users table"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('SELECT user_id FROM dashboard_users WHERE user_id = ?', (user_id,))
            if not c.fetchone():
                c.execute('''INSERT INTO dashboard_users
                             (user_id, username, discriminator, display_name, created_date, last_active)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (user_id, username, discriminator, display_name,
                           datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            print(f"[DB] Error ensuring user exists: {e}")
        finally:
            conn.close()

    # =========================================================================
    # INVALID TICKER CACHING
    # =========================================================================

    def is_invalid_ticker(self, ticker: str) -> bool:
        """Check if ticker is known to be invalid"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT 1 FROM invalid_tickers WHERE ticker = ?", (ticker.upper(),))
        result = c.fetchone()
        conn.close()
        return result is not None

    def save_invalid_ticker(self, ticker: str, reason: str = "not found"):
        """Save an invalid ticker to skip in future scans"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''INSERT OR IGNORE INTO invalid_tickers 
                         (ticker, invalid_date, reason)
                         VALUES (?, ?, ?)''',
                      (ticker.upper(), datetime.now().isoformat(), reason))
            conn.commit()
        except Exception as e:
            print(f"[DB] Error saving invalid ticker: {e}")
        finally:
            conn.close()
