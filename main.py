"""
Turd News Network - Enhanced Dashboard v6.0
Complete dashboard redesign with all new features + Slash Commands
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
        print(f"[DASHBOARD] SearchModal submitted for ticker: {ticker} by user: {interaction.user.id}")
        
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
            
            embed.set_footer(text="Turd News Network v6.0 - Short Squeeze Watch")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)


class InsiderModal(discord.ui.Modal, title="👀 Insider Feed"):
    """Show recent insider trading activity"""
    
    async def on_submit(self, interaction: discord.Interaction):
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
    
    @discord.ui.button(label="🔍 Quick Search", style=discord.ButtonStyle.primary, row=0)
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Quick Search button clicked by user {interaction.user.id}")
            await interaction.response.send_modal(SearchModal())
        except Exception as e:
            print(f"[DASHBOARD ERROR] Quick Search button: {e}")
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {str(e)[:100]}", ephemeral=True)
    
    @discord.ui.button(label="📊 Full Report", style=discord.ButtonStyle.primary, row=0)
    async def reports_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Full Report button clicked by user {interaction.user.id}")
            await interaction.response.send_modal(ReportsModal())
        except Exception as e:
            print(f"[DASHBOARD ERROR] Full Report button: {e}")
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {str(e)[:100]}", ephemeral=True)
    
    @discord.ui.button(label="⭐ Watchlist", style=discord.ButtonStyle.success, row=0)
    async def watchlist_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Watchlist button clicked by user {interaction.user.id}")
            user_id = str(interaction.user.id)
            
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
                print(f"[DASHBOARD ERROR] Watchlist fetch: {e}")
                desc = f"Watchlist: {str(e)[:100]}"
            
            embed = discord.Embed(
                title="⭐ Your Watchlist",
                description=desc,
                color=0x3498db,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[DASHBOARD ERROR] Watchlist button: {e}")
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {str(e)[:100]}", ephemeral=True)
    
    @discord.ui.button(label="📈 Market Overview", style=discord.ButtonStyle.primary, row=1)
    async def market_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Market Overview button clicked by user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True, thinking=True)
            
            indices = ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT']
            loop = asyncio.get_running_loop()
            market_data = {}
            
            def fetch_market():
                import yfinance as yf
                for ticker in indices:
                    try:
                        stock = yf.Ticker(ticker)
                        info = stock.info
                        if info and 'currentPrice' in info:
                            price = info.get('currentPrice', 0)
                            change_pct = info.get('regularMarketChangePercent', 0)
                            market_data[ticker] = {'price': price, 'change_pct': change_pct}
                    except Exception as e:
                        print(f"[X] Error getting data for {ticker}: {e}")
                    time.sleep(0.3)
            
            await loop.run_in_executor(None, fetch_market)
            
            embed = discord.Embed(title="📈 Market Overview", description="Major indices and ETFs", color=0x3498db, timestamp=datetime.now())
            for ticker, data in market_data.items():
                price = data.get('price', 0)
                change = data.get('change_pct', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                embed.add_field(name=f"{ticker}", value=f"${price:.2f} {emoji} {change:+.2f}%", inline=True)
            
            if not market_data:
                embed.description = "Could not fetch market data. Try again later."
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[DASHBOARD ERROR] Market Overview: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="🔥 Top Movers", style=discord.ButtonStyle.primary, row=1)
    async def movers_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Top Movers button clicked by user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True, thinking=True)
            
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
            embed.set_footer(text="Turd News Network v6.0")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)[:200]}", ephemeral=True)
    
    @discord.ui.button(label="🎯 Short Squeeze", style=discord.ButtonStyle.danger, row=1)
    async def squeeze_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Short Squeeze button clicked by user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True, thinking=True)
            
            from database import DatabaseManager
            db = DatabaseManager()
            conn = db.get_connection()
            c = conn.cursor()
            
            # Check if short_interest column exists
            c.execute("PRAGMA table_info(stock_tracking)")
            columns = [row[1] for row in c.fetchall()]
            
            if 'short_interest' not in columns:
                conn.close()
                await interaction.followup.send("🎯 **Short Squeeze Watch**\n\nShort interest data is not available. This feature requires short interest data to be collected first.", ephemeral=True)
                return
            
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
                await interaction.followup.send("🎯 **Short Squeeze Watch**\n\nNo high short interest stocks found in database yet.", ephemeral=True)
                return
            
            embed = discord.Embed(title="🎯 Short Squeeze Watch", description="Stocks with high short interest (>10%)", color=0xFF6600, timestamp=datetime.now())
            for ticker, change, short_pct in results:
                short_emoji = "🔥" if short_pct > 0.20 else "⚠️" if short_pct > 0.15 else "👀"
                change_emoji = "🟢" if change >= 0 else "🔴"
                embed.add_field(name=f"{short_emoji} ${ticker}", value=f"Short: **{short_pct*100:.1f}%** | {change_emoji} {change:+.1f}%", inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[DASHBOARD ERROR] Short Squeeze: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="👀 Insider Feed", style=discord.ButtonStyle.secondary, row=2)
    async def insider_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Insider Feed button clicked by user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True, thinking=True)
            
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
                            insider_trades.append({'ticker': ticker, 'data': data})
                    except: continue
                    time.sleep(0.3)
            
            await loop.run_in_executor(None, fetch_insider)
            
            embed = discord.Embed(title="👀 Insider Activity Feed", description="Recent insider buying activity", color=0x9B59B6, timestamp=datetime.now())
            if not insider_trades:
                embed.description = "No recent insider activity found."
            else:
                for item in insider_trades[:10]:
                    ticker = item['ticker']
                    data = item['data']
                    buys = data.get('buys', 0)
                    sells = data.get('sells', 0)
                    embed.add_field(name=f"${ticker}", value=f"🟢 **{buys}** Buys | 🔴 **{sells}** Sells", inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[DASHBOARD ERROR] Insider Feed: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="🏛️ Congress", style=discord.ButtonStyle.secondary, row=2)
    async def congress_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Congress button clicked by user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True, thinking=True)
            
            from database import DatabaseManager
            db = DatabaseManager()
            conn = db.get_connection()
            c = conn.cursor()
            
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='congress_trades'")
            if c.fetchone():
                c.execute('SELECT ticker, politician_name, party, transaction_type, amount_range FROM congress_trades ORDER BY transaction_date DESC LIMIT 15')
                results = c.fetchall()
                conn.close()
                
                embed = discord.Embed(title="🏛️ Congressional Trading", description="Recent trades by US Congress members", color=0x1ABC9C, timestamp=datetime.now())
                if results:
                    for ticker, member, party, txn_type, amount in results:
                        emoji = "🟢" if "PURCHASE" in str(txn_type).upper() else "🔴"
                        embed.add_field(name=f"{emoji} ${ticker}", value=f"{member} ({party})\n{txn_type} - {amount}", inline=True)
                else:
                    embed.description = "No recent congressional trades found."
            else:
                conn.close()
                embed = discord.Embed(title="🏛️ Congressional Trading", description="Congress trading data will appear here after scans!", color=0x1ABC9C, timestamp=datetime.now())
                embed.add_field(name="📝 Note", value="Run some stock scans to collect congress trading data.", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[DASHBOARD ERROR] Congress: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="📅 Earnings", style=discord.ButtonStyle.secondary, row=2)
    async def earnings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Earnings button clicked by user {interaction.user.id}")
            await interaction.response.defer(ephemeral=True, thinking=True)
            
            from database import DatabaseManager
            from stock_data import StockDataFetcher
            user_id = str(interaction.user.id)
            db = DatabaseManager()
            fetcher = StockDataFetcher(db)
            watchlist = db.get_user_watchlist(user_id)
            
            if not watchlist:
                await interaction.followup.send("📅 **Earnings Calendar**\n\nYour watchlist is empty! Add stocks to see their earnings dates.", ephemeral=True)
                return
            
            embed = discord.Embed(title="📅 Earnings Calendar", description="Upcoming earnings for your watchlist stocks", color=0xE67E22, timestamp=datetime.now())
            
            loop = asyncio.get_running_loop()
            def fetch_earnings():
                for item in watchlist[:15]:
                    ticker = item['ticker']
                    try:
                        data = fetcher.get_stock_data(ticker)
                        if data and data.get('earnings_date'):
                            embed.add_field(name=f"${ticker}", value=f"📅 {data.get('earnings_date', 'TBA')}", inline=True)
                    except: continue
            
            await loop.run_in_executor(None, fetch_earnings)
            if len(embed.fields) == 0:
                embed.description = "No earnings dates found for your watchlist stocks."
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"[DASHBOARD ERROR] Earnings: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)[:100]}", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.success, row=3)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Refresh button clicked by user {interaction.user.id}")
            await interaction.response.send_message("🔄 Dashboard refreshed!", ephemeral=True, delete_after=3)
        except Exception as e:
            print(f"[DASHBOARD ERROR] Refresh button: {e}")
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {str(e)[:100]}", ephemeral=True)
    
    @discord.ui.button(label="⚙️ Settings", style=discord.ButtonStyle.secondary, row=3)
    async def settings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            print(f"[DASHBOARD] Settings button clicked by user {interaction.user.id}")
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
        except Exception as e:
            print(f"[DASHBOARD ERROR] Settings button: {e}")
            traceback.print_exc()
            await interaction.response.send_message(f"❌ Error: {str(e)[:100]}", ephemeral=True)


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


# ============== SLASH COMMANDS ==============

class SlashCommands:
    """Slash command handlers"""
    
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
            
            embed.set_footer(text="Turd News Network v6.0 - Market Overview")
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
            embed.set_footer(text="Turd News Network v6.0")
            
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
            
            embed.set_footer(text="Turd News Network v6.0 - Short Squeeze Watch")
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
            
            embed.set_footer(text="Turd News Network v6.0 - Insider Feed")
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
            
            embed.set_footer(text="Turd News Network v6.0 - Congress Trading")
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
        
        embed.set_footer(text="Turd News Network v6.0")
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
                embed.set_footer(text="Turd News Network v6.0")
                
                await interaction.followup.send(embed=embed, file=discord.File(html_file), ephemeral=True)
                try:
                    os.remove(html_file)
                except:
                    pass
            else:
                await interaction.followup.send(f"Could not generate report for **{ticker}**", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)[:200]}", ephemeral=True)


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
        self._seen_posts_this_scan: set = set()
        self.stock_fetcher = StockDataFetcher(self.db)
        self.analysis = AnalysisEngine()
        self.discord = DiscordEmbedBuilder(WEBHOOK_URL, self.db)
        self.performance = PerformanceTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.backtester = EnhancedBacktester()
        self.stats_reporter = StatsReporter()
        self.watchlist_manager = WatchlistManager(self.db, self.stock_fetcher, self)
        
        # Add slash commands
        self.slash_cmds = SlashCommands(self)
        
        print("[INIT] All loaded!")
    
    async def setup_hook(self):
        # Sync slash commands
        await self.watchlist_manager.start_monitoring()
        self.reddit_scanner.start()
        
        # Add slash commands to bot
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
        
        # Sync commands with Discord
        try:
            await self.tree.sync()
            print("[SLASH] Commands synced successfully!")
        except Exception as e:
            print(f"[SLASH] Error syncing commands: {e}")
    
    @tasks.loop(hours=3)
    async def reddit_scanner(self):
        try:
            # Run directly in the event loop - this works fine now that we use executor for user interactions
            await self.process_posts()
        except Exception as e:
            print(f"[SCAN ERROR] {e}")
    
    @reddit_scanner.before_loop
    async def before_scan(self):
        await self.wait_until_ready()
    
    async def on_ready(self):
        print(f"[BOT] Ready: {self.user}")
        print(f"[SLASH] Available commands: /search, /watchlist, /market, /movers, /shortsqueeze, /insider, /congress, /earnings, /alert, /alerts, /report")
        
        for guild in self.guilds:
            await self.create_dashboard_channel(guild)
            await self.create_stonks_channel(guild)
        
        await self.send_dashboard()
    
    async def send_dashboard(self):
        """Send the interactive dashboard to the stonk-bot channel"""
        try:
            print("[DASHBOARD] Sending dashboard...")
            
            for guild in self.guilds:
                print(f"[DASHBOARD] Checking guild: {guild.name}")
                dashboard_channel = None
                stonks_channel = None
                
                # Try to find or create the channel
                channel_name = DASHBOARD_CHANNEL_NAME
                for ch in guild.text_channels:
                    if ch.name == channel_name:
                        dashboard_channel = ch
                        print(f"[DASHBOARD] Found {channel_name} channel")
                    if ch.name == "stonks":
                        stonks_channel = ch
                
                # If not found, create it
                if not dashboard_channel:
                    print(f"[DASHBOARD] Creating #{channel_name} channel...")
                    try:
                        overwrites = {
                            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                        }
                        dashboard_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
                        print(f"[DASHBOARD] Created #{channel_name}")
                    except Exception as e:
                        print(f"[DASHBOARD] Error creating channel: {e}")
                        continue
                
                if not dashboard_channel:
                    print("[DASHBOARD] ERROR: stonk-bot channel not found and could not create!")
                    continue
                
                # Clear previous dashboard messages (keep only pinned)
                try:
                    async for msg in dashboard_channel.history(limit=50):
                        if msg.author == self.user and not msg.pinned:
                            try:
                                await msg.delete()
                            except:
                                pass
                    print("[DASHBOARD] Cleared old dashboard messages")
                except Exception as e:
                    print(f"[DASHBOARD] Error clearing channel: {e}")
                
                if stonks_channel:
                    await self.send_pinned_help_message(stonks_channel)
                
                # Create dashboard embed
                embed = discord.Embed(
                    title="🚀 Turd News Network v6.0",
                    description="**Stock Market Dashboard**\n\nUse /search [ticker] for quick lookup, or click buttons below!",
                    color=0x5865F2,
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="🔍 Quick Search", value="Use /search NVDA", inline=True)
                embed.add_field(name="📊 Full Report", value="Use /search TICKER", inline=True)
                embed.add_field(name="⭐ Watchlist", value="Use /watchlist add TICKER", inline=True)
                embed.add_field(name="📈 Market Overview", value="Use /market", inline=True)
                embed.add_field(name="🔥 Top Movers", value="Use /movers", inline=True)
                embed.add_field(name="🎯 Short Squeeze", value="Use /shortsqueeze", inline=True)
                embed.add_field(name="👀 Insider Feed", value="Use /insider", inline=True)
                embed.add_field(name="🏛️ Congress", value="Use /congress", inline=True)
                embed.add_field(name="📅 Earnings", value="Use /earnings", inline=True)
                
                embed.set_footer(text="Turd News Network v6.0 • /search [ticker] to search!")
                embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
                
                view = OverviewView(self.stock_fetcher, self.watchlist_manager)
                message = await dashboard_channel.send(embed=embed, view=view)
                print(f"[DASHBOARD] ✅ Dashboard sent to #{dashboard_channel.name}")
                
        except Exception as e:
            print(f"[DASHBOARD ERROR] Failed to send dashboard: {e}")
            traceback.print_exc()
    
    async def send_pinned_help_message(self, channel):
        """Send a pinned glossary message"""
        try:
            # Check if already posted - more thorough check
            existing_messages = []
            async for message in channel.history(limit=100):
                if message.author == self.user:
                    existing_messages.append(message)
                    if message.embeds and "Glossary" in message.embeds[0].title:
                        # Check if already pinned
                        if message.pinned:
                            print(f"[PIN] Glossary already pinned, skipping")
                            return
                        else:
                            # Unpin old message if exists but not pinned
                            try:
                                await message.unpin()
                            except:
                                pass
            
            # Build comprehensive glossary
            # Embed 1: Getting Started & Basics
            embed1 = discord.Embed(
                title="📚 Stock Market Glossary - Getting Started",
                description="🎯 **Learn to speak 'stock' in 5 minutes!**\n\nThink of stocks like tiny pieces of a company pizza. When you buy a stock, you own a slice of that company!",
                color=0x3498DB,
                timestamp=datetime.now()
            )
            embed1.add_field(name="🏢 What is a Stock?", value="A stock is like a tiny golden ticket. When you buy one, you own a tiny piece of a company! Companies sell these to get money to grow.", inline=False)
            embed1.add_field(name="📈 Stock Price", value="The price changes every day - like how the price of your favorite toy might go up or down based on how popular it is!", inline=False)
            embed1.add_field(name="🐂 Bull Market", value="When prices are going UP! 📈 Think of a bull (the animal) charging forward - that's the market charging up too!", inline=False)
            embed1.add_field(name="🐻 Bear Market", value="When prices are going DOWN! 📉 Think of a bear sleeping - the market is 'down' just like the bear!", inline=False)
            embed1.add_field(name="📊 Market Cap", value="Market Capitalization = How much the WHOLE company is worth. It's like knowing how much the entire toy store is worth!", inline=False)
            embed1.set_footer(text="Turd News Network • Part 1/10")
            
            # Embed 2: Trading Basics
            embed2 = discord.Embed(
                title="💰 Trading 101 - Let's Buy & Sell!",
                color=0x2ECC71,
                timestamp=datetime.now()
            )
            embed2.add_field(name="🟢 Buy / Long", value="When you think a stock will go UP, you 'buy' or go 'long'. It's like buying a toy because you think it'll be worth more later!", inline=False)
            embed2.add_field(name="🔴 Sell / Short", value="When you think a stock will go DOWN, you 'sell short'. It's like borrowing your friend's toy, selling it, and hoping to buy it back cheaper!", inline=False)
            embed2.add_field(name="💵 Bid Price", value="The price people are OFFERING to pay for a stock. Like the price on the tag at a store!", inline=False)
            embed2.add_field(name="💎 Ask Price", value="The price sellers want to RECEIVE. Like when you sell your old bike, what's the lowest you'll take?", inline=False)
            embed2.add_field(name="📊 Volume", value="How many stocks changed hands today! High volume = lots of people trading!", inline=False)
            embed2.set_footer(text="Turd News Network • Part 2/10")
            
            # Embed 3: Due Diligence
            embed3 = discord.Embed(
                title="🔍 Due Diligence (DD) - Research Time!",
                color=0x9B59B6,
                timestamp=datetime.now()
            )
            embed3.add_field(name="🔬 DD - Due Diligence", value="Doing your homework before buying! It's like reading reviews before buying a video game.", inline=False)
            embed3.add_field(name="📊 Fundamental Analysis (FA/FD)", value="Looking at the company's MONEY stuff - earnings, revenue, debt. Like checking if your friend's lemonade stand is actually making money!", inline=False)
            embed3.add_field(name="📈 Technical Analysis (TA)", value="Looking at CHART patterns to predict where price is going. Like looking at weather patterns to predict tomorrow's weather!", inline=False)
            embed3.add_field(name="🏢 Company Fundamentals", value="**Revenue** = How much money they make\n**Earnings/Profit** = Money left after paying bills\n**P/E Ratio** = Price compared to earnings - is the stock expensive or cheap?", inline=False)
            embed3.set_footer(text="Turd News Network • Part 3/10")
            
            # Embed 4: Important Metrics
            embed4 = discord.Embed(
                title="📊 Key Numbers to Know",
                color=0xE74C3C,
                timestamp=datetime.now()
            )
            embed4.add_field(name="💵 EPS", value="Earnings Per Share - How much profit the company makes for EACH stock. More is better! Like splitting a pizza - bigger slices = more profit per person.", inline=False)
            embed4.add_field(name="📈 P/E Ratio", value="Price to Earnings - How expensive is the stock? Lower can mean 'on sale' but not always!", inline=False)
            embed4.add_field(name="📉 RSI", value="Relative Strength Index - Is the stock OVERBOUGHT (too expensive, might drop) or OVERSOLD (might be a bargain)?", inline=False)
            embed4.add_field(name="📊 Market Cap", value="Price × Number of stocks = Total company value. Big cap = big company. Small cap = smaller company with more room to grow!", inline=False)
            embed4.set_footer(text="Turd News Network • Part 4/10")
            
            # Embed 5: Options Trading
            embed5 = discord.Embed(
                title="🎯 Options - Fancy Trading Tools",
                color=0xFF6600,
                timestamp=datetime.now()
            )
            embed5.add_field(name="📜 Options", value="Special contracts that let you BUY or SELL stocks at a certain price. They're like RESERVATION tickets for stocks!", inline=False)
            embed5.add_field(name="📞 Call Option", value="A ticket that says 'I can BUY this stock at this price later.' Used when you think price will GO UP! 📈", inline=False)
            embed5.add_field(name="📉 Put Option", value="A ticket that says 'I can SELL this stock at this price later.' Used when you think price will GO DOWN! 📉", inline=False)
            embed5.add_field(name="💰 Premium", value="The price you pay for an option ticket. Like a non-refundable deposit!", inline=False)
            embed5.add_field(name="Strike Price", value="The price the option lets you buy/sell at. Like the price written on your coupon!", inline=False)
            embed5.set_footer(text="Turd News Network • Part 5/10")
            
            # Embed 6: Short Selling
            embed6 = discord.Embed(
                title="🔥 Short Selling - Betting Against",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            embed6.add_field(name="🐻 Shorting", value="Borrowing a stock, selling it, hoping to buy it back cheaper! Like borrowing your mom's jewelry, selling it, and hoping you can buy it back for less!", inline=False)
            embed6.add_field(name="👀 Short Interest", value="How many shares people have borrowed and sold short. HIGH short interest = lots of people bet against it!", inline=False)
            embed6.add_field(name="🔥 Short Squeeze", value="When a stock goes UP but short sellers MUST buy it back (to cut losses), causing even MORE price increases! Like panic buying!", inline=False)
            embed6.add_field(name="📊 Days to Cover", value="How many days it'd take for short sellers to buy back all their borrowed shares. More days = harder to squeeze!", inline=False)
            embed6.set_footer(text="Turd News Network • Part 6/10")
            
            # Embed 7: Advanced Analysis
            embed7 = discord.Embed(
                title="📈📉 Technical Analysis - Chart Reading",
                color=0x3498DB,
                timestamp=datetime.now()
            )
            embed7.add_field(name="🕯️ Candlestick", value="A type of price chart showing open, high, low, close. Green = went up, Red = went down!", inline=False)
            embed7.add_field(name="📉 Support", value="A price 'floor' where the stock tends to stop falling. Like the floor beneath a bouncing ball!", inline=False)
            embed7.add_field(name="📈 Resistance", value="A price 'ceiling' where the stock tends to stop rising. Like the ceiling that keeps the ball from going higher!", inline=False)
            embed7.add_field(name="🔄 Breakout", value="When price goes ABOVE resistance - might keep going up!", inline=False)
            embed7.add_field(name="💔 Breakdown", value="When price goes BELOW support - might keep going down!", inline=False)
            embed7.set_footer(text="Turd News Network • Part 7/10")
            
            # Embed 8: Sentiment & Social
            embed8 = discord.Embed(
                title="👥 Sentiment & Social - What Are Others Doing?",
                color=0x9B59B6,
                timestamp=datetime.now()
            )
            embed8.add_field(name="💎 Diamond Hands", value="Investors who HOLD onto their stocks through the rough times. They're strong like diamonds!", inline=False)
            embed8.add_field(name="🧻 Paper Hands", value="Investors who sell at the first sign of trouble. Like paper - weak!", inline=False)
            embed8.add_field(name="🐒 Ape", value="A term for retail investors who band together. Like monkeys working together!", inline=False)
            embed8.add_field(name="🌙 To the Moon", value="When people think a stock will go WAY up in price! 🚀", inline=False)
            embed8.add_field(name="📊 Sentiment", value="How do people FEEL about a stock? Bullish = excited/hopeful, Bearish = worried/negative.", inline=False)
            embed8.set_footer(text="Turd News Network • Part 8/10")
            
            # Embed 9: Special Events
            embed9 = discord.Embed(
                title="⭐ Special Events & Data",
                color=0xE67E22,
                timestamp=datetime.now()
            )
            embed9.add_field(name="📅 Earnings", value="When a company tells everyone how much money they made! Big earnings = stock price might move a LOT!", inline=False)
            embed9.add_field(name="👤 Insider Trading", value="When people who RUN the company buy or sell stock. If insiders are buying, they might know something good!", inline=False)
            embed9.add_field(name="🏛️ Congress Trading", value="When US politicians trade stocks. They have to report their trades publicly!", inline=False)
            embed9.add_field(name="📊 IPO", value="Initial Public Offering - When a company first sells stock to the public! Like a grand opening!", inline=False)
            embed9.add_field(name="🔄 Split", value="When a company divides each share into more shares. The pizza gets cut into more slices, but you still own the same amount!", inline=False)
            embed9.set_footer(text="Turd News Network • Part 9/10")
            
            # Embed 10: Risk & Strategy
            embed10 = discord.Embed(
                title="🎓 Risk & Strategy - How to Not Lose",
                color=0x1ABC9C,
                timestamp=datetime.now()
            )
            embed10.add_field(name="🛡️ Stop Loss", value="An automatic sell order if price drops too much. Like an emergency exit!", inline=False)
            embed10.add_field(name="📊 Position Sizing", value="How much of your money you put in ONE stock. Don't put all eggs in one basket!", inline=False)
            embed10.add_field(name="⚖️ Risk/Reward", value="How much you could GAIN vs how much you could LOSE. Always want more upside than downside!", inline=False)
            embed10.add_field(name="📈 Diversification", value="Buying many different stocks so if one fails, you don't lose everything!", inline=False)
            embed10.add_field(name="💡 Key Rule", value="Only invest what you can afford to lose! Never invest rent money or food money!", inline=False)
            embed10.set_footer(text="Turd News Network • Part 10/10 • /search [ticker] to learn more!")
            
            # Send all embeds
            await channel.send(embed=embed1)
            await channel.send(embed=embed2)
            await channel.send(embed=embed3)
            await channel.send(embed=embed4)
            await channel.send(embed=embed5)
            await channel.send(embed=embed6)
            await channel.send(embed=embed7)
            await channel.send(embed=embed8)
            await channel.send(embed=embed9)
            msg = await channel.send(embed=embed10)
            await msg.pin()
            
            print(f"[PIN] ✅ Pinned comprehensive glossary (10 parts)")
            
        except Exception as e:
            print(f"[PIN ERROR] Failed to create pinned message: {e}")
    async def create_dashboard_channel(self, guild: discord.Guild):
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
    
    async def create_stonks_channel(self, guild: discord.Guild):
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
            
            if post_id in self._seen_posts_this_scan or self.db.is_post_already_sent(post_id):
                skipped_already_sent += 1
                continue
            
            self._seen_posts_this_scan.add(post_id)
            
            combined = post['title'] + ' ' + post['selftext']
            tickers = self.scraper.extract_tickers(combined)
            
            if not tickers:
                skipped_no_tickers += 1
                continue
            
            stock_list = []
            for ticker in tickers:
                data = self.stock_fetcher.get_stock_data(ticker)
                if data:
                    stock_list.append(data)
                    self.db.save_stock_tracking(ticker, post_id, data.get('price', 0))
                time.sleep(API_DELAY)
            
            if stock_list:
                result = await self.send_to_stonks_channel(post, stock_list)
                if result:
                    self.db.save_post(post, tickers, post['quality_score'], "")
                    processed += 1
            else:
                skipped_no_stock_data += 1
        
        print(f"[COMPLETE] Processed: {processed}/{len(all_posts)}")
    
    async def send_to_stonks_channel(self, post, stock_list):
        try:
            for guild in self.guilds:
                stonks_channel = None
                for ch in guild.text_channels:
                    if ch.name == "stonks":
                        stonks_channel = ch
                        break
                
                if not stonks_channel:
                    continue
                
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
                title_embed.set_footer(text="Turd News Network v6.0 | Due Diligence Scanner")
                await stonks_channel.send(embed=title_embed)
                
                for sd in stock_list[:3]:
                    ticker = sd.get('ticker')
                    if not ticker:
                        continue
                    
                    try:
                        from ticker_report import TickerReportBuilder
                        builder = TickerReportBuilder()
                        
                        loop = asyncio.get_running_loop()
                        embeds_list, chart_path = await loop.run_in_executor(
                            None, builder.build_report_sync, ticker
                        )
                        
                        if embeds_list:
                            embed_indices = [0, 1, 2, 3, 4]
                            
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
                                    await stonks_channel.send(embed=embed)
                                    await asyncio.sleep(0.5)
                            
                            if chart_path and os.path.exists(chart_path):
                                try:
                                    chart_file = discord.File(chart_path, filename=f"{ticker}_chart.png")
                                    await stonks_channel.send(file=chart_file)
                                except:
                                    pass
                        
                    except Exception as e:
                        await self._send_simple_embed(stonks_channel, sd, post)
                
                return True
                
        except Exception as e:
            print(f"[ERROR] send_to_stonks_channel failed: {e}")
            return False
        return False
    
    async def _send_simple_embed(self, channel, sd, post):
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
