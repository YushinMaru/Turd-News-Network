"""
Channel Manager for Discord Dashboard
Handles finding, creating, and managing dashboard channels
"""

import discord
from discord.ext import commands
from typing import Optional, Dict, Any
from datetime import datetime
from config import DASHBOARD_CHANNEL_NAME, DASHBOARD_REFRESH_INTERVAL
from database import DatabaseManager


class ChannelManager:
    """Manages Discord dashboard channels and state"""
    
    def __init__(self, bot: commands.Bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self._channel_cache: Dict[str, discord.TextChannel] = {}
    
    async def find_or_create_dashboard_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """
        Find existing dashboard channel or create a new one
        
        Args:
            guild: Discord guild to search/create in
            
        Returns:
            TextChannel object or None if failed
        """
        # Check cache first
        if guild.id in self._channel_cache:
            return self._channel_cache[guild.id]
        
        # Search for existing channel
        channel = discord.utils.get(guild.text_channels, name=DASHBOARD_CHANNEL_NAME)
        
        if channel:
            print(f"[Dashboard] Found existing channel: #{channel.name}")
            self._channel_cache[guild.id] = channel
            return channel
        
        # Create new channel
        try:
            # Create channel at the top (position 0)
            channel = await guild.create_text_channel(
                name=DASHBOARD_CHANNEL_NAME,
                reason="Turd News Network Dashboard Channel"
            )
            
            print(f"[Dashboard] Created new channel: #{channel.name}")
            self._channel_cache[guild.id] = channel
            
            # Set up initial state in database
            self._initialize_channel_state(channel.id)
            
            return channel
            
        except Exception as e:
            print(f"[ERROR] Failed to create dashboard channel: {e}")
            return None
    
    def _initialize_channel_state(self, channel_id: str):
        """Initialize channel state in database"""
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''INSERT OR REPLACE INTO dashboard_state 
                         (channel_id, current_view, refresh_interval, auto_refresh, last_refresh)
                         VALUES (?, ?, ?, ?, ?)''',
                     (str(channel_id), 'overview', DASHBOARD_REFRESH_INTERVAL, True, datetime.now().isoformat()))
            conn.commit()
        except Exception as e:
            print(f"[ERROR] Failed to initialize channel state: {e}")
        finally:
            conn.close()
    
    def get_channel_state(self, channel_id: str) -> Dict[str, Any]:
        """
        Get current dashboard state for a channel
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            Dictionary with channel state
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''SELECT current_view, current_ticker, refresh_interval, 
                               auto_refresh, last_refresh, pinned_message_id
                         FROM dashboard_state 
                         WHERE channel_id = ?''', (str(channel_id),))
            
            row = c.fetchone()
            
            if row:
                return {
                    'current_view': row[0],
                    'current_ticker': row[1],
                    'refresh_interval': row[2],
                    'auto_refresh': bool(row[3]),
                    'last_refresh': row[4],
                    'pinned_message_id': row[5]
                }
            else:
                # Return default state
                return {
                    'current_view': 'overview',
                    'current_ticker': None,
                    'refresh_interval': DASHBOARD_REFRESH_INTERVAL,
                    'auto_refresh': True,
                    'last_refresh': None,
                    'pinned_message_id': None
                }
                
        except Exception as e:
            print(f"[ERROR] Failed to get channel state: {e}")
            return self._get_default_state()
        finally:
            conn.close()
    
    def update_channel_state(self, channel_id: str, **kwargs):
        """
        Update dashboard state for a channel
        
        Args:
            channel_id: Discord channel ID
            **kwargs: State fields to update (current_view, current_ticker, etc.)
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            # Build update query dynamically
            if kwargs:
                set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
                values = list(kwargs.values())
                
                c.execute(f'''UPDATE dashboard_state 
                             SET {set_clause}, last_refresh = ?
                             WHERE channel_id = ?''', values + [datetime.now().isoformat(), str(channel_id)])
                conn.commit()
                
        except Exception as e:
            print(f"[ERROR] Failed to update channel state: {e}")
        finally:
            conn.close()
    
    def save_pinned_message(self, channel_id: str, message_id: str):
        """Save the pinned dashboard message ID"""
        self.update_channel_state(channel_id, pinned_message_id=message_id)
    
    def get_pinned_message_id(self, channel_id: str) -> Optional[str]:
        """Get the pinned dashboard message ID"""
        state = self.get_channel_state(channel_id)
        return state.get('pinned_message_id')
    
    def _get_default_state(self) -> Dict[str, Any]:
        """Get default channel state"""
        return {
            'current_view': 'overview',
            'current_ticker': None,
            'refresh_interval': DASHBOARD_REFRESH_INTERVAL,
            'auto_refresh': True,
            'last_refresh': None,
            'pinned_message_id': None
        }
    
    def register_user(self, user: discord.User):
        """
        Register a user in the database
        
        Args:
            user: Discord user object
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            c.execute('''INSERT OR REPLACE INTO dashboard_users 
                         (user_id, username, discriminator, display_name, 
                          is_admin, created_date, last_active)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (str(user.id), user.name, user.discriminator, 
                      user.display_name, False, now, now))
            conn.commit()
            
        except Exception as e:
            print(f"[ERROR] Failed to register user: {e}")
        finally:
            conn.close()
    
    def update_user_activity(self, user_id: str):
        """Update user's last activity timestamp"""
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''UPDATE dashboard_users 
                         SET last_active = ? 
                         WHERE user_id = ?''',
                     (datetime.now().isoformat(), str(user_id)))
            conn.commit()
            
        except Exception as e:
            print(f"[ERROR] Failed to update user activity: {e}")
        finally:
            conn.close()
    
    def get_user_watchlist(self, user_id: str) -> list:
        """
        Get user's watchlist tickers
        
        Args:
            user_id: Discord user ID
            
        Returns:
            List of ticker symbols
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''SELECT ticker, added_date, notes, alert_enabled
                         FROM user_watchlists 
                         WHERE user_id = ? 
                         ORDER BY added_date DESC''', (str(user_id),))
            
            rows = c.fetchall()
            
            return [
                {
                    'ticker': row[0],
                    'added_date': row[1],
                    'notes': row[2],
                    'alert_enabled': bool(row[3])
                }
                for row in rows
            ]
            
        except Exception as e:
            print(f"[ERROR] Failed to get user watchlist: {e}")
            return []
        finally:
            conn.close()
    
    def add_to_watchlist(self, user_id: str, ticker: str, notes: str = None):
        """
        Add ticker to user's watchlist
        
        Args:
            user_id: Discord user ID
            ticker: Stock ticker symbol
            notes: Optional notes for the ticker
            
        Returns:
            True if successful, False otherwise
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            c.execute('''INSERT OR IGNORE INTO user_watchlists 
                         (user_id, ticker, added_date, notes, alert_enabled)
                         VALUES (?, ?, ?, ?, ?)''',
                     (str(user_id), ticker.upper(), now, notes, True))
            
            conn.commit()
            return c.rowcount > 0
            
        except Exception as e:
            print(f"[ERROR] Failed to add to watchlist: {e}")
            return False
        finally:
            conn.close()
    
    def remove_from_watchlist(self, user_id: str, ticker: str) -> bool:
        """
        Remove ticker from user's watchlist
        
        Args:
            user_id: Discord user ID
            ticker: Stock ticker symbol
            
        Returns:
            True if removed, False otherwise
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            c.execute('''DELETE FROM user_watchlists 
                         WHERE user_id = ? AND ticker = ?''',
                     (str(user_id), ticker.upper()))
            
            conn.commit()
            return c.rowcount > 0
            
        except Exception as e:
            print(f"[ERROR] Failed to remove from watchlist: {e}")
            return False
        finally:
            conn.close()
    
    def save_report(self, report_type: str, ticker: str, user_id: str, 
                   channel_id: str, file_path: str, pages: int, file_size: int) -> bool:
        """
        Save generated report information to database
        
        Args:
            report_type: Type of report (e.g., 'comprehensive', 'quick')
            ticker: Stock ticker
            user_id: User who requested the report
            channel_id: Channel where report was sent
            file_path: Path to generated PDF file
            pages: Number of pages in report
            file_size: Size of report file in bytes
            
        Returns:
            True if successful
        """
        conn = self.db.get_connection()
        c = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            c.execute('''INSERT INTO generated_reports 
                         (report_type, ticker, user_id, channel_id, file_path, 
                          generated_date, pages, file_size)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (report_type, ticker, str(user_id), str(channel_id), 
                      file_path, now, pages, file_size))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save report: {e}")
            return False
        finally:
            conn.close()
    
    def cleanup_cache(self):
        """Clear the channel cache"""
        self._channel_cache.clear()