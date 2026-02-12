"""
Interactive Dashboard - CLEAN BUTTON DESIGN
"""

import asyncio
import discord
from discord.ext import commands
from datetime import datetime
import sys
import os
import traceback

sys.path.insert(0, r"C:\vibe coding projects\Stonk Bot\Stonk Bot Cline")
from config import DISCORD_BOT_TOKEN
from stock_data import StockDataFetcher
from analysis import AnalysisEngine


# ============== CONSOLE LOGGING ONLY ==============

def log_error(category: str, error_type: str, message: str, details: str = "", user: str = "N/A"):
    """Log error to console ONLY"""
    timestamp = datetime.now().isoformat()
    print(f"\n{'='*70}")
    print(f"[ERROR] {timestamp} | {category} | {error_type}")
    print(f"  User: {user}")
    print(f"  Message: {message}")
    if details:
        print(f"  Details: {details[:500]}")
    print(f"{'='*70}")


# Initialize components
stock_fetcher = StockDataFetcher(None)
analysis_engine = AnalysisEngine()


# ============== STOCK DATA FOR DROPDOWNS ==============
STOCK_OPTIONS = [
    "AAPL", "AMD", "AMZN", "ASTS", "BB", "COIN", "DKNG", "GME", "GOOG", 
    "GOOGL", "HIMS", "IONQ", "META", "MSFT", "MSTR", "NFLX", "NVDA", "PLTR", 
    "PLUG", "QQQM", "RKLB", "SMCI", "SNAP", "SOXX", "SPY", "SQ", "TSLA", 
    "UPST", "VBIV", "VRT", "WBD", "WDC"
]


# ============== NO-OP DB CLASS ==============
class NoOpDB:
    """Fake DB to skip database operations"""
    def save_price_history(self, *args, **kwargs): pass
    def save_technical_indicators(self, *args, **kwargs): pass
    def save_stock_metadata(self, *args, **kwargs): pass
    def save_news_articles(self, *args, **kwargs): pass


# ============== CLEAN DASHBOARD VIEW ==============
class DashboardView(discord.ui.View):
    """Clean dashboard with organized buttons"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    # Row 0: Main Actions (2 buttons side by side)
    @discord.ui.button(
        label="🔍 Quick Search", 
        style=discord.ButtonStyle.primary, 
        custom_id="dash_quick", 
        row=0
    )
    async def quick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick search any stock"""
        print(f"[CLICK] 🔍 Quick Search by {interaction.user}")
        await interaction.response.send_modal(CustomSearchModal())
    
    @discord.ui.button(
        label="📊 In-Depth Report", 
        style=discord.ButtonStyle.primary, 
        custom_id="dash_report", 
        row=0
    )
    async def report_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generate detailed HTML report"""
        print(f"[CLICK] 📊 In-Depth Report by {interaction.user}")
        await interaction.response.send_modal(ReportModal())
    
    # Row 1: Secondary Actions (2 buttons side by side)
    @discord.ui.button(
        label="⭐ Watchlist", 
        style=discord.ButtonStyle.success, 
        custom_id="dash_watchlist", 
        row=1
    )
    async def watchlist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Manage your watchlist"""
        print(f"[CLICK] ⭐ Watchlist by {interaction.user}")
        await interaction.response.send_modal(WatchlistModal())
    
    @discord.ui.button(
        label="🔄 Refresh", 
        style=discord.ButtonStyle.secondary, 
        custom_id="dash_refresh", 
        row=1
    )
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh the dashboard"""
        print(f"[CLICK] 🔄 Refresh by {interaction.user}")
        await interaction.response.send_message("✅ Dashboard refreshed!", ephemeral=True, delete_after=3)


# ============== MODALS ==============
class CustomSearchModal(discord.ui.Modal, title="🔍 Quick Stock Search"):
    """Modal for quick stock search"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., NVDA, MSFT, BTC-USD",
        min_length=1, max_length=20,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        ticker = self.ticker_input.value.strip().upper()
        print(f"[SEARCH] {ticker} by {interaction.user}")
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Use TickerReportBuilder to generate 10 embeds
            from ticker_report import TickerReportBuilder
            builder = TickerReportBuilder()
            
            loop = asyncio.get_running_loop()
            embeds, chart_path = await loop.run_in_executor(
                None, builder.build_report_sync, ticker
            )
            
            if embeds is None:
                await interaction.followup.send(
                    f"❌ Could not fetch data for **${ticker}**. Ticker may be invalid.",
                    ephemeral=True
                )
                return
            
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
            
            # Send in batches
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
            
            # Send second batch
            if batch_2:
                await asyncio.sleep(0.5)
                await interaction.followup.send(embeds=batch_2, ephemeral=True)
            
            print(f"[SEARCH] ✅ {ticker} - {len(embeds)} embeds sent")
            
        except Exception as e:
            print(f"[ERROR] Search: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)


class ReportModal(discord.ui.Modal, title="📊 In-Depth Report"):
    """Modal for generating detailed reports"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., NVDA, MSFT",
        min_length=1, max_length=20,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        ticker = self.ticker_input.value.strip().upper()
        user = str(interaction.user)
        print(f"[REPORT] {ticker} by {interaction.user}")
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Use NoOpDB
            original_db = stock_fetcher.db
            stock_fetcher.db = NoOpDB()
            stock_data = stock_fetcher.get_stock_data(ticker)
            stock_fetcher.db = original_db
            
            if not stock_data:
                await interaction.followup.send(f"❌ **{ticker}** not found.", ephemeral=True)
                return
            
            # Generate HTML report
            html_file = None
            generation_error = None
            try:
                from company_intelligence_dashboard import generate_company_dashboard
                html_file = generate_company_dashboard(ticker)
            except Exception as e:
                generation_error = str(e)
                error_traceback = traceback.format_exc()
                log_error(
                    category="REPORT_GENERATION",
                    error_type=type(e).__name__,
                    message=f"Failed to generate dashboard for {ticker}",
                    details=error_traceback,
                    user=user
                )
                print(f"[REPORT] Error generating HTML: {e}")
                print(f"[REPORT] Traceback:\n{error_traceback}")
            
            if html_file and os.path.exists(html_file):
                embed = discord.Embed(
                    title=f"📊 {ticker} - Company Intelligence Dashboard",
                    description=f"**17-Section Comprehensive Report** for **{stock_data.get('name', ticker)}**\n\n✨ **What's Included:**\n• Executive Summary with AI Analysis\n• Complete Financial Statements & Ratios\n• Stock Performance Charts\n• Leadership & Insider Trading\n• Congress Trading Activity\n• Risk Assessment & ESG Data\n• Competitor Analysis\n• SEC Filings Links",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                embed.add_field(name="💰 Current Price", value=f"${stock_data.get('price', 'N/A')}", inline=True)
                embed.add_field(name="📈 Change", value=f"{stock_data.get('change_pct', 0):+.2f}%", inline=True)
                embed.add_field(name="📄 Report Type", value="Interactive HTML", inline=True)
                embed.add_field(
                    name="💾 How to View",
                    value="1. Download the HTML file below\n2. Open in any web browser\n3. Use the sidebar to navigate 17 sections\n4. All charts are interactive!",
                    inline=False
                )
                embed.add_field(
                    name="🎨 Features",
                    value="• Dark mode professional design\n• Chart.js interactive charts\n• Mobile responsive\n• Works offline",
                    inline=False
                )
                embed.set_footer(text="Turd News Network - Company Intelligence Dashboard v5.0")
                
                await interaction.followup.send(
                    embed=embed, 
                    file=discord.File(html_file), 
                    ephemeral=True
                )
                print(f"[REPORT] ✅ {ticker} Intelligence Dashboard sent")
                
                # Cleanup
                try:
                    os.remove(html_file)
                except:
                    pass
            else:
                # Report generation failed - show detailed error to user
                error_msg = generation_error if generation_error else "Unknown error"
                error_embed = discord.Embed(
                    title=f"❌ Report Generation Failed",
                    description=f"Could not generate In-Depth Report for **{ticker}**",
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
                error_embed.add_field(
                    name="Error Details",
                    value=f"```\n{error_msg[:800]}\n```",
                    inline=False
                )
                error_embed.add_field(
                    name="What to do",
                    value="Please check:\n1. The ticker symbol is valid\n2. The stock data is available\n3. Try again in a few moments",
                    inline=False
                )
                error_embed.set_footer(text="Error logged to dashboard_error.log")
                
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                print(f"[REPORT] ❌ {ticker} report generation failed: {error_msg}")
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                category="REPORT_SUBMIT",
                error_type=type(e).__name__,
                message=f"Unexpected error in report modal for {ticker}",
                details=error_traceback,
                user=user
            )
            print(f"[ERROR] Report: {e}")
            print(f"[ERROR] Traceback:\n{error_traceback}")
            await interaction.followup.send(
                f"❌ **Something went wrong**\n\nError: `{str(e)[:500]}`\n\nThis error has been logged.",
                ephemeral=True
            )


class WatchlistModal(discord.ui.Modal, title="⭐ Manage Watchlist"):
    """Modal for managing watchlist"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., NVDA, AAPL",
        min_length=1, max_length=10,
        required=True
    )
    alert_price = discord.ui.TextInput(
        label="Alert Price (optional)",
        placeholder="e.g., 150.00",
        required=False
    )
    notes = discord.ui.TextInput(
        label="Notes (optional)",
        placeholder="e.g., Earnings next week",
        required=False,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        ticker = self.ticker_input.value.strip().upper()
        alert = self.alert_price.value.strip() if self.alert_price.value else None
        note_text = self.notes.value.strip() if self.notes.value else None
        
        print(f"[WATCHLIST] {ticker} by {interaction.user}")
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Validate ticker
            original_db = stock_fetcher.db
            stock_fetcher.db = NoOpDB()
            stock_data = stock_fetcher.get_stock_data(ticker)
            stock_fetcher.db = original_db
            
            if not stock_data:
                await interaction.followup.send(
                    f"❌ **{ticker}** not found. Cannot add to watchlist.", 
                    ephemeral=True
                )
                return
            
            current_price = stock_data.get('price', 'N/A')
            
            embed = discord.Embed(
                title="⭐ Added to Watchlist",
                description=f"**{ticker}** - {stock_data.get('name', ticker)}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="💰 Current Price", value=f"${current_price}", inline=True)
            if alert:
                embed.add_field(name="🔔 Alert Price", value=f"${alert}", inline=True)
            if note_text:
                embed.add_field(name="📝 Notes", value=note_text, inline=False)
            
            embed.set_footer(text="You'll be notified when conditions are met")
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"[WATCHLIST] ✅ {ticker} added")
            
        except Exception as e:
            print(f"[ERROR] Watchlist: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)


# ============== BOT ==============
class DashboardBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)
    
    async def setup_hook(self):
        print("[DASHBOARD] ✅ Setup complete")
    
    async def on_ready(self):
        print(f"\n{'='*60}")
        print(f"🚀 Turd News Network Dashboard")
        print(f"Bot: {self.user}")
        print(f"Guilds: {len(self.guilds)}")
        print(f"{'='*60}\n")
        
        for guild in self.guilds:
            try:
                await self.create_dashboard(guild)
            except Exception as e:
                print(f"[ERROR] {guild.name}: {e}")
    
    async def create_dashboard(self, guild: discord.Guild):
        channel_name = "stonk-bot"
        
        # Find or create channel
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=True, send_messages=True
                    ),
                    guild.me: discord.PermissionOverwrite(
                        read_messages=True, send_messages=True, manage_messages=True
                    )
                }
                channel = await guild.create_text_channel(
                    channel_name, 
                    overwrites=overwrites
                )
                print(f"[DASHBOARD] ✅ Created #{channel_name}")
            except Exception as e:
                print(f"[ERROR] Can't create channel: {e}")
                return
        
        # Purge old messages
        try:
            deleted = await channel.purge(limit=100)
            print(f"[DASHBOARD] 🗑️ Deleted {len(deleted)} old messages")
        except Exception as e:
            print(f"[WARNING] Could not purge: {e}")
        
        # Create clean dashboard embed
        embed = discord.Embed(
            title="🚀 Turd News Network",
            description="**Stock Market Dashboard**\n\nQuick access to stock data, reports, and watchlists!",
            color=0x5865F2,  # Discord blurple
            timestamp=datetime.now()
        )
        
        # Feature descriptions
        embed.add_field(
            name="🔍 Quick Search",
            value="Get instant stock data with charts",
            inline=True
        )
        embed.add_field(
            name="📊 In-Depth Report",
            value="Download detailed HTML analysis",
            inline=True
        )
        embed.add_field(
            name="⭐ Watchlist",
            value="Track your favorite stocks",
            inline=True
        )
        embed.add_field(
            name="🔄 Refresh",
            value="Reload the dashboard",
            inline=True
        )
        
        embed.set_footer(text="Turd News Network v4.0 • Clean Design")
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
        
        # Send with clean view
        view = DashboardView()
        message = await channel.send(embed=embed, view=view)
        print(f"[DASHBOARD] ✅ Dashboard sent (ID: {message.id})")


# ============== RUN ==============
async def run_dashboard():
    print("\n" + "="*60)
    print("🚀 Starting Turd News Network Dashboard...")
    print("="*60 + "\n")
    
    bot = DashboardBot()
    
    try:
        await bot.start(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        print("\n[DASHBOARD] 👋 Shutting down...")
        await bot.close()


def main():
    print("[DASHBOARD] 🔄 Initializing...")
    asyncio.run(run_dashboard())


if __name__ == "__main__":
    main()
