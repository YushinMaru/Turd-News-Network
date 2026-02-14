"""
Add missing slash commands to main.py - simpler version
"""

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The new commands to add
new_commands = '''
    @app_commands.command(name="alert", description="Set a price alert for a stock")
    @app_commands.describe(ticker="Stock ticker (e.g., NVDA)")
    @app_commands.describe(direction="above or below current price")
    @app_commands.describe(price="Target price")
    async def alert(self, interaction: discord.Interaction, ticker: str, direction: str, price: str):
        """Set a price alert"""
        user_id = str(interaction.user.id)
        ticker = ticker.strip().upper()
        
        # Parse price (remove $ if present)
        try:
            price_val = float(price.replace('$', '').replace(',', ''))
        except ValueError:
            await interaction.response.send_message("Invalid price format. Use like: 100 or 100.50", ephemeral=True)
            return
        
        if direction.lower() not in ['above', 'below']:
            await interaction.response.send_message("Direction must be 'above' or 'below'", ephemeral=True)
            return
        
        # Save alert to database
        self.bot.db.ensure_user_exists(user_id, username=interaction.user.name)
        self.bot.db.add_price_alert(user_id, ticker, price_val, direction.lower())
        
        emoji = "above" if direction.lower() == "above" else "below"
        await interaction.response.send_message(
            f"Alert set for **{ticker}** {direction} **${price_val:.2f}**",
            ephemeral=True
        )
    
    @app_commands.command(name="alerts", description="View your price alerts")
    async def alerts(self, interaction: discord.Interaction):
        """View your price alerts"""
        user_id = str(interaction.user.id)
        
        alerts = self.bot.db.get_user_alerts(user_id)
        
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
            for alert in alerts[:10]:
                ticker = alert.get('ticker', 'N/A')
                target = alert.get('target_price', 0)
                direction = alert.get('direction', 'above')
                embed.add_field(
                    name=f"${ticker}",
                    value=f"{direction} ${target:.2f}",
                    inline=True
                )
        
        embed.set_footer(text="Turd News Network v6.0")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="report", description="Generate a comprehensive HTML report")
    @app_commands.describe(ticker="Stock ticker (e.g., NVDA)")
    async def report(self, interaction: discord.Interaction, ticker: str):
        """Generate HTML report"""
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        ticker = ticker.strip().upper()
        
        try:
            from company_intelligence_dashboard import generate_company_dashboard
            
            loop = asyncio.get_running_loop()
            html_file = await loop.run_in_executor(
                None, generate_company_dashboard, ticker
            )
            
            if html_file and os.path.exists(html_file):
                embed = discord.Embed(
                    title=f"{ticker} - Company Intelligence Report",
                    description="17-Section Comprehensive Analysis",
                    color=0x3498db,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="Download",
                    value="Download the HTML file below to view the full interactive dashboard",
                    inline=False
                )
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
'''

# Find the end of the earnings command and add new commands after it
# Look for the earnings command and add after its code block
target = '            await interaction.followup.send(f"Error: {str(e)[:200]}", ephemeral=True)\n'
insert_pos = content.find(target)

if insert_pos != -1:
    insert_pos = insert_pos + len(target)
    content = content[:insert_pos] + new_commands + content[insert_pos:]
    
    # Add commands to setup_hook
    setup_target = 'self.tree.add_command(self.slash_cmds.earnings)'
    content = content.replace(setup_target, 
        setup_target + '''
        self.tree.add_command(self.slash_cmds.alert)
        self.tree.add_command(self.slash_cmds.alerts)
        self.tree.add_command(self.slash_cmds.report)''')
    
    # Write the updated content
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully added /alert, /alerts, and /report commands!")
else:
    print("Could not find insertion point")
