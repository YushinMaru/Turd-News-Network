"""
Performance tracking and winner/loser detection
FIXED: Division by zero errors, database locking issues
"""

import sqlite3
import yfinance as yf
from datetime import datetime
from typing import Dict, List, Tuple
from config import DB_PATH, WINNER_THRESHOLD, LOSER_THRESHOLD
import time


class PerformanceTracker:
    """Tracks stock performance and identifies winners/losers"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with timeout to prevent locking"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable Write-Ahead Logging
        return conn
    
    def update_stock_performance(self):
        """Update all tracked stocks and determine winners/losers"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Get all tracked stocks
        c.execute('''SELECT id, ticker, initial_price, initial_date, max_price, min_price,
                            max_gain_pct, max_loss_pct, reached_winner, reached_loser,
                            time_to_peak_days, time_to_bottom_days
                     FROM stock_tracking WHERE status IN ('TRACKED', 'WINNER', 'LOSER')''')
        stocks = c.fetchall()
        
        for (stock_id, ticker, initial_price, initial_date, max_price, min_price, 
             max_gain, max_loss, reached_winner, reached_loser, 
             time_to_peak, time_to_bottom) in stocks:
            try:
                # Skip if initial_price is 0 or None
                if not initial_price or initial_price == 0:
                    print(f"   ⚠️  Skipping {ticker}: invalid initial_price ({initial_price})")
                    continue
                
                stock = yf.Ticker(ticker)
                hist = stock.history(period='1d')
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    # Skip if current_price is invalid
                    if not current_price or current_price == 0:
                        print(f"   ⚠️  Skipping {ticker}: invalid current_price ({current_price})")
                        continue
                    
                    change_pct = ((current_price - initial_price) / initial_price) * 100
                    
                    # Calculate days tracked
                    init_date = datetime.fromisoformat(initial_date)
                    days_tracked = (datetime.now() - init_date).days
                    
                    # Update max/min tracking
                    new_max = False
                    new_min = False
                    
                    if max_price is None or current_price > max_price:
                        max_price = current_price
                        max_gain = ((max_price - initial_price) / initial_price) * 100
                        time_to_peak = days_tracked
                        new_max = True
                    
                    if min_price is None or current_price < min_price:
                        min_price = current_price
                        max_loss = ((min_price - initial_price) / initial_price) * 100
                        time_to_bottom = days_tracked
                        new_min = True
                    
                    # Check for winner/loser status
                    if max_gain >= WINNER_THRESHOLD and not reached_winner:
                        reached_winner = 1
                        print(f"   [^] {ticker} reached WINNER status! (+{max_gain:.1f}%)")
                        self.log_alert(ticker, 'WINNER', max_gain)
                    
                    if max_loss <= LOSER_THRESHOLD and not reached_loser:
                        reached_loser = 1
                        print(f"   💀 {ticker} reached LOSER status! ({max_loss:.1f}%)")
                        self.log_alert(ticker, 'LOSER', max_loss)
                    
                    # Determine current status
                    status = 'TRACKED'
                    if change_pct >= WINNER_THRESHOLD:
                        status = 'WINNER'
                    elif change_pct <= LOSER_THRESHOLD:
                        status = 'LOSER'
                    
                    # Update database with retry logic
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            c.execute('''UPDATE stock_tracking 
                                         SET current_price = ?, last_updated = ?, 
                                             price_change_pct = ?, status = ?,
                                             max_price = ?, min_price = ?,
                                             max_gain_pct = ?, max_loss_pct = ?,
                                             days_tracked = ?, reached_winner = ?,
                                             reached_loser = ?, time_to_peak_days = ?,
                                             time_to_bottom_days = ?
                                         WHERE id = ?''',
                                      (current_price, datetime.now().isoformat(), change_pct, status,
                                       max_price, min_price, max_gain, max_loss, days_tracked,
                                       reached_winner, reached_loser, time_to_peak, time_to_bottom,
                                       stock_id))
                            conn.commit()
                            break  # Success, exit retry loop
                        except sqlite3.OperationalError as e:
                            if "locked" in str(e) and attempt < max_retries - 1:
                                print(f"   [~] Database locked, retrying {ticker} (attempt {attempt + 1}/{max_retries})...")
                                time.sleep(1)  # Wait 1 second before retry
                            else:
                                raise  # Re-raise if final attempt or different error
                                
            except Exception as e:
                print(f"Error updating {ticker}: {e}")
        
        conn.close()
    
    def log_alert(self, ticker: str, alert_type: str, trigger_value: float):
        """Log alert to database with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = self.get_connection()
                c = conn.cursor()
                
                message = f"{ticker} reached {alert_type} status with {trigger_value:+.1f}%"
                
                c.execute('''INSERT INTO alert_log 
                             (ticker, alert_type, alert_date, trigger_value, message)
                             VALUES (?, ?, ?, ?, ?)''',
                          (ticker, alert_type, datetime.now().isoformat(), trigger_value, message))
                
                conn.commit()
                conn.close()
                break  # Success
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    print(f"   [~] Database locked for alert log, retrying (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(1)
                else:
                    print(f"   ❌ Failed to log alert for {ticker}: {e}")
                    break
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Get overall stats
        c.execute('''SELECT 
                        COUNT(DISTINCT ticker) as unique_stocks,
                        COUNT(*) as total_mentions,
                        SUM(CASE WHEN reached_winner = 1 THEN 1 ELSE 0 END) as winners,
                        SUM(CASE WHEN reached_loser = 1 THEN 1 ELSE 0 END) as losers,
                        AVG(price_change_pct) as avg_change,
                        MAX(max_gain_pct) as best_gain,
                        MIN(max_loss_pct) as worst_loss,
                        AVG(time_to_peak_days) as avg_time_to_peak,
                        AVG(time_to_bottom_days) as avg_time_to_bottom
                     FROM stock_tracking''')
        
        overall = c.fetchone()
        
        # Get top performers
        c.execute('''SELECT ticker, max_gain_pct, time_to_peak_days, initial_date
                     FROM stock_tracking
                     WHERE max_gain_pct IS NOT NULL
                     ORDER BY max_gain_pct DESC
                     LIMIT 10''')
        
        top_performers = c.fetchall()
        
        # Get worst performers
        c.execute('''SELECT ticker, max_loss_pct, time_to_bottom_days
                     FROM stock_tracking
                     WHERE max_loss_pct IS NOT NULL
                     ORDER BY max_loss_pct ASC
                     LIMIT 10''')
        
        worst_performers = c.fetchall()
        
        # Get most mentioned
        c.execute('''SELECT ticker, COUNT(*) as mentions, 
                            AVG(price_change_pct) as avg_performance
                     FROM stock_tracking
                     GROUP BY ticker
                     ORDER BY mentions DESC
                     LIMIT 10''')
        
        most_mentioned = c.fetchall()
        
        # Get fastest winners
        c.execute('''SELECT ticker, max_gain_pct, time_to_peak_days
                     FROM stock_tracking
                     WHERE reached_winner = 1 AND time_to_peak_days IS NOT NULL
                     ORDER BY time_to_peak_days ASC
                     LIMIT 5''')
        
        fastest_winners = c.fetchall()
        
        conn.close()
        
        # Format report
        win_rate = (overall[2] / overall[1] * 100) if overall[1] > 0 else 0
        
        report = f"""
======================================================================
           ENHANCED WSB MONITOR - PERFORMANCE REPORT                
======================================================================

[*] OVERALL STATISTICS:
     * Unique Stocks Tracked: {overall[0]}
     * Total Mentions: {overall[1]}
     * Winners (>={WINNER_THRESHOLD}%): {overall[2]}
     * Losers (<={LOSER_THRESHOLD}%): {overall[3]}
     * Average Change: {overall[4]:.2f}%
     * Best Gain: +{overall[5]:.2f}%
     * Worst Loss: {overall[6]:.2f}%
     * Win Rate: {win_rate:.1f}%
     * Avg Days to Peak: {overall[7]:.1f} days
     * Avg Days to Bottom: {overall[8]:.1f} days

[^] TOP 10 PERFORMERS (Peak Gains):
"""
        
        for i, (ticker, gain, days_to_peak, date) in enumerate(top_performers, 1):
            days_str = f"{int(days_to_peak)}d" if days_to_peak else "N/A"
            report += f"   {i:2d}. ${ticker:5s} +{gain:6.2f}% (peak in {days_str}, tracked since {date[:10]})\n"
        
        report += "\n[*] FASTEST WINNERS (Shortest Time to +20%):\n"
        for i, (ticker, gain, days) in enumerate(fastest_winners, 1):
            report += f"   {i}. ${ticker:5s} +{gain:.1f}% in just {int(days)} days!  [^]\n"
        
        report += "\n💀 WORST 10 PERFORMERS (Peak Losses):\n"
        for i, (ticker, loss, days_to_bottom) in enumerate(worst_performers, 1):
            days_str = f"{int(days_to_bottom)}d" if days_to_bottom else "N/A"
            report += f"   {i:2d}. ${ticker:5s} {loss:6.2f}% (bottom in {days_str})\n"
        
        report += "\n[#] MOST MENTIONED STOCKS:\n"
        for i, (ticker, mentions, avg_perf) in enumerate(most_mentioned, 1):
            report += f"   {i:2d}. ${ticker:5s} ({mentions} mentions, avg {avg_perf:+.1f}%)\n"
        
        report += "\n" + "="*70 + "\n"
        
        return report
    
    def get_winner_loser_breakdown(self) -> Dict:
        """Get detailed breakdown of winners and losers"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Winners breakdown
        c.execute('''SELECT 
                        COUNT(*) as total_winners,
                        AVG(max_gain_pct) as avg_gain,
                        AVG(time_to_peak_days) as avg_days_to_peak,
                        MAX(max_gain_pct) as best_winner,
                        MIN(time_to_peak_days) as fastest_win
                     FROM stock_tracking 
                     WHERE reached_winner = 1''')
        
        winners = c.fetchone()
        
        # Losers breakdown
        c.execute('''SELECT 
                        COUNT(*) as total_losers,
                        AVG(max_loss_pct) as avg_loss,
                        AVG(time_to_bottom_days) as avg_days_to_bottom,
                        MIN(max_loss_pct) as worst_loser,
                        MIN(time_to_bottom_days) as fastest_loss
                     FROM stock_tracking 
                     WHERE reached_loser = 1''')
        
        losers = c.fetchone()
        
        conn.close()
        
        return {
            'winners': {
                'count': winners[0] if winners else 0,
                'avg_gain': winners[1] if winners else 0,
                'avg_days_to_peak': winners[2] if winners else 0,
                'best_gain': winners[3] if winners else 0,
                'fastest_days': winners[4] if winners else 0
            },
            'losers': {
                'count': losers[0] if losers else 0,
                'avg_loss': losers[1] if losers else 0,
                'avg_days_to_bottom': losers[2] if losers else 0,
                'worst_loss': losers[3] if losers else 0,
                'fastest_days': losers[4] if losers else 0
            }
        }
