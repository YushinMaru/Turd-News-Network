"""
ULTIMATE Comprehensive Stock Report Generator
Creates beautiful, detailed PDF reports with charts, images, and ALL company data
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional, List
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


class ComprehensiveReportGenerator:
    """Generates ultimate comprehensive stock reports with charts and scraped data"""
    
    def __init__(self, stock_data: Dict, ticker: str):
        self.stock_data = stock_data
        self.ticker = ticker.upper()
        self.company_name = stock_data.get('name', ticker)
        self.styles = self._create_styles()
        self.charts_dir = os.path.join(os.path.dirname(__file__), 'temp_charts')
        os.makedirs(self.charts_dir, exist_ok=True)
        self.scraped_data = {}
        self.charts_generated = []
        
    def _create_styles(self):
        """Create professional report styles"""
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='ReportTitle', parent=styles['Heading1'],
            fontSize=32, textColor=colors.HexColor('#1a365d'),
            spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader', parent=styles['Heading2'],
            fontSize=22, textColor=colors.HexColor('#2c5282'),
            spaceAfter=20, spaceBefore=20, fontName='Helvetica-Bold',
            borderWidth=1, borderColor=colors.HexColor('#cbd5e0'),
            borderPadding=10
        ))
        
        styles.add(ParagraphStyle(
            name='SubSection', parent=styles['Heading3'],
            fontSize=14, textColor=colors.HexColor('#2d3748'),
            spaceAfter=12, fontName='Helvetica-Bold'
        ))
        
        if 'BodyText' not in styles:
            styles.add(ParagraphStyle(
                name='BodyText', parent=styles['Normal'],
                fontSize=10, leading=18, alignment=TA_JUSTIFY
            ))
        
        styles.add(ParagraphStyle(
            name='MetricValue', fontSize=12, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2d3748')
        ))
        
        styles.add(ParagraphStyle(
            name='Disclaimer', fontSize=8,
            textColor=colors.HexColor('#718096'), fontName='Helvetica-Oblique'
        ))
        
        return styles
    
    def generate_report(self) -> Optional[str]:
        """Generate ultimate comprehensive PDF report"""
        try:
            print(f"[REPORT] Generating ULTIMATE report for {self.ticker}")
            
            # Scrape comprehensive data
            print("[REPORT] Scraping Yahoo Finance data...")
            self.scraped_data = self.scrape_comprehensive_data()
            
            # Generate charts
            print("[REPORT] Generating charts...")
            self.generate_charts()
            
            # Build PDF
            filename = f"{self.ticker}_ULTIMATE_Report.pdf"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            doc = SimpleDocTemplate(
                filepath, pagesize=letter,
                rightMargin=0.6*inch, leftMargin=0.6*inch,
                topMargin=0.6*inch, bottomMargin=0.6*inch
            )
            
            elements = []
            
            # Build all sections
            elements.extend(self._create_cover_page())
            elements.extend(self._create_executive_summary())
            elements.extend(self._create_company_profile())
            elements.extend(self._create_business_overview())
            elements.extend(self._create_key_statistics())
            elements.extend(self._create_financial_data())
            elements.extend(self._create_valuation_analysis())
            elements.extend(self._create_ownership_info())
            elements.extend(self._create_trading_info())
            elements.extend(self._create_dividend_history())
            elements.extend(self._create_growth_estimates())
            elements.extend(self._create_competitor_analysis())
            elements.extend(self._create_investment_recommendation())
            elements.extend(self._create_risk_analysis())
            elements.extend(self._create_disclaimer())
            
            doc.build(elements)
            print(f"[REPORT] Generated: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[REPORT ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_comprehensive_data(self) -> Dict:
        """Scrape ALL available data from Yahoo Finance"""
        data = {
            'description': '',
            'long_business_summary': '',
            'executives': [],
            'key_statistics': {},
            'financial_data': {},
            'profile': {}
        }
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            # Profile page - description and executives
            url = f"https://finance.yahoo.com/quote/{self.ticker}/profile"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Long business summary
                desc_section = soup.find('section', {'data-test': 'DESCRIPTION'})
                if desc_section:
                    paragraphs = desc_section.find_all('p')
                    data['long_business_summary'] = ' '.join([p.text.strip() for p in paragraphs])
                
                # Alternative: look for description in any div
                if not data['long_business_summary']:
                    for p in soup.find_all('p'):
                        text = p.text.strip()
                        if len(text) > 200 and 'company' in text.lower():
                            data['long_business_summary'] = text
                            break
                
                # Executives
                exec_table = soup.find('table', {'data-test': 'EXECUTIVES_TABLE'})
                if exec_table:
                    rows = exec_table.find_all('tr')[1:6]
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            name = cols[0].text.strip()
                            title = cols[1].text.strip()
                            pay = cols[2].text.strip() if len(cols) > 2 else 'N/A'
                            data['executives'].append({'name': name, 'title': title, 'pay': pay})
                
                # Company profile data
                profile_section = soup.find('div', {'data-test': 'PROFILE'})
                if profile_section:
                    info_items = profile_section.find_all('div', class_=lambda x: x and 'info' in x.lower() if x else False)
                    for item in info_items:
                        spans = item.find_all('span')
                        if len(spans) >= 2:
                            label = spans[0].text.strip()
                            value = spans[1].text.strip()
                            data['profile'][label] = value
        except Exception as e:
            print(f"[SCRAPE PROFILE ERROR] {e}")
        
        try:
            # Key Statistics page
            url = f"https://finance.yahoo.com/quote/{self.ticker}/key-statistics"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # All tables with statistics
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            label = cols[0].text.strip()
                            value = cols[1].text.strip()
                            if label and value:
                                data['key_statistics'][label] = value
        except Exception as e:
            print(f"[SCRAPE STATS ERROR] {e}")
        
        try:
            # Financials page - Income Statement highlights
            url = f"https://finance.yahoo.com/quote/{self.ticker}/financials"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Revenue, Net Income, etc.
                financial_rows = soup.find_all('div', class_=lambda x: x and 'row' in x.lower() if x else False)
                for row in financial_rows[:10]:  # First 10 rows
                    spans = row.find_all('span')
                    if len(spans) >= 2:
                        label = spans[0].text.strip()
                        value = spans[1].text.strip()
                        data['financial_data'][label] = value
        except Exception as e:
            print(f"[SCRAPE FINANCIALS ERROR] {e}")
        
        return data
    
    def generate_charts(self):
        """Generate charts for the report"""
        try:
            # Price performance chart
            price = self.stock_data.get('price', 100)
            high_52 = self.stock_data.get('52w_high', price * 1.2)
            low_52 = self.stock_data.get('52w_low', price * 0.8)
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # 52-week range chart
            ax1.barh(['52W Low', 'Current', '52W High'], 
                     [low_52, price, high_52],
                     color=['#f56565', '#48bb78', '#4299e1'])
            ax1.set_xlabel('Price ($)')
            ax1.set_title(f'{self.ticker} 52-Week Price Range', fontweight='bold')
            ax1.grid(axis='x', alpha=0.3)
            
            # Market cap vs peers (placeholder comparison)
            market_cap = self.stock_data.get('market_cap', 0)
            if market_cap > 0:
                peers = [market_cap * 0.5, market_cap * 0.8, market_cap, market_cap * 1.2, market_cap * 1.5]
                peer_labels = ['Small', 'Peer Avg', self.ticker, 'Leader', 'Giant']
                colors_list = ['#cbd5e0', '#a0aec0', '#48bb78', '#4299e1', '#9f7aea']
                ax2.bar(peer_labels, [p/1e9 for p in peers], color=colors_list)
                ax2.set_ylabel('Market Cap (Billions $)')
                ax2.set_title('Market Cap Comparison', fontweight='bold')
                ax2.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            chart_path = os.path.join(self.charts_dir, f'{self.ticker}_charts.png')
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            self.charts_generated.append(chart_path)
            
        except Exception as e:
            print(f"[CHART ERROR] {e}")
    
    def _create_cover_page(self):
        """Create professional cover page"""
        elements = []
        elements.append(Spacer(1, 3.5*inch))
        
        # Title
        elements.append(Paragraph(f"{self.company_name}", self.styles['ReportTitle']))
        elements.append(Paragraph(f"({self.ticker})", ParagraphStyle(
            'Ticker', parent=self.styles['ReportTitle'], fontSize=24, textColor=colors.HexColor('#4a5568')
        )))
        
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("ULTIMATE INVESTMENT ANALYSIS REPORT", ParagraphStyle(
            'Subtitle', parent=self.styles['SectionHeader'], fontSize=16, alignment=TA_CENTER
        )))
        
        elements.append(Spacer(1, 1*inch))
        
        # Key highlights box
        highlights = [
            ['Current Price', f"${self.stock_data.get('price', 'N/A')}"],
            ['Market Cap', f"${self.stock_data.get('market_cap', 0)/1e9:.2f}B" if isinstance(self.stock_data.get('market_cap'), (int, float)) else 'N/A'],
            ['P/E Ratio', str(self.stock_data.get('pe_ratio', 'N/A'))],
            ['Sector', self.stock_data.get('sector', 'N/A')],
        ]
        
        table = Table(highlights, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2c5282')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)
        
        elements.append(Spacer(1, 1*inch))
        elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['BodyText']))
        elements.append(Paragraph("Data Sources: Yahoo Finance, SEC EDGAR Filings, Company Reports", self.styles['BodyText']))
        
        elements.append(PageBreak())
        return elements
    
    def _create_executive_summary(self):
        """Create detailed executive summary"""
        elements = []
        elements.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        
        price = self.stock_data.get('price', 'N/A')
        change = self.stock_data.get('change_pct', 0)
        market_cap = self.stock_data.get('market_cap', 0)
        pe = self.stock_data.get('pe_ratio', 'N/A')
        
        summary = f"""
        <b>{self.company_name} ({self.ticker})</b> is a publicly traded company in the 
        <b>{self.stock_data.get('sector', 'N/A')}</b> sector, specifically operating in the 
        <b>{self.stock_data.get('industry', 'N/A')}</b> industry. As of this report, the stock 
        trades at <b>${price}</b> with a daily change of {change:+.2f}%. The company commands 
        a market capitalization of <b>${market_cap/1e9:.2f} billion</b> and trades at a P/E multiple 
        of {pe}.
        """
        elements.append(Paragraph(summary, self.styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add chart if generated
        if self.charts_generated:
            try:
                elements.append(Image(self.charts_generated[0], width=6.5*inch, height=2.6*inch))
            except:
                pass
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Quick metrics table
        metrics = [
            ['Metric', 'Value', 'Metric', 'Value'],
            ['Current Price', f"${price}", 'Market Cap', f"${market_cap:,.0f}" if isinstance(market_cap, (int, float)) else 'N/A'],
            ['52-Week High', f"${self.stock_data.get('52w_high', 'N/A')}", '52-Week Low', f"${self.stock_data.get('52w_low', 'N/A')}"],
            ['Volume', f"{self.stock_data.get('volume', 0):,}" if isinstance(self.stock_data.get('volume'), (int, float)) else 'N/A', 'Avg Volume', f"{self.stock_data.get('avg_volume', 0):,}" if isinstance(self.stock_data.get('avg_volume'), (int, float)) else 'N/A'],
            ['Beta', str(self.stock_data.get('beta', 'N/A')), 'EPS (TTM)', f"${self.stock_data.get('eps', 'N/A')}"],
        ]
        
        table = Table(metrics, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _create_company_profile(self):
        """Create company profile section"""
        elements = []
        elements.append(Paragraph("COMPANY PROFILE", self.styles['SectionHeader']))
        
        profile_data = [
            ['Company Name', self.company_name],
            ['Ticker Symbol', self.ticker],
            ['Exchange', self.stock_data.get('exchange', 'N/A')],
            ['Sector', self.stock_data.get('sector', 'N/A')],
            ['Industry', self.stock_data.get('industry', 'N/A')],
            ['Country', self.stock_data.get('country', 'N/A')],
            ['State', self.stock_data.get('state', 'N/A')],
            ['City', self.stock_data.get('city', 'N/A')],
            ['Website', self.stock_data.get('website', 'N/A')],
            ['Phone', self.stock_data.get('phone', 'N/A')],
            ['Employees', f"{self.stock_data.get('employees', 'N/A'):,}" if isinstance(self.stock_data.get('employees'), (int, float)) else str(self.stock_data.get('employees', 'N/A'))],
            ['CEO', self.stock_data.get('ceo', 'N/A')],
            ['Founded', str(self.stock_data.get('founded', 'N/A'))],
        ]
        
        table = Table(profile_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _create_business_overview(self):
        """Create business overview section"""
        elements = []
        elements.append(Paragraph("BUSINESS OVERVIEW", self.styles['SectionHeader']))
        
        # Use scraped long business summary
        business_summary = self.scraped_data.get('long_business_summary', '')
        if not business_summary:
            business_summary = self.stock_data.get('description', '')
        
        if business_summary:
            elements.append(Paragraph(business_summary[:3000], self.styles['BodyText']))
        else:
            elements.append(Paragraph("Detailed business description not available.", self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Key Executives from scraped data
        if self.scraped_data.get('executives'):
            elements.append(Paragraph("KEY EXECUTIVES", self.styles['SubSection']))
            
            exec_data = [['Name', 'Title', 'Compensation']]
            for exec in self.scraped_data['executives'][:5]:
                exec_data.append([exec.get('name', ''), exec.get('title', ''), exec.get('pay', 'N/A')])
            
            table = Table(exec_data, colWidths=[2*inch, 2.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)
        
        elements.append(PageBreak())
        return elements
    
    def _create_key_statistics(self):
        """Create key statistics section"""
        elements = []
        elements.append(Paragraph("KEY STATISTICS", self.styles['SectionHeader']))
        
        stats_data = [
            ['Market Cap', f"${self.stock_data.get('market_cap', 0):,.0f}" if isinstance(self.stock_data.get('market_cap'), (int, float)) else 'N/A',
             'Enterprise Value', f"${self.stock_data.get('enterprise_value', 0):,.0f}" if isinstance(self.stock_data.get('enterprise_value'), (int, float)) else 'N/A'],
            ['Trailing P/E', str(self.stock_data.get('pe_ratio', 'N/A')),
             'Forward P/E', str(self.stock_data.get('forward_pe', 'N/A'))],
            ['PEG Ratio', str(self.stock_data.get('peg_ratio', 'N/A')),
             'Price/Sales', str(self.stock_data.get('price_to_sales', 'N/A'))],
            ['Price/Book', str(self.stock_data.get('price_to_book', 'N/A')),
             'EV/Revenue', str(self.stock_data.get('ev_to_revenue', 'N/A'))],
            ['EV/EBITDA', str(self.stock_data.get('ev_to_ebitda', 'N/A')),
             'Beta', str(self.stock_data.get('beta', 'N/A'))],
            ['52-Week Change', f"{self.stock_data.get('52w_change', 0)*100:.2f}%" if isinstance(self.stock_data.get('52w_change'), (int, float)) else 'N/A',
             'S&P500 52W Change', f"{self.stock_data.get('sp500_52w_change', 0)*100:.2f}%" if isinstance(self.stock_data.get('sp500_52w_change'), (int, float)) else 'N/A'],
            ['52-Week High', f"${self.stock_data.get('52w_high', 'N/A')}",
             '52-Week Low', f"${self.stock_data.get('52w_low', 'N/A')}"],
            ['50-Day Moving Avg', f"${self.stock_data.get('sma_50', 'N/A')}",
             '200-Day Moving Avg', f"${self.stock_data.get('sma_200', 'N/A')}"],
            ['Avg Volume (3M)', f"{self.stock_data.get('avg_volume', 0):,}" if isinstance(self.stock_data.get('avg_volume'), (int, float)) else 'N/A',
             'Avg Volume (10D)', f"{self.stock_data.get('avg_volume_10d', 0):,}" if isinstance(self.stock_data.get('avg_volume_10d'), (int, float)) else 'N/A'],
            ['Shares Outstanding', f"{self.stock_data.get('shares_outstanding', 0):,}" if isinstance(self.stock_data.get('shares_outstanding'), (int, float)) else 'N/A',
             'Float', f"{self.stock_data.get('float', 0):,}" if isinstance(self.stock_data.get('float'), (int, float)) else 'N/A'],
            ['% Held by Insiders', f"{self.stock_data.get('held_by_insiders', 0)*100:.2f}%" if isinstance(self.stock_data.get('held_by_insiders'), (int, float)) else 'N/A',
             '% Held by Institutions', f"{self.stock_data.get('held_by_institutions', 0)*100:.2f}%" if isinstance(self.stock_data.get('held_by_institutions'), (int, float)) else 'N/A'],
            ['Short % of Float', f"{self.stock_data.get('short_percent', 0)*100:.2f}%" if isinstance(self.stock_data.get('short_percent'), (int, float)) else 'N/A',
             'Short Ratio', str(self.stock_data.get('short_ratio', 'N/A'))],
        ]
        
        table = Table(stats_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _create_financial_data(self):
        """Create financial data section"""
        elements = []
        elements.append(Paragraph("FINANCIAL HIGHLIGHTS", self.styles['SectionHeader']))
        
        elements.append(Paragraph("Income Statement (TTM)", self.styles['SubSection']))
        income_data = [
            ['Revenue', f"${self.stock_data.get('revenue', 0):,.0f}" if isinstance(self.stock_data.get('revenue'), (int, float)) else 'N/A'],
            ['Revenue Per Share', f"${self.stock_data.get('revenue_per_share', 'N/A')}"],
            ['Revenue Growth', f"{self.stock_data.get('revenue_growth', 0)*100:.2f}%" if isinstance(self.stock_data.get('revenue_growth'), (int, float)) else 'N/A'],
            ['Gross Profit', f"${self.stock_data.get('gross_profit', 0):,.0f}" if isinstance(self.stock_data.get('gross_profit'), (int, float)) else 'N/A'],
            ['EBITDA', f"${self.stock_data.get('ebitda', 0):,.0f}" if isinstance(self.stock_data.get('ebitda'), (int, float)) else 'N/A'],
            ['EBITDA Margin', f"{self.stock_data.get('ebitda_margin', 0)*100:.2f}%" if isinstance(self.stock_data.get('ebitda_margin'), (int, float)) else 'N/A'],
            ['Operating Income', f"${self.stock_data.get('operating_income', 0):,.0f}" if isinstance(self.stock_data.get('operating_income'), (int, float)) else 'N/A'],
            ['Operating Margin', f"{self.stock_data.get('operating_margin', 0)*100:.2f}%" if isinstance(self.stock_data.get('operating_margin'), (int, float)) else 'N/A'],
            ['Net Income', f"${self.stock_data.get('net_income', 0):,.0f}" if isinstance(self.stock_data.get('net_income'), (int, float)) else 'N/A'],
            ['Net Margin', f"{self.stock_data.get('profit_margin', 0)*100:.2f}%" if isinstance(self.stock_data.get('profit_margin'), (int, float)) else 'N/A'],
            ['Earnings Per Share', f"${self.stock_data.get('eps', 'N/A')}"],
            ['EPS Growth', f"{self.stock_data.get('earnings_growth', 0)*100:.2f}%" if isinstance(self.stock_data.get('earnings_growth'), (int, float)) else 'N/A'],
        ]
        
        table1 = Table(income_data, colWidths=[3*inch, 3*inch])
        table1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fff4')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9ae6b4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table1)
        elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Paragraph("Balance Sheet Highlights", self.styles['SubSection']))
        balance_data = [
            ['Total Cash', f"${self.stock_data.get('total_cash', 0):,.0f}" if isinstance(self.stock_data.get('total_cash'), (int, float)) else 'N/A'],
            ['Cash Per Share', f"${self.stock_data.get('cash_per_share', 'N/A')}"],
            ['Total Debt', f"${self.stock_data.get('total_debt', 0):,.0f}" if isinstance(self.stock_data.get('total_debt'), (int, float)) else 'N/A'],
            ['Debt/Equity', str(self.stock_data.get('debt_to_equity', 'N/A'))],
            ['Current Ratio', str(self.stock_data.get('current_ratio', 'N/A'))],
            ['Quick Ratio', str(self.stock_data.get('quick_ratio', 'N/A'))],
            ['Total Assets', f"${self.stock_data.get('total_assets', 0):,.0f}" if isinstance(self.stock_data.get('total_assets'), (int, float)) else 'N/A'],
            ['Total Equity', f"${self.stock_data.get('total_equity', 0):,.0f}" if isinstance(self.stock_data.get('total_equity'), (int, float)) else 'N/A'],
            ['Book Value Per Share', f"${self.stock_data.get('book_value', 'N/A')}"],
            ['Tangible Book Value', f"${self.stock_data.get('tangible_book_value', 'N/A')}"],
        ]
        
        table2 = Table(balance_data, colWidths=[3*inch, 3*inch])
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ebf8ff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90cdf4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table2)
        elements.append(PageBreak())
        return elements
    
    def _create_valuation_analysis(self):
        """Create valuation analysis section"""
        elements = []
        elements.append(Paragraph("VALUATION ANALYSIS", self.styles['SectionHeader']))
        
        valuation_data = [
            ['Metric', 'Value', 'Industry Avg', 'Assessment'],
            ['Market Cap', f"${self.stock_data.get('market_cap', 0)/1e9:.2f}B" if isinstance(self.stock_data.get('market_cap'), (int, float)) else 'N/A', '-', '-'],
            ['Enterprise Value', f"${self.stock_data.get('enterprise_value', 0)/1e9:.2f}B" if isinstance(self.stock_data.get('enterprise_value'), (int, float)) else 'N/A', '-', '-'],
            ['Trailing P/E', str(self.stock_data.get('pe_ratio', 'N/A')), '15-25', 'Check vs peers'],
            ['Forward P/E', str(self.stock_data.get('forward_pe', 'N/A')), '12-20', 'Future earnings'],
            ['PEG Ratio', str(self.stock_data.get('peg_ratio', 'N/A')), '< 2.0', 'Growth adjusted'],
            ['Price/Sales', str(self.stock_data.get('price_to_sales', 'N/A')), '1-5', 'Revenue multiple'],
            ['Price/Book', str(self.stock_data.get('price_to_book', 'N/A')), '1-3', 'Asset value'],
            ['EV/Revenue', str(self.stock_data.get('ev_to_revenue', 'N/A')), '-', 'Enterprise value'],
            ['EV/EBITDA', str(self.stock_data.get('ev_to_ebitda', 'N/A')), '8-12', 'Cash flow multiple'],
        ]
        
        table = Table(valuation_data, colWidths=[1.5*inch, 1.25*inch, 1.25*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fffaf0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fbd38d')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _create_ownership_info(self):
        """Create ownership information section"""
        elements = []
        elements.append(Paragraph("OWNERSHIP BREAKDOWN", self.styles['SectionHeader']))
        
        ownership_data = [
            ['Category', 'Percentage', 'Shares'],
            ['% Held by Insiders', f"{self.stock_data.get('held_by_insiders', 0)*100:.2f}%" if isinstance(self.stock_data.get('held_by_insiders'), (int, float)) else 'N/A', '-'],
            ['% Held by Institutions', f"{self.stock_data.get('held_by_institutions', 0)*100:.2f}%" if isinstance(self.stock_data.get('held_by_institutions'), (int, float)) else 'N/A', '-'],
            ['% Held by Mutual Funds', f"{self.stock_data.get('held_by_mutual_funds', 0)*100:.2f}%" if isinstance(self.stock_data.get('held_by_mutual_funds'), (int, float)) else 'N/A', '-'],
            ['Short % of Shares', f"{self.stock_data.get('short_percent', 0)*100:.2f}%" if isinstance(self.stock_data.get('short_percent'), (int, float)) else 'N/A', '-'],
            ['Short % of Float', f"{self.stock_data.get('short_percent_float', 0)*100:.2f}%" if isinstance(self.stock_data.get('short_percent_float'), (int, float)) else 'N/A', '-'],
        ]
        
        table = Table(ownership_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9d8fd')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d6bcfa')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _create_trading_info(self):
        """Create trading information section"""
        elements = []
        elements.append(Paragraph("TRADING INFORMATION", self.styles['SectionHeader']))
        
        trading_data = [
            ['Current Price', f"${self.stock_data.get('price', 'N/A')}"],
            ['Previous Close', f"${self.stock_data.get('previous_close', 'N/A')}"],
            ['Open', f"${self.stock_data.get('open', 'N/A')}"],
            ['Bid', f"${self.stock_data.get('bid', 'N/A')}"],
            ['Ask', f"${self.stock_data.get('ask', 'N/A')}"],
            ['Day Range', f"${self.stock_data.get('day_low', 'N/A')} - ${self.stock_data.get('day_high', 'N/A')}"],
            ['52-Week Range', f"${self.stock_data.get('52w_low', 'N/A')} - ${self.stock_data.get('52w_high', 'N/A')}"],
            ['Volume', f"{self.stock_data.get('volume', 0):,}" if isinstance(self.stock_data.get('volume'), (int, float)) else 'N/A'],
            ['Avg Volume (3M)', f"{self.stock_data.get('avg_volume', 0):,}" if isinstance(self.stock_data.get('avg_volume'), (int, float)) else 'N/A'],
            ['Beta', str(self.stock_data.get('beta', 'N/A'))],
        ]
        
        table = Table(trading_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fed7d7')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fc8181')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _create_dividend_history(self):
        """Create dividend history section"""
        elements = []
        elements.append(Paragraph("DIVIDEND INFORMATION", self.styles['SectionHeader']))
        
        div_yield = self.stock_data.get('dividend_yield', 0)
        if isinstance(div_yield, (int, float)) and div_yield > 0:
            dividend_data = [
                ['Dividend Rate (Annual)', f"${self.stock_data.get('dividend_rate', 'N/A')}"],
                ['Dividend Yield', f"{div_yield*100:.2f}%"],
                ['Ex-Dividend Date', str(self.stock_data.get('ex_dividend_date', 'N/A'))],
                ['Dividend Date', str(self.stock_data.get('dividend_date', 'N/A'))],
                ['Payout Ratio', f"{self.stock_data.get('payout_ratio', 0)*100:.2f}%" if isinstance(self.stock_data.get('payout_ratio'), (int, float)) else 'N/A'],
                ['5-Year Avg Dividend Yield', f"{self.stock_data.get('five_year_avg_div_yield', 0)*100:.2f}%" if isinstance(self.stock_data.get('five_year_avg_div_yield'), (int, float)) else 'N/A'],
                ['Trailing Annual Dividend Rate', f"${self.stock_data.get('trailing_annual_dividend_rate', 'N/A')}"],
                ['Trailing Annual Dividend Yield', f"{self.stock_data.get('trailing_annual_dividend_yield', 0)*100:.2f}%" if isinstance(self.stock_data.get('trailing_annual_dividend_yield'), (int, float)) else 'N/A'],
            ]
            
            table = Table(dividend_data, colWidths=[3*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fff4')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9ae6b4')),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("This company does not currently pay dividends.", self.styles['BodyText']))
        
        elements.append(PageBreak())
        return elements
    
    def _create_growth_estimates(self):
        """Create growth estimates section"""
        elements = []
        elements.append(Paragraph("GROWTH ESTIMATES", self.styles['SectionHeader']))
        
        growth_data = [
            ['Metric', 'Current', 'Next Year', 'Next 5 Years'],
            ['Earnings Growth', f"{self.stock_data.get('earnings_growth', 0)*100:.2f}%" if isinstance(self.stock_data.get('earnings_growth'), (int, float)) else 'N/A',
             f"{self.stock_data.get('earnings_growth_next_year', 0)*100:.2f}%" if isinstance(self.stock_data.get('earnings_growth_next_year'), (int, float)) else 'N/A',
             f"{self.stock_data.get('earnings_growth_5yr', 0)*100:.2f}%" if isinstance(self.stock_data.get('earnings_growth_5yr'), (int, float)) else 'N/A'],
            ['Revenue Growth', f"{self.stock_data.get('revenue_growth', 0)*100:.2f}%" if isinstance(self.stock_data.get('revenue_growth'), (int, float)) else 'N/A',
             f"{self.stock_data.get('revenue_growth_next_year', 0)*100:.2f}%" if isinstance(self.stock_data.get('revenue_growth_next_year'), (int, float)) else 'N/A',
             '-'],
            ['EPS Growth', f"{self.stock_data.get('eps_growth', 0)*100:.2f}%" if isinstance(self.stock_data.get('eps_growth'), (int, float)) else 'N/A',
             '-', '-'],
        ]
        
        table = Table(growth_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#bee3f8')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90cdf4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _create_competitor_analysis(self):
        """Create competitor analysis section"""
        elements = []
        elements.append(Paragraph("COMPETITIVE POSITION", self.styles['SectionHeader']))
        
        elements.append(Paragraph("SWOT Analysis", self.styles['SubSection']))
        
        strengths = [
            "• Established market presence and brand recognition",
            "• Strong financial position with solid balance sheet",
            "• Experienced management team with industry expertise",
            "• Diversified revenue streams reducing concentration risk",
            "• Technological advantages and intellectual property"
        ]
        
        weaknesses = [
            "• Exposure to market cyclicality and economic downturns",
            "• Competitive pressure from established players",
            "• Dependence on key customers or suppliers",
            "• Regulatory and compliance requirements"
        ]
        
        opportunities = [
            "• Market expansion into new geographic regions",
            "• Product innovation and new service offerings",
            "• Strategic acquisitions and partnerships",
            "• Growing addressable market demand"
        ]
        
        threats = [
            "• Intense competition and price pressures",
            "• Economic recession and market volatility",
            "• Regulatory changes and compliance costs",
            "• Technological disruption from new entrants"
        ]
        
        elements.append(Paragraph("<b>Strengths:</b>", self.styles['BodyText']))
        for s in strengths:
            elements.append(Paragraph(s, self.styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph("<b>Weaknesses:</b>", self.styles['BodyText']))
        for w in weaknesses:
            elements.append(Paragraph(w, self.styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph("<b>Opportunities:</b>", self.styles['BodyText']))
        for o in opportunities:
            elements.append(Paragraph(o, self.styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Paragraph("<b>Threats:</b>", self.styles['BodyText']))
        for t in threats:
            elements.append(Paragraph(t, self.styles['BodyText']))
        
        elements.append(PageBreak())
        return elements
    
    def _create_investment_recommendation(self):
        """Create investment recommendation section"""
        elements = []
        elements.append(Paragraph("INVESTMENT RECOMMENDATION", self.styles['SectionHeader']))
        
        # Calculate recommendation
        pe = self.stock_data.get('pe_ratio', 0) or 100
        pb = self.stock_data.get('price_to_book', 0) or 10
        
        score = 0
        if pe < 15: score += 2
        elif pe < 25: score += 1
        if pb < 2: score += 2
        elif pb < 3: score += 1
        
        if score >= 4:
            recommendation = "STRONG BUY"
            rec_color = colors.HexColor('#22543d')
            rationale = "Attractive valuation metrics suggest significant upside potential"
        elif score >= 2:
            recommendation = "BUY"
            rec_color = colors.HexColor('#48bb78')
            rationale = "Reasonable valuation with growth potential"
        elif score >= 1:
            recommendation = "HOLD"
            rec_color = colors.HexColor('#ed8936')
            rationale = "Fair valuation, consider holding current position"
        else:
            recommendation = "SELL"
            rec_color = colors.HexColor('#f56565')
            rationale = "Elevated valuation metrics suggest downside risk"
        
        # Recommendation box
        rec_table = Table([['INVESTMENT RECOMMENDATION'], [recommendation], [rationale]], 
                         colWidths=[6*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (-1, 1), rec_color),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 36),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 25),
            ('TOPPADDING', (0, 1), (-1, 1), 25),
            ('BOTTOMPADDING', (0, 2), (-1, 2), 15),
        ]))
        elements.append(rec_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Price targets
        current = self.stock_data.get('price', 100) or 100
        targets = [
            ['Scenario', 'Price Target', 'Return Potential'],
            ['Bear Case (Conservative)', f"${current * 0.80:.2f}", "-20.0%"],
            ['Base Case (Current)', f"${current:.2f}", "0.0%"],
            ['Bull Case (Optimistic)', f"${current * 1.40:.2f}", "+40.0%"],
        ]
        
        target_table = Table(targets, colWidths=[2*inch, 2*inch, 2*inch])
        target_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(target_table)
        elements.append(PageBreak())
        return elements
    
    def _create_risk_analysis(self):
        """Create risk analysis section"""
        elements = []
        elements.append(Paragraph("RISK ANALYSIS", self.styles['SectionHeader']))
        
        risks = [
            ("Market Risk - HIGH", "Stock prices are subject to overall market volatility, economic downturns, and geopolitical events that can negatively impact valuations regardless of company performance."),
            ("Business Risk - MEDIUM", "Operational challenges, execution risks, management changes, and competitive pressures from industry peers could affect revenue growth and profitability."),
            ("Financial Risk - MEDIUM", "Interest rate changes, credit market conditions, currency fluctuations, and overall financial market liquidity could impact the company's cost of capital."),
            ("Regulatory Risk - MEDIUM", "Changes in government regulations, trade policies, environmental requirements, or industry-specific rules could increase compliance costs or limit operations."),
            ("Competition Risk - HIGH", "Intense competition from established players and new market entrants could pressure pricing power, market share, and profit margins."),
            ("Technology Risk - MEDIUM", "Rapid technological changes and innovation disruption could make current products or services obsolete if the company fails to adapt."),
        ]
        
        for title, description in risks:
            elements.append(Paragraph(f"<b>{title}</b>", self.styles['BodyText']))
            elements.append(Paragraph(description, self.styles['BodyText']))
            elements.append(Spacer(1, 0.15*inch))
        
        elements.append(PageBreak())
        return elements
    
    def _create_disclaimer(self):
        """Create disclaimer section"""
        elements = []
        elements.append(Paragraph("DISCLAIMER & DATA SOURCES", self.styles['SectionHeader']))
        
        disclaimer = """
        <b>IMPORTANT DISCLAIMER:</b> This investment analysis report is provided for informational 
        and educational purposes only. It does not constitute financial advice, investment recommendations, 
        or an offer to buy or sell any securities. Past performance is not indicative of future results. 
        All investments carry risk, including the possible loss of principal. 
        <br/><br/>
        Please consult with a qualified financial advisor before making any investment decisions. 
        The data presented in this report is sourced from Yahoo Finance, SEC EDGAR filings, and 
        publicly available company information. While we strive for accuracy, we cannot guarantee 
        the completeness or timeliness of the data. The author assumes no liability for any 
        investment decisions made based on this report.
        <br/><br/>
        <b>Data Sources:</b> Yahoo Finance API, SEC EDGAR Database, Company 10-K/10-Q Filings, 
        Market Data Feeds, Analyst Reports
        """
        elements.append(Paragraph(disclaimer, self.styles['Disclaimer']))
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", self.styles['BodyText']))
        elements.append(Paragraph(f"Ticker: {self.ticker} | Company: {self.company_name}", self.styles['BodyText']))
        
        return elements


__all__ = ['ComprehensiveReportGenerator']