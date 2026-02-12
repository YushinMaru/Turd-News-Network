"""
Auto Refresh Manager for Discord Dashboard
Handles automatic dashboard updates at configurable intervals
"""

import asyncio
import discord
from discord.ext import tasks
from typing import Optional, Dict
from datetime import datetime, timedelta

from database import DatabaseManager
from channel_manager import ChannelManager


class AutoRefreshManager:
    """Manages automatic dashboard refreshing"""
    
    def __init__(self, bot, channel_manager: ChannelManager, db: DatabaseManager):
        self.bot = bot
        self.channel_manager = channel_manager
        self.db = db
        self._refresh_task: Optional[tasks.Loop] = None
        self._running = False
        self._refresh_interval = 60  # seconds (safer for Discord rate limits)
        self._last_interaction: datetime = datetime.now()
        self._interaction_lock = False
        self._last_error_time: datetime = None
        self._error_count = 0
        self._rate_limited = False
        self._rate_limit_retry_after = 0
    
    def record_interaction(self):
        """Record that a user is interacting with the dashboard"""
        self._last_interaction = datetime.now()
        self._interaction_lock = False  # Release lock when interaction recorded
    
    def acquire_lock(self):
        """Acquire interaction lock - call before processing interactions"""
        self._interaction_lock = True
        self._last_interaction = datetime.now()
    
    def release_lock(self):
        """Release interaction lock - call after processing interactions"""
        self._interaction_lock = False
    
    def _should_refresh(self) -> bool:
        """Check if refresh should happen based on user activity and rate limits"""
        # Don't refresh if lock is acquired (user interacting)
        if self._interaction_lock:
            return False
        # Don't refresh if user interacted recently (within 3 seconds)
        if datetime.now() - self._last_interaction < timedelta(seconds=3):
            return False
        # If we've been rate limited recently, skip this cycle
        if self._rate_limited:
            time_since_error = datetime.now() - self._last_error_time
            if time_since_error < timedelta(seconds=self._rate_limit_retry_after + 10):
                return False
            # Reset rate limit after waiting
            self._rate_limited = False
        return True
    
    def _on_rate_limit(self, retry_after: int):
        """Called when we hit a rate limit"""
        self._rate_limited = True
        self._last_error_time = datetime.now()
        self._rate_limit_retry_after = retry_after
        print(f"[AutoRefresh] Rate limited! Pausing for {retry_after} seconds")
    
    def start(self):
        """Start the auto-refresh loop"""
        if self._running:
            return
        
        print("[AutoRefresh] Starting auto-refresh manager")
        self._running = True
        self._refresh_loop.start()
    
    def stop(self):
        """Stop the auto-refresh loop"""
        if not self._running:
            return
        
        print("[AutoRefresh] Stopping auto-refresh manager")
        self._running = False
        
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None
    
    @tasks.loop(seconds=60)
    async def _refresh_loop(self):
        """Main auto-refresh loop"""
        try:
            await self.refresh_all_dashboards()
        except Exception as e:
            print(f"[AutoRefresh] Error in refresh loop: {e}")
    
    async def refresh_all_dashboards(self):
        """Refresh all active dashboard channels"""
        # Skip refresh if user is interacting
        if not self._should_refresh():
            return
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            # Get all active dashboard channels
            c.execute('''SELECT channel_id, current_view, current_ticker, refresh_interval, auto_refresh
                         FROM dashboard_state WHERE auto_refresh = 1''')
            
            channels = c.fetchall()
            
            if not channels:
                return
            
            print(f"[AutoRefresh] Refreshing {len(channels)} dashboards")
            
            for channel_id, current_view, current_ticker, refresh_interval, auto_refresh in channels:
                if not auto_refresh:
                    continue
                
                try:
                    # Get channel from bot
                    channel = self.bot.get_channel(int(channel_id))
                    
                    if not channel:
                        continue
                    
                    # Find pinned message
                    state = self.channel_manager.get_channel_state(channel_id)
                    pinned_msg_id = state.get('pinned_message_id')
                    
                    if not pinned_msg_id:
                        continue
                    
                    # Fetch and update message
                    try:
                        message = await channel.fetch_message(int(pinned_msg_id))
                        
                        # Generate fresh embed based on view
                        if current_view == 'overview':
                            embed = await self._generate_overview_embed()
                        elif current_view == 'ticker' and current_ticker:
                            embed = await self._generate_ticker_embed(current_ticker)
                        elif current_view == 'settings':
                            embed = await self._generate_settings_embed()
                        else:
                            embed = await self._generate_overview_embed()
                        
                        await message.edit(embed=embed)
                        
                    except discord.NotFound:
                        # Message deleted, need to recreate
                        print(f"[AutoRefresh] Message not found for channel {channel_id}")
                    except discord.Forbidden:
                        print(f"[AutoRefresh] No permission in channel {channel_id}")
                    
                except Exception as e:
                    print(f"[AutoRefresh] Error refreshing channel {channel_id}: {e}")
            
        except Exception as e:
            print(f"[AutoRefresh] Error: {e}")
        finally:
            conn.close()
    
    async def refresh_single_dashboard(self, channel_id: str):
        """Refresh a single dashboard channel
        
        Args:
            channel_id: Discord channel ID
        """
        try:
            channel = self.bot.get_channel(int(channel_id))
            
            if not channel:
                return False
            
            state = self.channel_manager.get_channel_state(channel_id)
            pinned_msg_id = state.get('pinned_message_id')
            
            if not pinned_msg_id:
                return False
            
            try:
                message = await channel.fetch_message(int(pinned_msg_id))
                
                current_view = state.get('current_view', 'overview')
                current_ticker = state.get('current_ticker')
                
                if current_view == 'overview':
                    embed = await self._generate_overview_embed()
                elif current_view == 'ticker' and current_ticker:
                    embed = await self._generate_ticker_embed(current_ticker)
                elif current_view == 'settings':
                    embed = await self._generate_settings_embed()
                else:
                    embed = await self._generate_overview_embed()
                
                await message.edit(embed=embed)
                return True
                
            except (discord.NotFound, discord.Forbidden):
                return False
                
        except Exception as e:
            print(f"[AutoRefresh] Error refreshing dashboard: {e}")
            return False
    
    async def _generate_overview_embed(self) -> discord.Embed:
        """Generate overview embed data"""
        embed = discord.Embed(
            title="Market Overview",
            description="Real-time market analysis",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            # Get active tracking count
            c.execute('SELECT COUNT(*) FROM stock_tracking WHERE status = "tracking"')
            active_count = c.fetchone()[0]
            
            # Get recent alerts
            c.execute('''SELECT ticker, alert_type, confidence 
                         FROM alert_log ORDER BY alert_date DESC LIMIT 5''')
            recent_alerts = c.fetchall()
            
            # Get top gainers
            c.execute('''SELECT ticker, price_change_pct, current_price
                         FROM stock_tracking WHERE status = "tracking"
                         ORDER BY price_change_pct DESC LIMIT 5''')
            top_gainers = c.fetchall()
            
            # Get top losers
            c.execute('''SELECT ticker, price_change_pct, current_price
                         FROM stock_tracking WHERE status = "tracking"
                         ORDER BY price_change_pct ASC LIMIT 5''')
            top_losers = c.fetchall()
            
            if recent_alerts:
                alerts_text = '\n'.join([f"**{row[0]}**: {row[1]} ({row[2]:.0%})" for row in recent_alerts])
                embed.add_field(name="Recent Alerts", value=alerts_text, inline=False)
            
            if top_gainers:
                gainers_text = '\n'.join([f"**{row[0]}**: +{row[1]:.2f}% @ ${row[2]:.2f}" for row in top_gainers])
                embed.add_field(name="Top Gainers", value=gainers_text, inline=True)
            
            if top_losers:
                losers_text = '\n'.join([f"**{row[0]}**: {row[1]:.2f}% @ ${row[2]:.2f}" for row in top_losers])
                embed.add_field(name="Top Losers", value=losers_text, inline=True)
            
            embed.add_field(name="Active Tracking", value=f"{active_count} stocks", inline=False)
            embed.set_footer(text="Auto-refreshed")
            
        except Exception as e:
            print(f"[AutoRefresh] Error generating overview: {e}")
            embed.description = "Error loading market data"
        finally:
            conn.close()
        
        return embed
    
    async def _generate_ticker_embed(self, ticker: str) -> discord.Embed:
        """Generate ticker embed data"""
        embed = discord.Embed(
            title=f"{ticker.upper()} Analysis",
            description="Detailed stock analysis",
            color=0x00aaff,
            timestamp=datetime.now()
        )
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''SELECT current_price, price_change_pct, max_price, min_price,
                               days_tracked, initial_price, status
                         FROM stock_tracking WHERE ticker = ? AND status = "tracking"
                         ORDER BY initial_date DESC LIMIT 1''', (ticker.upper(),))
            
            tracking = c.fetchone()
            
            if tracking:
                current, change, high, low, days, initial, status = tracking
                
                emoji = "+" if change > 0 else ""
                embed.add_field(name="Price", value=f"${current:.2f} ({emoji}{change:.2f}%)", inline=True)
                embed.add_field(name="Range", value=f"High: ${high:.2f}\nLow: ${low:.2f}", inline=True)
                embed.add_field(name="Tracking", value=f"{days} days\nInitial: ${initial:.2f}", inline=True)
            else:
                embed.description = "No active tracking data"
            
            embed.set_footer(text="Auto-refreshed")
            
        except Exception as e:
            print(f"[AutoRefresh] Error generating ticker embed: {e}")
            embed.description = "Error loading ticker data"
        finally:
            conn.close()
        
        return embed
    
    async def _generate_settings_embed(self) -> discord.Embed:
        """Generate settings embed data"""
        embed = discord.Embed(
            title="Dashboard Settings",
            description="Configure dashboard options",
            color=0xffaa00,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Auto-Refresh", value="Enabled", inline=False)
        embed.add_field(name="Interval", value="30 seconds", inline=True)
        embed.add_field(name="Status", value="Active", inline=True)
        
        return embed
    
    def update_refresh_interval(self, channel_id: str, interval: int):
        """Update refresh interval for a channel
        
        Args:
            channel_id: Discord channel ID
            interval: New interval in seconds
        """
        self.channel_manager.update_channel_state(channel_id, refresh_interval=interval)
        print(f"[AutoRefresh] Updated interval for channel {channel_id} to {interval}s")
    
    def set_channel_auto_refresh(self, channel_id: str, enabled: bool):
        """Enable or disable auto-refresh for a channel
        
        Args:
            channel_id: Discord channel ID
            enabled: True to enable, False to disable
        """
        self.channel_manager.update_channel_state(channel_id, auto_refresh=enabled)
        status = "enabled" if enabled else "disabled"
        print(f"[AutoRefresh] Auto-refresh {status} for channel {channel_id}")
    
    @property
    def is_running(self) -> bool:
        """Check if auto-refresh is running"""
        return self._running
    
    @property
    def refresh_interval(self) -> int:
        """Get current refresh interval"""
        return self._refresh_interval
    
    @refresh_interval.setter
    def refresh_interval(self, value: int):
        """Set refresh interval"""
        self._refresh_interval = max(10, min(300, value))
        if self._refresh_task:
            self._refresh_task.change_interval(seconds=self._refresh_interval)
