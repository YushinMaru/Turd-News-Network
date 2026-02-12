class ReportsModal(discord.ui.Modal):
    """Generate a comprehensive Company Intelligence Dashboard report"""
    def __init__(self, stock_fetcher):
        super().__init__(title="📊 Company Intelligence Report", timeout=300)
        self.stock_fetcher = stock_fetcher
        self.ticker_input = discord.ui.TextInput(
            label="Ticker Symbol",
            placeholder="e.g., AAPL, NVDA, TSLA",
            min_length=1, max_length=10, required=True
        )
        self.add_item(self.ticker_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Generate comprehensive 17-section HTML report"""
        import traceback
        user = interaction.user
        ticker = self.ticker_input.value.strip().upper()
        
        print(f"\n{'='*70}")
        print(f"[REPORTS MODAL] Generating Company Intelligence Dashboard for {ticker}")
        print(f"  User: {user}")
        print(f"  Time: {datetime.now().isoformat()}")
        print(f"{'='*70}")
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Fetch basic stock data first
            stock_data = self.stock_fetcher.get_stock_data(ticker)
            if not stock_data:
                await interaction.followup.send(
                    f"❌ **{ticker}** not found.\n\nPlease check the ticker symbol.",
                    ephemeral=True
                )
                return
            
            # Generate comprehensive HTML report using Company Intelligence Dashboard
            await interaction.followup.send(
                f"📊 Generating **Company Intelligence Dashboard** for **{ticker}**...\n"
                f"⏳ This may take 30-60 seconds (fetching 17 sections of data)...",
                ephemeral=True
            )
            
            # Import and use the Company Intelligence Dashboard
            try:
                from company_intelligence_dashboard import generate_company_dashboard
                html_file = generate_company_dashboard(ticker)
                
                if html_file and os.path.exists(html_file):
                    # Send success message with file
                    embed = discord.Embed(
                        title=f"📊 {ticker} - Company Intelligence Dashboard",
                        description=f"**17-Section Comprehensive Report** for **{stock_data.get('name', ticker)}**",
                        color=0x3498db,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="✨ What's Included",
                        value="• Executive Summary with AI Analysis\n"
                              "• Complete Financial Statements & Ratios\n"
                              "• Stock Performance with Interactive Charts\n"
                              "• Leadership & Insider Trading Data\n"
                              "• Congress Trading Activity\n"
                              "• Risk Assessment & ESG Data\n"
                              "• Competitor Analysis\n"
                              "• SEC Filings Links",
                        inline=False
                    )
                    embed.add_field(
                        name="💾 How to View",
                        value="1. Download the HTML file below\n"
                              "2. Open in any web browser (Chrome, Firefox, Edge)\n"
                              "3. Use the left sidebar to navigate 17 sections\n"
                              "4. All charts are interactive!",
                        inline=False
                    )
                    embed.add_field(
                        name="🎨 Features",
                        value="• Dark mode professional design\n"
                              "• Chart.js interactive charts\n"
                              "• Mobile responsive layout\n"
                              "• Works offline - all data embedded",
                        inline=False
                    )
                    embed.set_footer(text="Turd News Network - Company Intelligence Dashboard v5.0")
                    
                    await interaction.followup.send(
                        embed=embed,
                        file=discord.File(html_file),
                        ephemeral=True
                    )
                    
                    # Clean up the file after sending
                    try:
                        os.remove(html_file)
                    except:
                        pass
                    
                    print(f"[SUCCESS] Company Intelligence Dashboard sent for {ticker}")
                else:
                    await interaction.followup.send(
                        f"❌ Failed to generate report for **{ticker}**.\n"
                        f"The dashboard generator encountered an error.",
                        ephemeral=True
                    )
                    
            except ImportError as e:
                print(f"[ERROR] Could not import company_intelligence_dashboard: {e}")
                await interaction.followup.send(
                    f"❌ Dashboard module not available. Using fallback report...",
                    ephemeral=True
                )
                # Fallback to simple embed report
                await self._send_fallback_report(interaction, ticker, stock_data)
                
        except discord.errors.NotFound as e:
            print(f"[ERROR] Interaction not found: {e}")
        except Exception as e:
            print(f"[ERROR] ReportsModal error: {e}")
            print(traceback.format_exc())
            try:
                await interaction.followup.send(
                    f"❌ An error occurred while generating the report.\n"
                    f"Error: {str(e)[:100]}",
                    ephemeral=True
                )
            except:
                pass
    
    async def _send_fallback_report(self, interaction: discord.Interaction, ticker: str, stock_data: dict):
        """Send a simple fallback report if dashboard fails"""
        embed = discord.Embed(
            title=f"📊 {ticker} - Stock Report",
            description=f"Report for {stock_data.get('name', ticker)}",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        price = stock_data.get('price', 'N/A')
        change = stock_data.get('change_pct', 0)
        embed.add_field(name="💰 Price", value=f"${price}" if price != 'N/A' else "N/A", inline=True)
        embed.add_field(name="📈 Change", value=f"{change:+.2f}%" if isinstance(change, (int, float)) else "N/A", inline=True)
        embed.add_field(name="📋 P/E", value=str(stock_data.get('pe_ratio', 'N/A')), inline=True)
        embed.add_field(name="💵 Market Cap", value=f"${stock_data.get('market_cap', 0):,}" if stock_data.get('market_cap') else "N/A", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
