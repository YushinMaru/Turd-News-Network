"""
Watchlist Manager - Handles watchlist operations and monitoring
Integrates with existing DatabaseManager and StockDataFetcher
"""

import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import discord
from discord.ext import tasks, commands

from database import DatabaseManager
from stock_data import StockDataFetcher


class WatchlistManager:
    """Manages user watchlists with real-time monitoring and notifications"""
    
    def __init__(self, db: DatabaseManager, stock_fetcher: StockDataFetcher, bot: commands.Bot):
        self.db = db
        self.stock_fetcher = stock_fetcher
        self.bot = bot
        self.monitoring_active = False
        self.last_check = {}
        
    async def start_monitoring(self):
        """Start the background watchlist monitoring task"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.watchlist_monitor.start()
            print("[WATCHLIST] ✅ Monitoring started")
    
    async def stop_monitoring(self):
        """Stop the background monitoring task"""
        self.monitoring_active = False
        self.watchlist_monitor.cancel()
        print("[WATCHLIST] ⛔ Monitoring stopped")
    
    @tasks.loop(seconds=60)  # Check every minute
    async def watchlist_monitor(self):
        """Background task to monitor all watchlists for alert conditions"""
        try:
            # Get all active watchlist items
            watchlist_items = self.db.get_all_watchlist_items()
            
            if not watchlist_items:
                return
            
            print(f"[WATCHLIST] Checking {len(watchlist_items)} watchlist items...")
            
            # Group by ticker to minimize API calls
            ticker_groups = {}
            for item in watchlist_items:
                ticker = item['ticker']
                if ticker not in ticker_groups:
                    ticker_groups[ticker] = []
                ticker_groups[ticker].append(item)
            
            # Check each unique ticker
            for ticker, items in ticker_groups.items():
                try:
                    await self._check_ticker_alerts(ticker, items)
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    print(f"[WATCHLIST] Error checking {ticker}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[WATCHLIST] Monitor error: {e}")
            traceback.print_exc()
    
    async def _check_ticker_alerts(self, ticker: str, watchlist_items: List[Dict]):
        """Check alerts for a specific ticker across all users watching it"""
        # Fetch current stock data
        stock_data = self.stock_fetcher.get_stock_data(ticker)
        if not stock_data:
            return
        
        current_price = stock_data.get('price', 0)
        change_pct = stock_data.get('change_pct', 0)
        volume = stock_data.get('volume', 0)
        avg_volume = stock_data.get('average_volume', 0)
        
        # Check each user's watchlist item
        for item in watchlist_items:
            user_id = item['user_id']
            
            # Update last known price
            self.db.update_watchlist_price(user_id, ticker, current_price)
            
            # Check alert conditions
            alerts_triggered = []
            
            # Price above alert
            if item['alert_price_above'] and current_price >= item['alert_price_above']:
                if self._should_trigger_alert(user_id, ticker, 'price_above'):
                    alerts_triggered.append({
                        'type': 'price_above',
                        'message': f"🚀 **{ticker}** crossed above ${item['alert_price_above']:.2f}!\n"
                                  f"Current price: **${current_price:.2f}**",
                        'condition': f'Above ${item["alert_price_above"]:.2f}'
                    })
            
            # Price below alert
            if item['alert_price_below'] and current_price <= item['alert_price_below']:
                if self._should_trigger_alert(user_id, ticker, 'price_below'):
                    alerts_triggered.append({
                        'type': 'price_below',
                        'message': f"📉 **{ticker}** dropped below ${item['alert_price_below']:.2f}!\n"
                                  f"Current price: **${current_price:.2f}**",
                        'condition': f'Below ${item["alert_price_below"]:.2f}'
                    })
            
            # Percent change alert
            if item['alert_percent_change'] and abs(change_pct) >= item['alert_percent_change']:
                if self._should_trigger_alert(user_id, ticker, 'percent_change'):
                    direction = "📈 up" if change_pct > 0 else "📉 down"
                    alerts_triggered.append({
                        'type': 'percent_change',
                        'message': f"⚡ **{ticker}** is {direction} **{abs(change_pct):.2f}%** today!\n"
                                  f"Current price: **${current_price:.2f}**",
                        'condition': f'{abs(change_pct):.2f}% change'
                    })
            
            # Volume spike alert
            if item['alert_volume_spike'] and avg_volume > 0:
                volume_ratio = volume / avg_volume
                if volume_ratio >= 2.0:  # 2x average volume
                    if self._should_trigger_alert(user_id, ticker, 'volume_spike'):
                        alerts_triggered.append({
                            'type': 'volume_spike',
                            'message': f"📊 **{ticker}** volume spike! **{volume_ratio:.1f}x** average\n"
                                      f"Current volume: **{volume:,}**",
                            'condition': f'{volume_ratio:.1f}x volume'
                        })
            
            # Send notifications
            for alert in alerts_triggered:
                await self._send_alert(user_id, ticker, alert, current_price)
    
    def _should_trigger_alert(self, user_id: str, ticker: str, alert_type: str) -> bool:
        """Check if alert should be triggered (rate limiting)"""
        key = f"{user_id}:{ticker}:{alert_type}"
        now = datetime.now()
        
        # Check last alert time (don't alert more than once per hour for same condition)
        if key in self.last_check:
            last_time = self.last_check[key]
            if now - last_time < timedelta(hours=1):
                return False
        
        self.last_check[key] = now
        return True
    
    async def _send_alert(self, user_id: str, ticker: str, alert: Dict, trigger_price: float):
        """Send alert notification to user"""
        try:
            # Log the alert
            self.db.log_watchlist_alert(
                user_id, ticker, alert['type'],
                trigger_price, alert['condition'], alert['message']
            )
            
            # Get user's notification settings
            settings = self.db.get_notification_settings(user_id)
            
            # Check quiet hours
            current_hour = datetime.now().hour
            if settings['quiet_hours_start'] <= current_hour or current_hour < settings['quiet_hours_end']:
                return  # In quiet hours, don't send
            
            # Get user object
            user = await self.bot.fetch_user(int(user_id))
            if not user:
                return
            
            # Send DM if enabled
            if settings['dm_enabled']:
                embed = discord.Embed(
                    title=f"🔔 Watchlist Alert: {ticker}",
                    description=alert['message'],
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="Alert Type",
                    value=alert['type'].replace('_', ' ').title(),
                    inline=True
                )
                embed.add_field(
                    name="Time",
                    value=datetime.now().strftime('%I:%M %p'),
                    inline=True
                )
                embed.set_footer(text="Turd News Network - Watchlist Monitor")
                
                await user.send(embed=embed)
                print(f"[WATCHLIST] ✅ Alert sent to user {user_id} for {ticker}")
                
        except Exception as e:
            print(f"[WATCHLIST] Error sending alert: {e}")
    
    async def add_stock(self, user_id: str, ticker: str, **kwargs) -> Tuple[bool, str]:
        """Add a stock to user's watchlist"""
        try:
            # Validate ticker
            ticker = ticker.upper().strip()
            stock_data = self.stock_fetcher.get_stock_data(ticker)
            
            if not stock_data:
                return False, f"❌ Could not find ticker **{ticker}**. Please check the symbol."
            
            # Check if already in watchlist
            if self.db.is_in_watchlist(user_id, ticker):
                return False, f"⚠️ **{ticker}** is already in your watchlist!"
            
            # Check watchlist limit (20 stocks)
            current_watchlist = self.db.get_user_watchlist(user_id)
            if len(current_watchlist) >= 20:
                return False, "❌ Watchlist limit reached (20 stocks). Remove some to add more."
            
            # Add to watchlist
            success = self.db.add_to_watchlist(user_id, ticker, **kwargs)
            
            if success:
                company_name = stock_data.get('name', ticker)
                return True, f"✅ Added **{ticker}** ({company_name}) to your watchlist!"
            else:
                return False, "❌ Failed to add to watchlist. Please try again."
                
        except Exception as e:
            print(f"[WATCHLIST] Error adding stock: {e}")
            return False, f"❌ Error: {str(e)}"
    
    async def remove_stock(self, user_id: str, ticker: str) -> Tuple[bool, str]:
        """Remove a stock from user's watchlist"""
        try:
            ticker = ticker.upper().strip()
            
            if not self.db.is_in_watchlist(user_id, ticker):
                return False, f"⚠️ **{ticker}** is not in your watchlist!"
            
            success = self.db.remove_from_watchlist(user_id, ticker)
            
            if success:
                return True, f"✅ Removed **{ticker}** from your watchlist!"
            else:
                return False, "❌ Failed to remove from watchlist."
                
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    async def get_watchlist_display(self, user_id: str) -> Tuple[List[Dict], str]:
        """Get formatted watchlist data for display"""
        try:
            watchlist = self.db.get_user_watchlist(user_id)
            
            if not watchlist:
                return [], "Your watchlist is empty! Use 'Add Stock' to start tracking stocks."
            
            # Fetch current data for each stock
            enriched_data = []
            for item in watchlist:
                ticker = item['ticker']
                stock_data = self.stock_fetcher.get_stock_data(ticker)
                
                if stock_data:
                    enriched_data.append({
                        **item,
                        'current_price': stock_data.get('price', item['last_price']),
                        'change_pct': stock_data.get('change_pct', 0),
                        'volume': stock_data.get('volume', 0),
                        'market_cap': stock_data.get('market_cap', 0),
                        'company_name': stock_data.get('name', ticker)
                    })
                else:
                    enriched_data.append({
                        **item,
                        'current_price': item['last_price'] or 'N/A',
                        'change_pct': 0,
                        'volume': 0,
                        'market_cap': 0,
                        'company_name': ticker
                    })
            
            return enriched_data, None
            
        except Exception as e:
            return [], f"❌ Error loading watchlist: {str(e)}"
    
    def update_alert_settings(self, user_id: str, ticker: str, **kwargs) -> Tuple[bool, str]:
        """Update alert settings for a watchlist item"""
        try:
            success = self.db.update_watchlist_alerts(user_id, ticker, **kwargs)
            
            if success:
                return True, f"✅ Alert settings updated for **{ticker}**!"
            else:
                return False, "❌ Failed to update alert settings."
                
        except Exception as e:
            return False, f"❌ Error: {str(e)}"


# ============================================================================
# DISCORD UI COMPONENTS
# ============================================================================

class AddToWatchlistModal(discord.ui.Modal, title="⭐ Add to Watchlist"):
    """Modal for adding a stock to watchlist with alert settings"""
    
    ticker_input = discord.ui.TextInput(
        label="Ticker Symbol",
        placeholder="e.g., AAPL, NVDA, TSLA",
        min_length=1,
        max_length=10,
        required=True
    )
    
    notes_input = discord.ui.TextInput(
        label="Notes (optional)",
        placeholder="Why are you watching this stock?",
        max_length=200,
        required=False
    )
    
    price_above_input = discord.ui.TextInput(
        label="Alert when price goes ABOVE ($)",
        placeholder="Leave blank for no alert",
        required=False
    )
    
    price_below_input = discord.ui.TextInput(
        label="Alert when price goes BELOW ($)",
        placeholder="Leave blank for no alert",
        required=False
    )
    
    percent_change_input = discord.ui.TextInput(
        label="Alert on % change (e.g., 5 for 5%)",
        placeholder="Leave blank for no alert",
        required=False
    )
    
    def __init__(self, watchlist_manager: WatchlistManager):
        super().__init__()
        self.watchlist_manager = watchlist_manager
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parse inputs
            ticker = self.ticker_input.value.upper().strip()
            notes = self.notes_input.value or ''
            
            # Parse optional alert values
            alert_price_above = None
            alert_price_below = None
            alert_percent_change = None
            
            if self.price_above_input.value:
                try:
                    alert_price_above = float(self.price_above_input.value)
                except ValueError:
                    pass
            
            if self.price_below_input.value:
                try:
                    alert_price_below = float(self.price_below_input.value)
                except ValueError:
                    pass
            
            if self.percent_change_input.value:
                try:
                    alert_percent_change = float(self.percent_change_input.value)
                except ValueError:
                    pass
            
            # Add to watchlist
            success, message = await self.watchlist_manager.add_stock(
                str(interaction.user.id),
                ticker,
                notes=notes,
                alert_price_above=alert_price_above,
                alert_price_below=alert_price_below,
                alert_percent_change=alert_percent_change
            )
            
            await interaction.followup.send(message, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class RemoveFromWatchlistSelect(discord.ui.Select):
    """Dropdown to select a stock to remove from watchlist"""
    
    def __init__(self, watchlist_items: List[Dict], watchlist_manager: WatchlistManager, user_id: str):
        self.watchlist_manager = watchlist_manager
        self.user_id = user_id
        
        options = [
            discord.SelectOption(
                label=f"{item['ticker']} - {item.get('company_name', item['ticker'])[:30]}",
                value=item['ticker'],
                description=item['notes'][:50] if item['notes'] else "No notes"
            )
            for item in watchlist_items[:25]  # Discord limit
        ]
        
        super().__init__(
            placeholder="Select a stock to remove...",
            options=options if options else [discord.SelectOption(label="Empty", value="empty")]
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "empty":
            await interaction.response.send_message("❌ Watchlist is empty!", ephemeral=True)
            return
        
        ticker = self.values[0]
        success, message = await self.watchlist_manager.remove_stock(self.user_id, ticker)
        await interaction.response.send_message(message, ephemeral=True)


class RemoveFromWatchlistView(discord.ui.View):
    """View for removing stocks from watchlist"""
    
    def __init__(self, watchlist_items: List[Dict], watchlist_manager: WatchlistManager, user_id: str):
        super().__init__()
        if watchlist_items:
            self.add_item(RemoveFromWatchlistSelect(watchlist_items, watchlist_manager, user_id))


class EditAlertsSelect(discord.ui.Select):
    """Dropdown to select a stock to edit alerts"""
    
    def __init__(self, watchlist_items: List[Dict], watchlist_manager: WatchlistManager, user_id: str):
        self.watchlist_manager = watchlist_manager
        self.user_id = user_id
        self.watchlist_items = {item['ticker']: item for item in watchlist_items}
        
        options = [
            discord.SelectOption(
                label=f"{item['ticker']} - {item.get('company_name', item['ticker'])[:30]}",
                value=item['ticker'],
                description=f"Alerts: {'Above $' + str(item['alert_price_above']) if item['alert_price_above'] else ''} {'Below $' + str(item['alert_price_below']) if item['alert_price_below'] else ''}"[:50]
            )
            for item in watchlist_items[:25]
        ]
        
        super().__init__(
            placeholder="Select a stock to edit alerts...",
            options=options if options else [discord.SelectOption(label="Empty", value="empty")]
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "empty":
            await interaction.response.send_message("❌ Watchlist is empty!", ephemeral=True)
            return
        
        ticker = self.values[0]
        item = self.watchlist_items.get(ticker, {})
        
        # Open modal for selected ticker
        await interaction.response.send_modal(
            AlertSettingsModal(
                self.watchlist_manager,
                self.user_id,
                ticker,
                item
            )
        )


class EditAlertsSelectView(discord.ui.View):
    """View for selecting which stock to edit alerts for"""
    
    def __init__(self, watchlist_items: List[Dict], watchlist_manager: WatchlistManager, user_id: str):
        super().__init__()
        if watchlist_items:
            self.add_item(EditAlertsSelect(watchlist_items, watchlist_manager, user_id))


class AlertSettingsModal(discord.ui.Modal, title="🔔 Alert Settings"):
    """Modal for editing alert settings for a watchlist item"""
    
    price_above = discord.ui.TextInput(
        label="Alert when price goes ABOVE ($)",
        placeholder="Leave blank for no alert",
        required=False
    )
    
    price_below = discord.ui.TextInput(
        label="Alert when price goes BELOW ($)",
        placeholder="Leave blank for no alert",
        required=False
    )
    
    percent_change = discord.ui.TextInput(
        label="Alert on % change (e.g., 5 for 5%)",
        placeholder="Leave blank for no alert",
        required=False
    )
    
    def __init__(self, watchlist_manager: WatchlistManager, user_id: str, ticker: str, current_settings: Dict):
        super().__init__()
        self.watchlist_manager = watchlist_manager
        self.user_id = user_id
        self.ticker = ticker
        
        # Pre-fill current values
        if current_settings.get('alert_price_above'):
            self.price_above.default = str(current_settings['alert_price_above'])
        if current_settings.get('alert_price_below'):
            self.price_below.default = str(current_settings['alert_price_below'])
        if current_settings.get('alert_percent_change'):
            self.percent_change.default = str(current_settings['alert_percent_change'])
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Parse inputs
            alert_price_above = float(self.price_above.value) if self.price_above.value else None
            alert_price_below = float(self.price_below.value) if self.price_below.value else None
            alert_percent_change = float(self.percent_change.value) if self.percent_change.value else None
            
            # Update settings
            success, message = self.watchlist_manager.update_alert_settings(
                self.user_id,
                self.ticker,
                alert_price_above=alert_price_above,
                alert_price_below=alert_price_below,
                alert_percent_change=alert_percent_change
            )
            
            await interaction.followup.send(message, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class NotificationSettingsModal(discord.ui.Modal, title="⚙️ Notification Settings"):
    """Modal for configuring notification preferences"""
    
    quiet_start = discord.ui.TextInput(
        label="Quiet Hours Start (24h format)",
        placeholder="22 for 10 PM",
        default="22",
        min_length=1,
        max_length=2,
        required=True
    )
    
    quiet_end = discord.ui.TextInput(
        label="Quiet Hours End (24h format)",
        placeholder="7 for 7 AM",
        default="7",
        min_length=1,
        max_length=2,
        required=True
    )
    
    max_alerts = discord.ui.TextInput(
        label="Max Alerts Per Day",
        placeholder="50",
        default="50",
        min_length=1,
        max_length=3,
        required=True
    )
    
    def __init__(self, db: DatabaseManager, user_id: str, current_settings: Dict):
        super().__init__()
        self.db = db
        self.user_id = user_id
        
        # Pre-fill current values
        self.quiet_start.default = str(current_settings.get('quiet_hours_start', 22))
        self.quiet_end.default = str(current_settings.get('quiet_hours_end', 7))
        self.max_alerts.default = str(current_settings.get('max_alerts_per_day', 50))
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get current settings
            settings = self.db.get_notification_settings(self.user_id)
            
            # Update with new values
            settings['quiet_hours_start'] = int(self.quiet_start.value)
            settings['quiet_hours_end'] = int(self.quiet_end.value)
            settings['max_alerts_per_day'] = int(self.max_alerts.value)
            
            # Save
            success = self.db.save_notification_settings(self.user_id, settings)
            
            if success:
                await interaction.followup.send(
                    f"✅ Notification settings updated!\n"
                    f"Quiet hours: {settings['quiet_hours_start']}:00 - {settings['quiet_hours_end']}:00",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ Failed to save settings.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class WatchlistView(discord.ui.View):
    """Main watchlist view with buttons for managing watchlist"""
    
    def __init__(self, watchlist_manager: WatchlistManager, user_id: str):
        super().__init__(timeout=300)
        self.watchlist_manager = watchlist_manager
        self.user_id = user_id
    
    @discord.ui.button(label="➕ Add Stock", style=discord.ButtonStyle.success, row=0)
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddToWatchlistModal(self.watchlist_manager))
    
    @discord.ui.button(label="➖ Remove Stock", style=discord.ButtonStyle.danger, row=0)
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        watchlist, error = await self.watchlist_manager.get_watchlist_display(self.user_id)
        
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        
        view = RemoveFromWatchlistView(watchlist, self.watchlist_manager, self.user_id)
        await interaction.response.send_message("Select a stock to remove:", view=view, ephemeral=True)
    
    @discord.ui.button(label="📊 View Watchlist", style=discord.ButtonStyle.primary, row=0)
    async def view_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        watchlist, error = await self.watchlist_manager.get_watchlist_display(self.user_id)
        
        if error:
            await interaction.followup.send(error, ephemeral=True)
            return
        
        if not watchlist:
            await interaction.followup.send("Your watchlist is empty!", ephemeral=True)
            return
        
        # Create embed with watchlist data
        embed = discord.Embed(
            title=f"⭐ Your Watchlist ({len(watchlist)} stocks)",
            description="Track your favorite stocks with real-time alerts",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        # Sort by daily change (gainers first)
        watchlist_sorted = sorted(watchlist, key=lambda x: x.get('change_pct', 0), reverse=True)
        
        for item in watchlist_sorted[:10]:  # Show top 10
            ticker = item['ticker']
            price = item.get('current_price', 'N/A')
            change = item.get('change_pct', 0)
            alerts = []
            
            if item.get('alert_price_above'):
                alerts.append(f"Above ${item['alert_price_above']:.2f}")
            if item.get('alert_price_below'):
                alerts.append(f"Below ${item['alert_price_below']:.2f}")
            if item.get('alert_percent_change'):
                alerts.append(f"±{item['alert_percent_change']:.1f}%")
            
            alert_text = " | ".join(alerts) if alerts else "No alerts set"
            
            change_emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            change_str = f"{change:+.2f}%"
            
            price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
            
            embed.add_field(
                name=f"{change_emoji} {ticker} - {price_str} ({change_str})",
                value=f"🔔 {alert_text}",
                inline=False
            )
        
        if len(watchlist) > 10:
            embed.set_footer(text=f"... and {len(watchlist) - 10} more stocks")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔔 Edit Alerts", style=discord.ButtonStyle.secondary, row=1)
    async def edit_alerts_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show select menu for which stock to edit
        watchlist, error = await self.watchlist_manager.get_watchlist_display(self.user_id)
        
        if error or not watchlist:
            await interaction.response.send_message("Your watchlist is empty!", ephemeral=True)
            return
        
        # Show dropdown to select which ticker to edit
        view = EditAlertsSelectView(watchlist, self.watchlist_manager, self.user_id)
        await interaction.response.send_message("Select a stock to edit alerts:", view=view, ephemeral=True)
