"""
Statistics Reporter - ENHANCED VERSION
New features: Visual charts, sector analysis, trending stocks, performance heatmaps
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import DB_PATH, COLOR_PREMIUM, COLOR_QUALITY, WINNER_THRESHOLD, LOSER_THRESHOLD
from ai_summary import AISummaryGenerator


class StatsReporter:
    """Generate comprehensive statistics reports for Discord with visualizations"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def generate_performance_embed(self, include_charts: bool = True) -> List[Dict]:
        """Generate Discord embeds with comprehensive performance statistics"""
        embeds = []
        
        # Main statistics embed
        main_embed = self._build_main_stats_embed()
        if main_embed:
            embeds.append(main_embed)
        
        # Top performers embed (COMPACT)
        top_embed = self._build_top_performers_compact()
        if top_embed:
            embeds.append(top_embed)
        
        # NEW: Sector performance breakdown
        sector_embed = self._build_sector_performance()
        if sector_embed:
            embeds.append(sector_embed)
        
        # NEW: Trending stocks (high momentum)
        trending_embed = self._build_trending_stocks()
        if trending_embed:
            embeds.append(trending_embed)
        
        # NEW: Risk-adjusted returns leaderboard
        risk_adj_embed = self._build_risk_adjusted_leaderboard()
        if risk_adj_embed:
            embeds.append(risk_adj_embed)
        
        return embeds
    
    def _build_main_stats_embed(self) -> Optional[Dict]:
        """Build COMPACT main statistics overview"""
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
                        AVG(time_to_bottom_days) as avg_time_to_bottom,
                        AVG(days_tracked) as avg_days_tracked
                     FROM stock_tracking''')
        
        stats = c.fetchone()
        
        # Get recent activity (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        c.execute('''SELECT COUNT(DISTINCT ticker) FROM stock_tracking 
                     WHERE initial_date > ?''', (week_ago,))
        new_this_week = c.fetchone()[0]
        
        conn.close()
        
        if not stats or stats[0] == 0:
            return None
        
        unique_stocks, total_mentions, winners, losers, avg_change, best_gain, worst_loss, avg_peak, avg_bottom, avg_days = stats
        
        # Handle None values
        avg_peak = avg_peak if avg_peak is not None else 0
        avg_bottom = avg_bottom if avg_bottom is not None else 0
        avg_days = avg_days if avg_days is not None else 0
        best_gain = best_gain if best_gain is not None else 0
        worst_loss = worst_loss if worst_loss is not None else 0
        avg_change = avg_change if avg_change is not None else 0
        
        win_rate = (winners / total_mentions * 100) if total_mentions > 0 else 0
        
        # Build compact description with key metrics
        description = f"""**📊 Total Tracked:** {unique_stocks:,} stocks | {total_mentions:,} DD mentions
**🆕 New This Week:** {new_this_week} stocks added
**📈 Avg Performance:** {avg_change:+.2f}% | **Best:** +{best_gain:.2f}% | **Worst:** {worst_loss:.2f}%"""
        
        # Compact fields - 3 column layout
        fields = [
            {
                "name": "🏆 Winners",
                "value": f"**{winners}** picks\n**{win_rate:.1f}%** win rate\n**{avg_peak:.1f}** days to peak",
                "inline": True
            },
            {
                "name": "💰 Losers",
                "value": f"**{losers}** picks\n**{(losers/total_mentions*100):.1f}%** loss rate\n**{avg_bottom:.1f}** days to bottom",
                "inline": True
            },
            {
                "name": "⏱️ Tracking",
                "value": f"**{avg_days:.1f}** avg days\n**{total_mentions}** total\n**{unique_stocks}** unique",
                "inline": True
            }
        ]
        
        # Win rate visualization
        win_bar = self._create_progress_bar(win_rate, 100)
        fields.append({
            "name": "📊 Win Rate Visualization",
            "value": f"{win_bar}\n**{win_rate:.1f}%** success rate ({winners}W/{losers}L/{total_mentions - winners - losers}N)",
            "inline": False
        })
        
        return {
            "title": "📊 Turd News Network - Performance Dashboard",
            "description": description,
            "color": COLOR_PREMIUM,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "💎 Turd News Network Enhanced v4.0 | Performance Statistics"}
        }
    
    def _build_top_performers_compact(self) -> Optional[Dict]:
        """Build COMPACT top performers - single embed with top 10"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT ticker, MAX(max_gain_pct) as max_gain_pct,
                            AVG(time_to_peak_days) as time_to_peak_days,
                            MIN(initial_date) as initial_date
                     FROM stock_tracking
                     WHERE max_gain_pct IS NOT NULL
                     GROUP BY ticker
                     ORDER BY MAX(max_gain_pct) DESC
                     LIMIT 10''')
        
        performers = c.fetchall()
        
        # Also get worst performers
        c.execute('''SELECT ticker, MIN(max_loss_pct) as max_loss_pct,
                            AVG(time_to_bottom_days) as time_to_bottom_days
                     FROM stock_tracking
                     WHERE max_loss_pct IS NOT NULL
                     GROUP BY ticker
                     ORDER BY MIN(max_loss_pct) ASC
                     LIMIT 5''')
        
        worst = c.fetchall()
        
        # Get fastest winners
        c.execute('''SELECT ticker, MAX(max_gain_pct) as max_gain_pct,
                            MIN(time_to_peak_days) as time_to_peak_days
                     FROM stock_tracking
                     WHERE reached_winner = 1 AND time_to_peak_days IS NOT NULL
                     GROUP BY ticker
                     ORDER BY MIN(time_to_peak_days) ASC
                     LIMIT 5''')
        
        fastest = c.fetchall()
        
        conn.close()
        
        if not performers:
            return None
        
        fields = []
        
        # Top gainers - compact format
        top_lines = []
        for i, (ticker, gain, days, date) in enumerate(performers, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            days_str = f"{int(days)}d" if days else "N/A"
            top_lines.append(f"{emoji} **${ticker}** +{gain:.1f}% (peak: {days_str})")
        
        fields.append({
            "name": "🏆 Top 10 Gainers",
            "value": "\n".join(top_lines),
            "inline": True
        })
        
        # Worst performers - compact
        worst_lines = []
        for i, (ticker, loss, days) in enumerate(worst, 1):
            days_str = f"{int(days)}d" if days else "N/A"
            worst_lines.append(f"{i}. **${ticker}** {loss:.1f}% ({days_str})")

        if worst_lines:
            fields.append({
                "name": "💰 Worst 5 Losers",
                "value": "\n".join(worst_lines),
                "inline": True
            })

        # Fastest winners
        fast_lines = []
        for i, (ticker, gain, days) in enumerate(fastest, 1):
            fast_lines.append(f"{i}. **${ticker}** +{gain:.1f}% in **{int(days)}** days 🚀")

        if fast_lines:
            fields.append({
                "name": "⚡ Fastest to +20%",
                "value": "\n".join(fast_lines),
                "inline": True
            })
        
        return {
            "title": "🎯 Performance Leaderboards",
            "color": 0x00FF00,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_sector_performance(self) -> Optional[Dict]:
        """NEW: Build sector breakdown embed"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT sm.sector, 
                            COUNT(*) as mentions,
                            AVG(st.price_change_pct) as avg_perf,
                            SUM(CASE WHEN st.reached_winner = 1 THEN 1 ELSE 0 END) as wins,
                            SUM(CASE WHEN st.reached_loser = 1 THEN 1 ELSE 0 END) as losses
                     FROM stock_tracking st
                     JOIN stock_metadata sm ON st.ticker = sm.ticker
                     WHERE sm.sector IS NOT NULL AND sm.sector != 'N/A'
                     GROUP BY sm.sector
                     ORDER BY avg_perf DESC''')
        
        sectors = c.fetchall()
        conn.close()
        
        if not sectors:
            return None
        
        lines = []
        for sector, mentions, avg_perf, wins, losses in sectors[:10]:
            emoji = "🟢" if avg_perf > 5 else "🟡" if avg_perf > -5 else "🔴"
            win_rate = (wins / mentions * 100) if mentions > 0 else 0
            lines.append(f"{emoji} **{sector}**: {avg_perf:+.1f}% avg | {mentions} picks | {win_rate:.0f}% WR")
        
        return {
            "title": "🏢 Sector Performance Analysis",
            "description": "Average performance by sector from Reddit DD picks",
            "color": COLOR_QUALITY,
            "fields": [
                {
                    "name": "Sector Rankings",
                    "value": "\n".join(lines),
                    "inline": False
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_trending_stocks(self) -> Optional[Dict]:
        """NEW: Show stocks with recent momentum (mentioned in last 7 days with good performance)"""
        conn = self.get_connection()
        c = conn.cursor()
        
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        c.execute('''SELECT ticker, MAX(price_change_pct) as price_change_pct,
                            AVG(days_tracked) as days_tracked,
                            MIN(initial_date) as initial_date
                     FROM stock_tracking
                     WHERE initial_date > ? AND price_change_pct > 0
                     GROUP BY ticker
                     ORDER BY MAX(price_change_pct) DESC
                     LIMIT 10''', (week_ago,))
        
        trending = c.fetchall()
        conn.close()
        
        if not trending:
            return None
        
        lines = []
        for ticker, change, days, date in trending:
            days_int = int(days) if days else 0
            emoji = "🚀" if change > 20 else "📈" if change > 10 else "🟢"
            lines.append(f"{emoji} **${ticker}** {change:+.1f}% in {days_int} days")
        
        return {
            "title": "🔥 Trending Stocks (Last 7 Days)",
            "description": "Recently mentioned stocks with strong performance",
            "color": 0xFF6600,
            "fields": [
                {
                    "name": "Hot Picks",
                    "value": "\n".join(lines),
                    "inline": False
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_risk_adjusted_leaderboard(self) -> Optional[Dict]:
        """NEW: Show stocks with best risk-adjusted returns (using backtest data)"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Get stocks with backtest data (deduplicated)
        c.execute('''SELECT ticker, MAX(sharpe_ratio) as sharpe_ratio,
                            AVG(sortino_ratio) as sortino_ratio,
                            AVG(total_return) as total_return,
                            AVG(max_drawdown) as max_drawdown,
                            AVG(calmar_ratio) as calmar_ratio
                     FROM backtest_results
                     WHERE sharpe_ratio IS NOT NULL
                     GROUP BY ticker
                     ORDER BY MAX(sharpe_ratio) DESC
                     LIMIT 10''')
        
        risk_adj = c.fetchall()
        conn.close()
        
        if not risk_adj:
            return None
        
        lines = []
        for i, (ticker, sharpe, sortino, total_ret, max_dd, calmar) in enumerate(risk_adj, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            sharpe_emoji = "🟢" if sharpe > 1.5 else "🟡" if sharpe > 0.5 else "🔴"
            lines.append(f"{emoji} **${ticker}** {sharpe_emoji} Sharpe: {sharpe:.2f} | Return: {total_ret:+.1f}%")
        
        return {
            "title": "⚖️ Best Risk-Adjusted Returns",
            "description": "Top stocks by Sharpe Ratio (3-year backtest)",
            "color": COLOR_QUALITY,
            "fields": [
                {
                    "name": "Risk-Adjusted Leaderboard",
                    "value": "\n".join(lines),
                    "inline": False
                }
            ],
            "footer": {"text": "Higher Sharpe Ratio = Better return per unit of risk"},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_most_mentioned_compact(self) -> Optional[Dict]:
        """Build compact most mentioned stocks"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''SELECT ticker, COUNT(*) as mentions, 
                            AVG(price_change_pct) as avg_perf,
                            SUM(CASE WHEN reached_winner = 1 THEN 1 ELSE 0 END) as wins,
                            SUM(CASE WHEN reached_loser = 1 THEN 1 ELSE 0 END) as losses
                     FROM stock_tracking
                     GROUP BY ticker
                     HAVING mentions >= 2
                     ORDER BY mentions DESC
                     LIMIT 10''')
        
        mentioned = c.fetchall()
        conn.close()
        
        if not mentioned:
            return None
        
        lines = []
        for i, (ticker, mentions, avg_perf, wins, losses) in enumerate(mentioned, 1):
            win_rate = (wins / mentions * 100) if mentions > 0 else 0
            emoji = "🔥" if mentions >= 5 else "📊"
            perf_emoji = "🟢" if avg_perf > 0 else "🔴"
            lines.append(f"{i}. {emoji} **${ticker}** ({mentions}x) {perf_emoji} {avg_perf:+.1f}% | WR: {win_rate:.0f}%")
        
        return {
            "title": "🗣️ Most Mentioned Stocks",
            "color": 0xFF6600,
            "fields": [
                {
                    "name": "Reddit DD Frequency",
                    "value": "\n".join(lines),
                    "inline": False
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_recent_activity_summary(self, hours: int = 24) -> Dict:
        """Get summary of recent activity"""
        conn = self.get_connection()
        c = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        c.execute('''SELECT COUNT(*) FROM posted_submissions 
                     WHERE scraped_date > ?''', (cutoff_time,))
        new_posts = c.fetchone()[0]
        
        c.execute('''SELECT COUNT(DISTINCT ticker) FROM stock_tracking 
                     WHERE initial_date > ?''', (cutoff_time,))
        new_tickers = c.fetchone()[0]
        
        c.execute('''SELECT COUNT(*) FROM stock_tracking 
                     WHERE last_updated > ? AND status IN ('WINNER', 'LOSER')''', (cutoff_time,))
        new_alerts = c.fetchone()[0]
        
        conn.close()
        
        return {
            'new_posts': new_posts,
            'new_tickers': new_tickers,
            'new_alerts': new_alerts,
            'period_hours': hours
        }
    
    def _create_progress_bar(self, value: float, max_value: float, length: int = 10) -> str:
        """Create a visual progress bar using Unicode blocks"""
        if max_value == 0:
            return "░" * length
        
        filled_length = int((value / max_value) * length)
        filled_length = max(0, min(length, filled_length))
        
        # Use block characters
        bar = "▓" * filled_length + "░" * (length - filled_length)
        return bar
    
    def generate_daily_digest_embed(self) -> List[Dict]:
        """NEW: Generate a comprehensive daily digest email-style embed"""
        embeds = []
        
        # Header with date
        now = datetime.now()
        
        header_embed = {
            "title": f"📊 Daily Turd News Network Digest - {now.strftime('%B %d, %Y')}",
            "description": "Your daily summary of Reddit DD performance and market insights",
            "color": COLOR_PREMIUM,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "💎 Turd News Network Enhanced v4.0"}
        }
        
        # Get 24h stats
        activity = self.get_recent_activity_summary(24)
        
        header_embed["fields"] = [
            {
                "name": "📈 Last 24 Hours",
                "value": f"**{activity['new_posts']}** new DD posts\n**{activity['new_tickers']}** new stocks tracked\n**{activity['new_alerts']}** win/loss alerts",
                "inline": False
            }
        ]
        
        embeds.append(header_embed)

        # Add ONLY the most-mentioned stocks to the digest (other stats are sent separately)
        most_mentioned = self._build_most_mentioned_compact()
        if most_mentioned:
            embeds.append(most_mentioned)

        return embeds
