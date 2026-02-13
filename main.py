"""
Turd News Network - Enhanced Dashboard v6.0
Complete dashboard redesign with all new features
"""

import asyncio
import time
import os
import traceback
import warnings
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from config import *
from database import DatabaseManager

warnings.filterwarnings('ignore', category=DeprecationWarning, module='yfinance')

from console_formatter import Colors, print_banner, print_separator
from scraper import RedditScraper
from stock_data import StockDataFetcher
from analysis import AnalysisEngine
from discord_embed import DiscordEmbedBuilder
from performance import PerformanceTracker
from sentiment import SentimentAnalyzer
from backtesting import EnhancedBacktester
from stats_reporter import StatsReporter
from watchlist_manager import WatchlistManager, WatchlistView, NotificationSettingsModal


# ============== DASHBOARD MODALS ==============

class SearchModal(discord.ui.Modal, title="🔍 Quick Search"):
    """Quick Search - Generate 10-embed detailed stock report"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., NVDA, MSFT, BTC-USD",
        min_length=1, max_length=20,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        ticker = self.ticker_input.value.strip().upper()
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from ticker_report import TickerReportBuilder
            builder = TickerReportBuilder()
            
            loop = asyncio.get_running_loop()
            embeds, chart_path = await loop.run_in_executor(
                None, builder.build_report_sync, ticker
            )
            
            if embeds is None:
                await interaction.followup.send(f"❌ Could not fetch data for **${ticker}**", ephemeral=True)
                return
            
            discord_embeds = []
            for embed_dict in embeds:
                embed = discord.Embed(
                    title=embed_dict.get('title'),
                    description=embed_dict.get('description'),
                    color=embed_dict.get('color', 0x3498DB),
                    url=embed_dict.get('url')
                )
                for field in embed_dict.get('fields', []):
                    embed.add_field(
                        name=field.get('name', '\u200b')[:256],
                        value=str(field.get('value', '\u200b'))[:1024],
                        inline=field.get('inline', False)
                    )
                discord_embeds.append(embed)
            
            batch_1 = discord_embeds[:5]
            batch_2 = discord_embeds[5:]
            
            if chart_path and os.path.exists(chart_path):
                file = discord.File(chart_path, filename=os.path.basename(chart_path))
                await interaction.followup.send(embeds=batch_1, file=file, ephemeral=True)
                try:
                    os.remove(chart_path)
                except:
                    pass
            else:
                await interaction.followup.send(embeds=batch_1, ephemeral=True)
            
            if batch_2:
                await asyncio.sleep(0.5)
                await interaction.followup.send(embeds=batch_2, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class ReportsModal(discord.ui.Modal, title="📊 In-Depth Report"):
    """Generate HTML dashboard report"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., NVDA, MSFT",
        min_length=1, max_length=20,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        ticker = self.ticker_input.value.strip().upper()
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from company_intelligence_dashboard import generate_company_dashboard
            
            loop = asyncio.get_running_loop()
            html_file = await loop.run_in_executor(
                None, generate_company_dashboard, ticker
            )
            
            if html_file and os.path.exists(html_file):
                embed = discord.Embed(
                    title=f"📊 {ticker} - Company Intelligence Dashboard",
                    description="**17-Section Comprehensive Report**",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="💾 How to View",
                    value="1. Download the HTML file below\n2. Open in any web browser\n3. Use the sidebar to navigate",
                    inline=False
                )
                embed.set_footer(text="Turd News Network v6.0")
                
                await interaction.followup.send(embed=embed, file=discord.File(html_file), ephemeral=True)
                
                try:
                    os.remove(html_file)
                except:
                    pass
            else:
                await interaction.followup.send(f"❌ Could not generate report for **{ticker}**", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class MarketOverviewModal(discord.ui.Modal, title="📈 Market Overview"):
    """Quick Market Overview - Show major indices"""
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            # Get market data
            indices = ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT', 'VIX']
            
            loop = asyncio.get_running_loop()
            market_data = {}
            
            def fetch_market():
                from stock_data import StockDataFetcher
                fetcher = StockDataFetcher(None)
                for ticker in indices:
                    data = fetcher.get_stock_data(ticker)
                    if data:
                        market_data[ticker] = data
                    time.sleep(0.5)
            
            await loop.run_in_executor(None, fetch_market)
            
            embed = discord.Embed(
                title="📈 Market Overview",
                description="Major indices and ETFs",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            for ticker, data in market_data.items():
                price = data.get('price', 0)
                change = data.get('change_pct', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                
                embed.add_field(
                    name=f"{ticker}",
                    value=f"${price:.2f} {emoji} {change:+.2f}%",
                    inline=True
                )
            
            embed.set_footer(text="Turd News Network v6.0 - Market Overview")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class ShortSqueezeModal(discord.ui.Modal, title="🎯 Short Squeeze Watch"):
    """Show stocks with high short interest"""
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            # Get stocks from database with high short interest
            from database import DatabaseManager
            db = DatabaseManager()
            
            conn = db.get_connection()
            c = conn.cursor()
            
            # Get stocks with short interest data
            c.execute('''
                SELECT ticker, MAX(price_change_pct) as change_pct, 
                       MAX(short_interest) as short_interest
                FROM stock_tracking 
                WHERE short_interest IS NOT NULL AND short_interest > 0.1
                GROUP BY ticker
                ORDER BY short_interest DESC
                LIMIT 15
            ''')
            
            results = c.fetchall()
            conn.close()
            
            if not results:
                await interaction.followup.send(
                    "🎯 **Short Squeeze Watch**\n\nNo high short interest stocks found in database yet. Run some scans first!",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="🎯 Short Squeeze Watch",
                description="Stocks with high short interest (>10%)",
                color=0xFF6600,
                timestamp=datetime.now()
            )
            
            for ticker, change, short_pct in results:
                short_emoji = "🔥" if short_pct > 0.20 else "⚠️" if short_pct > 0.15 else "👀"
                change_emoji = "🟢" if change >= 0 else "🔴"
                
                embed.add_field(
                    name=f"{short_emoji} ${ticker}",
                    value=f"Short: **{short_pct*100:.1f}%** | {change_emoji} {change:+.1f}%",
                    inline=True
                )
            
            embed.set_footer(text="Turd News Network v6.0 - Short Squeeze Watch")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class InsiderModal(discord.ui.Modal, title="👀 Insider Feed"):
    """Show recent insider trading activity"""
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            # Try to get insider data from Finnhub or database
            from database import DatabaseManager
            from stock_data import StockDataFetcher
            
            db = DatabaseManager()
            fetcher = StockDataFetcher(db)
            
            # Get some popular tickers to check
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD']
            
            insider_trades = []
            
            loop = asyncio.get_running_loop()
            
            def fetch_insider():
                for ticker in tickers:
                    try:
                        data = fetcher.get_insider_data(ticker, ticker)
                        if data and data.get('buys', 0) > 0:
                            insider_trades.append({
                                'ticker': ticker,
                                'data': data
                            })
                    except:
                        continue
                    time.sleep(0.5)
            
            await loop.run_in_executor(None, fetch_insider)
            
            embed = discord.Embed(
                title="👀 Insider Activity Feed",
                description="Recent insider buying activity",
                color=0x9B59B6,
                timestamp=datetime.now()
            )
            
            if not insider_trades:
                embed.description = "No recent insider activity found. Try again later!"
            else:
                for item in insider_trades[:10]:
                    ticker = item['ticker']
                    data = item['data']
                    buys = data.get('buys', 0)
                    sells = data.get('sells', 0)
                    
                    embed.add_field(
                        name=f"${ticker}",
                        value=f"🟢 **{buys}** Buys | 🔴 **{sells}** Sells",
                        inline=True
                    )
            
            embed.set_footer(text="Turd News Network v6.0 - Insider Feed")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class CongressModal(discord.ui.Modal, title="🏛️ Congress Trading"):
    """Show recent congressional trading activity"""
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            # Get recent congress trades from database
            conn = db.get_connection()
            c = conn.cursor()
            
            # Check if congress_trades table exists and has data
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='congress_trades'")
            if c.fetchone():
                c.execute('''
                    SELECT ticker, politician_name, party, transaction_type, amount_range
                    FROM congress_trades
                    ORDER BY transaction_date DESC
                    LIMIT 15
                ''')
                results = c.fetchall()
                conn.close()
                
                embed = discord.Embed(
                    title="🏛️ Congressional Trading",
                    description="Recent trades by US Congress members",
                    color=0x1ABC9C,
                    timestamp=datetime.now()
                )
                
                if results:
                    for ticker, member, party, txn_type, amount in results:
                        emoji = "🟢" if "PURCHASE" in str(txn_type).upper() else "🔴"
                        embed.add_field(
                            name=f"{emoji} ${ticker}",
                            value=f"{member} ({party})\n{txn_type} - {amount}",
                            inline=True
                        )
                else:
                    embed.description = "No recent congressional trades found. Run some scans first!"
            else:
                conn.close()
                embed = discord.Embed(
                    title="🏛️ Congressional Trading",
                    description="Congress trading data will appear here after scans!",
                    color=0x1ABC9C,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="📝 Note",
                    value="Run some stock scans to collect congress trading data. The bot tracks when stocks mentioned in DD have congress activity.",
                    inline=False
                )
            
            embed.set_footer(text="Turd News Network v6.0 - Congress Trading")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class EarningsModal(discord.ui.Modal, title="📅 Earnings Calendar"):
    """Show upcoming earnings for watchlist stocks"""
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            from stock_data import StockDataFetcher
            
            user_id = str(interaction.user.id)
            db = DatabaseManager()
            fetcher = StockDataFetcher(db)
            
            # Get user's watchlist
            watchlist = db.get_user_watchlist(user_id)
            
            if not watchlist:
                await interaction.followup.send(
                    "📅 **Earnings Calendar**\n\nYour watchlist is empty! Add stocks to see their earnings dates.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="📅 Earnings Calendar",
                description="Upcoming earnings for your watchlist stocks",
                color=0xE67E22,
                timestamp=datetime.now()
            )
            
            loop = asyncio.get_running_loop()
            
            def fetch_earnings():
                for item in watchlist[:15]:
                    ticker = item['ticker']
                    try:
                        data = fetcher.get_stock_data(ticker)
                        if data and data.get('earnings_date'):
                            embed.add_field(
                                name=f"${ticker}",
                                value=f"📅 {data.get('earnings_date', 'TBA')}",
                                inline=True
                            )
                    except:
                        continue
            
            await loop.run_in_executor(None, fetch_earnings)
            
            if len(embed.fields) == 0:
                embed.description = "No earnings dates found for your watchlist stocks."
            
            embed.set_footer(text="Turd News Network v6.0 - Earnings Calendar")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class IntervalModal(discord.ui.Modal, title="⏱️ Refresh Interval"):
    """Set refresh interval"""
    
    def __init__(self):
        super().__init__(timeout=60)
        self.interval = discord.ui.TextInput(
            label="Interval (seconds)",
            placeholder="30, 60, 120 (min: 10, max: 300)",
            default="30",
            required=True
        )
        self.add_item(self.interval)
    
    async def callback(self, interaction: discord.Interaction):
        try:
            interval = int(self.interval.value)
            interval = max(10, min(300, interval))
            await interaction.response.send_message(
                f"✅ Refresh interval set to **{interval} seconds**",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message("❌ Invalid interval", ephemeral=True)


# ============== MAIN DASHBOARD VIEW ==============

class OverviewView(discord.ui.View):
    """Main dashboard with all buttons - ENHANCED v6.0"""
    
    def __init__(self, stock_fetcher, watchlist_manager):
        super().__init__(timeout=None)
        self.stock_fetcher = stock_fetcher
        self.watchlist_manager = watchlist_manager
    
    # === ROW 1: Search & Reports ===
    @discord.ui.button(label="🔍 Quick Search", style=discord.ButtonStyle.primary, row=0)
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModal())
    
    @discord.ui.button(label="📊 Full Report", style=discord.ButtonStyle.primary, row=0)
    async def reports_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReportsModal())
    
    @discord.ui.button(label="⭐ Watchlist", style=discord.ButtonStyle.success, row=0)
    async def watchlist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        
        # Try to use watchlist manager, fall back to simple message
        try:
            if hasattr(self, 'watchlist_manager') and self.watchlist_manager:
                self.watchlist_manager.db.ensure_user_exists(user_id, username=interaction.user.name)
                watchlist = self.watchlist_manager.db.get_user_watchlist(user_id)
                
                if watchlist:
                    stocks = "\n".join([f"• ${item['ticker']}" for item in watchlist[:10]])
                    desc = f"**Your tracked stocks:**\n{stocks}"
                else:
                    desc = "Your watchlist is empty! Use Quick Search to add stocks."
            else:
                desc = "Watchlist feature is loading..."
        except Exception as e:
            desc = f"Watchlist: {str(e)[:100]}"
        
        embed = discord.Embed(
            title="⭐ Your Watchlist",
            description=desc,
            color=0x3498db,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # === ROW 2: Market Data ===
    @discord.ui.button(label="📈 Market Overview", style=discord.ButtonStyle.primary, row=1)
    async def market_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MarketOverviewModal())
    
    @discord.ui.button(label="🔥 Top Movers", style=discord.ButtonStyle.primary, row=1)
    async def movers_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            conn = db.get_connection()
            c = conn.cursor()
            
            # Get top gainers
            c.execute('''
                SELECT ticker, MAX(price_change_pct) as max_gain
                FROM stock_tracking
                WHERE price_change_pct > 0
                GROUP BY ticker
                ORDER BY max_gain DESC
                LIMIT 10
            ''')
            gainers = c.fetchall()
            
            # Get top losers
            c.execute('''
                SELECT ticker, MIN(price_change_pct) as max_loss
                FROM stock_tracking
                WHERE price_change_pct < 0
                GROUP BY ticker
                ORDER BY max_loss ASC
                LIMIT 10
            ''')
            losers = c.fetchall()
            conn.close()
            
            embed = discord.Embed(
                title="🔥 Top Movers",
                description="Best and worst performing stocks from DD mentions",
                color=0xFF6600,
                timestamp=datetime.now()
            )
            
            gainer_text = "\n".join([f"📈 **${t}** {g:+.1f}%" for t, g in gainers]) if gainers else "No gainers yet"
            loser_text = "\n".join([f"📉 **${t}** {l:.1f}%" for t, l in losers]) if losers else "No losers yet"
            
            embed.add_field(name="📈 Top Gainers", value=gainer_text, inline=True)
            embed.add_field(name="📉 Top Losers", value=loser_text, inline=True)
            embed.set_footer(text="Turd News Network v6.0")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @discord.ui.button(label="🎯 Short Squeeze", style=discord.ButtonStyle.danger, row=1)
    async def squeeze_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ShortSqueezeModal())
    
    # === ROW 3: Activity Feeds ===
    @discord.ui.button(label="👀 Insider Feed", style=discord.ButtonStyle.secondary, row=2)
    async def insider_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(InsiderModal())
    
    @discord.ui.button(label="🏛️ Congress", style=discord.ButtonStyle.secondary, row=2)
    async def congress_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CongressModal())
    
    @discord.ui.button(label="📅 Earnings", style=discord.ButtonStyle.secondary, row=2)
    async def earnings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EarningsModal())
    
    # === ROW 4: Settings ===
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.success, row=3)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 Dashboard refreshed!", ephemeral=True, delete_after=3)
    
    @discord.ui.button(label="⚙️ Settings", style=discord.ButtonStyle.secondary, row=3)
    async def settings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ Settings",
            description="**Configure Your Preferences**\n\n"
                       "🔔 **Notifications:** DM alerts on price targets\n"
                       "⏱️ **Refresh Rate:** How often to check prices\n\n"
                       "Use the command `!alerts` in chat to set up price alerts.",
            color=0x3498db,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class SettingsView(discord.ui.View):
    """Settings with more options"""
    
    def __init__(self, watchlist_manager, user_id):
        super().__init__(timeout=300)
        self.watchlist_manager = watchlist_manager
        self.user_id = user_id
    
    @discord.ui.button(label="🔔 Notifications", style=discord.ButtonStyle.primary, row=0)
    async def notif_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = self.watchlist_manager.db.get_notification_settings(self.user_id)
        await interaction.response.send_modal(
            NotificationSettingsModal(self.watchlist_manager.db, self.user_id, settings)
        )
    
    @discord.ui.button(label="⏱️ Refresh Rate", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IntervalModal())


# ============== DASHBOARD BOT ==============

class DashboardBot(commands.Bot):
    """Main bot class"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
        print("[INIT] Loading components...")
        self.db = DatabaseManager()
        self.scraper = RedditScraper()
        self._seen_posts_this_scan: set = set()  # Track posts seen during current scan
        self.stock_fetcher = StockDataFetcher(self.db)
        self.analysis = AnalysisEngine()
        self.discord = DiscordEmbedBuilder(WEBHOOK_URL, self.db)
        self.performance = PerformanceTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.backtester = EnhancedBacktester()
        self.stats_reporter = StatsReporter()
        self.watchlist_manager = WatchlistManager(self.db, self.stock_fetcher, self)
        
        print("[INIT] All loaded!")
    
    async def setup_hook(self):
        await self.watchlist_manager.start_monitoring()
        self.reddit_scanner.start()
    
    @tasks.loop(hours=3)
    async def reddit_scanner(self):
        try:
            await self.process_posts()
        except Exception as e:
            print(f"[SCAN ERROR] {e}")
    
    @reddit_scanner.before_loop
    async def before_scan(self):
        await self.wait_until_ready()
    
    async def on_ready(self):
        print(f"[BOT] Ready: {self.user}")
        for guild in self.guilds:
            # Create stonk-bot channel for dashboard
            await self.create_dashboard_channel(guild)
            # Create stonks channel for DD posts
            await self.create_stonks_channel(guild)
    
    async def create_dashboard_channel(self, guild: discord.Guild):
        """Create #stonk-bot channel for the dashboard"""
        channel_name = "stonk-bot"
        
        channel = None
        for ch in guild.channels:
            if ch.name == channel_name and isinstance(ch, discord.TextChannel):
                channel = ch
                break
        
        if not channel:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
                print(f"[DASHBOARD] Created #{channel_name} channel")
            except Exception as e:
                print(f"[DASHBOARD] Error creating channel: {e}")
                return
    
    async def create_stonks_channel(self, guild: discord.Guild):
        """Create #stonks channel for DD posts"""
        channel_name = "stonks"
        
        channel = None
        for ch in guild.channels:
            if ch.name == channel_name and isinstance(ch, discord.TextChannel):
                channel = ch
                break
        
        if not channel:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
                print(f"[DD POST] Created #{channel_name} channel")
            except Exception as e:
                print(f"[DD POST] Error creating channel: {e}")
    
    async def process_posts(self):
        print_separator()
        print(f">> Starting Reddit Scan...")
        
        # Clear the in-memory seen posts set for this scan
        self._seen_posts_this_scan.clear()
        
        all_posts = self.scraper.scrape_all_subreddits()
        print(f"[DEBUG] Scraped {len(all_posts)} posts from subreddits")
        
        for post in all_posts:
            post['quality_score'] = self.analysis.calculate_quality_score(post)
            if ENABLE_SENTIMENT:
                sentiment = self.sentiment_analyzer.analyze_post_sentiment(post['title'], post['selftext'])
                post['sentiment'] = sentiment
        
        all_posts.sort(key=lambda x: x['quality_score'], reverse=True)
        
        print(f"[STATS] Found {len(all_posts)} DD posts")
        
        processed = 0
        skipped_already_sent = 0
        skipped_no_tickers = 0
        skipped_no_stock_data = 0
        
        for post in all_posts:
            post_id = post.get('id', 'unknown')
            
            # Check both database AND in-memory cache for this scan
            if post_id in self._seen_posts_this_scan or self.db.is_post_already_sent(post_id):
                skipped_already_sent += 1
                continue
            
            # Mark as seen in this scan
            self._seen_posts_this_scan.add(post_id)
            
            combined = post['title'] + ' ' + post['selftext']
            tickers = self.scraper.extract_tickers(combined)
            print(f"[DEBUG] Post {post_id}: Found tickers: {tickers}")
            
            if not tickers:
                skipped_no_tickers += 1
                print(f"[DEBUG] Post {post_id}: No tickers found, skipping")
                continue
            
            stock_list = []
            for ticker in tickers:
                print(f"[DEBUG] Fetching data for ticker: {ticker}")
                data = self.stock_fetcher.get_stock_data(ticker)
                if data:
                    stock_list.append(data)
                    self.db.save_stock_tracking(ticker, post_id, data.get('price', 0))
                    print(f"[DEBUG] Got stock data for {ticker}: price={data.get('price')}")
                else:
                    print(f"[DEBUG] No stock data for {ticker}")
                time.sleep(API_DELAY)
            
            if stock_list:
                print(f"[DEBUG] Sending {len(stock_list)} stocks to Discord: {[s.get('ticker') for s in stock_list]}")
                result = await self.send_to_stonks_channel(post, stock_list)
                if result:
                    print(f"[DEBUG] Successfully sent post to Discord")
                else:
                    print(f"[WARNING] Failed to send post to Discord")
                self.db.save_post(post, tickers, post['quality_score'], "")
                processed += 1
            else:
                skipped_no_stock_data += 1
                print(f"[DEBUG] No stock data found for any ticker, skipping post")
        
        print(f"[COMPLETE] Processed: {processed}/{len(all_posts)} (skipped: already_sent={skipped_already_sent}, no_tickers={skipped_no_tickers}, no_stock_data={skipped_no_stock_data})")
    
    async def send_to_stonks_channel(self, post, stock_list):
        try:
            print(f"[DEBUG] send_to_stonks_channel called. Guilds: {len(self.guilds)}")
            
            for guild in self.guilds:
                print(f"[DEBUG] Checking guild: {guild.name}")
                
                # Find the stonks channel
                stonks_channel = None
                for ch in guild.text_channels:
                    print(f"[DEBUG] Found channel: {ch.name}")
                    if ch.name == "stonks":
                        stonks_channel = ch
                        print(f"[DEBUG] Found #stonks channel!")
                        break
                
                if not stonks_channel:
                    print(f"[ERROR] No #stonks channel found in {guild.name}!")
                    continue
                
                print(f"[DEBUG] Posting to #{stonks_channel.name} in {guild.name}")
                
                quality = post.get('quality_score', 0)
                q_emoji = "💎" if quality >= 80 else "⭐" if quality >= 60 else "📊"
                color = COLOR_PREMIUM if quality >= 80 else COLOR_QUALITY if quality >= 60 else COLOR_STANDARD
                
                sentiment = post.get('sentiment', {})
                sent_text = sentiment.get('sentiment', 'NEUTRAL')
                sent_emoji = "🟢" if sent_text == 'BULLISH' else "🔴" if sent_text == 'BEARISH' else "🟡"
                
                # Post title
                title_embed = discord.Embed(
                    title=f"{q_emoji} {post['title'][:200]}",
                    url=post['url'],
                    color=color,
                    timestamp=datetime.now()
                )
                title_embed.description = f"**r/{post['subreddit']}** | {sent_emoji} {sent_text} | ⭐ {quality:.0f}/100"
                title_embed.set_footer(text="Turd News Network v6.0 | Due Diligence Scanner")
                await stonks_channel.send(embed=title_embed)
                
                # For each stock, generate 3 detailed embeds using TickerReportBuilder
                for sd in stock_list[:3]:
                    ticker = sd.get('ticker')
                    if not ticker:
                        continue
                    
                    print(f"[DEBUG] Building detailed embeds for {ticker}")
                    
                    # Use TickerReportBuilder to get the detailed embeds
                    try:
                        from ticker_report import TickerReportBuilder
                        builder = TickerReportBuilder()
                        
                        # Build the 10 embeds (we'll use specific ones)
                        loop = asyncio.get_running_loop()
                        embeds_list, chart_path = await loop.run_in_executor(
                            None, builder.build_report_sync, ticker
                        )
                        
                        if embeds_list:
                            # Send 3 detailed embeds: Signals/ML, Insider/Congress, Analyst/News
                            # Embed 7: Signals & ML (index 6)
                            # Embed 9: Insider/Congress (index 8)
                            # Embed 10: Analyst/News (index 9)
                            
                            embed_indices = [0, 1, 2]  # Sentiment/ML, Insider/Congress, Company Info
                            
                            for idx in embed_indices:
                                if idx < len(embeds_list):
                                    embed_dict = embeds_list[idx]
                                    embed = discord.Embed(
                                        title=embed_dict.get('title'),
                                        description=embed_dict.get('description'),
                                        color=embed_dict.get('color', 0x3498DB),
                                        url=embed_dict.get('url')
                                    )
                                    for field in embed_dict.get('fields', []):
                                        embed.add_field(
                                            name=field.get('name', '\u200b')[:256],
                                            value=str(field.get('value', '\u200b'))[:1024],
                                            inline=field.get('inline', False)
                                        )
                                    if embed_dict.get('footer', {}).get('text'):
                                        embed.set_footer(text=embed_dict['footer']['text'])
                                    if embed_dict.get('thumbnail', {}).get('url'):
                                        embed.set_thumbnail(url=embed_dict['thumbnail']['url'])
                                    
                                    await stonks_channel.send(embed=embed)
                                    await asyncio.sleep(0.5)  # Small delay between embeds
                                    
                            print(f"[DEBUG] Sent 3 detailed embeds for {ticker}")
                        else:
                            # Fallback to simple embed if builder fails
                            await self._send_simple_embed(stonks_channel, sd, post)
                            
                    except Exception as e:
                        print(f"[ERROR] TickerReportBuilder failed: {e}")
                        # Fallback to simple embed
                        await self._send_simple_embed(stonks_channel, sd, post)
                
                print(f"[DEBUG] Successfully sent all embeds to #{stonks_channel.name}")
                return True
                
        except Exception as e:
            print(f"[ERROR] send_to_stonks_channel failed: {e}")
            traceback.print_exc()
            return False
        return False
    
    async def _send_simple_embed(self, channel, sd, post):
        """Fallback simple embed if TickerReportBuilder fails"""
        ticker = sd.get('ticker', 'N/A')
        price = sd.get('price', 0)
        change = sd.get('change_pct', 0)
        sector = sd.get('sector', 'N/A')
        
        c_emoji = "🟢" if change >= 0 else "🔴"
        
        embed = discord.Embed(
            title=f"📊 {ticker} - {sector}",
            color=0x3498DB
        )
        embed.add_field(
            name=f"💰 Price",
            value=f"**${price:.2f}** {c_emoji} {change:+.2f}%",
            inline=True
        )
        
        # Add available data
        if sd.get('pe_ratio'):
            embed.add_field(name="📈 P/E", value=f"{sd.get('pe_ratio'):.1f}", inline=True)
        if sd.get('market_cap'):
            mc = sd.get('market_cap')
            mc_str = f"${mc/1e9:.1f}B" if mc >= 1e9 else f"${mc/1e6:.1f}M"
            embed.add_field(name="🏢 Market Cap", value=mc_str, inline=True)
        
        await channel.send(embed=embed)


# ============== MAIN ==============

async def run_bot():
    print("="*50)
    print("TURD NEWS NETWORK v6.0 - Starting...")
    print("="*50)
    
    bot = DashboardBot()
    
    try:
        await bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"[FATAL] {e}")


def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
