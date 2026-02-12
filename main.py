"""
Main application orchestrator for Turd News Network Enhanced v4.0
INCLUDES: Interactive Dashboard with working buttons
CONSOLE ONLY - No file logging
"""

import asyncio
import time
import os
import traceback
import warnings
import discord
from discord.ext import commands, tasks
from datetime import datetime
from config import *
from database import DatabaseManager

# Suppress deprecation warnings from yfinance
warnings.filterwarnings('ignore', category=DeprecationWarning, module='yfinance')

from console_formatter import Colors, print_banner, print_separator, print_section_header, print_success, print_error, print_warning, print_info, print_stat, print_processing
from scraper import RedditScraper
from stock_data import StockDataFetcher
from analysis import AnalysisEngine
from discord_embed import DiscordEmbedBuilder
from performance import PerformanceTracker
from sentiment import SentimentAnalyzer
from backtesting import EnhancedBacktester
from stats_reporter import StatsReporter
from watchlist_manager import WatchlistManager, WatchlistView, NotificationSettingsModal


# ============== CONSOLE LOGGING ONLY ==============

def log_error(category: str, error_type: str, message: str, details: str = "", user: str = "N/A", guild: str = "N/A"):
    """Log error to console ONLY"""
    timestamp = datetime.now().isoformat()
    print(f"\n{'='*70}")
    print(f"[ERROR] {timestamp} | {category} | {error_type}")
    print(f"  User: {user} | Guild: {guild}")
    print(f"  Message: {message}")
    if details:
        print(f"  Details: {details[:500]}")
    print(f"{'='*70}")


# ============== DASHBOARD COMPONENTS ==============

class SearchModal(discord.ui.Modal, title="🔍 Quick Search"):
    """Quick Search - Uses TickerReportBuilder to generate 10 embeds"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., NVDA, MSFT, BTC-USD",
        min_length=1, max_length=20,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Generate 10-embed report using TickerReportBuilder"""
        ticker = self.ticker_input.value.strip().upper()
        user = str(interaction.user)
        
        print(f"\n{'='*70}")
        print(f"[QUICK SEARCH] {ticker} by {user}")
        print(f"{'='*70}")
        
        try:
            # Defer immediately
            print("[QUICK SEARCH] Sending defer...")
            await interaction.response.defer(ephemeral=True, thinking=True)
            print("[QUICK SEARCH] Defer successful")
            
            # Use TickerReportBuilder to generate 10 embeds
            print(f"[QUICK SEARCH] Building 10-embed report for {ticker}...")
            from ticker_report import TickerReportBuilder
            builder = TickerReportBuilder()
            
            loop = asyncio.get_running_loop()
            embeds, chart_path = await loop.run_in_executor(
                None, builder.build_report_sync, ticker
            )
            
            if embeds is None:
                print(f"[QUICK SEARCH] ❌ No data found for {ticker}")
                await interaction.followup.send(
                    f"❌ Could not fetch data for **${ticker}**. Ticker may be invalid.",
                    ephemeral=True
                )
                return
            
            print(f"[QUICK SEARCH] ✅ Generated {len(embeds)} embeds")
            
            # Convert dict embeds to discord.Embed objects
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
                if embed_dict.get('footer', {}).get('text'):
                    embed.set_footer(text=embed_dict['footer']['text'])
                if embed_dict.get('thumbnail', {}).get('url'):
                    embed.set_thumbnail(url=embed_dict['thumbnail']['url'])
                discord_embeds.append(embed)
            
            # Send in batches (Discord max 10 embeds per message)
            print("[QUICK SEARCH] Sending batch 1 (embeds 1-5)...")
            batch_1 = discord_embeds[:5]
            batch_2 = discord_embeds[5:]
            
            # Send first batch with chart
            if chart_path and os.path.exists(chart_path):
                file = discord.File(chart_path, filename=os.path.basename(chart_path))
                await interaction.followup.send(embeds=batch_1, file=file, ephemeral=True)
                try:
                    os.remove(chart_path)
                except OSError:
                    pass
            else:
                await interaction.followup.send(embeds=batch_1, ephemeral=True)
            
            # Send second batch if exists
            if batch_2:
                print("[QUICK SEARCH] Sending batch 2 (embeds 6-10)...")
                await asyncio.sleep(0.5)
                await interaction.followup.send(embeds=batch_2, ephemeral=True)
            
            print(f"[QUICK SEARCH] ✅ Successfully sent {len(embeds)} embeds for {ticker}")
            
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] Quick Search failed")
            print(f"  Type: {type(e).__name__}")
            print(f"  Message: {e}")
            traceback.print_exc()
            print(f"{'='*70}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
            except:
                pass


class ReportsModal(discord.ui.Modal, title="📊 In-Depth Report"):
    """In-Depth Report - Generates HTML file using company_intelligence_dashboard"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., NVDA, MSFT",
        min_length=1, max_length=20,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Generate HTML report using company_intelligence_dashboard"""
        ticker = self.ticker_input.value.strip().upper()
        user = str(interaction.user)
        
        print(f"\n{'='*70}")
        print(f"[IN-DEPTH REPORT] {ticker} by {user}")
        print(f"{'='*70}")
        
        try:
            # Defer immediately
            print("[IN-DEPTH REPORT] Sending defer...")
            await interaction.response.defer(ephemeral=True, thinking=True)
            print("[IN-DEPTH REPORT] Defer successful")
            
            # Generate HTML report
            print(f"[IN-DEPTH REPORT] Generating HTML dashboard for {ticker}...")
            from company_intelligence_dashboard import generate_company_dashboard
            
            loop = asyncio.get_running_loop()
            html_file = await loop.run_in_executor(
                None, generate_company_dashboard, ticker
            )
            
            if html_file and os.path.exists(html_file):
                print(f"[IN-DEPTH REPORT] ✅ HTML generated: {html_file}")
                
                # Build success embed
                embed = discord.Embed(
                    title=f"📊 {ticker} - Company Intelligence Dashboard",
                    description=f"**17-Section Comprehensive Report**\n\n"
                               f"✨ **What's Included:**\n"
                               f"• Executive Summary with AI Analysis\n"
                               f"• Complete Financial Statements & Ratios\n"
                               f"• Stock Performance Charts\n"
                               f"• Leadership & Insider Trading\n"
                               f"• Congress Trading Activity\n"
                               f"• Risk Assessment & ESG Data\n"
                               f"• Competitor Analysis\n"
                               f"• SEC Filings Links",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="💾 How to View",
                    value="1. Download the HTML file below\n"
                          "2. Open in any web browser\n"
                          "3. Use the sidebar to navigate 17 sections\n"
                          "4. All charts are interactive!",
                    inline=False
                )
                embed.add_field(
                    name="🎨 Features",
                    value="• Dark mode professional design\n"
                          "• Chart.js interactive charts\n"
                          "• Mobile responsive\n"
                          "• Works offline",
                    inline=False
                )
                embed.set_footer(text="Turd News Network - Company Intelligence Dashboard v5.0")
                
                # Send with file
                await interaction.followup.send(
                    embed=embed,
                    file=discord.File(html_file),
                    ephemeral=True
                )
                print(f"[IN-DEPTH REPORT] ✅ Report sent to user")
                
                # Cleanup
                try:
                    os.remove(html_file)
                    print(f"[IN-DEPTH REPORT] Cleaned up temp file")
                except:
                    pass
            else:
                print(f"[IN-DEPTH REPORT] ❌ Failed to generate HTML")
                await interaction.followup.send(
                    f"❌ Could not generate In-Depth Report for **{ticker}**.\n\n"
                    f"Please check the ticker symbol and try again.",
                    ephemeral=True
                )
            
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] In-Depth Report failed")
            print(f"  Type: {type(e).__name__}")
            print(f"  Message: {e}")
            traceback.print_exc()
            print(f"{'='*70}")
            try:
                error_msg = f"❌ **Error generating report for {ticker}**\n\n`{str(e)[:200]}`"
                await interaction.followup.send(error_msg, ephemeral=True)
            except:
                pass


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
        """Interval modal callback with FULL LOGGING"""
        user = interaction.user
        
        print(f"\n{'='*70}")
        print(f"[INTERVAL] Setting interval for {user}")
        
        try:
            interval = int(self.interval.value)
            interval = max(10, min(300, interval))
            print(f"[INTERVAL] Set to {interval}s")
            await interaction.response.send_message(
                f"✅ Refresh interval set to **{interval} seconds**",
                ephemeral=True
            )
            print(f"[INTERVAL] ✅ Success")
        except ValueError:
            print(f"[INTERVAL] ❌ Invalid value: '{self.interval.value}'")
            await interaction.response.send_message("❌ Invalid interval - enter a number", ephemeral=True)
        except Exception as e:
            print(f"[INTERVAL] ❌ Error: {e}")
            traceback.print_exc()


class OverviewView(discord.ui.View):
    """Main dashboard view with 5 buttons - FULLY LOGGED"""
    def __init__(self, stock_fetcher, watchlist_manager):
        super().__init__(timeout=None)
        self.stock_fetcher = stock_fetcher
        self.watchlist_manager = watchlist_manager
    
    @discord.ui.button(label="🔍 Quick Search", style=discord.ButtonStyle.primary, custom_id="dash_search")
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        print(f"\n{'='*70}")
        print(f"[CLICK] Quick Search by {user}")
        print(f"{'='*70}")
        await interaction.response.send_modal(SearchModal())
    
    @discord.ui.button(label="📊 In-Depth Report", style=discord.ButtonStyle.primary, custom_id="dash_reports")
    async def reports_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        print(f"\n{'='*70}")
        print(f"[CLICK] In-Depth Report by {user}")
        print(f"{'='*70}")
        await interaction.response.send_modal(ReportsModal())
    
    @discord.ui.button(label="⭐ Watchlist", style=discord.ButtonStyle.success, custom_id="dash_watchlist")
    async def watchlist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        print(f"\n{'='*70}")
        print(f"[CLICK] Watchlist by {user}")
        print(f"{'='*70}")
        
        # Ensure user exists in database
        self.watchlist_manager.db.ensure_user_exists(
            str(user.id),
            username=user.name,
            discriminator=user.discriminator,
            display_name=user.display_name
        )
        
        # Show watchlist view with buttons
        view = WatchlistView(self.watchlist_manager, str(user.id))
        embed = discord.Embed(
            title="⭐ Your Watchlist",
            description="Track your favorite stocks with real-time alerts!\n\n"
                       "**Features:**\n"
                       "• Add stocks with custom price alerts\n"
                       "• Get notified when conditions are met\n"
                       "• View real-time price data\n"
                       "• Manage your portfolio\n\n"
                       "Use the buttons below to manage your watchlist!",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.success, custom_id="dash_refresh")
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        print(f"\n{'='*70}")
        print(f"[CLICK] Refresh by {user}")
        print(f"{'='*70}")
        await interaction.response.send_message("🔄 Dashboard refreshed!", ephemeral=True, delete_after=3)
    
    @discord.ui.button(label="⚙️ Settings", style=discord.ButtonStyle.secondary, custom_id="dash_settings")
    async def settings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        print(f"\n{'='*70}")
        print(f"[CLICK] Settings by {user}")
        print(f"{'='*70}")
        
        # Show settings options
        view = SettingsView(self.watchlist_manager, str(user.id))
        await interaction.response.send_message(
            "⚙️ **Settings**\n\nChoose what you'd like to configure:",
            view=view,
            ephemeral=True
        )


class SettingsView(discord.ui.View):
    """Settings view with multiple configuration options"""
    
    def __init__(self, watchlist_manager, user_id):
        super().__init__(timeout=300)
        self.watchlist_manager = watchlist_manager
        self.user_id = user_id
    
    @discord.ui.button(label="🔔 Notification Settings", style=discord.ButtonStyle.primary, row=0)
    async def notif_settings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get current settings
        settings = self.watchlist_manager.db.get_notification_settings(self.user_id)
        await interaction.response.send_modal(
            NotificationSettingsModal(self.watchlist_manager.db, self.user_id, settings)
        )
    
    @discord.ui.button(label="⏱️ Dashboard Refresh Rate", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_rate_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IntervalModal())


# ============== DASHBOARD BOT CLASS ==============

class DashboardBot(commands.Bot):
    """Bot that includes Turd News Network AND Dashboard"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
        print("[INIT] Loading components...")
        self.db = DatabaseManager()
        print("[INIT] Database loaded")
        self.scraper = RedditScraper()
        print("[INIT] Reddit scraper loaded")
        self.stock_fetcher = StockDataFetcher(self.db)
        print("[INIT] Stock fetcher loaded")
        self.analysis = AnalysisEngine()
        print("[INIT] Analysis engine loaded")
        self.discord = DiscordEmbedBuilder(WEBHOOK_URL, self.db)
        print("[INIT] Discord embed builder loaded")
        self.performance = PerformanceTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.backtester = EnhancedBacktester()
        self.stats_reporter = StatsReporter()
        
        # Initialize Watchlist Manager
        self.watchlist_manager = WatchlistManager(self.db, self.stock_fetcher, self)
        print("[INIT] Watchlist manager loaded")
        
        print("[INIT] All components loaded successfully")
    
    async def setup_hook(self):
        """Setup - NO add_view() per FIXME_dashboard.md"""
        print("[DASHBOARD] setup_hook called")
        
        # Start watchlist monitoring
        await self.watchlist_manager.start_monitoring()
        
        # Start Reddit scanning schedule (4 times a day = every 6 hours)
        self.reddit_scanner.start()
        print("[DASHBOARD] Reddit scanner scheduled (every 6 hours)")
    
    @tasks.loop(hours=3)  # Scan every 3 hours
    async def reddit_scanner(self):
        """Background task to scan Reddit every 3 hours - runs in separate thread"""
        try:
            print(f"\n{'='*70}")
            print(f"[SCHEDULED SCAN] Starting Reddit scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"[SCHEDULED SCAN] Next scan in 3 hours")
            print(f"[SCHEDULED SCAN] Running in background thread...")
            print(f"{'='*70}")
            
            # Run process_posts in a separate thread to avoid blocking Discord
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._process_posts_sync)
            
            print(f"[SCHEDULED SCAN] Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")
        except Exception as e:
            print(f"[SCHEDULED SCAN ERROR] {e}")
            traceback.print_exc()
    
    def _process_posts_sync(self):
        """Synchronous wrapper for process_posts to run in thread"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.process_posts())
            loop.close()
        except Exception as e:
            print(f"[THREAD ERROR] {e}")
            traceback.print_exc()
    
    @reddit_scanner.before_loop
    async def before_reddit_scanner(self):
        """Wait for bot to be ready before starting scans"""
        await self.wait_until_ready()
        print("[SCHEDULED SCAN] Bot ready, Reddit scanner will start")
    
    async def on_ready(self):
        """Bot is ready"""
        print(f"\n{'='*70}")
        print(f"[BOT] ✅ Bot ready: {self.user}")
        print(f"[BOT] ✅ Connected to {len(self.guilds)} guilds")
        for guild in self.guilds:
            print(f"[BOT]   - {guild.name} (ID: {guild.id})")
        print(f"{'='*70}\n")
        
        for guild in self.guilds:
            try:
                await self.create_dashboard(guild)
            except Exception as e:
                print(f"[ERROR] Failed in {guild.name}: {e}")
                traceback.print_exc()
    
    async def create_dashboard(self, guild: discord.Guild):
        """Create dashboard in guild"""
        channel_name = "stonk-bot"
        print(f"[DASHBOARD] Setting up dashboard for {guild.name}...")
        
        channel = None
        for ch in guild.channels:
            if ch.name == channel_name and isinstance(ch, discord.TextChannel):
                channel = ch
                print(f"[DASHBOARD] Found existing #{channel_name}")
                break
        
        if not channel:
            try:
                print(f"[DASHBOARD] Creating #{channel_name}...")
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
                }
                channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
                print(f"[DASHBOARD] Created #{channel_name}")
            except Exception as e:
                print(f"[ERROR] Can't create channel: {e}")
                traceback.print_exc()
                return
        
        try:
            print(f"[DASHBOARD] Clearing #{channel_name}...")
            deleted = await channel.purge(limit=100)
            print(f"[DASHBOARD] Deleted {len(deleted)} old messages")
        except Exception as e:
            print(f"[WARNING] Could not clear channel: {e}")
        
        embed = discord.Embed(
            title="📊 WSB MONITOR DASHBOARD",
            description="Click the buttons below to interact!",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="🔍 Quick Search", value="10-embed detailed stock report", inline=False)
        embed.add_field(name="📊 In-Depth Report", value="Download HTML analysis dashboard", inline=False)
        embed.add_field(name="⭐ Watchlist", value="View your saved stocks", inline=False)
        embed.add_field(name="🔄 Refresh", value="Refresh the dashboard", inline=False)
        embed.add_field(name="⚙️ Settings", value="Configure refresh interval", inline=False)
        embed.set_footer(text="Turd News Network v4.0 - Buttons work!")
        
        view = OverviewView(self.stock_fetcher, self.watchlist_manager)
        message = await channel.send(embed=embed, view=view)
        print(f"[DASHBOARD] ✅ Dashboard sent to #{channel.name} (Message ID: {message.id})")
    
    async def process_posts(self):
        """Main processing loop - sends to both webhook AND stonks channel"""
        print_separator()
        print(f">> Starting Enhanced Turd News Network Scan v4.0")
        print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("[SCRAPER] Scraping Reddit...")
        all_posts = self.scraper.scrape_all_subreddits()
        print(f"[SCRAPER] Found {len(all_posts)} posts")
        
        for post in all_posts:
            post['quality_score'] = self.analysis.calculate_quality_score(post)
            if ENABLE_SENTIMENT:
                sentiment = self.sentiment_analyzer.analyze_post_sentiment(post['title'], post['selftext'])
                post['sentiment'] = sentiment
        
        all_posts.sort(key=lambda x: x['quality_score'], reverse=True)
        
        print(f"\n[STATS] Total DD posts found: {len(all_posts)}")
        
        processed_count = 0
        for post in all_posts:
            if self.db.is_post_already_sent(post['id']):
                print(f"[SKIP] Post {post['id']} already sent")
                continue
            
            combined_text = post['title'] + ' ' + post['selftext']
            tickers = self.scraper.extract_tickers(combined_text)
            
            if not tickers:
                print(f"[SKIP] No tickers found in post: {post['title'][:50]}...")
                continue
            
            print_separator()
            print(f"[PROCESSING] {post['title'][:60]}...")
            print(f"   Quality: {post['quality_score']:.0f}/100")
            print(f"   Tickers: {', '.join(tickers)}")
            
            stock_data_list = []
            for ticker in tickers:
                print(f"   [FETCH] ${ticker}...")
                stock_data = self.stock_fetcher.get_stock_data(ticker)
                if stock_data:
                    # Enrich with backtest data
                    if ENABLE_BACKTEST:
                        bt = self.backtester.backtest_ticker_history(ticker, years=BACKTEST_YEARS)
                        if bt:
                            stock_data['backtest'] = bt
                    
                    # Enrich with ML prediction
                    try:
                        from ml_predictor import MLPredictor
                        ml = MLPredictor()
                        ml_pred = ml.predict(ticker)
                        if ml_pred:
                            stock_data['ml_prediction'] = {
                                'direction': ml_pred.get('direction', 'NEUTRAL'),
                                'confidence': int(ml_pred.get('confidence', 0) * 100),
                                'days': ml_pred.get('days', 5),
                                'emoji': '🟢' if ml_pred.get('direction') == 'UP' else '🔴' if ml_pred.get('direction') == 'DOWN' else '🟡',
                                'features': ml_pred.get('features_used', 'N/A')[:50]
                            }
                    except Exception as e:
                        print(f"   [ML] Warning: Could not get ML prediction for {ticker}: {e}")
                    
                    # Enrich with technical signal summary
                    try:
                        tech_indicators = stock_data.get('technical_indicators', {})
                        current_price = stock_data.get('price', 0)
                        
                        # Calculate unified signal
                        signal_data = self.analysis.calculate_unified_signal(tech_indicators, current_price)
                        if signal_data:
                            stock_data['signal_summary'] = signal_data
                    except Exception as e:
                        print(f"   [SIGNAL] Warning: Could not calculate signal for {ticker}: {e}")
                    
                    # Enrich with options flow data
                    try:
                        options_data = self.stock_fetcher.get_options_data(ticker, ticker)
                        if options_data:
                            # Determine options flow sentiment
                            pc_ratio = options_data.get('pc_ratio', 1.0)
                            unusual = options_data.get('unusual_strikes', [])
                            
                            if pc_ratio < 0.7:
                                flow = 'BULLISH_FLOW'
                                emoji = '🟢'
                            elif pc_ratio > 1.3:
                                flow = 'BEARISH_FLOW'
                                emoji = '🔴'
                            else:
                                flow = 'NEUTRAL_FLOW'
                                emoji = '🟡'
                            
                            stock_data['options_flow'] = {
                                'flow': flow,
                                'emoji': emoji,
                                'pc_ratio': pc_ratio,
                                'max_pain': options_data.get('max_pain'),
                                'expiry': options_data.get('expiry'),
                                'unusual_strikes': unusual[:3]
                            }
                    except Exception as e:
                        print(f"   [OPTIONS] Warning: Could not get options data for {ticker}: {e}")
                    
                    # Enrich with insider data
                    try:
                        insider_data = self.stock_fetcher.get_insider_data(ticker, ticker)
                        if insider_data:
                            stock_data['insider_data'] = insider_data
                    except Exception as e:
                        print(f"   [INSIDER] Warning: Could not get insider data for {ticker}: {e}")
                    
                    # Enrich with Congress trading data
                    try:
                        from congress_tracker import CongressTracker
                        congress = CongressTracker(self.db)
                        congress_trades = congress.check_congress_trades(ticker)
                        if congress_trades:
                            buys = sum(1 for t in congress_trades if 'PURCHASE' in str(t.get('transaction_type', '')).upper())
                            sells = sum(1 for t in congress_trades if 'SALE' in str(t.get('transaction_type', '')).upper())
                            stock_data['congress_data'] = {
                                'trades': congress_trades[:5],
                                'buys': buys,
                                'sells': sells,
                                'total': len(congress_trades)
                            }
                    except Exception as e:
                        print(f"   [CONGRESS] Warning: Could not get Congress data for {ticker}: {e}")
                    
                    stock_data_list.append(stock_data)
                    self.db.save_stock_tracking(ticker, post['id'], stock_data['price'])
                    print(f"   [FETCH] ✅ ${ticker} - ${stock_data['price']}")
                else:
                    print(f"   [FETCH] ❌ ${ticker} - No data")
                time.sleep(API_DELAY)
            
            if stock_data_list:
                print(f"   [SEND] Sending to webhook...")
                webhook_sent = self.discord.send_discord_embed(post, stock_data_list)
                print(f"   [SEND] Webhook: {'✅' if webhook_sent else '❌'}")
                
                print(f"   [SEND] Sending to stonks channel...")
                stonks_sent = await self.send_to_stonks_channel(post, stock_data_list)
                print(f"   [SEND] Stonks: {'✅' if stonks_sent else '❌'}")
                
                if webhook_sent or stonks_sent:
                    self.db.save_post(post, tickers, post['quality_score'], "")
                    processed_count += 1
                    print(f"   [SAVED] Post saved to database")
                time.sleep(API_DELAY)
            else:
                print(f"   [SKIP] No valid stock data")
        
        print_separator()
        print(f"[COMPLETE] Scan complete! Processed: {processed_count}/{len(all_posts)}")
    
    async def send_to_stonks_channel(self, post: dict, stock_data_list: list) -> bool:
        """Send the DD post to the #stonks channel in each guild"""
        try:
            stonks_channel_name = "stonks"
            any_sent = False
            
            for guild in self.guilds:
                print(f"   [STONKS] Looking for #{stonks_channel_name} in {guild.name}...")
                stonks_channel = None
                for channel in guild.text_channels:
                    if channel.name == stonks_channel_name:
                        stonks_channel = channel
                        break
                
                if not stonks_channel:
                    print(f"   [STONKS] ❌ No #{stonks_channel_name} channel found in {guild.name}")
                    continue
                
                quality_score = post.get('quality_score', 0)
                if quality_score >= PREMIUM_DD_SCORE:
                    quality_emoji, quality_text = "💎", "PREMIUM DD"
                    color = COLOR_PREMIUM
                elif quality_score >= QUALITY_DD_SCORE:
                    quality_emoji, quality_text = "⭐", "QUALITY DD"
                    color = COLOR_QUALITY
                else:
                    quality_emoji, quality_text = "📊", "Standard DD"
                    color = COLOR_STANDARD
                
                sentiment = post.get('sentiment', {})
                sentiment_text = sentiment.get('sentiment', 'NEUTRAL')
                sentiment_confidence = sentiment.get('confidence', 0)
                
                if sentiment_text == 'BULLISH':
                    sentiment_emoji = '🟢'
                elif sentiment_text == 'BEARISH':
                    sentiment_emoji = '🔴'
                else:
                    sentiment_emoji = '🟡'
                
                embed = discord.Embed(
                    title=f"{quality_emoji} {quality_text}: {post['title'][:200]}",
                    url=post['url'],
                    color=color,
                    timestamp=datetime.now()
                )
                
                description = f"**📉 r/{post['subreddit']}** • {post.get('score', 0):,}⬆️ {post.get('num_comments', 0):,}💬\n"
                description += f"**{sentiment_emoji} Sentiment:** {sentiment_text} ({sentiment_confidence:.0%} confidence)\n"
                description += f"**Quality Score:** {quality_score:.0f}/100"
                
                if post.get('flair'):
                    description = f"**🏷️ {post['flair']}**\n{description}"
                
                embed.description = description
                
                for stock_data in stock_data_list[:3]:
                    ticker = stock_data['ticker']
                    price = stock_data.get('price', 'N/A')
                    change = stock_data.get('change_pct', 0)
                    change_str = f"{change:+.2f}%" if isinstance(change, (int, float)) else "N/A"
                    change_emoji = "📈" if change >= 0 else "📉"
                    
                    value = f"💰 ${price} | {change_emoji} {change_str}"
                    
                    mcap = stock_data.get('market_cap')
                    if mcap:
                        value += f"\n🏢 MC: {self.analysis.format_number(mcap)}"
                    
                    pe = stock_data.get('pe_ratio')
                    if pe and pe > 0:
                        value += f" | P/E: {pe:.1f}"
                    
                    embed.add_field(
                        name=f"${ticker} - {stock_data.get('name', ticker)[:30]}",
                        value=value,
                        inline=True
                    )
                
                if stock_data_list:
                    sd = stock_data_list[0]
                    links = f"[Yahoo]({sd.get('yahoo_link', '#')}) | [Finviz]({sd.get('finviz_link', '#')}) | [TradingView]({sd.get('tradingview_link', '#')})"
                    embed.add_field(name="🔗 Links", value=links, inline=False)
                
                embed.set_footer(text=f"💎 Turd News Network v5.0 | {len(stock_data_list)} stock(s) analyzed")
                
                await stonks_channel.send(embed=embed)
                print(f"   [STONKS] ✅ Sent to #{stonks_channel_name} in {guild.name}")
                any_sent = True
                
            return any_sent
            
        except Exception as e:
            print(f"   [STONKS] ❌ Error: {e}")
            traceback.print_exc()
            return False


def print_separator():
    print("="*70)


# ============== MAIN ==============

async def run_bot():
    """Run the combined bot"""
    print("="*70)
    print("[*] WSB MONITOR ENHANCED v4.0 WITH DASHBOARD")
    print("[*] Console-only output mode")
    print("="*70)
    
    bot = DashboardBot()
    
    try:
        print("[STARTUP] Starting bot...")
        await bot.start(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Shutting down...")
        await bot.close()
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        traceback.print_exc()


def main():
    """Main entry point"""
    print("="*70)
    print("[*] WSB MONITOR ENHANCED v4.0 WITH DASHBOARD")
    print("="*70)
    print()
    
    asyncio.run(run_bot())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--dashboard-only':
        from discord_dashboard import run_dashboard
        asyncio.run(run_dashboard())
    else:
        main()
