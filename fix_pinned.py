"""
Patch script to update the pinned message function in main.py
"""

import re

# Read the main.py file
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The old function to replace
old_function = '''    async def send_pinned_help_message(self, channel):
        """Send a pinned help message"""
        try:
            async for message in channel.history(limit=50):
                if message.author == self.user and message.content.startswith("📚 **TURD NEWS NETWORK"):
                    return
            
            embed = discord.Embed(
                title="📚 Stock Terms Explained - Complete Guide",
                description="Use /search [ticker] to look up stocks!",
                color=0x3498DB,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📖 Available Commands",
                value="• /search [ticker] - Search stock data\n"
                       "• /watchlist add/remove/list - Manage watchlist\n"
                       "• /market - Market overview\n"
                       "• /movers - Top gainers/losers\n"
                       "• /shortsqueeze - High short interest\n"
                       "• /insider - Insider activity\n"
                       "• /congress - Congress trading\n"
                       "• /earnings - Upcoming earnings",
                inline=False
            )
            
            embed.set_footer(text="Turd News Network v6.0 • 📌 Pinned for easy reference")
            
            help_msg = await channel.send(embed=embed)
            await help_msg.pin()
            print(f"[PIN] ✅ Pinned help message")
            
        except Exception as e:
            print(f"[PIN ERROR] Failed to create pinned message: {e}")'''

# The new function with glossary
new_function = '''    async def send_pinned_help_message(self, channel):
        """Send a pinned glossary message"""
        try:
            # Check if already posted
            async for message in channel.history(limit=50):
                if message.author == self.user and message.embeds:
                    if "Glossary" in message.embeds[0].title:
                        return
            
            # Embed 1: Title & Intro
            embed1 = discord.Embed(
                title="📚 Stock Terms Glossary",
                description="Your guide to understanding stock market terminology!",
                color=0x3498DB,
                timestamp=datetime.now()
            )
            embed1.add_field(name="📖 How to Use", value="Use /search [ticker] to look up stocks and see these terms in action!", inline=False)
            embed1.set_footer(text="Turd News Network v6.0 • Part 1/4")
            
            # Embed 2: Basic Terms
            embed2 = discord.Embed(
                title="💰 Basic Terms",
                color=0x2ECC71,
                timestamp=datetime.now()
            )
            embed2.add_field(name="📊 DD", value="Due Diligence - Research before investing", inline=False)
            embed2.add_field(name="🐂 Bull", value="Expecting price to go up", inline=False)
            embed2.add_field(name="🐻 Bear", value="Expecting price to go down", inline=False)
            embed2.add_field(name="📈 TA", value="Technical Analysis - Chart patterns", inline=False)
            embed2.add_field(name="📉 FD", value="Fundamental Analysis - Financials/earnings", inline=False)
            embed2.set_footer(text="Turd News Network v6.0 • Part 2/4")
            
            # Embed 3: Trading Terms
            embed3 = discord.Embed(
                title="🎯 Trading Terms",
                color=0xE74C3C,
                timestamp=datetime.now()
            )
            embed3.add_field(name="🔥 Short Squeeze", value="When short sellers forced to buy", inline=False)
            embed3.add_field(name="📊 Options", value="Contracts to buy/sell at set prices", inline=False)
            embed3.add_field(name="⚡ Gamma", value="Rate of delta change - options sensitivity", inline=False)
            embed3.add_field(name="💎 Diamond Hands", value="Hold through volatility", inline=False)
            embed3.add_field(name="🧻 Paper Hands", value="Sell at first sign of red", inline=False)
            embed3.set_footer(text="Turd News Network v6.0 • Part 3/4")
            
            # Embed 4: Advanced Terms
            embed4 = discord.Embed(
                title="🚀 Advanced Terms",
                color=0x9B59B6,
                timestamp=datetime.now()
            )
            embed4.add_field(name="👀 Short Interest", value="% of shares sold short", inline=False)
            embed4.add_field(name="🏛️ Congress Trading", value="Trades by US politicians", inline=False)
            embed4.add_field(name="👤 Insider Trading", value="Trades by company executives", inline=False)
            embed4.add_field(name="📈 RSI", value="Relative Strength Index - momentum", inline=False)
            embed4.add_field(name="💵 EPS", value="Earnings Per Share", inline=False)
            embed4.set_footer(text="Turd News Network v6.0 • Part 4/4")
            
            # Send all embeds
            await channel.send(embed=embed1)
            await channel.send(embed=embed2)
            await channel.send(embed=embed3)
            msg = await channel.send(embed=embed4)
            await msg.pin()
            
            print(f"[PIN] ✅ Pinned glossary message")
            
        except Exception as e:
            print(f"[PIN ERROR] Failed to create pinned message: {e}")'''

# Replace the function
if old_function in content:
    content = content.replace(old_function, new_function)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Successfully patched main.py!")
else:
    print("❌ Could not find the exact function to replace. Trying alternative...")
    # Try with just the function definition line
    alt_pattern = r'    async def send_pinned_help_message\(self, channel\):.*?(?=\n    async def |\n    def |\nclass |\Z)'
    if re.search(alt_pattern, content, re.DOTALL):
        content = re.sub(alt_pattern, new_function, content, flags=re.DOTALL)
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Successfully patched main.py (alternative)!")
    else:
        print("❌ Could not find function to replace")
