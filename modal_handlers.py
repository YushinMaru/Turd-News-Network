"""
Modal Handlers for Discord Dashboard
Handles all interactions for data input
EXTREME LOGGING ENABLED - Every action is logged
"""

import discord
from discord import ui
from typing import Optional
from datetime import datetime
import traceback

# EXTREME LOGGING SETTINGS
LOG_ALL_FUNCTIONS = True
LOG_MODAL_SUBMISSIONS = True
LOG_ERRORS = True


class ModalHandlers:
    """Handles all modal form submissions and slash commands"""
    
    def __init__(self, bot, db, channel_manager):
        self.bot = bot
        self.db = db
        self.channel_manager = channel_manager
        
        print(f"\n{'='*70}")
        print(f"[INIT] ModalHandlers initialized")
        print(f"  Bot: {bot}")
        print(f"  DB: {db}")
        print(f"  Channel Manager: {channel_manager}")
        print(f"{'='*70}\n")
    
    # ========== SLASH COMMAND HANDLERS ==========
    
    async def handle_search_slash(self, interaction, ticker: str):
        """Handle /search command"""
        print(f"\n{'='*70}")
        print(f"[FUNCTION] handle_search_slash called")
        print(f"  Ticker: {ticker}")
        print(f"  User: {interaction.user}")
        print(f"{'='*70}\n")
        
        await interaction.response.defer(ephemeral=True)
        ticker = ticker.strip().upper()
        await self.show_ticker_analysis(interaction, ticker)
    
    async def handle_report_slash(self, interaction, ticker: str, report_type: str):
        """Handle /report command"""
        print(f"\n{'='*70}")
        print(f"[FUNCTION] handle_report_slash called")
        print(f"  Ticker: {ticker}")
        print(f"  Report Type: {report_type}")
        print(f"  User: {interaction.user}")
        print(f"{'='*70}\n")
        
        await interaction.response.defer(ephemeral=True)
        ticker = ticker.strip().upper()
        await self.process_report_generation(interaction, ticker, report_type)
    
    async def handle_watchlist(self, ctx_or_interaction):
        """Handle /watchlist command or button"""
        print(f"\n{'='*70}")
        print(f"[FUNCTION] handle_watchlist called")
        print(f"  User: {ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author}")
        print(f"{'='*70}\n")
        
        user_id = str(ctx_or_interaction.user.id if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author.id)
        
        # Register/update user
        print(f"  Registering user: {ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author}")
        self.channel_manager.register_user(ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author)
        self.channel_manager.update_user_activity(user_id)
        print(f"  User registered and activity updated")
        
        # Get watchlist
        print(f"  Fetching watchlist for user: {user_id}")
        watchlist = self.channel_manager.get_user_watchlist(user_id)
        print(f"  Watchlist: {watchlist}")
        
        embed = discord.Embed(
            title="⭐ Your Watchlist",
            description=f"You have {len(watchlist)} tickers in your watchlist" if watchlist else "Your watchlist is empty",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        if watchlist:
            for item in watchlist:
                ticker = item['ticker']
                notes = item['notes'] or "No notes"
                alert = "🔔 On" if item['alert_enabled'] else "🔕 Off"
                
                embed.add_field(
                    name=ticker,
                    value=f"{notes} • {alert}",
                    inline=False
                )
        else:
            embed.add_field(
                name="💡 Add Tickers",
                value="Use /search to find and add tickers",
                inline=False
            )
        
        try:
            await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def handle_refresh(self, ctx_or_interaction):
        """Handle /refresh command or button"""
        print(f"\n{'='*70}")
        print(f"[FUNCTION] handle_refresh called")
        print(f"  User: {ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author}")
        print(f"  Channel: {ctx_or_interaction.channel}")
        print(f"{'='*70}\n")
        
        channel_id = str(ctx_or_interaction.channel_id)
        
        # Get channel state
        state = self.channel_manager.get_channel_state(channel_id)
        print(f"  Current state: {state}")
        
        pinned_msg_id = state.get('pinned_message_id')
        
        if pinned_msg_id:
            try:
                print(f"  Fetching pinned message: {pinned_msg_id}")
                channel = ctx_or_interaction.channel
                message = await channel.fetch_message(int(pinned_msg_id))
                
                current_view = state.get('current_view', 'overview')
                print(f"  Current view: {current_view}")
                
                if current_view == 'overview':
                    print(f"  Getting overview embed")
                    embed = await self.bot.get_overview_embed()
                elif current_view == 'ticker':
                    ticker = state.get('current_ticker')
                    print(f"  Getting ticker embed for: {ticker}")
                    embed = await self.bot.get_ticker_embed(ticker) if ticker else await self.bot.get_overview_embed()
                else:
                    print(f"  Getting overview embed (fallback)")
                    embed = await self.bot.get_overview_embed()
                
                print(f"  Editing message with new embed")
                await message.edit(embed=embed)
                
                try:
                    await ctx_or_interaction.response.send_message("✅ Dashboard refreshed!", ephemeral=True, delete_after=3)
                except:
                    await ctx_or_interaction.followup.send("✅ Dashboard refreshed!", ephemeral=True, delete_after=3)
                    
            except Exception as e:
                print(f"\n{'='*70}")
                print(f"[ERROR] Refresh failed!")
                print(f"  Error: {e}")
                print(f"  Traceback:\n{traceback.format_exc()}")
                print(f"{'='*70}\n")
                try:
                    await ctx_or_interaction.response.send_message("❌ Failed to refresh", ephemeral=True)
                except:
                    await ctx_or_interaction.followup.send("❌ Failed to refresh", ephemeral=True)
        else:
            print(f"  No pinned message found in this channel")
            try:
                await ctx_or_interaction.response.send_message("No dashboard found in this channel", ephemeral=True)
            except:
                await ctx_or_interaction.followup.send("No dashboard found in this channel", ephemeral=True)
    
    # ========== TICKER ANALYSIS ==========
    
    async def show_ticker_analysis(self, ctx_or_interaction, ticker: str):
        """Show detailed ticker analysis"""
        print(f"\n{'='*70}")
        print(f"[FUNCTION] show_ticker_analysis called")
        print(f"  Ticker: {ticker}")
        print(f"  User: {ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author}")
        print(f"{'='*70}\n")
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            print(f"  Querying database for ticker: {ticker}")
            c.execute('''SELECT * FROM stock_tracking 
                         WHERE ticker = ? AND status = "tracking"
                         ORDER BY initial_date DESC LIMIT 1''', (ticker,))
            
            tracking = c.fetchone()
            print(f"  Query result: {tracking}")
            
            if tracking:
                columns = [desc[0] for desc in c.description]
                data = dict(zip(columns, tracking))
                
                print(f"  Creating embed for tracked ticker")
                embed = discord.Embed(
                    title=f"📊 {ticker} Analysis",
                    description="Tracked stock data found",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💰 Price",
                    value=f"Current: ${data.get('current_price', 'N/A')}\n"
                          f"Change: {data.get('price_change_pct', 0):+.2f}%\n"
                          f"High: ${data.get('max_price', 'N/A')}\n"
                          f"Low: ${data.get('min_price', 'N/A')}",
                    inline=True
                )
                
                embed.add_field(
                    name="📅 Tracking",
                    value=f"Days: {data.get('days_tracked', 0)}\n"
                          f"Status: {data.get('status', 'N/A')}\n"
                          f"Initial: ${data.get('initial_price', 'N/A')}",
                    inline=True
                )
                
                try:
                    await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
                except:
                    await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                print(f"  Ticker not found in tracking database")
                embed = discord.Embed(
                    title=f"📊 {ticker} - Not Tracked",
                    description=f"'{ticker}' is not currently being tracked by the Turd News Network.",
                    color=0xffaa00,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💡 How to Track",
                    value="This ticker will be automatically tracked when mentioned in WSB posts.",
                    inline=False
                )
                
                try:
                    await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
                except:
                    await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] Failed to show ticker analysis!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            try:
                await ctx_or_interaction.followup.send(f"❌ Error retrieving data for {ticker}", ephemeral=True)
            except:
                await ctx_or_interaction.response.send_message(f"❌ Error retrieving data for {ticker}", ephemeral=True)
        finally:
            conn.close()
            print(f"  Database connection closed")
    
    # ========== REPORT GENERATION ==========
    
    async def process_report_generation(self, ctx_or_interaction, ticker: str, report_type: str = 'comprehensive'):
        """Process report generation request"""
        print(f"\n{'='*70}")
        print(f"[FUNCTION] process_report_generation called")
        print(f"  Ticker: {ticker}")
        print(f"  Report Type: {report_type}")
        print(f"  User: {ctx_or_interaction.user if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author}")
        print(f"{'='*70}\n")
        
        try:
            print(f"  Importing TickerReportGenerator")
            from ticker_report import TickerReportGenerator
            
            generator = TickerReportGenerator(self.db)
            
            if report_type == 'comprehensive':
                print(f"  Generating comprehensive report for {ticker}")
                report_file = generator.generate_comprehensive_report(ticker)
            else:
                print(f"  Generating quick report for {ticker}")
                report_file = generator.generate_quick_report(ticker)
            
            print(f"  Report file: {report_file}")
            
            if report_file:
                import os
                file_size = os.path.getsize(report_file)
                print(f"  File size: {file_size} bytes")
                
                print(f"  Saving report to database...")
                self.channel_manager.save_report(
                    report_type=report_type,
                    ticker=ticker,
                    user_id=str(ctx_or_interaction.user.id if hasattr(ctx_or_interaction, 'user') else ctx_or_interaction.author.id),
                    channel_id=str(ctx_or_interaction.channel_id),
                    file_path=report_file,
                    pages=generator.page_count,
                    file_size=file_size
                )
                print(f"  Report saved to database")
                
                try:
                    await ctx_or_interaction.followup.send(
                        f"📄 **{ticker} Report Generated**",
                        file=discord.File(report_file),
                        ephemeral=True
                    )
                except:
                    await ctx_or_interaction.response.send_message(
                        f"📄 **{ticker} Report Generated**",
                        file=discord.File(report_file),
                        ephemeral=True
                    )
                print(f"  Report sent to user")
            else:
                print(f"  Report generation returned None")
                try:
                    await ctx_or_interaction.followup.send(f"❌ Could not generate report for {ticker}", ephemeral=True)
                except:
                    await ctx_or_interaction.response.send_message(f"❌ Could not generate report for {ticker}", ephemeral=True)
                
        except ImportError as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] Ticker report generator not available!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            try:
                await ctx_or_interaction.followup.send("📄 Report generation is being prepared. Please try again shortly.", ephemeral=True)
            except:
                await ctx_or_interaction.response.send_message("📄 Report generation is being prepared. Please try again shortly.", ephemeral=True)
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] Failed to process report!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            try:
                await ctx_or_interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                await ctx_or_interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    async def handle_ticker_report(self, interaction: discord.Interaction, ticker: str):
        """Handle ticker report button click"""
        print(f"\n{'='*70}")
        print(f"[FUNCTION] handle_ticker_report called")
        print(f"  Ticker: {ticker}")
        print(f"  User: {interaction.user}")
        print(f"{'='*70}\n")
        
        await interaction.response.defer(ephemeral=True)
        await self.process_report_generation(interaction, ticker, "comprehensive")


# ========== MODAL CLASSES ==========

class SearchTickerModal(ui.Modal):
    """Modal for searching stock tickers"""
    
    def __init__(self, handlers: ModalHandlers):
        super().__init__(title="📊 Search Stock", timeout=120)
        self.handlers = handlers
        
        self.ticker_input = ui.TextInput(
            label="Ticker Symbol",
            placeholder="e.g., GME, AAPL, TSLA",
            min_length=1,
            max_length=10,
            required=True
        )
        self.add_item(self.ticker_input)
        
        print(f"\n{'='*70}")
        print(f"[INIT] SearchTickerModal created")
        print(f"  Handlers: {handlers}")
        print(f"{'='*70}\n")
    
    async def callback(self, interaction: discord.Interaction):
        """Handle modal submission"""
        ticker = self.ticker_input.value
        
        print(f"\n{'='*70}")
        print(f"[MODAL CALLBACK] SearchTickerModal submitted")
        print(f"  User: {interaction.user}")
        print(f"  Ticker: {ticker}")
        print(f"  Time: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        try:
            await interaction.response.defer(ephemeral=True)
            print(f"  Calling show_ticker_analysis...")
            await self.handlers.show_ticker_analysis(interaction, ticker)
            print(f"  Analysis shown successfully")
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] SearchTickerModal error!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                pass


class GenerateReportModal(ui.Modal):
    """Modal for generating reports"""
    
    def __init__(self, handlers: ModalHandlers, report_type: str = "comprehensive"):
        super().__init__(title="📄 Generate Report", timeout=120)
        self.handlers = handlers
        self.report_type = report_type
        
        self.ticker_input = ui.TextInput(
            label="Ticker Symbol",
            placeholder="e.g., GME, AAPL, TSLA",
            min_length=1,
            max_length=10,
            required=True
        )
        self.add_item(self.ticker_input)
        
        print(f"\n{'='*70}")
        print(f"[INIT] GenerateReportModal created")
        print(f"  Handlers: {handlers}")
        print(f"  Report Type: {report_type}")
        print(f"{'='*70}\n")
    
    async def callback(self, interaction: discord.Interaction):
        """Handle modal submission"""
        ticker = self.ticker_input.value
        
        print(f"\n{'='*70}")
        print(f"[MODAL CALLBACK] GenerateReportModal submitted")
        print(f"  User: {interaction.user}")
        print(f"  Ticker: {ticker}")
        print(f"  Report Type: {self.report_type}")
        print(f"  Time: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        try:
            await interaction.response.defer(ephemeral=True)
            print(f"  Calling process_report_generation...")
            await self.handlers.process_report_generation(interaction, ticker, self.report_type)
            print(f"  Report generation initiated")
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] GenerateReportModal error!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")


class RefreshIntervalModal(ui.Modal):
    """Modal for setting refresh interval"""
    
    def __init__(self, channel_manager):
        super().__init__(title="⏱️ Set Refresh Interval", timeout=60)
        self.channel_manager = channel_manager
        
        self.interval_input = ui.TextInput(
            label="Interval (seconds)",
            placeholder="30, 60, 120 (min: 10, max: 300)",
            default="30",
            required=True
        )
        self.add_item(self.interval_input)
        
        print(f"\n{'='*70}")
        print(f"[INIT] RefreshIntervalModal created")
        print(f"  Channel Manager: {channel_manager}")
        print(f"{'='*70}\n")
    
    async def callback(self, interaction: discord.Interaction):
        """Handle modal submission"""
        print(f"\n{'='*70}")
        print(f"[MODAL CALLBACK] RefreshIntervalModal submitted")
        print(f"  User: {interaction.user}")
        print(f"  Interval: {self.interval_input.value}")
        print(f"  Time: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        try:
            interval = int(self.interval_input.value)
            interval = max(10, min(300, interval))
            
            channel_id = str(interaction.channel_id)
            self.channel_manager.update_channel_state(channel_id, refresh_interval=interval)
            print(f"  Updated refresh interval to: {interval} seconds")
            
            embed = discord.Embed(
                title="✅ Interval Updated",
                description=f"Refresh interval set to **{interval} seconds**",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"  Response sent successfully")
            
        except ValueError:
            print(f"\n{'='*70}")
            print(f"[ERROR] Invalid interval input!")
            print(f"  Input: {self.interval_input.value}")
            print(f"{'='*70}\n")
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please enter a valid number",
                color=0xff0000,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
