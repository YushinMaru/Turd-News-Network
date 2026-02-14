#!/usr/bin/env python3
"""Patch script to add enhanced summary embeds to main.py"""

# Read main.py
with open('main.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# The target section to replace
old_code = '''                await stonks_channel.send(embed=embed)
                print(f"[SUMMARY] Sent scan summary to #{stonks_channel.name}")
                
        except Exception as e:
            print(f"[SUMMARY ERROR] Failed to send scan summary: {e}")
            traceback.print_exc()'''

# New code with 5 embeds
new_code = '''                await stonks_channel.send(embed=embed)
                print(f"[SUMMARY] Sent scan summary to #{stonks_channel.name}")
                
                # EMBED 2: Top Reddit DD Gainers (from database)
                try:
                    conn = self.db.get_connection()
                    c = conn.cursor()
                    
                    c.execute("SELECT ticker, MAX(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct > 0 GROUP BY ticker ORDER BY change_pct DESC LIMIT 10")
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
                    
                    # EMBED 3: Top Reddit DD Losers
                    c.execute("SELECT ticker, MIN(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct < 0 GROUP BY ticker ORDER BY change_pct ASC LIMIT 10")
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
                    
                    # EMBED 4: Top 10 Market Gainers Today
                    c.execute("SELECT ticker, MAX(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct > 0 GROUP BY ticker ORDER BY change_pct DESC LIMIT 10")
                    market_gainers = c.fetchall()
                    
                    if market_gainers:
                        market_gainer_text = "\\n".join([f"🟢 **${t}** {c:+.1f}%" for t, c in market_gainers])
                        embed4 = discord.Embed(
                            title="📈 Top 10 Gainers Today",
                            description="Best performing stocks across all tracked tickers",
                            color=0x00FF00,
                            timestamp=datetime.now()
                        )
                        embed4.add_field(name="Gainers", value=market_gainer_text, inline=False)
                        embed4.set_footer(text="Turd News Network v6.0")
                        await stonks_channel.send(embed=embed4)
                    
                    # EMBED 5: Top 10 Market Losers Today
                    c.execute("SELECT ticker, MIN(price_change_pct) as change_pct FROM stock_tracking WHERE price_change_pct < 0 GROUP BY ticker ORDER BY change_pct ASC LIMIT 10")
                    market_losers = c.fetchall()
                    
                    if market_losers:
                        market_loser_text = "\\n".join([f"🔴 **${t}** {c:.1f}%" for t, c in market_losers])
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
                    print(f"[SUMMARY] Sent 4 additional summary embeds")
                except Exception as db_err:
                    print(f"[SUMMARY DB ERROR] {db_err}")
                
        except Exception as e:
            print(f"[SUMMARY ERROR] Failed to send scan summary: {e}")
            traceback.print_exc()'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Enhanced summary with 5 embeds!")
else:
    print("ERROR: Could not find target section to patch")
    print("Searching for variations...")
    if "Sent scan summary" in content:
        print("Found 'Sent scan summary' in file")
