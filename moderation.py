"""
Moderation Cog for Turd News Network
Comprehensive Discord moderation with extensive logging
"""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
import sqlite3

# Configuration
MOD_LOG_CHANNEL_NAME = "mod-logs"
MOD_ROLE_NAME = "Moderator"  # Adjust as needed


def get_db_connection():
    """Get database connection"""
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'turd_news.db')
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_moderation_db():
    """Initialize moderation tables"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Warnings table
    c.execute('''CREATE TABLE IF NOT EXISTS moderation_warnings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  guild_id TEXT,
                  moderator_id TEXT,
                  reason TEXT,
                  warning_date TEXT,
                  acknowledged BOOLEAN DEFAULT 0)''')
    
    conn.commit()
    conn.close()


class ModerationCog(commands.Cog):
    """Moderation commands for Turd News Network"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db if hasattr(bot, 'db') else None
        init_moderation_db()
        print("[MOD] Moderation Cog loaded successfully")
    
    async def log_to_console(self, message: str):
        """Log with [MOD] prefix to console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[MOD] [{timestamp}] {message}")
    
    async def log_to_channel(self, guild: discord.Guild, embed: discord.Embed):
        """Log to #mod-logs channel"""
        channel = discord.utils.get(guild.text_channels, name=MOD_LOG_CHANNEL_NAME)
        
        if not channel:
            # Try to create the channel
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await guild.create_text_channel(MOD_LOG_CHANNEL_NAME, overwrites=overwrites)
                await self.log_to_console(f"CHANNEL: #{MOD_LOG_CHANNEL_NAME} created in {guild.name}")
            except Exception as e:
                await self.log_to_console(f"ERROR: Could not create mod-logs channel: {e}")
                return
        
        try:
            await channel.send(embed=embed)
        except Exception as e:
            await self.log_to_console(f"ERROR: Could not send to mod-logs: {e}")
    
    async def create_log_embed(self, guild: discord.Guild, action: str, details: str, 
                              moderator: discord.Member, target_user: discord.Member = None,
                              color: int = 0xFF6600) -> discord.Embed:
        """Create a standard log embed"""
        embed = discord.Embed(
            title=f"⚖️ {action}",
            description=details,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Server: {guild.name} | Mod: {moderator.display_name}")
        
        if target_user:
            embed.add_field(name="👤 Target User", value=f"{target_user.mention}\n{target_user.name}#{target_user.discriminator}\n(ID: {target_user.id})", inline=True)
        
        embed.add_field(name="🛡️ Moderator", value=f"{moderator.mention}\n{moderator.name}#{moderator.discriminator}", inline=True)
        
        return embed
    
    # =========================================================================
    # PERMISSION CHECK
    # =========================================================================
    
    async def check_moderator(self, interaction: discord.Interaction) -> bool:
        """Check if user has moderator permissions"""
        # Check if user is admin
        if interaction.user.guild_permissions.administrator:
            return True
        
        # Check for moderator role
        guild = interaction.guild
        mod_role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
        if mod_role and mod_role in interaction.user.roles:
            return True
        
        return False
    
    # =========================================================================
    # USER MANAGEMENT COMMANDS
    # =========================================================================
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(user="User to ban")
    @app_commands.describe(reason="Reason for the ban")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Ban a user from the server"""
        await self.log_to_console(f"ACTION: BAN | User: {user.name}#{user.discriminator} ({user.id}) | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            await user.ban(reason=reason)
            
            embed = await self.create_log_embed(
                interaction.guild,
                "USER BANNED",
                f"**Reason:** {reason}",
                interaction.user,
                user,
                0xFF0000
            )
            
            await interaction.response.send_message(f"✅ Successfully banned {user.mention}", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - User {user.name}#{user.discriminator} banned")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to ban user: {e}")
            await interaction.response.send_message(f"❌ Failed to ban user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user="Username to unban (e.g., username#1234)")
    @app_commands.describe(reason="Reason for the unban")
    async def unban(self, interaction: discord.Interaction, user: str, reason: str = "No reason provided"):
        """Unban a user from the server"""
        await self.log_to_console(f"ACTION: UNBAN | User: {user} | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            # Parse username#discriminator
            if '#' in user:
                username, discriminator = user.split('#')
                banned_users = await interaction.guild.bans()
                found_user = None
                for ban_entry in banned_users:
                    if ban_entry.user.name == username and ban_entry.user.discriminator == discriminator:
                        found_user = ban_entry.user
                        break
                
                if found_user:
                    await interaction.guild.unban(found_user, reason=reason)
                    
                    embed = await self.create_log_embed(
                        interaction.guild,
                        "USER UNBANNED",
                        f"**Reason:** {reason}",
                        interaction.user,
                        found_user,
                        0x00FF00
                    )
                    
                    await interaction.response.send_message(f"✅ Successfully unbanned {username}#{discriminator}", ephemeral=True)
                    await self.log_to_channel(interaction.guild, embed)
                    await self.log_to_console(f"RESULT: SUCCESS - User {username}#{discriminator} unbanned")
                else:
                    await interaction.response.send_message(f"❌ User {user} not found in ban list", ephemeral=True)
                    await self.log_to_console(f"RESULT: FAIL - User {user} not in ban list")
            else:
                await interaction.response.send_message(f"❌ Please use format: username#1234", ephemeral=True)
                
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to unban user: {e}")
            await interaction.response.send_message(f"❌ Failed to unban user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(user="User to kick")
    @app_commands.describe(reason="Reason for the kick")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Kick a user from the server"""
        await self.log_to_console(f"ACTION: KICK | User: {user.name}#{user.discriminator} ({user.id}) | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            await user.kick(reason=reason)
            
            embed = await self.create_log_embed(
                interaction.guild,
                "USER KICKED",
                f"**Reason:** {reason}",
                interaction.user,
                user,
                0xFFA500
            )
            
            await interaction.response.send_message(f"✅ Successfully kicked {user.mention}", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - User {user.name}#{user.discriminator} kicked")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to kick user: {e}")
            await interaction.response.send_message(f"❌ Failed to kick user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="timeout", description="Timeout a user")
    @app_commands.describe(user="User to timeout")
    @app_commands.describe(duration="Duration (e.g., 1m, 1h, 1d, 1w)")
    @app_commands.describe(reason="Reason for the timeout")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
        """Timeout a user"""
        await self.log_to_console(f"ACTION: TIMEOUT | User: {user.name}#{user.discriminator} ({user.id}) | Duration: {duration} | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        # Parse duration
        duration = duration.lower().strip()
        multipliers = {'m': 60, 'h': 3600, 'd': 86400, 'w': 604800}
        
        try:
            if duration[-1] in multipliers:
                amount = int(duration[:-1])
                seconds = amount * multipliers[duration[-1]]
                timeout_duration = timedelta(seconds=seconds)
            else:
                await interaction.response.send_message("❌ Invalid duration format. Use: 1m, 1h, 1d, or 1w", ephemeral=True)
                return
            
            # Discord has max timeout of 28 days
            if seconds > 2419200:
                seconds = 2419200
                timeout_duration = timedelta(seconds=seconds)
            
            await user.timeout(timeout_duration, reason=reason)
            
            embed = await self.create_log_embed(
                interaction.guild,
                "USER TIMED OUT",
                f"**Duration:** {duration}\n**Reason:** {reason}",
                interaction.user,
                user,
                0xFFFF00
            )
            
            await interaction.response.send_message(f"✅ Successfully timed out {user.mention} for {duration}", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - User {user.name}#{user.discriminator} timed out for {duration}")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to timeout user: {e}")
            await interaction.response.send_message(f"❌ Failed to timeout user: {str(e)}", ephemeral=True)
    
    # =========================================================================
    # MESSAGE MANAGEMENT COMMANDS
    # =========================================================================
    
    @app_commands.command(name="purge", description="Delete multiple messages")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    @app_commands.describe(reason="Reason for purging")
    async def purge(self, interaction: discord.Interaction, amount: int, reason: str = "No reason provided"):
        """Delete multiple messages in the channel"""
        amount = min(max(1, amount), 100)  # Clamp between 1 and 100
        
        await self.log_to_console(f"ACTION: PURGE | Channel: #{interaction.channel.name} | Amount: {amount} | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            # Delete messages
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title="🧹 MESSAGES PURGED",
                description=f"**Amount:** {len(deleted)} messages\n**Reason:** {reason}",
                color=0xFF6600,
                timestamp=datetime.now()
            )
            embed.add_field(name="🛡️ Moderator", value=f"{interaction.user.mention}\n{interaction.user.name}#{interaction.user.discriminator}", inline=True)
            embed.add_field(name="📍 Channel", value=f"#{interaction.channel.name}", inline=True)
            embed.set_footer(text=f"Server: {interaction.guild.name}")
            
            await interaction.response.send_message(f"✅ Deleted {len(deleted)} messages", ephemeral=True, delete_after=3)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - {len(deleted)} messages purged from #{interaction.channel.name}")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to purge messages: {e}")
            await interaction.response.send_message(f"❌ Failed to purge messages: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="delete", description="Delete a specific message")
    @app_commands.describe(message_id="ID of the message to delete")
    @app_commands.describe(reason="Reason for deletion")
    async def delete_message(self, interaction: discord.Interaction, message_id: str, reason: str = "No reason provided"):
        """Delete a specific message by ID"""
        await self.log_to_console(f"ACTION: DELETE MESSAGE | Message ID: {message_id} | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            message_id = int(message_id)
            message = await interaction.channel.fetch_message(message_id)
            
            await message.delete()
            
            embed = discord.Embed(
                title="🗑️ MESSAGE DELETED",
                description=f"**Message ID:** {message_id}\n**Reason:** {reason}\n**Content:** {message.content[:200]}...",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            embed.add_field(name="🛡️ Moderator", value=f"{interaction.user.mention}", inline=True)
            embed.set_footer(text=f"Server: {interaction.guild.name}")
            
            await interaction.response.send_message(f"✅ Message deleted", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - Message {message_id} deleted")
            
        except discord.NotFound:
            await interaction.response.send_message(f"❌ Message not found", ephemeral=True)
            await self.log_to_console(f"RESULT: FAIL - Message {message_id} not found")
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to delete message: {e}")
            await interaction.response.send_message(f"❌ Failed to delete message: {str(e)}", ephemeral=True)
    
    # =========================================================================
    # CHANNEL MANAGEMENT COMMANDS
    # =========================================================================
    
    @app_commands.command(name="channel", description="Manage channels")
    @app_commands.describe(action="Action: create, delete, or clear")
    @app_commands.describe(name="Channel name (for create/delete)")
    @app_commands.describe(reason="Reason for the action")
    async def channel(self, interaction: discord.Interaction, action: str, name: str = None, reason: str = "No reason provided"):
        """Channel management commands"""
        action = action.lower()
        
        if action == "create":
            await self._create_channel(interaction, name, reason)
        elif action == "delete":
            await self._delete_channel(interaction, name, reason)
        elif action == "clear":
            await self._clear_channel(interaction, reason)
        else:
            await interaction.response.send_message("❌ Invalid action. Use: create, delete, or clear", ephemeral=True)
    
    async def _create_channel(self, interaction: discord.Interaction, name: str, reason: str):
        """Create a new channel"""
        if not name:
            await interaction.response.send_message("❌ Please provide a channel name", ephemeral=True)
            return
        
        await self.log_to_console(f"ACTION: CREATE CHANNEL | Name: {name} | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            channel = await interaction.guild.create_text_channel(name)
            
            embed = discord.Embed(
                title="📝 CHANNEL CREATED",
                description=f"**Channel:** #{channel.mention}\n**Reason:** {reason}",
                color=0x00FF00,
                timestamp=datetime.now()
            )
            embed.add_field(name="🛡️ Moderator", value=f"{interaction.user.mention}", inline=True)
            embed.set_footer(text=f"Server: {interaction.guild.name}")
            
            await interaction.response.send_message(f"✅ Channel #{name} created", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - Channel #{name} created")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to create channel: {e}")
            await interaction.response.send_message(f"❌ Failed to create channel: {str(e)}", ephemeral=True)
    
    async def _delete_channel(self, interaction: discord.Interaction, name: str, reason: str):
        """Delete a channel"""
        if not name:
            await interaction.response.send_message("❌ Please provide a channel name", ephemeral=True)
            return
        
        await self.log_to_console(f"ACTION: DELETE CHANNEL | Name: {name} | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            channel = discord.utils.get(interaction.guild.text_channels, name=name)
            
            if channel:
                await channel.delete()
                
                embed = discord.Embed(
                    title="🗑️ CHANNEL DELETED",
                    description=f"**Channel:** #{name}\n**Reason:** {reason}",
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
                embed.add_field(name="🛡️ Moderator", value=f"{interaction.user.mention}", inline=True)
                embed.set_footer(text=f"Server: {interaction.guild.name}")
                
                await interaction.response.send_message(f"✅ Channel #{name} deleted", ephemeral=True)
                await self.log_to_channel(interaction.guild, embed)
                await self.log_to_console(f"RESULT: SUCCESS - Channel #{name} deleted")
            else:
                await interaction.response.send_message(f"❌ Channel #{name} not found", ephemeral=True)
                await self.log_to_console(f"RESULT: FAIL - Channel #{name} not found")
                
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to delete channel: {e}")
            await interaction.response.send_message(f"❌ Failed to delete channel: {str(e)}", ephemeral=True)
    
    async def _clear_channel(self, interaction: discord.Interaction, reason: str):
        """Clear all messages in a channel"""
        await self.log_to_console(f"ACTION: CLEAR CHANNEL | Channel: #{interaction.channel.name} | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            # Get message count (limit to 100)
            messages = await interaction.channel.purge(limit=100, check=lambda m: True)
            
            embed = discord.Embed(
                title="🧹 CHANNEL CLEARED",
                description=f"**Channel:** #{interaction.channel.name}\n**Messages deleted:** {len(messages)}\n**Reason:** {reason}",
                color=0xFF6600,
                timestamp=datetime.now()
            )
            embed.add_field(name="🛡️ Moderator", value=f"{interaction.user.mention}", inline=True)
            embed.set_footer(text=f"Server: {interaction.guild.name}")
            
            await interaction.response.send_message(f"✅ Cleared {len(messages)} messages from this channel", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - {len(messages)} messages cleared from #{interaction.channel.name}")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to clear channel: {e}")
            await interaction.response.send_message(f"❌ Failed to clear channel: {str(e)}", ephemeral=True)
    
    # =========================================================================
    # WARN SYSTEM COMMANDS
    # =========================================================================
    
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(user="User to warn")
    @app_commands.describe(reason="Reason for the warning")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Warn a user and store in database"""
        await self.log_to_console(f"ACTION: WARN | User: {user.name}#{user.discriminator} ({user.id}) | Mod: {interaction.user.name}#{interaction.user.discriminator} | Reason: {reason}")
        
        try:
            # Store warning in database
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''INSERT INTO moderation_warnings 
                         (user_id, guild_id, moderator_id, reason, warning_date, acknowledged)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (str(user.id), str(interaction.guild.id), str(interaction.user.id), 
                       reason, datetime.now().isoformat(), False))
            
            conn.commit()
            
            # Get total warnings for this user
            c.execute('SELECT COUNT(*) FROM moderation_warnings WHERE user_id = ? AND guild_id = ?',
                      (str(user.id), str(interaction.guild.id)))
            warning_count = c.fetchone()[0]
            
            conn.close()
            
            embed = await self.create_log_embed(
                interaction.guild,
                "USER WARNED",
                f"**Reason:** {reason}\n**Total Warnings:** {warning_count}",
                interaction.user,
                user,
                0xFFA500
            )
            
            await interaction.response.send_message(f"✅ {user.mention} has been warned. Total warnings: {warning_count}", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - User {user.name}#{user.discriminator} warned. Total: {warning_count}")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to warn user: {e}")
            await interaction.response.send_message(f"❌ Failed to warn user: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(user="User to check warnings for")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        """View all warnings for a user"""
        await self.log_to_console(f"ACTION: VIEW WARNINGS | User: {user.name}#{user.discriminator} ({user.id}) | Requested by: {interaction.user.name}")
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''SELECT id, reason, warning_date, moderator_id, acknowledged 
                         FROM moderation_warnings 
                         WHERE user_id = ? AND guild_id = ?
                         ORDER BY warning_date DESC
                         LIMIT 10''',
                      (str(user.id), str(interaction.guild.id)))
            
            warnings = c.fetchall()
            conn.close()
            
            if not warnings:
                await interaction.response.send_message(f"No warnings found for {user.mention}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"⚠️ Warnings for {user.name}#{user.discriminator}",
                description=f"Total warnings: {len(warnings)}",
                color=0xFFA500,
                timestamp=datetime.now()
            )
            
            for w in warnings:
                warning_id, reason, date, mod_id, acknowledged = w
                mod_user = interaction.guild.get_member(int(mod_id))
                mod_name = mod_user.name if mod_user else "Unknown"
                ack_status = "✅ Acknowledged" if acknowledged else "❌ Pending"
                
                embed.add_field(
                    name=f"Warning #{warning_id} - {ack_status}",
                    value=f"**Reason:** {reason}\n**Date:** {date[:10]}\n**By:** {mod_name}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.log_to_console(f"RESULT: SUCCESS - Retrieved {len(warnings)} warnings for {user.name}")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to get warnings: {e}")
            await interaction.response.send_message(f"❌ Failed to get warnings: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    @app_commands.describe(user="User to clear warnings for")
    @app_commands.describe(reason="Reason for clearing warnings")
    async def clearwarnings(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Clear all warnings for a user"""
        await self.log_to_console(f"ACTION: CLEAR WARNINGS | User: {user.name}#{user.discriminator} ({user.id}) | Mod: {interaction.user.name} | Reason: {reason}")
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('DELETE FROM moderation_warnings WHERE user_id = ? AND guild_id = ?',
                      (str(user.id), str(interaction.guild.id)))
            
            deleted_count = c.rowcount
            conn.commit()
            conn.close()
            
            embed = await self.create_log_embed(
                interaction.guild,
                "WARNINGS CLEARED",
                f"**Warnings Deleted:** {deleted_count}\n**Reason:** {reason}",
                interaction.user,
                user,
                0x00FF00
            )
            
            await interaction.response.send_message(f"✅ Cleared {deleted_count} warnings for {user.mention}", ephemeral=True)
            await self.log_to_channel(interaction.guild, embed)
            await self.log_to_console(f"RESULT: SUCCESS - {deleted_count} warnings cleared for {user.name}")
            
        except Exception as e:
            await self.log_to_console(f"ERROR: Failed to clear warnings: {e}")
            await interaction.response.send_message(f"❌ Failed to clear warnings: {str(e)}", ephemeral=True)


async def setup(bot):
    """Setup function for the cog"""
    await bot.add_cog(ModerationCog(bot))
    print("[MOD] Moderation cog setup complete")
