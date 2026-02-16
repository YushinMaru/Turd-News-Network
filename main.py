"""
Turd News Network - DD Scanner + Slash Commands Only
Dashboard UI removed - pure functionality retained
"""

import asyncio
import time
import os
import traceback
import warnings
import discord
from discord import app_commands
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
from watchlist_manager import WatchlistManager
from moderation import ModerationCog


# ============== SLASH COMMANDS ==============

class SlashCommands:
    """Slash command handlers - All kept for user access"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="search", description="Search for a stock ticker")
    @app_commands.describe(ticker="Stock ticker symbol (e.g., NVDA, MSFT)")
    async def search(self, interaction: discord.Interaction, ticker: str):
        """Search for a stock ticker"""
        print(f"[SLASH] /search called by user {interaction.user.id} ({interaction.user.name}) with ticker: {ticker}")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from ticker_report import TickerReportBuilder
            builder = TickerReportBuilder()
            
            ticker = ticker.strip().upper()
            loop = asyncio.get_running_loop()
            embeds, chart_path, chart_paths = await loop.run_in_executor(
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
    
    @app_commands.command(name="watchlist", description="Manage your watchlist")
    @app_commands.describe(action="Action: add, remove, or list")
    @app_commands.describe(ticker="Stock ticker to add or remove")
    async def watchlist(self, interaction: discord.Interaction, action: str, ticker: str = None):
        """Manage your watchlist"""
        print(f"[SLASH] /watchlist called by user {interaction.user.id} ({interaction.user.name}) action: {action} ticker: {ticker}")
        user_id = str(interaction.user.id)
        
        if action.lower() == "list":
            self.bot.db.ensure_user_exists(user_id, username=interaction.user.name)
            watchlist = self.bot.db.get_user_watchlist(user_id)
            
            if not watchlist:
                embed = discord.Embed(
                    title="⭐ Your Watchlist",
                    description="Your watchlist is empty! Use `/watchlist add TICKER` to add stocks.",
                    color=0x3498db
                )
            else:
                stocks = "\n".join([f"• ${item['ticker']}" for item in watchlist])
                embed = discord.Embed(
                    title="⭐ Your Watchlist",
                    description=f"**Tracked stocks:**\n{stocks}",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        elif action.lower() == "add":
            if not ticker:
                await interaction.response.send_message("❌ Please provide a ticker symbol", ephemeral=True)
                return
            
            ticker = ticker.strip().upper()
            self.bot.db.ensure_user_exists(user_id, username=interaction.user.name)
            self.bot.db.add_to_watchlist(user_id, ticker)
            
            await interaction.response.send_message(f"✅ Added **${ticker}** to your watchlist!", ephemeral=True)
        
        elif action.lower() == "remove":
            if not ticker:
                await interaction.response.send_message("❌ Please provide a ticker symbol", ephemeral=True)
                return
            
            ticker = ticker.strip().upper()
            self.bot.db.ensure_user_exists(user_id, username=interaction.user.name)
            self.bot.db.remove_from_watchlist(user_id, ticker)
            
            await interaction.response.send_message(f"✅ Removed **${ticker}** from your watchlist!", ephemeral=True)
        
        else:
            await interaction.response.send_message("❌ Invalid action. Use: add, remove, or list", ephemeral=True)
    
    @app_commands.command(name="market", description="Show market overview")
    async def market(self, interaction: discord.Interaction):
        """Show market overview"""
        print(f"[SLASH] /market called by user {interaction.user.id} ({interaction.user.name})")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
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
            
            embed.set_footer(text="Turd News Network - Market Overview")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @app_commands.command(name="movers", description="Show top movers")
    async def movers(self, interaction: discord.Interaction):
        """Show top movers"""
        print(f"[SLASH] /movers called by user {interaction.user.id} ({interaction.user.name})")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            conn = db.get_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT ticker, MAX(price_change_pct) as max_gain
                FROM stock_tracking
                WHERE price_change_pct > 0
                GROUP BY ticker
                ORDER BY max_gain DESC
                LIMIT 10
            ''')
            gainers = c.fetchall()
            
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
            embed.set_footer(text="Turd News Network")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @app_commands.command(name="shortsqueeze", description="Show short squeeze candidates")
    async def shortsqueeze(self, interaction: discord.Interaction):
        """Show short squeeze candidates"""
        print(f"[SLASH] /shortsqueeze called by user {interaction.user.id} ({interaction.user.name})")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            conn = db.get_connection()
            c = conn.cursor()
            
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
            
            embed.set_footer(text="Turd News Network - Short Squeeze Watch")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @app_commands.command(name="insider", description="Show insider activity")
    async def insider(self, interaction: discord.Interaction):
        """Show insider activity"""
        print(f"[SLASH] /insider called by user {interaction.user.id} ({interaction.user.name})")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            from stock_data import StockDataFetcher
            
            db = DatabaseManager()
            fetcher = StockDataFetcher(db)
            
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
            
            embed.set_footer(text="Turd News Network - Insider Feed")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @app_commands.command(name="congress", description="Show congress trading activity")
    async def congress(self, interaction: discord.Interaction):
        """Show congress trading"""
        print(f"[SLASH] /congress called by user {interaction.user.id} ({interaction.user.name})")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            
            conn = db.get_connection()
            c = conn.cursor()
            
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
                    value="Run some stock scans to collect congress trading data.",
                    inline=False
                )
            
            embed.set_footer(text="Turd News Network - Congress Trading")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @app_commands.command(name="earnings", description="Show upcoming earnings")
    async def earnings(self, interaction: discord.Interaction):
        """Show upcoming earnings"""
        print(f"[SLASH] /earnings called by user {interaction.user.id} ({interaction.user.name})")
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            from database import DatabaseManager
            from stock_data import StockDataFetcher
            
            user_id = str(interaction.user.id)
            db = DatabaseManager()
            fetcher = StockDataFetcher(db)
            
            watchlist = db.get_user_watchlist(user_id)
            
            if not watchlist:
                await interaction.followup.send(
                    "📅 **Earnings Calendar**\n\nYour watchlist is empty! Use `/watchlist add TICKER` to add stocks.",
                    ephemeral=True
                )
                return
            
            loop = asyncio.get_running_loop()
            earnings_data = []
            
            def fetch_earnings():
                for item in watchlist[:15]:
                    ticker = item['ticker']
                    try:
                        data = fetcher.get_stock_data(ticker)
                        if data and data.get('earnings_date'):
                            earnings_data.append({
                                'ticker': ticker,
                                'date': data.get('earnings_date', 'TBA')
                            })
                    except:
                        continue
            
            await loop.run_in_executor(None, fetch_earnings)
            
            embed = discord.Embed(
                title="📅 Earnings Calendar",
                description="Upcoming earnings for your watchlist stocks",
                color=0xE67E22,
                timestamp=datetime.now()
            )
            
            if not earnings_data:
                embed.description = "No earnings dates found for your watchlist stocks."
            else:
                for item in earnings_data:
                    embed.add_field(
                        name=f"${item['ticker']}",
                        value=f"📅 {item['date']}",
                        inline=True
                    )
            
            embed.set_footer(text="Turd News Network - Earnings Calendar")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @app_commands.command(name="alert", description="Set a price alert for a stock")
    @app_commands.describe(ticker="Stock ticker (e.g., NVDA)")
    @app_commands.describe(direction="above or below current price")
    @app_commands.describe(price="Target price")
    async def alert(self, interaction: discord.Interaction, ticker: str, direction: str, price: str):
        """Set a price alert"""
        print(f"[SLASH] /alert called by user {interaction.user.id} ({interaction.user.name}) ticker: {ticker} direction: {direction} price: {price}")
        user_id = str(interaction.user.id)
        ticker = ticker.strip().upper()
        
        try:
            price_val = float(price.replace('$', '').replace(',', ''))
        except ValueError:
            await interaction.response.send_message("Invalid price format. Use like: 100 or 100.50", ephemeral=True)
            return
        
        if direction.lower() not in ['above', 'below']:
            await interaction.response.send_message("Direction must be 'above' or 'below'", ephemeral=True)
            return
        
        self.bot.db.ensure_user_exists(user_id, username=interaction.user.name)
        
        if direction.lower() == "above":
            self.bot.db.add_to_watchlist(user_id, ticker, notes='', alert_price_above=price_val, alert_price_below=None)
        else:
            self.bot.db.add_to_watchlist(user_id, ticker, notes='', alert_price_above=None, alert_price_below=price_val)
        
        emoji = "📈" if direction.lower() == "above" else "📉"
        await interaction.response.send_message(
            f"{emoji} Alert set for **{ticker}** {direction} **${price_val:.2f}**",
            ephemeral=True
        )
    
    @app_commands.command(name="alerts", description="View your price alerts")
    async def alerts(self, interaction: discord.Interaction):
        """View your price alerts"""
        print(f"[SLASH] /alerts called by user {interaction.user.id} ({interaction.user.name})")
        user_id = str(interaction.user.id)
        
        watchlist = self.bot.db.get_user_watchlist(user_id)
        alerts = [w for w in watchlist if w.get('alert_enabled') and (w.get('alert_price_above') or w.get('alert_price_below'))]
        
        if not alerts:
            embed = discord.Embed(
                title="Your Price Alerts",
                description="No alerts set! Use /alert TICKER above/below PRICE",
                color=0x3498db,
                timestamp=datetime.now()
            )
        else:
            embed = discord.Embed(
                title="Your Price Alerts",
                description=f"You have {len(alerts)} alert(s) set:",
                color=0x3498db,
                timestamp=datetime.now()
            )
            for item in alerts[:10]:
                ticker = item.get('ticker', 'N/A')
                above = item.get('alert_price_above')
                below = item.get('alert_price_below')
                above_str = f"📈 ${above:.2f}" if above else ""
                below_str = f"📉 ${below:.2f}" if below else ""
                embed.add_field(name=f"${ticker}", value=f"{above_str} {below_str}".strip(), inline=True)
        
        embed.set_footer(text="Turd News Network")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="report", description="Generate a comprehensive HTML report")
    @app_commands.describe(ticker="Stock ticker (e.g., NVDA)")
    async def report(self, interaction: discord.Interaction, ticker: str):
        """Generate HTML report"""
        print(f"[SLASH] /report called by user {interaction.user.id} ({interaction.user.name}) with ticker: {ticker}")
        await interaction.response.defer(ephemeral=True, thinking=True)
        ticker = ticker.strip().upper()
        
        try:
            from company_intelligence_dashboard import generate_company_dashboard
            
            loop = asyncio.get_running_loop()
            html_file = await loop.run_in_executor(None, generate_company_dashboard, ticker)
            
            if html_file and os.path.exists(html_file):
                embed = discord.Embed(
                    title=f"{ticker} - Company Intelligence Report",
                    description="17-Section Comprehensive Analysis",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                embed.add_field(name="Download", value="Download the HTML file below to view", inline=False)
                embed.set_footer(text="Turd News Network")
                
                await interaction.followup.send(embed=embed, file=discord.File(html_file), ephemeral=True)
                try:
                    os.remove(html_file)
                except:
                    pass
            else:
                await interaction.followup.send(f"Could not generate report for **{ticker}**", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)[:200]}", ephemeral=True)


# ============== MAIN BOT ==============

class TurdNewsBot(commands.Bot):
    """Main bot class - DD Scanner + Slash Commands only"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
        print("[INIT] Loading components...")
        self.db = DatabaseManager()
        self.scraper = RedditScraper()
        self._seen_posts_this_scan: set = set()
        self.stock_fetcher = StockDataFetcher(self.db)
        self.analysis = AnalysisEngine()
        self.discord = DiscordEmbedBuilder(WEBHOOK_URL, self.db)
        self.performance = PerformanceTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.backtester = EnhancedBacktester()
        self.stats_reporter = StatsReporter()
        self.watchlist_manager = WatchlistManager(self.db, self.stock_fetcher, self)
        
        # Slash commands
        self.slash_cmds = SlashCommands(self)
        
        print("[INIT] All loaded!")
    
    async def setup_hook(self):
        """Setup hook - starts tasks and syncs commands"""
        # Start background tasks
        await self.watchlist_manager.start_monitoring()
        self.reddit_scanner.start()
        
        # Load moderation cog
        try:
            await self.add_cog(ModerationCog(self))
            print("[MOD] Moderation cog loaded successfully")
        except Exception as e:
            print(f"[MOD] Error loading moderation cog: {e}")
        
        # Register slash commands
        self.tree.add_command(self.slash_cmds.search)
        self.tree.add_command(self.slash_cmds.watchlist)
        self.tree.add_command(self.slash_cmds.market)
        self.tree.add_command(self.slash_cmds.movers)
        self.tree.add_command(self.slash_cmds.shortsqueeze)
        self.tree.add_command(self.slash_cmds.insider)
        self.tree.add_command(self.slash_cmds.congress)
        self.tree.add_command(self.slash_cmds.earnings)
        self.tree.add_command(self.slash_cmds.alert)
        self.tree.add_command(self.slash_cmds.alerts)
        self.tree.add_command(self.slash_cmds.report)
        
        # Register moderation commands from cog
        try:
            mod_cog = self.get_cog("ModerationCog")
            if mod_cog:
                for cmd in mod_cog.walk_commands():
                    self.tree.add_command(cmd)
                print(f"[MOD] Added {len(list(mod_cog.walk_commands()))} mod commands to tree")
            else:
                print("[MOD] WARNING: ModerationCog not found")
        except Exception as e:
            print(f"[MOD] Error adding mod commands: {e}")
        
        # Sync commands with Discord
        try:
            await self.tree.sync()
            print("[SLASH] Commands synced successfully!")
        except Exception as e:
            print(f"[SLASH] Error syncing commands: {e}")
    
    @tasks.loop(hours=3)
    async def reddit_scanner(self):
        """Reddit DD Scanner - runs every 3 hours"""
        try:
            await self.process_posts()
        except Exception as e:
            print(f"[SCAN ERROR] {e}")
    
    @reddit_scanner.before_loop
    async def before_scan(self):
        await self.wait_until_ready()
    
    async def on_ready(self):
        """Bot ready - just log info"""
        print(f"[BOT] Ready: {self.user}")
        print(f"[SLASH] Available commands: /search, /watchlist, /market, /movers, /shortsqueeze, /insider, /congress, /earnings, /alert, /alerts, /report")
        print(f"[SCAN] Reddit DD scanner running - scans every 3 hours")
    
    async def process_posts(self):
        """Process DD posts from Reddit subreddits"""
        print_separator()
        print(f">> Starting Reddit DD Scan...")
        
        self._seen_posts_this_scan.clear()
        
        # Scrape all subreddits
        all_posts = self.scraper.scrape_all_subreddits()
        print(f"[DEBUG] Scraped {len(all_posts)} posts from subreddits")
        
        # Analyze and score posts
        for post in all_posts:
            post['quality_score'] = self.analysis.calculate_quality_score(post)
            if ENABLE_SENTIMENT:
                sentiment = self.sentiment_analyzer.analyze_post_sentiment(post['title'], post['selftext'])
                post['sentiment'] = sentiment
        
        # Sort by quality score
        all_posts.sort(key=lambda x: x['quality_score'], reverse=True)
        
        print(f"[STATS] Found {len(all_posts)} DD posts")
        
        processed = 0
        skipped_already_sent = 0
        skipped_no_tickers = 0
        skipped_no_stock_data = 0
        
        for post in all_posts:
            post_id = post.get('id', 'unknown')
            
            # Skip duplicates
            if post_id in self._seen_posts_this_scan or self.db.is_post_already_sent(post_id):
                skipped_already_sent += 1
                continue
            
            self._seen_posts_this_scan.add(post_id)
            
            # Extract tickers
            combined = post['title'] + ' ' + post['selftext']
            tickers = self.scraper.extract_tickers(combined)
            
            if not tickers:
                skipped_no_tickers += 1
                continue
            
            # Get stock data for each ticker
            stock_list = []
            for ticker in tickers:
                data = self.stock_fetcher.get_stock_data(ticker)
                if data:
                    stock_list.append(data)
                    self.db.save_stock_tracking(ticker, post_id, data.get('price', 0))
                time.sleep(API_DELAY)
            
            if stock_list:
                result = await self.send_dd_to_channel(post, stock_list)
                if result:
                    self.db.save_post(post, tickers, post['quality_score'], "")
                    processed += 1
            else:
                skipped_no_stock_data += 1
        
        print(f"[COMPLETE] Processed: {processed}/{len(all_posts)}")
        
        # Send summary embed after scan completes
        await self.send_scan_summary(processed, skipped_already_sent, skipped_no_tickers, skipped_no_stock_data, all_posts)
    
    async def send_dd_to_channel(self, post, stock_list):
        """Send DD post to stonks channel"""
        try:
            for guild in self.guilds:
                stonks_channel = None
                for ch in guild.text_channels:
                    if ch.name == "stonks":
                        stonks_channel = ch
                        break
                
                if not stonks_channel:
                    # Create stonks channel if it doesn't exist
                    try:
                        overwrites = {
                            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                        }
                        stonks_channel = await guild.create_text_channel("stonks", overwrites=overwrites)
                        print(f"[DD] Created #stonks channel")
                    except Exception as e:
                        print(f"[DD] Could not create stonks channel: {e}")
                        continue
                
                # Send the DD post
                quality = post.get('quality_score', 0)
                q_emoji = "💎" if quality >= 80 else "⭐" if quality >= 60 else "📊"
                color = COLOR_PREMIUM if quality >= 80 else COLOR_QUALITY if quality >= 60 else COLOR_STANDARD
                
                sentiment = post.get('sentiment', {})
                sent_text = sentiment.get('sentiment', 'NEUTRAL')
                sent_emoji = "🟢" if sent_text == 'BULLISH' else "🔴" if sent_text == 'BEARISH' else "🟡"
                
                title_embed = discord.Embed(
                    title=f"{q_emoji} {post['title'][:200]}",
                    url=post['url'],
                    color=color,
                    timestamp=datetime.now()
                )
                title_embed.description = f"**r/{post['subreddit']}** | {sent_emoji} {sent_text} | ⭐ {quality:.0f}/100"
                title_embed.set_footer(text="Turd News Network | Due Diligence Scanner")
                await stonks_channel.send(embed=title_embed)
                
                # Send stock data for up to 3 tickers
                for sd in stock_list[:3]:
                    ticker = sd.get('ticker')
                    if not ticker:
                        continue
                    
                    try:
                        from ticker_report import TickerReportBuilder
                        builder = TickerReportBuilder()
                        
                        loop = asyncio.get_running_loop()
                        embeds_list, chart_path, chart_paths = await loop.run_in_executor(
                            None, builder.build_report_sync, ticker
                        )
                        
                        if embeds_list:
                            print(f"[DD] Posting {len(embeds_list)} embeds for {ticker}")
                            embed_indices = [0, 1, 2, 3, 4]
                            
                            for idx in embed_indices:
                                if idx < len(embeds_list):
                                    embed_dict = embeds_list[idx]
                                    field_count = len(embed_dict.get('fields', []))
                                    print(f"[DD]   Embed {idx}: {embed_dict.get('title', 'No title')} ({field_count} fields)")
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
                                    await stonks_channel.send(embed=embed)
                                    await asyncio.sleep(0.5)
                            
                            print(f"[DD] ✅ Posted {len(embeds_list)} embeds for {ticker}")
                            
                            # Send all chart files (1 week, 3 month, 1 year)
                            # Use chart_paths from builder (returned from stock_data) or fallback to sd
                            charts_to_send = chart_paths if chart_paths else sd.get('chart_paths', [])
                            if charts_to_send:
                                for cp in charts_to_send:
                                    if cp and os.path.exists(cp):
                                        try:
                                            basename = os.path.basename(cp)
                                            chart_file = discord.File(cp, filename=basename)
                                            await stonks_channel.send(file=chart_file)
                                            print(f"[DD] Sent chart: {basename}")
                                        except Exception as e:
                                            print(f"[DD] Error sending chart {cp}: {e}")
                            elif chart_path and os.path.exists(chart_path):
                                # Fallback to single chart
                                try:
                                    chart_file = discord.File(chart_path, filename=f"{ticker}_chart.png")
                                    await stonks_channel.send(file=chart_file)
                                except:
                                    pass
                        
                    except Exception as e:
                        print(f"[DD ERROR] Ticker report failed for {ticker}: {e}")
                
                return True
                
        except Exception as e:
            print(f"[ERROR] send_dd_to_channel failed: {e}")
            return False
        return False
    
    async def _send_simple_embed(self, channel, sd, post):
        """Fallback simple embed if ticker report fails"""
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
        
        await channel.send(embed=embed)
    
    async def send_scan_summary(self, processed, skipped_already_sent, skipped_no_tickers, skipped_no_stock_data, all_posts):
        """Send a summary embed after scan completes"""
        try:
            for guild in self.guilds:
                stonks_channel = None
                for ch in guild.text_channels:
                    if ch.name == "stonks":
                        stonks_channel = ch
                        break
                
                if not stonks_channel:
                    continue
                
                # Get top and bottom posts from this scan
                if not all_posts:
                    return
                
                # Sort by quality score
                sorted_posts = sorted(all_posts, key=lambda x: x.get('quality_score', 0), reverse=True)
                
                # Top 5 posts
                top_posts = sorted_posts[:5]
                
                # Bottom 5 posts (lowest quality)
                bottom_posts = sorted_posts[-5:] if len(sorted_posts) >= 5 else sorted_posts
                
                # Create summary embed
                summary_embed = discord.Embed(
                    title="📊 **Daily DD Scan Summary**",
                    description=f"Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    color=0x3498DB,
                    timestamp=datetime.now()
                )
                
                # Stats
                stats_text = f"**Posts Scanned:** {len(all_posts)}\n"
                stats_text += f"**Processed:** {processed}\n"
                stats_text += f"**Skipped (already sent):** {skipped_already_sent}\n"
                stats_text += f"**Skipped (no tickers):** {skipped_no_tickers}\n"
                stats_text += f"**Skipped (no stock data):** {skipped_no_stock_data}"
                summary_embed.add_field(name="📈 Scan Stats", value=stats_text, inline=True)
                
                # Top posts
                top_text = ""
                for i, post in enumerate(top_posts, 1):
                    quality = post.get('quality_score', 0)
                    q_emoji = "💎" if quality >= 80 else "⭐" if quality >= 60 else "📊"
                    title = post.get('title', 'No title')[:50]
                    subreddit = post.get('subreddit', 'unknown')
                    top_text += f"{q_emoji} {i}. [{title}...]({post.get('url', '')})\n"
                    top_text += f"   r/{subreddit} | ⭐ {quality:.0f}\n"
                summary_embed.add_field(name="🏆 Top 5 DD Posts", value=top_text, inline=False)
                
                # Bottom posts
                bottom_text = ""
                for i, post in enumerate(bottom_posts, 1):
                    quality = post.get('quality_score', 0)
                    q_emoji = "📊"
                    title = post.get('title', 'No title')[:50]
                    subreddit = post.get('subreddit', 'unknown')
                    bottom_text += f"{q_emoji} {i}. [{title}...]({post.get('url', '')})\n"
                    bottom_text += f"   r/{subreddit} | ⭐ {quality:.0f}\n"
                summary_embed.add_field(name="📉 Bottom 5 DD Posts", value=bottom_text, inline=False)
                
                # Market overview
                try:
                    indices = ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT', 'VIX']
                    market_text = ""
                    
                    loop = asyncio.get_running_loop()
                    
                    def fetch_market():
                        from stock_data import StockDataFetcher
                        fetcher = StockDataFetcher(None)
                        result = {}
                        for ticker in indices:
                            try:
                                data = fetcher.get_stock_data(ticker)
                                if data:
                                    result[ticker] = data
                            except:
                                continue
                            time.sleep(0.3)
                        return result
                    
                    market_data = await loop.run_in_executor(None, fetch_market)
                    
                    for ticker, data in market_data.items():
                        price = data.get('price', 0)
                        change = data.get('change_pct', 0)
                        emoji = "🟢" if change >= 0 else "🔴"
                        market_text += f"{emoji} {ticker}: ${price:.2f} ({change:+.2f}%)\n"
                    
                    summary_embed.add_field(name="📈 Market Indices", value=market_text, inline=False)
                    
                    # NASDAQ Top/Bottom performers
                    # NASDAQ-100 components (major ones)
                    nasdaq_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'NFLX', 
                                     'ORCL', 'ADBE', 'CRM', 'PYPL', 'QCOM', 'TXN', 'AVGO', 'MU', 'LLY', 'NOW',
                                     'INTU', 'AMAT', 'BKNG', 'GILD', 'ADP', 'REGN', 'ZMD', 'MELI', 'PANW', 'CDNS']
                    
                    nasdaq_data = {}
                    
                    def fetch_nasdaq():
                        from stock_data import StockDataFetcher
                        nasdaq_fetcher = StockDataFetcher(None)
                        result = {}
                        for ticker in nasdaq_tickers:
                            try:
                                data = nasdaq_fetcher.get_stock_data(ticker)
                                if data and data.get('change_pct') is not None:
                                    result[ticker] = data
                            except:
                                continue
                            time.sleep(0.2)
                        return result
                    
                    nasdaq_data = await loop.run_in_executor(None, fetch_nasdaq)
                    
                    # Sort by change percentage
                    sorted_nasdaq = sorted(nasdaq_data.items(), key=lambda x: x[1].get('change_pct', 0), reverse=True)
                    
                    # Top 10 gainers
                    top_10 = sorted_nasdaq[:10]
                    top_text = ""
                    for ticker, data in top_10:
                        change = data.get('change_pct', 0)
                        price = data.get('price', 0)
                        top_text += f"🟢 {ticker}: ${price:.2f} ({change:+.2f}%)\n"
                    
                    # Bottom 10 losers
                    bottom_10 = sorted_nasdaq[-10:]
                    bottom_text = ""
                    for ticker, data in bottom_10:
                        change = data.get('change_pct', 0)
                        price = data.get('price', 0)
                        bottom_text += f"🔴 {ticker}: ${price:.2f} ({change:+.2f}%)\n"
                    
                    summary_embed.add_field(name="🚀 NASDAQ Top Gainers", value=top_text, inline=True)
                    summary_embed.add_field(name="📉 NASDAQ Bottom Losers", value=bottom_text, inline=True)
                except Exception as e:
                    print(f"[SUMMARY] Error fetching market data: {e}")
                
                summary_embed.set_footer(text="Turd News Network | Daily Summary")
                
                await stonks_channel.send(embed=summary_embed)
                print("[SUMMARY] Sent scan summary to channel")
                
        except Exception as e:
            print(f"[SUMMARY] Error sending scan summary: {e}")


# ============== MAIN ==============

async def run_bot():
    print("="*50)
    print("TURD NEWS NETWORK - DD Scanner + Slash Commands")
    print("="*50)
    print("Features:")
    print("  - Reddit DD Scanner (runs every 3 hours)")
    print("  - Slash Commands: /search, /watchlist, /market,")
    print("    /movers, /shortsqueeze, /insider, /congress,")
    print("    /earnings, /alert, /alerts, /report")
    print("="*50)
    
    bot = TurdNewsBot()
    
    try:
        await bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"[FATAL] {e}")


def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
