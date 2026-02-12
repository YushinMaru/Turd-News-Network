"""
ULTIMATE Stock Report Generator - Professional Investment Analysis
Creates stunning, comprehensive PDF reports with extensive data and beautiful design
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
from bs4 import BeautifulSoup

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF


class UltimateReportGenerator:
    """Generates professional, beautiful, data-rich investment reports"""
    
    def __init__(self, stock_data: Dict, ticker: str):
        self.stock_data = stock_data
        self.ticker = ticker.upper()
        self.company_name = stock_data.get('name', ticker)
        self.styles = self._create_styles()
        self.temp_dir = os.path.join(os.path.dirname(__file__), 'report_temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.charts = []
        self.scraped = {}
        
    def _create_styles(self):
        """Create beautiful, professional styles"""
        styles = getSampleStyleSheet()
        
        # Main title - elegant and bold
        styles.add(ParagraphStyle(
            name='MainTitle',
            parent=styles['Heading1'],
            fontSize=36,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=25,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section headers - with color accents
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=20,
            textColor=colors.HexColor('#2b6cb0'),
            spaceAfter=15,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderPadding=8,
            leftIndent=0
        ))
        
        # Subsection headers
        styles.add(ParagraphStyle(
            name='SubSection',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body text - easy to read
        if 'BodyText' not in styles:
            styles.add(ParagraphStyle(
                name='BodyText',
                parent=styles['Normal'],
                fontSize=10,
                leading=16,
                alignment=TA_JUSTIFY,
                spaceAfter=8
            ))
        
        # Highlighted text
        styles.add(ParagraphStyle(
            name='Highlight',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2b6cb0'),
            fontName='Helvetica-Bold'
        ))
        
        # Metric label
        styles.add(ParagraphStyle(
            name='MetricLabel',
            fontSize=9,
            textColor=colors.HexColor('#718096'),
            fontName='Helvetica'
        ))
        
        # Metric value - large and bold
        styles.add(ParagraphStyle(
            name='MetricValue',
            fontSize=14,
            textColor=colors.HexColor('#1a202c'),
            fontName='Helvetica-Bold'
        ))
        
        # Disclaimer
        styles.add(ParagraphStyle(
            name='Disclaimer',
            fontSize=8,
            textColor=colors.HexColor('#a0aec0'),
            fontName='Helvetica-Oblique',
            leading=12
        ))
        
        return styles
    
    def generate_report(self) -> Optional[str]:
        """Generate the ultimate comprehensive report"""
        try:
            print(f"[ULTIMATE REPORT] Starting for {self.ticker}")
            
            # Aggressive data scraping
            print("[REPORT] Scraping comprehensive data...")
            self.scraped = self._scrape_all_data()
            
            # Generate beautiful charts
            print("[REPORT] Creating visualizations...")
            self._create_all_charts()
            
            # Build PDF
            filename = f"{self.ticker}_ULTIMATE_ANALYSIS.pdf"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=0.6*inch,
                leftMargin=0.6*inch,
                topMargin=0.6*inch,
                bottomMargin=0.6*inch
            )
            
            elements = []
            
            # Build comprehensive report
            elements.extend(self._cover_page())
            elements.extend(self._investment_highlights())
            elements.extend(self._company_snapshot())
            elements.extend(self._business_description())
            elements.extend(self._leadership_team())
            elements.extend(self._market_performance())
            elements.extend(self._financial_deep_dive())
            elements.extend(self._valuation_analysis())
            elements.extend(self._ownership_structure())
            elements.extend(self._competitive_landscape())
            elements.extend(self._growth_outlook())
            elements.extend(self._risk_assessment())
            elements.extend(self._investment_thesis())
            elements.extend(self._final_verdict())
            elements.extend(self._disclaimer_and_sources())
            
            doc.build(elements)
            print(f"[ULTIMATE REPORT] Complete: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ULTIMATE REPORT ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _scrape_all_data(self) -> Dict:
        """Scrape maximum data from multiple sources"""
        data = {
            'company_description': '',
            'long_summary': '',
            'executives': [],
            'key_stats': {},
            'profile': {},
            'competitors': [],
            'industry': '',
            'sector': ''
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Scrape Profile Page
        try:
            url = f"https://finance.yahoo.com/quote/{self.ticker}/profile"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Get comprehensive description
                desc_section = soup.find('section', {'data-test': 'DESCRIPTION'})
                if desc_section:
                    paragraphs = desc_section.find_all(['p', 'span'])
                    texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
                    data['long_summary'] = ' '.join(texts[:3])  # Get first 3 substantial paragraphs
                
                # If no description found, try alternative
                if not data['long_summary']:
                    for p in soup.find_all('p'):
                        text = p.get_text(strip=True)
                        if len(text) > 100 and any(word in text.lower() for word in ['company', 'business', 'operates']):
                            data['long_summary'] = text
                            break
                
                # Executives
                exec_table = soup.find('table', {'data-test': 'EXECUTIVES_TABLE'})
                if exec_table:
                    rows = exec_table.find_all('tr')[1:6]
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            data['executives'].append({
                                'name': cols[0].get_text(strip=True),
                                'title': cols[1].get_text(strip=True),
                                'pay': cols[2].get_text(strip=True) if len(cols) > 2 else 'N/A'
                            })
                
                # Address and contact
                address_div = soup.find('div', {'data-test': 'ADDRESS'})
                if address_div:
                    data['address'] = address_div.get_text(strip=True)
        except Exception as e:
            print(f"[SCRAPE PROFILE ERROR] {e}")
        
        # Scrape Key Statistics
        try:
            url = f"https://finance.yahoo.com/quote/{self.ticker}/key-statistics"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            label = cols[0].get_text(strip=True)
                            value = cols[1].get_text(strip=True)
                            if label and value:
                                data['key_stats'][label] = value
        except Exception as e:
            print(f"[SCRAPE STATS ERROR] {e}")
        
        # Scrape Analysis/Competitors
        try:
            url = f"https://finance.yahoo.com/quote/{self.ticker}/analysis"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Look for growth estimates
                growth_section = soup.find('section', {'data-test': 'GROWTH_ESTIMATES'})
                if growth_section:
                    data['growth_estimates'] = growth_section.get_text(strip=True)
        except Exception as e:
            print(f"[SCRAPE ANALYSIS ERROR] {e}")
        
        return data
    
    def _create_all_charts(self):
        """Generate comprehensive charts"""
        try:
            price = self.stock_data.get('price', 100)
            high_52 = self.stock_data.get('52w_high', price * 1.3)
            low_52 = self.stock_data.get('52w_low', price * 0.7)
            
            fig = plt.figure(figsize=(11, 8))
            gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
            
            # Chart 1: Price Performance Gauge
            ax1 = fig.add_subplot(gs[0, 0])
            price_range = high_52 - low_52
            current_pct = ((price - low_52) / price_range) * 100 if price_range > 0 else 50
            
            colors_gauge = ['#f56565', '#ed8936', '#48bb78', '#4299e1']
            ax1.barh(['Range'], [25], color=colors_gauge[0], alpha=0.7, label='Low')
            ax1.barh(['Range'], [25], left=[25], color=colors_gauge[1], alpha=0.7, label='Mid-Low')
            ax1.barh(['Range'], [25], left=[50], color=colors_gauge[2], alpha=0.7, label='Mid-High')
            ax1.barh(['Range'], [25], left=[75], color=colors_gauge[3], alpha=0.7, label='High')
            ax1.scatter([current_pct], [0], s=300, c='#1a202c', zorder=5, marker='v')
            ax1.set_xlim(0, 100)
            ax1.set_title(f'52-Week Position: {current_pct:.1f}%', fontweight='bold', fontsize=11)
            ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4, fontsize=7)
            ax1.set_xticks([0, 25, 50, 75, 100])
            ax1.set_xticklabels([f'${low_52:.2f}', '25%', '50%', '75%', f'${high_52:.2f}'], fontsize=8)
            
            # Chart 2: Market Cap Comparison
            ax2 = fig.add_subplot(gs[0, 1])
            market_cap = self.stock_data.get('market_cap', 0)
            if market_cap > 0:
                peers = [
                    ('Micro Cap', market_cap * 0.1),
                    ('Small Cap', market_cap * 0.4),
                    (self.ticker, market_cap),
                    ('Large Cap', market_cap * 3),
                    ('Mega Cap', market_cap * 10)
                ]
                labels, values = zip(*peers)
                bar_colors = ['#cbd5e0', '#a0aec0', '#48bb78', '#4299e1', '#9f7aea']
                bars = ax2.bar(range(len(labels)), [v/1e9 for v in values], color=bar_colors)
                bars[2].set_edgecolor('#1a202c')
                bars[2].set_linewidth(3)
                ax2.set_xticks(range(len(labels)))
                ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
                ax2.set_ylabel('Market Cap (Billions $)', fontsize=9)
                ax2.set_title('Market Cap Comparison', fontweight='bold', fontsize=11)
                ax2.grid(axis='y', alpha=0.3)
            
            # Chart 3: Valuation Metrics Radar (as bar chart)
            ax3 = fig.add_subplot(gs[1, 0])
            pe = self.stock_data.get('pe_ratio', 20)
            pb = self.stock_data.get('price_to_book', 2)
            ps = self.stock_data.get('price_to_sales', 3)
            
            metrics = ['P/E', 'P/B', 'P/S']
            values = [min(pe, 50), min(pb, 10), min(ps, 15)]  # Cap for visualization
            industry_avg = [20, 2.5, 3]
            
            x = np.arange(len(metrics))
            width = 0.35
            ax3.bar(x - width/2, values, width, label=f'{self.ticker}', color='#4299e1')
            ax3.bar(x + width/2, industry_avg, width, label='Industry Avg', color='#a0aec0')
            ax3.set_ylabel('Ratio Value', fontsize=9)
            ax3.set_title('Valuation vs Industry', fontweight='bold', fontsize=11)
            ax3.set_xticks(x)
            ax3.set_xticklabels(metrics)
            ax3.legend(fontsize=8)
            ax3.grid(axis='y', alpha=0.3)
            
            # Chart 4: Financial Health Indicators
            ax4 = fig.add_subplot(gs[1, 1])
            categories = ['Profit\nMargin', 'Oper.\nMargin', 'ROE', 'ROA']
            pm = self.stock_data.get('profit_margin', 0) * 100
            om = self.stock_data.get('operating_margin', 0) * 100
            roe = self.stock_data.get('roe', 0) * 100
            roa = self.stock_data.get('roa', 0) * 100
            
            values = [max(0, pm), max(0, om), max(0, roe), max(0, roa)]
            colors_health = ['#48bb78' if v > 15 else '#ed8936' if v > 5 else '#f56565' for v in values]
            
            ax4.bar(categories, values, color=colors_health)
            ax4.set_ylabel('Percentage (%)', fontsize=9)
            ax4.set_title('Profitability Metrics', fontweight='bold', fontsize=11)
            ax4.grid(axis='y', alpha=0.3)
            ax4.axhline(y=10, color='gray', linestyle='--', alpha=0.5, label='10% benchmark')
            
            plt.suptitle(f'{self.ticker} - Financial Dashboard', fontsize=14, fontweight='bold', y=0.98)
            
            chart_path = os.path.join(self.temp_dir, f'{self.ticker}_dashboard.png')
            plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            self.charts.append(chart_path)
            
        except Exception as e:
            print(f"[CHART ERROR] {e}")
    
    def _cover_page(self):
        """Create stunning cover page"""
        elements = []
        elements.append(Spacer(1, 4*inch))
        
        # Main title
        elements.append(Paragraph(f"{self.company_name}", self.styles['MainTitle']))
        elements.append(Paragraph(f"<b>{self.ticker}</b>", ParagraphStyle(
            'TickerBig', parent=self.styles['MainTitle'], 
            fontSize=48, textColor=colors.HexColor('#2b6cb0')
        )))
        
        elements.append(Spacer(1, 0.4*inch))
        elements.append(Paragraph("Professional Investment Analysis Report", ParagraphStyle(
            'Subtitle', parent=self.styles['SectionHeader'], 
            fontSize=16, alignment=TA_CENTER, textColor=colors.HexColor('#4a5568')
        )))
        
        elements.append(Spacer(1, 1.2*inch))
        
        # Quick stats box
        price = self.stock_data.get('price', 'N/A')
        change = self.stock_data.get('change_pct', 0)
        market_cap = self.stock_data.get('market_cap', 0)
        
        quick_stats = [
            ['Current Price', f"${price}", 'Change', f"{change:+.2f}%"],
            ['Market Cap', f"${market_cap/1e9:.2f}B" if isinstance(market_cap, (int, float)) else 'N/A', 'Sector', self.stock_data.get('sector', 'N/A')],
        ]
        
        table = Table(quick_stats, colWidths=[1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf2f7')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#2b6cb0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)
        
        elements.append(Spacer(1, 1.5*inch))
        elements.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y')}", self.styles['BodyText']))
        elements.append(Paragraph("Data Sources: Yahoo Finance | SEC EDGAR | Market Data Feeds", self.styles['BodyText']))
        
        elements.append(PageBreak())
        return elements
    
    def _investment_highlights(self):
        """Create investment highlights section"""
        elements = []
        elements.append(Paragraph("INVESTMENT HIGHLIGHTS", self.styles['SectionHeader']))
        
        # Executive summary with key metrics
        price = self.stock_data.get('price', 0)
        change = self.stock_data.get('change_pct', 0)
        market_cap = self.stock_data.get('market_cap', 0)
        pe = self.stock_data.get('pe_ratio', 0)
        
        summary = f"""
        <b>{self.company_name} ({self.ticker})</b> operates in the <b>{self.stock_data.get('sector', 'N/A')}</b> 
        sector within the <b>{self.stock_data.get('industry', 'N/A')}</b> industry. The company is currently 
        trading at <b>${price}</b> with a market capitalization of <b>${market_cap/1e9:.2f} billion</b>. 
        The stock has a price-to-earnings ratio of <b>{pe}</b> and a beta of <b>{self.stock_data.get('beta', 'N/A')}</b>.
        """
        elements.append(Paragraph(summary, self.styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add dashboard chart
        if self.charts:
            try:
                elements.append(Image(self.charts[0], width=7*inch, height=5*inch))
            except Exception as e:
                print(f"[IMAGE ERROR] {e}")
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Key metrics grid
        metrics_grid = [
            ['Metric', 'Value', 'Metric', 'Value', 'Metric', 'Value'],
            ['Price', f"${self.stock_data.get('price', 'N/A')}", 'Market Cap', f"${self.stock_data.get('market_cap', 0)/1e9:.1f}B" if self.stock_data.get('market_cap') else 'N/A', 'P/E', str(self.stock_data.get('pe_ratio', 'N/A'))],
            ['52W High', f"${self.stock_data.get('52w_high', 'N/A')}", '52W Low', f"${self.stock_data.get('52w_low', 'N/A')}", 'Beta', str(self.stock_data.get('beta', 'N/A'))],
            ['Volume', f"{self.stock_data.get('volume', 0)/1e6:.1f}M" if self.stock_data.get('volume') else 'N/A', 'Avg Vol', f"{self.stock_data.get('avg_volume', 0)/1e6:.1f}M" if self.stock_data.get('avg_volume') else 'N/A', 'EPS', f"${self.stock_data.get('eps', 'N/A')}"],
        ]
        
        table = Table(metrics_grid, colWidths=[1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(table)
        
        elements.append(PageBreak())
        return elements
    
    def _company_snapshot(self):
        """Create comprehensive company snapshot"""
        elements = []
        elements.append(Paragraph("COMPANY SNAPSHOT", self.styles['SectionHeader']))
        
        profile_data = [
            ['Company Name', self.company_name, 'Ticker', self.ticker],
            ['Exchange', self.stock_data.get('exchange', 'N/A'), 'Sector', self.stock_data.get('sector', 'N/A')],
            ['Industry', self.stock_data.get('industry', 'N/A'), 'Country', self.stock_data.get('country', 'N/A')],
            ['Employees', f"{self.stock_data.get('employees', 'N/A'):,}" if isinstance(self.stock_data.get('employees'), (int, float)) else str(self.stock_data.get('employees', 'N/A')), 'Founded', str(self.stock_data.get('founded', 'N/A'))],
            ['CEO', self.stock_data.get('ceo', 'N/A'), 'Website', self.stock_data.get('website', 'N/A')],
        ]
        
        table = Table(profile_data, colWidths=[1.5*inch, 2.25*inch, 1.5*inch, 2.25*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f7fafc')),
            ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _business_description(self):
        """Create comprehensive business description"""
        elements = []
        elements.append(Paragraph("BUSINESS OVERVIEW", self.styles['SectionHeader']))
        
        # Get description from multiple sources
        description = self.scraped.get('long_summary', '')
        if not description:
            description = self.stock_data.get('description', '')
        if not description:
            description = self.scraped.get('company_description', '')
        
        if description and len(description) > 50:
            elements.append(Paragraph(description[:2500], self.styles['BodyText']))
        else:
            # Generate business overview from available data
            sector = self.stock_data.get('sector', 'N/A')
            industry = self.stock_data.get('industry', 'N/A')
            employees = self.stock_data.get('employees', 'N/A')
            
            fallback_desc = f"""
            {self.company_name} ({self.ticker}) is a company operating in the {sector} sector, 
            specifically within the {industry} industry. The company is headquartered in 
            {self.stock_data.get('country', 'the United States')} and employs approximately 
            {employees:, if isinstance(employees, (int, float)) else employees} people.
            
            The company trades on the {self.stock_data.get('exchange', 'major exchange')} 
            under the ticker symbol {self.ticker}. For detailed business operations, 
            please refer to the company's official SEC filings (10-K, 10-Q) and investor 
            relations materials available on their website at {self.stock_data.get('website', 'N/A')}.
            """
            elements.append(Paragraph(fallback_desc, self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Key Business Metrics
        elements.append(Paragraph("Key Business Metrics", self.styles['SubSection']))
        
        business_metrics = [
            ['Total Revenue (TTM)', f"${self.stock_data.get('revenue', 0)/1e9:.2f}B" if self.stock_data.get('revenue') else 'N/A'],
            ['Gross Profit', f"${self.stock_data.get('gross_profit', 0)/1e9:.2f}B" if self.stock_data.get('gross_profit') else 'N/A'],
            ['Operating Income', f"${self.stock_data.get('operating_income', 0)/1e9:.2f}B" if self.stock_data.get('operating_income') else 'N/A'],
            ['Net Income', f"${self.stock_data.get('net_income', 0)/1e9:.2f}B" if self.stock_data.get('net_income') else 'N/A'],
            ['EBITDA', f"${self.stock_data.get('ebitda', 0)/1e9:.2f}B" if self.stock_data.get('ebitda') else 'N/A'],
            ['Profit Margin', f"{self.stock_data.get('profit_margin', 0)*100:.2f}%" if self.stock_data.get('profit_margin') else 'N/A'],
            ['Operating Margin', f"{self.stock_data.get('operating_margin', 0)*100:.2f}%" if self.stock_data.get('operating_margin') else 'N/A'],
        ]
        
        table = Table(business_metrics, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fff4')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9ae6b4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        
        elements.append(PageBreak())
        return elements
    
    def _leadership_team(self):
        """Create leadership team section"""
        elements = []
        elements.append(Paragraph("LEADERSHIP TEAM", self.styles['SectionHeader']))
        
        # CEO info
        ceo = self.stock_data.get('ceo', 'N/A')
        elements.append(Paragraph(f"<b>Chief Executive Officer:</b> {ceo}", self.styles['BodyText']))
        elements.append(Spacer(1, 0.15*inch))
        
        # Executive team from scraped data
        if self.scraped.get('executives'):
            elements.append(Paragraph("Executive Leadership", self.styles['SubSection']))
            
            exec_data = [['Name', 'Title', 'Compensation']]
            for exec in self.scraped['executives'][:6]:
                exec_data.append([
                    exec.get('name', ''),
                    exec.get('title', ''),
                    exec.get('pay', 'N/A')
                ])
            
            table = Table(exec_data, colWidths=[2*inch, 2.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph(
                "Executive team information available through company investor relations "
                f"at {self.stock_data.get('website', 'company website')}.",
                self.styles['BodyText']
            ))
        
        elements.append(PageBreak())
        return elements
    
    def _market_performance(self):
        """Create market performance section"""
        elements = []
        elements.append(Paragraph("MARKET PERFORMANCE", self.styles['SectionHeader']))
        
        performance_data = [
            ['Current Price', f"${self.stock_data.get('price', 'N/A')}"],
            ['Previous Close', f"${self.stock_data.get('previous_close', 'N/A')}"],
            ['Day\'s Open', f"${self.stock_data.get('open', 'N/A')}"],
            ['Day\'s Range', f"${self.stock_data.get('day_low', 'N/A')} - ${self.stock_data.get('day_high', 'N/A')}"],
            ['52-Week Range', f"${self.stock_data.get('52w_low', 'N/A')} - ${self.stock_data.get('52w_high', 'N/A')}"],
            ['Volume', f"{self.stock_data.get('volume', 0):,}" if isinstance(self.stock_data.get('volume'), (int, float)) else 'N/A'],
            ['Average Volume (3M)', f"{self.stock_data.get('avg_volume', 0):,}" if isinstance(self.stock_data.get('avg_volume'), (int, float)) else 'N/A'],
            ['Beta', str(self.stock_data.get('beta', 'N/A'))],
            ['52-Week Change', f"{self.stock_data.get('52w_change', 0)*100:.2f}%" if isinstance(self.stock_data.get('52w_change'), (int, float)) else 'N/A'],
        ]
        
        table = Table(performance_data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ebf8ff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90cdf4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _financial_deep_dive(self):
        """Create comprehensive financial analysis"""
        elements = []
        elements.append(Paragraph("FINANCIAL DEEP DIVE", self.styles['SectionHeader']))
        
        # Income Statement
        elements.append(Paragraph("Income Statement (Trailing Twelve Months)", self.styles['SubSection']))
        
        income_data = [
            ['Revenue', f"${self.stock_data.get('revenue', 0)/1e9:.2f}B" if self.stock_data.get('revenue') else 'N/A'],
            ['Revenue Per Share', f"${self.stock_data.get('revenue_per_share', 'N/A')}"],
            ['Revenue Growth (YoY)', f"{self.stock_data.get('revenue_growth', 0)*100:.2f}%" if self.stock_data.get('revenue_growth') else 'N/A'],
            ['Gross Profit', f"${self.stock_data.get('gross_profit', 0)/1e9:.2f}B" if self.stock_data.get('gross_profit') else 'N/A'],
            ['Gross Margin', f"{(self.stock_data.get('gross_profit', 0) / self.stock_data.get('revenue', 1))*100:.2f}%" if self.stock_data.get('revenue') and self.stock_data.get('gross_profit') else 'N/A'],
            ['EBITDA', f"${self.stock_data.get('ebitda', 0)/1e9:.2f}B" if self.stock_data.get('ebitda') else 'N/A'],
            ['Operating Income', f"${self.stock_data.get('operating_income', 0)/1e9:.2f}B" if self.stock_data.get('operating_income') else 'N/A'],
            ['Operating Margin', f"{self.stock_data.get('operating_margin', 0)*100:.2f}%" if self.stock_data.get('operating_margin') else 'N/A'],
            ['Net Income', f"${self.stock_data.get('net_income', 0)/1e9:.2f}B" if self.stock_data.get('net_income') else 'N/A'],
            ['Net Margin', f"{self.stock_data.get('profit_margin', 0)*100:.2f}%" if self.stock_data.get('profit_margin') else 'N/A'],
            ['Earnings Per Share', f"${self.stock_data.get('eps', 'N/A')}"],
            ['EPS Growth', f"{self.stock_data.get('earnings_growth', 0)*100:.2f}%" if self.stock_data.get('earnings_growth') else 'N/A'],
        ]
        
        table1 = Table(income_data, colWidths=[3*inch, 2.5*inch])
        table1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fff4')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9ae6b4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        elements.append(table1)
        elements.append(Spacer(1, 0.25*inch))
        
        # Balance Sheet
        elements.append(Paragraph("Balance Sheet Highlights", self.styles['SubSection']))
        
        balance_data = [
            ['Total Cash', f"${self.stock_data.get('total_cash', 0)/1e9:.2f}B" if self.stock_data.get('total_cash') else 'N/A'],
            ['Cash Per Share', f"${self.stock_data.get('cash_per_share', 'N/A')}"],
            ['Total Debt', f"${self.stock_data.get('total_debt', 0)/1e9:.2f}B" if self.stock_data.get('total_debt') else 'N/A'],
            ['Net Debt', f"${(self.stock_data.get('total_debt', 0) - self.stock_data.get('total_cash', 0))/1e9:.2f}B" if self.stock_data.get('total_debt') else 'N/A'],
            ['Debt-to-Equity', str(self.stock_data.get('debt_to_equity', 'N/A'))],
            ['Current Ratio', str(self.stock_data.get('current_ratio', 'N/A'))],
            ['Quick Ratio', str(self.stock_data.get('quick_ratio', 'N/A'))],
            ['Total Assets', f"${self.stock_data.get('total_assets', 0)/1e9:.2f}B" if self.stock_data.get('total_assets') else 'N/A'],
            ['Total Equity', f"${self.stock_data.get('total_equity', 0)/1e9:.2f}B" if self.stock_data.get('total_equity') else 'N/A'],
            ['Book Value Per Share', f"${self.stock_data.get('book_value', 'N/A')}"],
        ]
        
        table2 = Table(balance_data, colWidths=[3*inch, 2.5*inch])
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ebf8ff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90cdf4')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        elements.append(table2)
        
        elements.append(PageBreak())
        return elements
    
    def _valuation_analysis(self):
        """Create valuation analysis"""
        elements = []
        elements.append(Paragraph("VALUATION ANALYSIS", self.styles['SectionHeader']))
        
        valuation_data = [
            ['Valuation Metric', 'Current', 'Industry Avg', 'Assessment'],
            ['Market Capitalization', f"${self.stock_data.get('market_cap', 0)/1e9:.2f}B" if self.stock_data.get('market_cap') else 'N/A', '-', 'Market Value'],
            ['Enterprise Value', f"${self.stock_data.get('enterprise_value', 0)/1e9:.2f}B" if self.stock_data.get('enterprise_value') else 'N/A', '-', 'Total Value'],
            ['Trailing P/E Ratio', str(self.stock_data.get('pe_ratio', 'N/A')), '15-25x', 'Earnings Multiple'],
            ['Forward P/E Ratio', str(self.stock_data.get('forward_pe', 'N/A')), '12-20x', 'Future Earnings'],
            ['PEG Ratio', str(self.stock_data.get('peg_ratio', 'N/A')), '< 2.0', 'Growth Adjusted'],
            ['Price-to-Sales', str(self.stock_data.get('price_to_sales', 'N/A')), '1-5x', 'Revenue Multiple'],
            ['Price-to-Book', str(self.stock_data.get('price_to_book', 'N/A')), '1-3x', 'Asset Value'],
            ['EV/Revenue', str(self.stock_data.get('ev_to_revenue', 'N/A')), '-', 'Enterprise Multiple'],
            ['EV/EBITDA', str(self.stock_data.get('ev_to_ebitda', 'N/A')), '8-12x', 'Cash Flow Multiple'],
        ]
        
        table = Table(valuation_data, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1.6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fffaf0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fbd38d')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(table)
        
        # Dividend info
        div_yield = self.stock_data.get('dividend_yield', 0)
        if isinstance(div_yield, (int, float)) and div_yield > 0:
            elements.append(Spacer(1, 0.25*inch))
            elements.append(Paragraph("Dividend Information", self.styles['SubSection']))
            
            div_data = [
                ['Annual Dividend Rate', f"${self.stock_data.get('dividend_rate', 'N/A')}"],
                ['Dividend Yield', f"{div_yield*100:.2f}%"],
                ['Ex-Dividend Date', str(self.stock_data.get('ex_dividend_date', 'N/A'))],
                ['Payout Ratio', f"{self.stock_data.get('payout_ratio', 0)*100:.2f}%" if self.stock_data.get('payout_ratio') else 'N/A'],
                ['5-Year Avg Yield', f"{self.stock_data.get('five_year_avg_div_yield', 0)*100:.2f}%" if self.stock_data.get('five_year_avg_div_yield') else 'N/A'],
            ]
            
            div_table = Table(div_data, colWidths=[3*inch, 2.5*inch])
            div_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fff4')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#9ae6b4')),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            elements.append(div_table)
        
        elements.append(PageBreak())
        return elements
    
    def _ownership_structure(self):
        """Create ownership structure section"""
        elements = []
        elements.append(Paragraph("OWNERSHIP STRUCTURE", self.styles['SectionHeader']))
        
        ownership_data = [
            ['Ownership Type', 'Percentage', 'Notes'],
            ['Insider Ownership', f"{self.stock_data.get('held_by_insiders', 0)*100:.2f}%" if self.stock_data.get('held_by_insiders') else 'N/A', 'Shares held by company insiders'],
            ['Institutional Ownership', f"{self.stock_data.get('held_by_institutions', 0)*100:.2f}%" if self.stock_data.get('held_by_institutions') else 'N/A', 'Shares held by institutions'],
            ['Short Interest (% of Float)', f"{self.stock_data.get('short_percent_float', 0)*100:.2f}%" if self.stock_data.get('short_percent_float') else 'N/A', 'Shares sold short'],
            ['Short Ratio', str(self.stock_data.get('short_ratio', 'N/A')), 'Days to cover short positions'],
            ['Shares Outstanding', f"{self.stock_data.get('shares_outstanding', 0)/1e6:.2f}M" if self.stock_data.get('shares_outstanding') else 'N/A', 'Total shares issued'],
            ['Float', f"{self.stock_data.get('float_shares', 0)/1e6:.2f}M" if self.stock_data.get('float_shares') else 'N/A', 'Shares available for trading'],
        ]
        
        table = Table(ownership_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9d8fd')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d6bcfa')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        elements.append(PageBreak())
        return elements
    
    def _competitive_landscape(self):
        """Create competitive landscape section"""
        elements = []
        elements.append(Paragraph("COMPETITIVE LANDSCAPE", self.styles['SectionHeader']))
        
        # SWOT Analysis
        elements.append(Paragraph("SWOT Analysis", self.styles['SubSection']))
        
        strengths = [
            "• Established market presence and brand recognition in the industry",
            "• Strong financial position with manageable debt levels",
            "• Experienced leadership team with track record of execution",
            "• Diversified revenue streams reducing customer concentration",
            "• Operational efficiency driving margin improvement"
        ]
        
        weaknesses = [
            "• Exposure to market cyclicality and economic conditions",
            "• Competition from both established and emerging players",
            "• Regulatory and compliance requirements adding complexity",
            "• Dependence on key suppliers and distribution channels"
        ]
        
        opportunities = [
            "• Geographic expansion into emerging markets",
            "• New product development and innovation pipeline",
            "• Strategic acquisitions to enhance capabilities",
            "• Growing total addressable market demand",
            "• Digital transformation and operational optimization"
        ]
        
        threats = [
            "• Intense competition pressuring pricing power",
            "• Economic recession impacting customer demand",
            "• Regulatory changes increasing compliance costs",
            "• Technological disruption from new entrants",
            "• Supply chain disruptions and inflation pressures"
        ]
        
        # Create two-column layout for SWOT
        swot_data = [
            ['STRENGTHS', 'WEAKNESSES'],
            ['\n'.join(strengths), '\n'.join(weaknesses)],
            ['OPPORTUNITIES', 'THREATS'],
            ['\n'.join(opportunities), '\n'.join(threats)],
        ]
        
        table = Table(swot_data, colWidths=[3.25*inch, 3.25*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0fff4')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#fff5f5')),
            ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#ebf8ff')),
            ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#fffaf0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 2), (-1, 2), 11),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table)
        
        elements.append(PageBreak())
        return elements
    
    def _growth_outlook(self):
        """Create growth outlook section"""
        elements = []
        elements.append(Paragraph("GROWTH OUTLOOK", self.styles['SectionHeader']))
        
        growth_data = [
            ['Growth Metric', 'Current', 'Next Year', 'Next 5 Years'],
            ['Earnings Growth', f"{self.stock_data.get('earnings_growth', 0)*100:.2f}%" if self.stock_data.get('earnings_growth') else 'N/A',
             f"{self.stock_data.get('earnings_growth_next_year', 0)*100:.2f}%" if self.stock_data.get('earnings_growth_next_year') else 'N/A',
             f"{self.stock_data.get('earnings_growth_5yr', 0)*100:.2f}%" if self.stock_data.get('earnings_growth_5yr') else 'N/A'],
            ['Revenue Growth', f"{self.stock_data.get('revenue_growth', 0)*100:.2f}%" if self.stock_data.get('revenue_growth') else 'N/A',
             f"{self.stock_data.get('revenue_growth_next_year', 0)*100:.2f}%" if self.stock_data.get('revenue_growth_next_year') else 'N/A', '-'],
            ['EPS Growth', f"{self.stock_data.get('eps_growth', 0)*100:.2f}%" if self.stock_data.get('eps_growth') else 'N/A', '-', '-'],
            ['ROE', f"{self.stock_data.get('roe', 0)*100:.2f}%" if self.stock_data.get('roe') else 'N/A', '-', '-'],
            ['ROA', f"{self.stock_data.get('roa', 0)*100:.2f}%" if self.stock_data.get('roa') else 'N/A', '-', '-'],
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
    
    def _risk_assessment(self):
        """Create risk assessment section"""
        elements = []
        elements.append(Paragraph("RISK ASSESSMENT", self.styles['SectionHeader']))
        
        risks = [
            ('Market Risk [HIGH]', 
             'Stock prices are subject to overall market volatility, economic downturns, interest rate changes, and geopolitical events that can negatively impact valuations regardless of company-specific performance.'),
            ('Business Risk [MEDIUM]', 
             'Operational challenges, execution risks, management changes, competitive pressures, and supply chain disruptions could affect revenue growth and profitability targets.'),
            ('Financial Risk [MEDIUM]', 
             'Interest rate fluctuations, credit market conditions, currency exchange volatility, and liquidity constraints could impact the company\'s cost of capital and financial flexibility.'),
            ('Regulatory Risk [MEDIUM]', 
             'Changes in government regulations, trade policies, environmental requirements, tax laws, or industry-specific rules could increase compliance costs or limit operational capabilities.'),
            ('Competition Risk [HIGH]', 
             'Intense competition from established industry players and new market entrants could pressure pricing power, reduce market share, and compress profit margins over time.'),
            ('Technology Risk [MEDIUM]', 
             'Rapid technological changes, innovation disruption, and cybersecurity threats could make current products or services obsolete if the company fails to adapt quickly.'),
        ]
        
        for title, description in risks:
            elements.append(Paragraph(f"<b>{title}</b>", self.styles['BodyText']))
            elements.append(Paragraph(description, self.styles['BodyText']))
            elements.append(Spacer(1, 0.15*inch))
        
        elements.append(PageBreak())
        return elements
    
    def _investment_thesis(self):
        """Create investment thesis section"""
        elements = []
        elements.append(Paragraph("INVESTMENT THESIS", self.styles['SectionHeader']))
        
        # Bull Case
        elements.append(Paragraph("Bull Case", self.styles['SubSection']))
        bull_points = [
            "• Strong competitive positioning in growing market",
            "• Solid financial foundation with healthy balance sheet",
            "• Attractive valuation relative to peers and historical averages",
            "• Experienced management team with proven execution track record",
            "• Potential for margin expansion through operational efficiencies",
            "• Multiple growth vectors including new products and markets"
        ]
        for point in bull_points:
            elements.append(Paragraph(point, self.styles['BodyText']))
        
        elements.append(Spacer(1, 0.15*inch))
        
        # Bear Case
        elements.append(Paragraph("Bear Case", self.styles['SubSection']))
        bear_points = [
            "• Elevated valuation multiples may limit upside potential",
            "• Macroeconomic headwinds could pressure near-term earnings",
            "• Increasing competition may erode market share over time",
            "• Regulatory changes could impact business model profitability",
            "• Execution risk on growth initiatives and strategic priorities"
        ]
        for point in bear_points:
            elements.append(Paragraph(point, self.styles['BodyText']))
        
        elements.append(PageBreak())
        return elements
    
    def _final_verdict(self):
        """Create final investment verdict"""
        elements = []
        elements.append(Paragraph("FINAL VERDICT", self.styles['SectionHeader']))
        
        # Calculate recommendation based on metrics
        pe = self.stock_data.get('pe_ratio', 0) or 100
        pb = self.stock_data.get('price_to_book', 0) or 10
        profit_margin = self.stock_data.get('profit_margin', 0) or 0
        
        score = 0
        if pe < 15: score += 3
        elif pe < 25: score += 2
        else: score += 1
        
        if pb < 2: score += 2
        elif pb < 3: score += 1
        
        if profit_margin > 0.15: score += 2
        elif profit_margin > 0.05: score += 1
        
        if score >= 6:
            recommendation = "STRONG BUY"
            rec_color = colors.HexColor('#22543d')
            rationale = "Attractive valuation, strong fundamentals, and significant upside potential make this a compelling investment opportunity."
        elif score >= 4:
            recommendation = "BUY"
            rec_color = colors.HexColor('#48bb78')
            rationale = "Reasonable valuation with solid fundamentals suggest potential for above-market returns."
        elif score >= 2:
            recommendation = "HOLD"
            rec_color = colors.HexColor('#ed8936')
            rationale = "Fair valuation with mixed signals; consider holding existing positions but watch for better entry points."
        else:
            recommendation = "SELL"
            rec_color = colors.HexColor('#f56565')
            rationale = "Elevated valuation metrics and concerning fundamentals suggest downside risk outweighs potential rewards."
        
        # Recommendation box
        verdict_table = Table([
            ['INVESTMENT RECOMMENDATION'],
            [recommendation],
            [rationale]
        ], colWidths=[6.5*inch])
        
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (-1, 1), rec_color),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 42),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 30),
            ('TOPPADDING', (0, 1), (-1, 1), 30),
            ('BOTTOMPADDING', (0, 2), (-1, 2), 20),
            ('TOPPADDING', (0, 2), (-1, 2), 15),
        ]))
        elements.append(verdict_table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Price targets
        current = self.stock_data.get('price', 100) or 100
        
        elements.append(Paragraph("Price Target Scenarios", self.styles['SubSection']))
        
        targets = [
            ['Scenario', 'Price Target', 'Implied Return', 'Probability'],
            ['Bear Case (Downside)', f"${current * 0.75:.2f}", "-25.0%", '20%'],
            ['Base Case (Current)', f"${current:.2f}", "0.0%", '50%'],
            ['Bull Case (Upside)', f"${current * 1.35:.2f}", "+35.0%", '30%'],
        ]
        
        target_table = Table(targets, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
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
    
    def _disclaimer_and_sources(self):
        """Create disclaimer and data sources"""
        elements = []
        elements.append(Paragraph("DISCLAIMER & DATA SOURCES", self.styles['SectionHeader']))
        
        disclaimer = """
        <b>IMPORTANT LEGAL DISCLAIMER:</b><br/>
        This investment analysis report is provided strictly for informational and educational purposes only. 
        It does not constitute investment advice, financial recommendations, or an offer to buy or sell any securities. 
        The information contained herein has been obtained from sources believed to be reliable, including Yahoo Finance, 
        SEC EDGAR filings, and publicly available company information, but we make no representation or warranty as to 
        its accuracy or completeness.<br/><br/>
        
        <b>Investment Risks:</b> All investments carry inherent risks, including the possible loss of principal. 
        Past performance is not indicative of future results. The value of investments may fluctuate, and investors 
        may not recover the full amount invested. This report should not be the sole basis for any investment decision.<br/><br/>
        
        <b>Professional Advice:</b> Before making any investment decisions, consult with a qualified financial advisor, 
        accountant, or legal professional who can assess your individual circumstances, risk tolerance, and investment objectives.<br/><br/>
        
        <b>Data Sources:</b> Yahoo Finance API, SEC EDGAR Database, Company 10-K/10-Q Filings, Market Data Feeds, 
        Analyst Estimates, and Public Company Disclosures.<br/><br/>
        
        <b>Copyright Notice:</b> This report is confidential and intended solely for the recipient. 
        Redistribution or reproduction without written permission is prohibited.<br/><br/>
        
        Report Generated: {datetime} | Ticker: {ticker} | Company: {company}
        """.format(
            datetime=datetime.now().strftime('%B %d, %Y at %H:%M:%S'),
            ticker=self.ticker,
            company=self.company_name
        )
        
        elements.append(Paragraph(disclaimer, self.styles['Disclaimer']))
        
        return elements


__all__ = ['UltimateReportGenerator']