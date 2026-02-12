"""
Button Handlers for Discord Dashboard
Handles all button click interactions
EXTREME LOGGING ENABLED - Every action is logged
"""

import discord
from discord import ui
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import traceback

from database import DatabaseManager
from channel_manager import ChannelManager
from modal_handlers import ModalHandlers

# EXTREME LOGGING SETTINGS
LOG_BUTTON_PRESSES = True
LOG_STATE_CHANGES = True
LOG_ERRORS = True
LOG_ALL_FUNCTIONS = True


def log_button_press(func):
    """Decorator to log all button press calls"""
    async def wrapper(*args, **kwargs):
        interaction = args[1] if len(args) > 1 else kwargs.get('interaction')
        button_label = getattr(interaction, 'custom_id', 'unknown') or getattr(interaction, 'data', {}).get('custom_id', 'unknown')
        user = interaction.user if hasattr(interaction, 'user') else 'unknown'
        guild = interaction.guild.name if hasattr(interaction, 'guild') and interaction.guild else 'DM'
        
        print(f"\n{'='*70}")
        print(f"[BUTTON PRESS] {func.__name__}")
        print(f"  Button/Action: {button_label}")
        print(f"  User: {user} (ID: {getattr(user, 'id', 'unknown')})")
        print(f"  Guild: {guild}")
        print(f"  Channel: {getattr(interaction, 'channel', 'unknown')}")
        print(f"  Time: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        try:
            result = await func(*args, **kwargs)
            print(f"[SUCCESS] {func.__name__} completed")
            return result
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] {func.__name__} FAILED!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            raise
    return wrapper


def log_state_change(state_description):
    """Decorator to log state changes"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            interaction = args[1] if len(args) > 1 else kwargs.get('interaction')
            print(f"\n{'='*70}")
            print(f"[STATE CHANGE] {state_description}")
            print(f"  Old state: Getting current state...")
            print(f"  New state: {state_description}")
            print(f"  User: {interaction.user if hasattr(interaction, 'user') else 'unknown'}")
            print(f"  Time: {datetime.now().isoformat()}")
            print(f"{'='*70}\n")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class ButtonHandlers:
    """Handles all button click interactions"""
    
    def __init__(self, bot, db: DatabaseManager, 
                 channel_manager: ChannelManager,
                 modal_handlers: ModalHandlers):
        self.bot = bot
        self.db = db
        self.channel_manager = channel_manager
        self.modal_handlers = modal_handlers
        
        print(f"\n{'='*70}")
        print(f"[INIT] ButtonHandlers initialized")
        print(f"  Bot: {bot}")
        print(f"  DB: {db}")
        print(f"  Channel Manager: {channel_manager}")
        print(f"  Modal Handlers: {modal_handlers}")
        print(f"{'='*70}\n")
    
    @log_button_press
    async def handle_back_to_overview(self, interaction: discord.Interaction):
        """Return to overview view"""
        print(f"[FUNCTION] handle_back_to_overview called")
        print(f"  Interaction: {interaction}")
        print(f"  User: {interaction.user}")
        print(f"  Channel: {interaction.channel}")
        
        channel_id = str(interaction.channel_id)
        old_state = self.channel_manager.get_channel_state(channel_id)
        print(f"  Old state: {old_state}")
        
        self.channel_manager.update_channel_state(
            channel_id, current_view='overview', current_ticker=None
        )
        print(f"  State updated to: overview")
        
        self.channel_manager.update_user_activity(str(interaction.user.id))
        print(f"  User activity updated")
        
        bot = interaction.client
        print(f"  Bot from interaction: {bot}")
        
        if hasattr(bot, 'get_overview_embed'):
            print(f"  Calling bot.get_overview_embed()")
            embed = await bot.get_overview_embed()
        else:
            print(f"  Bot doesn't have get_overview_embed - using fallback")
            embed = discord.Embed(title="Market Overview", color=0x00ff00)
        
        from discord_dashboard import OverviewView
        print(f"  Creating OverviewView")
        view = OverviewView(bot)
        
        print(f"  Sending response: edit message with embed and view")
        await interaction.response.edit_message(embed=embed, view=view)
        print(f"  Response sent successfully")
    
    @log_button_press
    async def handle_settings(self, interaction: discord.Interaction):
        """Open settings view"""
        print(f"[FUNCTION] handle_settings called")
        print(f"  Interaction: {interaction}")
        print(f"  User: {interaction.user}")
        
        channel_id = str(interaction.channel_id)
        old_state = self.channel_manager.get_channel_state(channel_id)
        print(f"  Old state: {old_state}")
        
        self.channel_manager.update_channel_state(channel_id, current_view='settings')
        print(f"  State updated to: settings")
        
        self.channel_manager.update_user_activity(str(interaction.user.id))
        print(f"  User activity updated")
        
        bot = interaction.client
        if hasattr(bot, 'get_settings_embed'):
            print(f"  Calling bot.get_settings_embed()")
            embed = await bot.get_settings_embed()
        else:
            print(f"  Bot doesn't have get_settings_embed - using fallback")
            embed = discord.Embed(title="Settings", color=0xffaa00)
        
        from discord_dashboard import SettingsView
        print(f"  Creating SettingsView")
        view = SettingsView(bot)
        
        print(f"  Sending response: edit message")
        await interaction.response.edit_message(embed=embed, view=view)
        print(f"  Response sent successfully")
    
    @log_button_press
    async def handle_refresh(self, interaction: discord.Interaction):
        """Force refresh dashboard data"""
        print(f"[FUNCTION] handle_refresh called")
        print(f"  Interaction: {interaction}")
        print(f"  User: {interaction.user}")
        print(f"  Channel: {interaction.channel}")
        
        self.channel_manager.update_user_activity(str(interaction.user.id))
        print(f"  User activity updated")
        
        print(f"  Deferring response (ephemeral)")
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel_id = str(interaction.channel_id)
            state = self.channel_manager.get_channel_state(channel_id)
            print(f"  Current state: {state}")
            
            bot = interaction.client
            print(f"  Bot: {bot}")
            
            current_view = state.get('current_view', 'overview')
            print(f"  Current view: {current_view}")
            
            if current_view == 'overview' and hasattr(bot, 'get_overview_embed'):
                print(f"  Refreshing overview embed")
                embed = await bot.get_overview_embed()
            elif current_view == 'ticker' and hasattr(bot, 'get_ticker_embed'):
                ticker = state.get('current_ticker')
                print(f"  Refreshing ticker embed for: {ticker}")
                embed = await bot.get_ticker_embed(ticker) if ticker else discord.Embed(title="Ticker", color=0x00aaff)
            elif hasattr(bot, 'get_settings_embed'):
                print(f"  Refreshing settings embed")
                embed = await bot.get_settings_embed()
            else:
                print(f"  Using fallback overview embed")
                embed = discord.Embed(title="Market Overview", color=0x00ff00)
            
            print(f"  Sending followup: Dashboard refreshed!")
            await interaction.followup.send("Dashboard refreshed!", ephemeral=True)
            print(f"  Refresh completed successfully")
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] Failed to refresh dashboard!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            await interaction.followup.send("Error refreshing dashboard", ephemeral=True)
    
    @log_button_press
    async def handle_view_ticker(self, interaction: discord.Interaction, ticker: str):
        """View detailed ticker information"""
        print(f"[FUNCTION] handle_view_ticker called")
        print(f"  Ticker: {ticker}")
        print(f"  User: {interaction.user}")
        print(f"  Channel: {interaction.channel}")
        
        channel_id = str(interaction.channel_id)
        old_state = self.channel_manager.get_channel_state(channel_id)
        print(f"  Old state: {old_state}")
        
        self.channel_manager.update_channel_state(
            channel_id, current_view='ticker', current_ticker=ticker.upper()
        )
        print(f"  State updated to ticker: {ticker.upper()}")
        
        self.channel_manager.update_user_activity(str(interaction.user.id))
        print(f"  User activity updated")
        
        bot = interaction.client
        if hasattr(bot, 'get_ticker_embed'):
            print(f"  Calling bot.get_ticker_embed({ticker})")
            embed = await bot.get_ticker_embed(ticker)
        else:
            print(f"  Bot doesn't have get_ticker_embed - using fallback")
            embed = discord.Embed(title=f"{ticker.upper()} Analysis", color=0x00aaff)
        
        from discord_dashboard import TickerView
        print(f"  Creating TickerView for {ticker}")
        view = TickerView(bot, ticker)
        
        print(f"  Sending response: edit message")
        await interaction.response.edit_message(embed=embed, view=view)
        print(f"  Response sent successfully")
    
    @log_button_press
    async def handle_add_to_watchlist(self, interaction: discord.Interaction, ticker: str):
        """Add ticker to user's watchlist"""
        print(f"[FUNCTION] handle_add_to_watchlist called")
        print(f"  Ticker: {ticker}")
        print(f"  User: {interaction.user}")
        print(f"  User ID: {interaction.user.id}")
        
        user_id = str(interaction.user.id)
        print(f"  Checking if already in watchlist...")
        success = self.channel_manager.add_to_watchlist(user_id, ticker)
        
        print(f"  Add to watchlist result: {success}")
        
        if success:
            print(f"  Creating success embed")
            embed = discord.Embed(
                title="Added to Watchlist",
                description=f"**{ticker.upper()}** has been added",
                color=0x00ff00
            )
        else:
            print(f"  Creating already exists embed")
            embed = discord.Embed(
                title="Already in Watchlist",
                description=f"**{ticker.upper()}** is already there",
                color=0xffaa00
            )
        
        print(f"  Sending ephemeral response")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        print(f"  Response sent successfully")
    
    @log_button_press
    async def handle_remove_from_watchlist(self, interaction: discord.Interaction, 
                                           ticker: str, user_id: str):
        """Remove ticker from watchlist"""
        print(f"[FUNCTION] handle_remove_from_watchlist called")
        print(f"  Ticker: {ticker}")
        print(f"  User ID: {user_id}")
        print(f"  User: {interaction.user}")
        
        success = self.channel_manager.remove_from_watchlist(user_id, ticker)
        print(f"  Remove result: {success}")
        
        if success:
            print(f"  Creating success embed")
            embed = discord.Embed(title="Removed", color=0x00ff00)
        else:
            print(f"  Creating not found embed")
            embed = discord.Embed(title="Not Found", color=0xffaa00)
        
        print(f"  Sending ephemeral response")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        print(f"  Response sent successfully")
    
    @log_button_press
    async def handle_toggle_autorefresh(self, interaction: discord.Interaction):
        """Toggle auto-refresh on/off"""
        print(f"[FUNCTION] handle_toggle_autorefresh called")
        print(f"  User: {interaction.user}")
        print(f"  Channel: {interaction.channel}")
        
        channel_id = str(interaction.channel_id)
        state = self.channel_manager.get_channel_state(channel_id)
        print(f"  Current auto_refresh: {state.get('auto_refresh', True)}")
        
        new_auto = not state.get('auto_refresh', True)
        print(f"  New auto_refresh: {new_auto}")
        
        self.channel_manager.update_channel_state(channel_id, auto_refresh=new_auto)
        print(f"  State updated")
        
        status = "enabled" if new_auto else "disabled"
        print(f"  Creating status embed")
        embed = discord.Embed(
            title=f"Auto-Refresh {status}",
            color=0x00ff00 if new_auto else 0xffaa00
        )
        
        print(f"  Sending ephemeral response")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        print(f"  Response sent successfully")
    
    @log_button_press
    async def handle_generate_ticker_report(self, interaction: discord.Interaction, 
                                           ticker: str, report_type: str = 'comprehensive'):
        """Generate report for a ticker"""
        print(f"[FUNCTION] handle_generate_ticker_report called")
        print(f"  Ticker: {ticker}")
        print(f"  Report Type: {report_type}")
        print(f"  User: {interaction.user}")
        
        print(f"  Deferring response (ephemeral)")
        await interaction.response.defer(ephemeral=True)
        
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
                    report_type=report_type, ticker=ticker,
                    user_id=str(interaction.user.id), channel_id=str(interaction.channel_id),
                    file_path=report_file, pages=generator.page_count, file_size=file_size
                )
                print(f"  Report saved")
                
                print(f"  Sending report file")
                await interaction.followup.send(
                    f"**{ticker} Report**", file=discord.File(report_file), ephemeral=True
                )
                print(f"  Report sent successfully")
            else:
                print(f"  Report generation returned None")
                await interaction.followup.send(f"Could not generate report for {ticker}", ephemeral=True)
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] Report generation failed!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)
    
    @log_button_press
    async def show_top_movers(self, interaction: discord.Interaction, direction: str = 'gainers'):
        """Show top gainers or losers"""
        print(f"[FUNCTION] show_top_movers called")
        print(f"  Direction: {direction}")
        print(f"  User: {interaction.user}")
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            if direction == 'gainers':
                print(f"  Querying top gainers...")
                c.execute('''SELECT ticker, price_change_pct, current_price
                             FROM stock_tracking WHERE status = "tracking"
                             ORDER BY price_change_pct DESC LIMIT 10''')
                title = "Top Gainers"
            else:
                print(f"  Querying top losers...")
                c.execute('''SELECT ticker, price_change_pct, current_price
                             FROM stock_tracking WHERE status = "tracking"
                             ORDER BY price_change_pct ASC LIMIT 10''')
                title = "Top Losers"
            
            results = c.fetchall()
            print(f"  Query returned {len(results)} results")
            
            embed = discord.Embed(title=title, color=0x00ff00 if direction == 'gainers' else 0xff0000)
            
            for i, (ticker, change, price) in enumerate(results[:10], 1):
                print(f"  {i}. {ticker}: {change:+.2f}% @ ${price:.2f}")
                embed.add_field(name=f"{i}. {ticker}", value=f"{change:+.2f}% @ ${price:.2f}", inline=True)
            
            print(f"  Sending ephemeral response")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"  Response sent successfully")
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"[ERROR] show_top_movers failed!")
            print(f"  Error: {e}")
            print(f"  Traceback:\n{traceback.format_exc()}")
            print(f"{'='*70}\n")
            await interaction.response.send_message("Error loading data", ephemeral=True)
        finally:
            conn.close()
            print(f"  Database connection closed")
    
    @log_button_press
    async def show_recent_alerts(self, interaction: discord.Interaction):
        """Show recent alerts"""
        print(f"[FUNCTION] show_recent_alerts called")
        print(f"  User: {interaction.user}")
        
        conn = self