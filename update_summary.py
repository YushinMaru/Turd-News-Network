#!/usr/bin/env python3
"""Enhanced summary with more data"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The current send_scan_summary function - find it by a smaller pattern
old_pattern = '''async def send_scan_summary(self, processed, total, skipped_already_sent, skipped_no_tickers, skipped_no_stock_data):
        """Send a summary embed to the stonks channel after scan completes"""
        try:
            for guild in self.guilds:
                # Find the stonks channel
                stonks_channel = None
                for ch in guild.text_channels:
                    if ch.name == "stonks":
                        stonks_channel = ch
                        break
                
                if not stonks_channel:
                    continue
                
                # Create summary embed
                embed = discord.Embed(
                    title="📊 Scan Complete!",
                    description="**Reddit DD Scan Results**",
                    color=0x3498DB,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="📈 Summary",
                    value=f"**Total Posts:** {total}\\n"
                          f"**Processed:** {processed}\\n"
                          f"**Skipped (already sent):** {skipped_already_sent}\\n"
                          f"**Skipped (no tickers):** {skipped_no_tickers}\\n"
                          f"**Skipped (no stock data):** {skipped_no_stock_data}",
                    inline=False
                )
                
                embed.set_footer(text="Turd News Network v6.0 • Next scan in 3 hours")
                
                await stonks_channel.send(embed=embed)
                print(f"[SUMMARY] Sent scan summary to #{stonks_channel.name}")
                
        except Exception as e:
            print(f"[SUMMARY ERROR] Failed to send scan summary: {e}")
            traceback.print_exc()'''

# Enhanced function with more embeds
new_code = '''async def send_scan_summary(self, processed, total, skipped_already_sent, skipped_no_tickers, skipped_no_stock_data):
        """Send summary embeds to the stonks channel after scan completes"""
        try:
            for guild in self.guilds:
                # Find the stonks channel
                stonks_channel = None
                for ch in guild.text_channels:
                    if ch.name == "stonks":
                        stonks_channel = ch
                        break
                
                if not stonks_channel:
                    continue
                
                # === EMBED 1: Scan Summary ===
                embed1 = discord.Embed(
                    title="📊 Scan Complete!",
                    description="**Reddit DD Scan Results**",
                    color=0x3498DB,
                    timestamp=datetime.now()
                )
                
                embed1.add_field(
                    name="📈 Scan Summary",
                    value=f"**Total Posts:** {total}\\n"
                          f"**Processed:** {processed}\\n"
                          f"**Skipped (already sent):** {skipped_already_sent}\\n"
                          f"**Skipped (no tickers):** {skipped_no_tickers}\\n"
                          f"**Skipped (no stock data):** {skipped_no_stock_data}",
                    inline=False
                )
                
                embed1.set_footer(text="Turd News Network v6.0 • Next scan in 3 hours")
                await stonks_channel.send(embed=embed1)
                
                # === EMBED 2: Top Reddit DD Gainers ===
                conn = self.db.get_connection()
                c = conn.cursor()
                
                c.execute(\"SELECT ticker, MAX(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct > 0 GROUP BY ticker ORDER BY change_pct DESC LIMIT 10\")
                gainers = c.fetchall()
                
                if gainers:
                    gainer_text = "\\n".join([f"📈 **${t}** {c:+.1f}%" for t, c in gainers])
                    embed2 = discord.Embed(
                        title="🔥 Top Reddit DD Gainers",
                        description="Highest performing stocks from today's DD posts",
                        color=0x00FF00,
                        timestamp=datetime.now()
                    )
                    embed2.add_field(name="Top Gainers", value=gainer_text, inline=False)
                    embed2.set_footer(text="Turd News Network v6.0")
                    await stonks_channel.send(embed=embed2)
                
                # === EMBED 3: Top Reddit DD Losers ===
                c.execute(\"SELECT ticker, MIN(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct < 0 GROUP BY ticker ORDER BY change_pct ASC LIMIT 10\")
                losers = c.fetchall()
                
                if losers:
                    loser_text = "\\n".join([f"📉 **${t}** {c:.1f}%" for t, c in losers])
                    embed3 = discord.Embed(
                        title="📉 Top Reddit DD Losers",
                        description="Lowest performing stocks from today's DD posts",
                        color=0xFF0000,
                        timestamp=datetime.now()
                    )
                    embed3.add_field(name="Top Losers", value=loser_text, inline=False)
                    embed3.set_footer(text="Turd News Network v6.0")
                    await stonks_channel.send(embed=embed3)
                
                # === EMBED 4: Top 10 Market Gainers Today ===
                c.execute(\"SELECT ticker, MAX(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct > 0 GROUP BY ticker ORDER BY change_pct DESC LIMIT 10\")
                market_gainers = c.fetchall()
                
                if market_gainers:
                    market_gainer_text = "\\n".join([f"🟢 **${t}** ${c:+.1f}%" for t, c in market_gainers])
                    embed4 = discord.Embed(
                        title="📈 Top 10 Gainers Today",
                        description="Best performing stocks across all tracked tickers",
                        color=0x00FF00,
                        timestamp=datetime.now()
                    )
                    embed4.add_field(name="Gainers", value=market_gainer_text, inline=False)
                    embed4.set_footer(text="Turd News Network v6.0")
                    await stonks_channel.send(embed=embed4)
                
                # === EMBED 5: Top 10 Market Losers Today ===
                c.execute(\"SELECT ticker, MIN(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct < 0 GROUP BY ticker ORDER BY change_pct ASC LIMIT 10\")
                market_losers = c.fetchall()
                
                if market_losers:
                    market_loser_text = "\\n".join([f"🔴 **${t}** ${c:.1f}%" for t, c in market_losers])
                    embed5 = discord.Embed(
                        title="📉 Top 10 Losers Today",
                        description="Worst performing stocks across all tracked tickers",
                        color=0xFF0000,
                        timestamp=datetime.now()
                    )
                    embed5.add_field(name="Losers", value=market_loser_text, inline=False)
                    embed5.set_footer(text="Turd News Network v6.0")
                    await stonks_channel.send(embed=embed5)
                
                conn.close()
                print(f"[SUMMARY] Sent 5 summary embeds to #{stonks_channel.name}")
                
        except Exception as e:
            print(f"[SUMMARY ERROR] Failed to send scan summary: {e}")
            traceback.print_exc()'''

if old_pattern in content:
    content = content.replace(old_pattern, new_code)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Enhanced summary with 5 embeds!")
else:
    print("ERROR: Could not find pattern to replace")
    # Let's try a simpler approach - just find and print what we have
    if 'async def send_scan_summary' in content:
        print("Found send_scan_summary function, but pattern doesn't match exactly")
