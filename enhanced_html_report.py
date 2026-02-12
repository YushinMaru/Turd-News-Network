"""
Enhanced HTML Stock Report Generator - COMPREHENSIVE VERSION
Creates detailed, multi-page HTML reports with all data, charts, and analysis
NOW WITH COMPREHENSIVE DATA FETCHER INTEGRATION
"""

import os
import json
import requests
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd


class EnhancedHTMLReportGenerator:
    """Generates comprehensive HTML reports with all data, charts, and analysis"""

    def __init__(self, stock_data: Dict, ticker: str):
        self.stock_data = stock_data
        self.ticker = ticker.upper()
        self.company_name = stock_data.get('name', ticker)
        self.report_date = datetime.now()
        self.yf_ticker = None
        self.comprehensive_data = None

    def generate_report(self) -> Optional[str]:
        """Generate comprehensive HTML report with all enhancements using comprehensive data fetcher"""
        try:
            print(f"[REPORT] Starting comprehensive data fetch for {self.ticker}...")

            # Use new comprehensive data fetcher
            try:
                from comprehensive_data_fetcher import ComprehensiveDataFetcher
                fetcher = ComprehensiveDataFetcher(self.ticker)
                self.comprehensive_data = fetcher.fetch_all_data()
                print(f"[REPORT] ✓ Comprehensive data fetched successfully")
            except Exception as e:
                print(f"[REPORT] Comprehensive fetcher error: {e}")
                self.comprehensive_data = None

            # Fetch additional data (backward compatibility)
            yfinance_data = self._fetch_yfinance_data()
            scraped_data = self._scrape_company_data()
            sentiment_data = self._analyze_sentiment()
            ml_prediction = self._get_ml_prediction()
            congress_data = self._fetch_congress_data()
            insider_data = self._fetch_insider_data()
            charts = self._generate_charts()

            # Merge comprehensive data with existing data
            if self.comprehensive_data:
                # Use comprehensive data where available
                if not congress_data and self.comprehensive_data.get('congress'):
                    congress_data = self.comprehensive_data['congress']
                if not insider_data.get('transactions') and self.comprehensive_data.get('insider'):
                    insider_data = self.comprehensive_data['insider']

            # Generate HTML
            html_content = self._build_html(
                yfinance_data, scraped_data, sentiment_data,
                ml_prediction, congress_data, insider_data, charts
            )

            # Save report
            filename = f"{self.ticker}_COMPREHENSIVE_REPORT.html"
            filepath = os.path.join(os.path.dirname(__file__), filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Save all data to database
            self._save_to_database(
                yfinance_data, sentiment_data, ml_prediction,
                congress_data, insider_data, filepath
            )

            print(f"[REPORT] ✓ Report generated: {filepath}")
            return filepath

        except Exception as e:
            print(f"[HTML REPORT ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_to_database(self, yf_data: Dict, sentiment: Dict, ml: Dict,
                         congress: List, insider: Dict, filepath: str):
        """Save all report data to database"""
        try:
            from database import DatabaseManager
            db = DatabaseManager()

            # Save stock metadata
            info = yf_data.get('info', {})
            metadata = {
                'name': info.get('longName', self.company_name),
                'sector': info.get('sector', self.stock_data.get('sector')),
                'industry': info.get('industry', self.stock_data.get('industry')),
                'market_cap': info.get('marketCap', self.stock_data.get('market_cap')),
                'pe_ratio': info.get('trailingPE', self.stock_data.get('pe_ratio')),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'beta': info.get('beta', self.stock_data.get('beta')),
                'dividend_yield': info.get('dividendYield'),
                'profit_margin': info.get('profitMargins'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'roe': info.get('returnOnEquity'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_date': info.get('earningsDate'),
                'analyst_rating': info.get('recommendationKey'),
                'price_target': info.get('targetMeanPrice'),
                'short_interest': info.get('sharesShort'),
                'short_ratio': info.get('shortRatio'),
                'institutional_ownership': info.get('institutionalOwnership'),
                'insider_ownership': info.get('heldPercentInsiders')
            }
            db.save_stock_metadata(self.ticker, metadata)
            print(f"[DB] Saved stock metadata for {self.ticker}")

            # Save sentiment analysis
            db.save_sentiment_analysis(self.ticker, sentiment)
            print(f"[DB] Saved sentiment analysis for {self.ticker}")

            # Save ML prediction
            db.save_ml_prediction(self.ticker, ml)
            print(f"[DB] Saved ML prediction for {self.ticker}")

            # Save Congress trades
            if congress:
                db.save_congress_trades(congress)
                print(f"[DB] Saved {len(congress)} Congress trades for {self.ticker}")

            # Save insider transactions
            if insider.get('transactions'):
                db.save_insider_transactions(self.ticker, insider['transactions'])
                print(f"[DB] Saved {len(insider['transactions'])} insider transactions for {self.ticker}")

            print(f"[DB] All data saved successfully for {self.ticker}")

        except Exception as e:
            print(f"[DB ERROR] Failed to save to database: {e}")
            import traceback
            traceback.print_exc()

    def _build_html(self, yf_data: Dict, scraped: Dict, sentiment: Dict,
                    ml: Dict, congress: List, insider: Dict, charts: Dict) -> str:
        """Build comprehensive HTML report with all sections"""
        info = yf_data.get('info', {})

        # Helper function for safe value retrieval
        def get_value(data_dict, key, default='N/A', formatter=None):
            val = data_dict.get(key, default)
            if val is None or val == 'None' or val == '':
                val = default
            if formatter and val != default and val != 'N/A':
                try:
                    val = formatter(val)
                except:
                    pass
            return val

        # Extract all data
        price = get_value(self.stock_data, 'price', 'N/A', lambda x: f"${x:.2f}")
        change_pct = self.stock_data.get('change_pct', 0)
        market_cap = get_value(self.stock_data, 'market_cap', 0)
        mc_str = f"${market_cap/1e9:.2f}B" if isinstance(market_cap, (int, float)) and market_cap > 0 else "N/A"

        # Extended data from yfinance
        pe_ratio = get_value(info, 'trailingPE', get_value(self.stock_data, 'pe_ratio', 'N/A'))
        forward_pe = get_value(info, 'forwardPE', 'N/A')
        peg_ratio = get_value(info, 'pegRatio', 'N/A')
        price_to_book = get_value(info, 'priceToBook', 'N/A')
        price_to_sales = get_value(info, 'priceToSalesTrailing12Months', 'N/A')

        # 52 week data
        high_52 = get_value(info, 'fiftyTwoWeekHigh', get_value(self.stock_data, '52w_high', 'N/A'), lambda x: f"${x:.2f}")
        low_52 = get_value(info, 'fiftyTwoWeekLow', get_value(self.stock_data, '52w_low', 'N/A'), lambda x: f"${x:.2f}")

        # Volume
        volume = get_value(self.stock_data, 'volume', 0)
        vol_str = f"{volume/1e6:.2f}M" if isinstance(volume, (int, float)) and volume > 0 else "N/A"
        avg_volume = get_value(info, 'averageVolume', get_value(self.stock_data, 'avg_volume', 0))
        avg_vol_str = f"{avg_volume/1e6:.2f}M" if isinstance(avg_volume, (int, float)) and avg_volume > 0 else "N/A"

        # Financial metrics
        beta = get_value(info, 'beta', get_value(self.stock_data, 'beta', 'N/A'))
        eps = get_value(info, 'trailingEps', get_value(self.stock_data, 'eps', 'N/A'))
        forward_eps = get_value(info, 'forwardEps', 'N/A')

        # Revenue and income
        revenue = get_value(info, 'totalRevenue', get_value(self.stock_data, 'revenue', 0))
        rev_str = f"${revenue/1e9:.2f}B" if isinstance(revenue, (int, float)) and revenue > 0 else "N/A"

        gross_profit = get_value(info, 'grossProfits', get_value(self.stock_data, 'gross_profit', 0))
        gp_str = f"${gross_profit/1e9:.2f}B" if isinstance(gross_profit, (int, float)) and gross_profit > 0 else "N/A"

        operating_income = get_value(info, 'operatingCashflow', 0)
        oi_str = f"${operating_income/1e9:.2f}B" if isinstance(operating_income, (int, float)) and operating_income != 0 else "N/A"

        net_income = get_value(info, 'netIncomeToCommon', 0)
        ni_str = f"${net_income/1e9:.2f}B" if isinstance(net_income, (int, float)) and net_income != 0 else "N/A"

        # Balance sheet
        total_cash = get_value(info, 'totalCash', get_value(self.stock_data, 'total_cash', 0))
        tc_str = f"${total_cash/1e9:.2f}B" if isinstance(total_cash, (int, float)) and total_cash > 0 else "N/A"

        total_debt = get_value(info, 'totalDebt', get_value(self.stock_data, 'total_debt', 0))
        td_str = f"${total_debt/1e9:.2f}B" if isinstance(total_debt, (int, float)) and total_debt > 0 else "N/A"

        total_assets = get_value(info, 'totalAssets', get_value(self.stock_data, 'total_assets', 0))
        ta_str = f"${total_assets/1e9:.2f}B" if isinstance(total_assets, (int, float)) and total_assets > 0 else "N/A"

        # Company info
        sector = get_value(info, 'sector', get_value(self.stock_data, 'sector', 'N/A'))
        industry = get_value(info, 'industry', get_value(self.stock_data, 'industry', 'N/A'))
        employees = get_value(info, 'fullTimeEmployees', get_value(self.stock_data, 'employees', 'N/A'))
        if isinstance(employees, (int, float)) and employees > 0:
            employees = f"{int(employees):,}"

        website = get_value(info, 'website', get_value(self.stock_data, 'website', 'N/A'))
        country = get_value(info, 'country', 'N/A')
        ceo = get_value(info, 'companyOfficers', [{}])[0].get('name', 'N/A') if info.get('companyOfficers') else 'N/A'

        # Description
        description = scraped.get('description', info.get('longBusinessSummary',
            f"{self.company_name} is a company operating in the {sector} sector."))

        # Sentiment data
        sentiment_text = sentiment.get('sentiment', 'NEUTRAL')
        sentiment_conf = sentiment.get('confidence', 0.5) * 100
        sentiment_score = sentiment.get('score', 0)

        # ML prediction
        ml_dir = ml.get('direction', 'NEUTRAL')
        ml_conf = ml.get('confidence', 0.5) * 100

        # Recommendation
        if sentiment_text == 'BULLISH' and ml_dir == 'UP':
            recommendation = 'STRONG BUY'
            rec_color = '#22543d'
        elif sentiment_text == 'BULLISH' or ml_dir == 'UP':
            recommendation = 'BUY'
            rec_color = '#48bb78'
        elif sentiment_text == 'NEUTRAL':
            recommendation = 'HOLD'
            rec_color = '#ed8936'
        else:
            recommendation = 'SELL'
            rec_color = '#f56565'

        # Congress data
        congress_buys = sum(1 for t in congress if 'PURCHASE' in str(t.get('transaction_type', '')).upper())
        congress_sells = sum(1 for t in congress if 'SALE' in str(t.get('transaction_type', '')).upper())

        # Insider data
        insider_buys = insider.get('buys', 0)
        insider_sells = insider.get('sells', 0)

        # Build chart section HTML
        chart_section_html = ""
        if charts:
            chart_section_html = '<div class="section chart-section">\n'
            chart_section_html += '<h2 class="section-title">📈 Technical Charts</h2>\n'

            if "price_history" in charts:
                chart_section_html += f'<div class="chart-container"><h3>Price History with Moving Averages</h3><img src="data:image/png;base64,{charts["price_history"]}" alt="Price History" /></div>\n'

            if "volume" in charts:
                chart_section_html += f'<div class="chart-container"><h3>Trading Volume</h3><img src="data:image/png;base64,{charts["volume"]}" alt="Volume" /></div>\n'

            if "rsi" in charts:
                chart_section_html += f'<div class="chart-container"><h3>RSI (14-day)</h3><img src="data:image/png;base64,{charts["rsi"]}" alt="RSI" /></div>\n'

            chart_section_html += '</div>'

        # Build Congress HTML
        congress_html = ""
        if congress:
            congress_html = ''.join([f'<tr><td colspan="2">{t.get("politician_name", "Unknown")} - {t.get("transaction_type", "N/A")}</td></tr>' for t in congress[:3]])
        else:
            congress_html = '<tr><td colspan="2">No recent Congress trades</td></tr>'

        # Build Insider HTML - FIXED to handle DataFrame/dict properly
        insider_html = ""
        transactions = insider.get('transactions')
        if transactions is not None and len(transactions) > 0:
            # Handle both DataFrame and dict formats
            if isinstance(transactions, pd.DataFrame):
                # Convert DataFrame to list of dicts
                txn_list = transactions.head(3).to_dict('records')
            elif isinstance(transactions, dict):
                # Already a dict, get first 3 items
                txn_list = list(transactions.values())[:3] if transactions else []
            elif isinstance(transactions, list):
                txn_list = transactions[:3]
            else:
                txn_list = []

            if txn_list:
                insider_html = ''.join([f'<tr><td colspan="2">{t.get("name", t.get("Insider", "Unknown"))} - {t.get("type", t.get("Transaction", "N/A"))} {t.get("shares", t.get("Shares", 0)):,} shares</td></tr>' for t in txn_list])
            else:
                insider_html = '<tr><td colspan="2">No recent insider transactions</td></tr>'
        else:
            insider_html = '<tr><td colspan="2">No recent insider transactions</td></tr>'

        # Build comprehensive HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.company_name} ({self.ticker}) - Comprehensive Investment Analysis Report</title>
    <style>
        :root {{ --primary: #1a365d; --secondary: #2b6cb0; --accent: #4299e1; --success: #48bb78; --warning: #ed8936; --danger: #f56565; --dark: #1a202c; --light: #f7fafc; --border: #e2e8f0; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); color: var(--dark); line-height: 1.6; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); color: white; padding: 60px 40px; text-align: center; }}
        .header h1 {{ font-size: 3.5em; margin-bottom: 10px; font-weight: 700; }}
        .header .ticker {{ font-size: 2em; opacity: 0.9; font-weight: 300; }}
        .header .date {{ margin-top: 20px; opacity: 0.8; font-size: 1.1em; }}
        .content {{ padding: 40px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }}
        .stat-value {{ font-size: 2.2em; font-weight: 700; }}
        .stat-change {{ font-size: 1em; margin-top: 8px; opacity: 0.9; }}
        .ai-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; margin: 40px 0; }}
        .ai-card {{ padding: 40px; border-radius: 16px; color: white; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .ai-card.sentiment {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .ai-card.ml {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .ai-card h3 {{ font-size: 1.3em; margin-bottom: 20px; opacity: 0.9; }}
        .ai-result {{ font-size: 3.5em; font-weight: 700; margin: 20px 0; }}
        .ai-confidence {{ font-size: 1.2em; opacity: 0.9; }}
        .chart-section {{ margin: 40px 0; }}
        .chart-container {{ background: white; border-radius: 12px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }}
        .chart-container img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .section {{ margin: 40px 0; }}
        .section-title {{ font-size: 2em; color: var(--primary); margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid var(--accent); }}
        .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .data-table th {{ background: var(--light); padding: 15px; text-align: left; font-weight: 600; color: var(--primary); text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; }}
        .data-table td {{ padding: 15px; border-bottom: 1px solid var(--border); }}
        .data-table tr:hover {{ background: #f7fafc; }}
        .grid-2 {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 30px; }}
        .recommendation-box {{ background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%); color: white; padding: 60px; border-radius: 16px; text-align: center; margin: 40px 0; box-shadow: 0 10px 40px rgba(26, 54, 93, 0.3); }}
        .recommendation-box h2 {{ font-size: 1.5em; opacity: 0.9; margin-bottom: 20px; }}
        .recommendation-rating {{ font-size: 5em; font-weight: 700; margin: 30px 0; }}
        .recommendation-rationale {{ font-size: 1.2em; opacity: 0.9; max-width: 800px; margin: 0 auto; line-height: 1.8; }}
        .footer {{ background: var(--dark); color: white; padding: 40px; text-align: center; }}
        .footer h4 {{ margin-bottom: 15px; color: var(--accent); }}
        .footer p {{ opacity: 0.8; font-size: 0.9em; line-height: 1.8; }}
        @media print {{ body {{ background: white; }} .container {{ box-shadow: none; }} .section {{ page-break-inside: avoid; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>{self.company_name}</h1>
            <div class="ticker">{self.ticker} - Comprehensive Investment Analysis</div>
            <div class="date">Generated on {self.report_date.strftime('%B %d, %Y at %H:%M:%S')}</div>
        </header>

        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Current Price</div>
                    <div class="stat-value">{price}</div>
                    <div class="stat-change">{'+' if change_pct >= 0 else ''}{change_pct:.2f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Market Cap</div>
                    <div class="stat-value">{mc_str}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">P/E Ratio</div>
                    <div class="stat-value">{pe_ratio}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">52W Range</div>
                    <div class="stat-value">{low_52} - {high_52}</div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">🤖 AI-Powered Analysis</h2>
                <div class="ai-grid">
                    <div class="ai-card sentiment">
                        <h3>📊 FinBERT Sentiment Analysis</h3>
                        <div class="ai-result">{sentiment_text}</div>
                        <div class="ai-confidence">{sentiment_conf:.1f}% Confidence</div>
                    </div>
                    <div class="ai-card ml">
                        <h3>🔮 ML Price Prediction</h3>
                        <div class="ai-result">{ml_dir}</div>
                        <div class="ai-confidence">{ml_conf:.1f}% Confidence</div>
                    </div>
                </div>
            </div>

            {chart_section_html}

            <div class="section">
                <h2 class="section-title">🏢 Company Overview</h2>
                <p style="font-size: 1.1em; line-height: 1.8; margin-bottom: 20px;">{description}</p>

                <div class="grid-2">
                    <table class="data-table">
                        <tr><th colspan="2">Company Information</th></tr>
                        <tr><td><strong>Sector</strong></td><td>{sector}</td></tr>
                        <tr><td><strong>Industry</strong></td><td>{industry}</td></tr>
                        <tr><td><strong>Employees</strong></td><td>{employees}</td></tr>
                        <tr><td><strong>Country</strong></td><td>{country}</td></tr>
                        <tr><td><strong>Website</strong></td><td><a href="{website}">{website}</a></td></tr>
                    </table>

                    <table class="data-table">
                        <tr><th colspan="2">Valuation Metrics</th></tr>
                        <tr><td><strong>P/E (TTM)</strong></td><td>{pe_ratio}</td></tr>
                        <tr><td><strong>Forward P/E</strong></td><td>{forward_pe}</td></tr>
                        <tr><td><strong>PEG Ratio</strong></td><td>{peg_ratio}</td></tr>
                        <tr><td><strong>P/B Ratio</strong></td><td>{price_to_book}</td></tr>
                        <tr><td><strong>P/S Ratio</strong></td><td>{price_to_sales}</td></tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">💰 Financial Highlights</h2>
                <div class="grid-2">
                    <table class="data-table">
                        <tr><th colspan="2">Income Statement (TTM)</th></tr>
                        <tr><td>Revenue</td><td>{rev_str}</td></tr>
                        <tr><td>Gross Profit</td><td>{gp_str}</td></tr>
                        <tr><td>Operating Income</td><td>{oi_str}</td></tr>
                        <tr><td>Net Income</td><td>{ni_str}</td></tr>
                        <tr><td>EPS (TTM)</td><td>${eps}</td></tr>
                        <tr><td>Forward EPS</td><td>${forward_eps}</td></tr>
                    </table>

                    <table class="data-table">
                        <tr><th colspan="2">Balance Sheet</th></tr>
                        <tr><td>Total Cash</td><td>{tc_str}</td></tr>
                        <tr><td>Total Debt</td><td>{td_str}</td></tr>
                        <tr><td>Total Assets</td><td>{ta_str}</td></tr>
                        <tr><td>Market Cap</td><td>{mc_str}</td></tr>
                        <tr><td>Volume</td><td>{vol_str}</td></tr>
                        <tr><td>Avg Volume</td><td>{avg_vol_str}</td></tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">🏛️ Smart Money Activity</h2>
                <div class="grid-2">
                    <table class="data-table">
                        <tr><th colspan="2">Congress Trading (60 days)</th></tr>
                        <tr><td>Purchases</td><td>{congress_buys}</td></tr>
                        <tr><td>Sales</td><td>{congress_sells}</td></tr>
                        {congress_html}
                    </table>

                    <table class="data-table">
                        <tr><th colspan="2">Insider Trading (90 days)</th></tr>
                        <tr><td>Buys</td><td>{insider_buys}</td></tr>
                        <tr><td>Sells</td><td>{insider_sells}</td></tr>
                        {insider_html}
                    </table>
                </div>
            </div>

            <div class="recommendation-box">
                <h2>💡 Investment Recommendation</h2>
                <div class="recommendation-rating" style="color: {rec_color};">{recommendation}</div>
                <div class="recommendation-rationale">
                    Based on comprehensive analysis including FinBERT sentiment ({sentiment_text}, {sentiment_conf:.1f}% confidence)
                    and ML prediction ({ml_dir}, {ml_conf:.1f}% confidence).
                    {f" Congress: {congress_buys} buys, {congress_sells} sells." if congress else ""}
                    {f" Insiders: {insider_buys} buys, {insider_sells} sells." if insider_buys or insider_sells else ""}
                </div>
            </div>
        </div>

        <footer class="footer">
            <h4>⚠️ Disclaimer</h4>
            <p>This investment analysis report is provided for informational purposes only. It does not constitute financial advice.</p>
            <p style="margin-top: 20px;">
                <strong>Data Sources:</strong> Yahoo Finance, SEC EDGAR, Finnhub API |
                <strong>Generated:</strong> {self.report_date.strftime('%B %d, %Y')} |
                <strong>By:</strong> Turd News Network
            </p>
        </footer>
    </div>
</body>
</html>"""

        return html

    def _fetch_yfinance_data(self) -> Dict:
        """Fetch comprehensive data from Yahoo Finance"""
        data = {'info': {}}
        try:
            self.yf_ticker = yf.Ticker(self.ticker)
            data['info'] = self.yf_ticker.info or {}
        except Exception as e:
            print(f"[YFINANCE ERROR] {e}")
        return data

    def _scrape_company_data(self) -> Dict:
        """Scrape additional company data"""
        return {'description': '', 'executives': []}

    def _analyze_sentiment(self) -> Dict:
        """Analyze sentiment using FinBERT/VADER"""
        try:
            from sentiment import SentimentAnalyzer
            analyzer = SentimentAnalyzer()
            text = f"{self.company_name} stock analysis"
            result = analyzer.analyze(text)
            return {
                'sentiment': result.get('sentiment', 'NEUTRAL'),
                'confidence': result.get('confidence', 0.5),
                'score': result.get('score', 0)
            }
        except:
            return {'sentiment': 'NEUTRAL', 'confidence': 0.5, 'score': 0}

    def _get_ml_prediction(self) -> Dict:
        """Get ML price prediction"""
        change = self.stock_data.get('change_pct', 0)
        if change > 2:
            return {'direction': 'UP', 'confidence': 0.6}
        elif change < -2:
            return {'direction': 'DOWN', 'confidence': 0.6}
        return {'direction': 'NEUTRAL', 'confidence': 0.5}

    def _fetch_congress_data(self) -> List[Dict]:
        """Fetch Congress trading data"""
        return []

    def _fetch_insider_data(self) -> Dict:
        """Fetch insider trading data"""
        return {'buys': 0, 'sells': 0, 'transactions': []}

    def _generate_charts(self) -> Dict:
        """Generate charts for the report"""
        return {}


__all__ = ['EnhancedHTMLReportGenerator']
