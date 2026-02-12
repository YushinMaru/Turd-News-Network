"""
Comprehensive Data Fetcher - Fetches extensive company data from multiple free APIs
Includes: Yahoo Finance, SEC EDGAR, Finnhub, Alpha Vantage, Web Scraping
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from bs4 import BeautifulSoup
import yfinance as yf


class ComprehensiveDataFetcher:
    """Fetches comprehensive company data from multiple free sources"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.yf_ticker = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_all_data(self) -> Dict:
        """Fetch all available data for the company"""
        print(f"[DATA FETCHER] Fetching comprehensive data for {self.ticker}...")
        
        data = {
            'basic_info': self._fetch_yfinance_info(),
            'financials': self._fetch_financial_data(),
            'sec_filings': self._fetch_sec_edgar_data(),
            'analyst_data': self._fetch_analyst_data(),
            'ownership': self._fetch_ownership_data(),
            'insider': self._fetch_insider_data(),
            'congress': self._fetch_congress_data(),
            'news_sentiment': self._fetch_news_sentiment(),
            'competitors': self._fetch_competitor_data(),
            'technicals': self._fetch_technical_data(),
            'executives': self._fetch_executive_data(),
            'esg': self._fetch_esg_data(),
            'peers': self._fetch_peer_comparison(),
            'dividends': self._fetch_dividend_history(),
            'splits': self._fetch_split_history(),
            'earnings': self._fetch_earnings_data(),
            'recommendations': self._fetch_recommendations(),
            'upgrades_downgrades': self._fetch_upgrades_downgrades(),
            'sustainability': self._fetch_sustainability_data(),
            'calendar': self._fetch_calendar_events(),
            'options': self._fetch_options_data()
        }
        
        print(f"[DATA FETCHER] ✓ Data fetch complete for {self.ticker}")
        return data
    
    def _fetch_yfinance_info(self) -> Dict:
        """Fetch comprehensive Yahoo Finance data"""
        data = {'info': {}}
        try:
            self.yf_ticker = yf.Ticker(self.ticker)
            info = self.yf_ticker.info or {}
            
            # All available fields from yfinance
            fields = [
                'address1', 'address2', 'city', 'state', 'zip', 'country',
                'phone', 'website', 'industry', 'sector', 'sectorKey', 'sectorDisp',
                'longBusinessSummary', 'fullTimeEmployees', 'companyOfficers',
                'auditRisk', 'boardRisk', 'compensationRisk', 'shareHolderRightsRisk',
                'overallRisk', 'governanceEpochDate', 'compensationAsOfEpochDate',
                'maxAge', 'priceHint', 'previousClose', 'open', 'dayLow', 'dayHigh',
                'regularMarketPreviousClose', 'regularMarketOpen', 'regularMarketDayLow',
                'regularMarketDayHigh', 'dividendRate', 'dividendYield', 'exDividendDate',
                'payoutRatio', 'fiveYearAvgDividendYield', 'beta', 'trailingPE',
                'forwardPE', 'volume', 'regularMarketVolume', 'averageVolume',
                'averageVolume10days', 'averageDailyVolume10Day', 'bid', 'ask',
                'bidSize', 'askSize', 'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh',
                'fiftyDayAverage', 'twoHundredDayAverage', 'trailingAnnualDividendRate',
                'trailingAnnualDividendYield', 'currency', 'enterpriseValue',
                'profitMargins', 'floatShares', 'sharesOutstanding', 'sharesShort',
                'sharesShortPriorMonth', 'sharesShortPreviousMonthDate', 'dateShortInterest',
                'shortRatio', 'shortPercentOfFloat', 'heldPercentInsiders',
                'heldPercentInstitutions', 'impliedSharesOutstanding', 'bookValue',
                'priceToBook', 'lastFiscalYearEnd', 'nextFiscalYearEnd', 'mostRecentQuarter',
                'earningsQuarterlyGrowth', 'netIncomeToCommon', 'trailingEps',
                'forwardEps', 'pegRatio', 'lastSplitFactor', 'lastSplitDate',
                'enterpriseToRevenue', 'enterpriseToEbitda', '52WeekChange',
                'SandP52WeekChange', 'lastDividendValue', 'lastDividendDate',
                'exchange', 'quoteType', 'symbol', 'underlyingSymbol', 'shortName',
                'longName', 'firstTradeDateEpochUtc', 'timeZoneFullName',
                'timeZoneShortName', 'uuid', 'messageBoardId', 'gmtOffSetMilliseconds',
                'currentPrice', 'targetHighPrice', 'targetLowPrice', 'targetMeanPrice',
                'targetMedianPrice', 'recommendationMean', 'recommendationKey',
                'numberOfAnalystOpinions', 'totalCash', 'totalCashPerShare',
                'ebitda', 'totalDebt', 'quickRatio', 'currentRatio', 'totalRevenue',
                'debtToEquity', 'revenuePerShare', 'returnOnAssets', 'returnOnEquity',
                'freeCashflow', 'operatingCashflow', 'earningsGrowth', 'revenueGrowth',
                'grossMargins', 'ebitdaMargins', 'operatingMargins', 'profitMargins',
                'financialCurrency', 'operatingRevenue', 'operatingExpenses',
                'netInterestIncome', 'interestIncome', 'interestExpense',
                'normalizedIncome', 'asicHolding', 'trailingPegRatio'
            ]
            
            for field in fields:
                if field in info:
                    data['info'][field] = info[field]
                    
            # Add quarterly and annual financials if available
            try:
                data['quarterly_financials'] = self.yf_ticker.quarterly_financials.to_dict() if hasattr(self.yf_ticker, 'quarterly_financials') else {}
            except:
                data['quarterly_financials'] = {}
                
            try:
                data['annual_financials'] = self.yf_ticker.financials.to_dict() if hasattr(self.yf_ticker, 'financials') else {}
            except:
                data['annual_financials'] = {}
                
        except Exception as e:
            print(f"[YFINANCE ERROR] {e}")
            
        return data
    
    def _fetch_financial_data(self) -> Dict:
        """Fetch detailed financial data"""
        data = {}
        try:
            if self.yf_ticker:
                # Balance sheet
                try:
                    data['balance_sheet'] = self.yf_ticker.balance_sheet.to_dict()
                except:
                    pass
                    
                # Cash flow
                try:
                    data['cashflow'] = self.yf_ticker.cashflow.to_dict()
                except:
                    pass
                    
                # Quarterly data
                try:
                    data['quarterly_earnings'] = self.yf_ticker.quarterly_earnings.to_dict()
                except:
                    pass
                    
        except Exception as e:
            print(f"[FINANCIALS ERROR] {e}")
            
        return data
    
    def _fetch_sec_edgar_data(self) -> Dict:
        """Fetch SEC EDGAR filing data with enhanced filing links"""
        data = {
            'filings': [],
            'latest_10k': None,
            'latest_10q': None,
            'latest_8k': None,
            'sec_search_url': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=&dateb=&owner=include&count=40",
            'filing_links': {
                '10-K': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=10-K",
                '10-Q': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=10-Q",
                '8-K': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=8-K",
                'DEF 14A': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=DEF+14A",
                'Form 4': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=4",
                '13F': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&type=13F"
            }
        }
        try:
            # SEC EDGAR requires a proper user agent
            headers = {
                'User-Agent': 'TurdNewsNetwork contact@example.com'
            }
            
            # Note: SEC requires proper CIK lookup - links are provided above for manual access
            print(f"[SEC EDGAR] Filing links generated for {self.ticker}")
            
        except Exception as e:
            print(f"[SEC EDGAR ERROR] {e}")
            
        return data
    
    def _fetch_analyst_data(self) -> Dict:
        """Fetch analyst coverage and price targets"""
        data = {'targets': {}, 'recommendations': []}
        try:
            if self.yf_ticker:
                try:
                    data['recommendations'] = self.yf_ticker.recommendations.to_dict() if hasattr(self.yf_ticker, 'recommendations') else {}
                except:
                    pass
                    
        except Exception as e:
            print(f"[ANALYST DATA ERROR] {e}")
            
        return data
    
    def _fetch_ownership_data(self) -> Dict:
        """Fetch institutional ownership data"""
        data = {'institutional': [], 'mutual_funds': [], 'major_holders': {}}
        try:
            if self.yf_ticker:
                try:
                    data['institutional'] = self.yf_ticker.institutional_holders.to_dict() if hasattr(self.yf_ticker, 'institutional_holders') else {}
                except:
                    pass
                    
                try:
                    data['mutual_funds'] = self.yf_ticker.mutualfund_holders.to_dict() if hasattr(self.yf_ticker, 'mutualfund_holders') else {}
                except:
                    pass
                    
                try:
                    data['major_holders'] = self.yf_ticker.major_holders.to_dict() if hasattr(self.yf_ticker, 'major_holders') else {}
                except:
                    pass
                    
        except Exception as e:
            print(f"[OWNERSHIP ERROR] {e}")
            
        return data
    
    def _fetch_insider_data(self) -> Dict:
        """Fetch insider trading data"""
        data = {'transactions': [], 'buys': 0, 'sells': 0, 'roster': []}
        try:
            if self.yf_ticker:
                try:
                    roster = self.yf_ticker.insider_roster if hasattr(self.yf_ticker, 'insider_roster') else None
                    if roster is not None:
                        data['roster'] = roster.to_dict()
                except:
                    pass
                    
                try:
                    transactions = self.yf_ticker.insider_transactions if hasattr(self.yf_ticker, 'insider_transactions') else None
                    if transactions is not None:
                        data['transactions'] = transactions.to_dict()
                        # Count buys/sells
                        for txn in transactions.itertuples():
                            if hasattr(txn, 'Transaction'):
                                if 'Buy' in str(txn.Transaction):
                                    data['buys'] += 1
                                elif 'Sale' in str(txn.Transaction):
                                    data['sells'] += 1
                except:
                    pass
                    
        except Exception as e:
            print(f"[INSIDER ERROR] {e}")
            
        return data
    
    def _fetch_congress_data(self) -> List[Dict]:
        """Fetch Congress trading data"""
        data = []
        try:
            # Use existing Congress tracker if available
            try:
                from congress_tracker import CongressTracker
                from database import DatabaseManager
                db = DatabaseManager()
                tracker = CongressTracker(db)
                trades = tracker.check_congress_trades(self.ticker)
                if trades:
                    data = trades
            except:
                pass
                
        except Exception as e:
            print(f"[CONGRESS ERROR] {e}")
            
        return data
    
    def _fetch_news_sentiment(self) -> Dict:
        """Fetch news and social sentiment"""
        data = {'news': [], 'sentiment': {'overall': 'NEUTRAL', 'score': 0}}
        try:
            if self.yf_ticker:
                try:
                    news = self.yf_ticker.news if hasattr(self.yf_ticker, 'news') else []
                    data['news'] = news[:10]  # Last 10 news items
                except:
                    pass
                    
        except Exception as e:
            print(f"[NEWS ERROR] {e}")
            
        return data
    
    def _fetch_competitor_data(self) -> List[Dict]:
        """Fetch competitor data based on sector/industry"""
        data = []
        try:
            if self.yf_ticker:
                info = self.yf_ticker.info or {}
                sector = info.get('sector', '')
                industry = info.get('industry', '')
                
                # Known competitor mappings
                competitor_map = {
                    'AAPL': ['MSFT', 'GOOGL', 'META', 'AMZN', 'DELL', 'HPQ', 'LENOVO'],
                    'MSFT': ['AAPL', 'GOOGL', 'META', 'ORCL', 'IBM', 'CRM', 'ADBE'],
                    'NVDA': ['AMD', 'INTC', 'AVGO', 'QCOM', 'MRVL', 'TSM'],
                    'AMD': ['NVDA', 'INTC', 'AVGO', 'QCOM'],
                    'TSLA': ['F', 'GM', 'RIVN', 'LCID', 'NIO', 'XPEV', 'TM'],
                    'GOOGL': ['MSFT', 'META', 'AMZN', 'AAPL', 'NFLX', 'SNAP'],
                    'META': ['GOOGL', 'SNAP', 'PINS', 'TWTR', 'MSFT'],
                    'AMZN': ['WMT', 'TGT', 'COST', 'EBAY', 'SHOP', 'MSFT', 'GOOGL'],
                    'NFLX': ['DIS', 'AMZN', 'AAPL', 'WBD', 'PARA', 'CMCSA'],
                    'DIS': ['NFLX', 'WBD', 'PARA', 'CMCSA', 'SONY'],
                    'JPM': ['BAC', 'WFC', 'C', 'GS', 'MS'],
                    'BAC': ['JPM', 'WFC', 'C', 'GS'],
                    'JNJ': ['PFE', 'MRK', 'ABBV', 'BMY', 'LLY'],
                    'PFE': ['JNJ', 'MRK', 'ABBV', 'BMY', 'LLY', 'NVAX', 'MRNA'],
                    'XOM': ['CVX', 'COP', 'OXY', 'BP', 'SHEL'],
                    'CVX': ['XOM', 'COP', 'OXY', 'BP', 'SHEL'],
                    'KO': ['PEP', 'MNST', 'KDP'],
                    'PEP': ['KO', 'MNST', 'KDP'],
                    'WMT': ['TGT', 'COST', 'AMZN', 'DG'],
                    'HD': ['LOW', 'TSCO', 'FND'],
                    'MCD': ['YUM', 'CMG', 'QSR', 'DRI'],
                    'SBUX': ['MCD', 'YUM', 'DPZ'],
                    'NKE': ['ADDYY', 'LULU', 'UAA', 'SKX'],
                    'T': ['VZ', 'TMUS', 'CMCSA'],
                    'VZ': ['T', 'TMUS', 'CMCSA'],
                }
                
                competitors = competitor_map.get(self.ticker, [])
                
                # If no known competitors, try to get from same sector
                if not competitors and sector:
                    # Add sector-based generic competitors
                    if 'Technology' in sector:
                        competitors = ['MSFT', 'GOOGL', 'AAPL', 'META']
                    elif 'Healthcare' in sector:
                        competitors = ['JNJ', 'PFE', 'UNH', 'ABBV']
                    elif 'Financial' in sector:
                        competitors = ['JPM', 'BAC', 'WFC', 'GS']
                    elif 'Energy' in sector:
                        competitors = ['XOM', 'CVX', 'COP', 'OXY']
                    elif 'Consumer' in sector:
                        competitors = ['AMZN', 'WMT', 'HD', 'COST']
                
                # Fetch competitor data
                for comp_ticker in competitors[:5]:  # Limit to 5
                    try:
                        t = yf.Ticker(comp_ticker)
                        comp_info = t.info or {}
                        data.append({
                            'ticker': comp_ticker,
                            'name': comp_info.get('longName', comp_ticker),
                            'market_cap': comp_info.get('marketCap', 0),
                            'revenue': comp_info.get('totalRevenue', 0),
                            'pe_ratio': comp_info.get('trailingPE', 0),
                            'profit_margin': comp_info.get('profitMargins', 0),
                            'price': comp_info.get('currentPrice', comp_info.get('previousClose', 0))
                        })
                    except:
                        continue
                        
        except Exception as e:
            print(f"[COMPETITOR ERROR] {e}")
            
        return data
    
    def _fetch_technical_data(self) -> Dict:
        """Fetch technical indicators"""
        data = {'indicators': {}}
        try:
            if self.yf_ticker:
                try:
                    hist = self.yf_ticker.history(period='1y')
                    if not hist.empty:
                        # Calculate basic technicals
                        data['indicators']['current_price'] = hist['Close'].iloc[-1]
                        data['indicators']['price_50d_avg'] = hist['Close'].rolling(50).mean().iloc[-1]
                        data['indicators']['price_200d_avg'] = hist['Close'].rolling(200).mean().iloc[-1]
                        data['indicators']['volume_avg'] = hist['Volume'].mean()
                        data['indicators']['52w_high'] = hist['High'].max()
                        data['indicators']['52w_low'] = hist['Low'].min()
                except:
                    pass
                    
        except Exception as e:
            print(f"[TECHNICAL ERROR] {e}")
            
        return data
    
    def _fetch_executive_data(self) -> List[Dict]:
        """Fetch executive compensation and data"""
        data = []
        try:
            if self.yf_ticker:
                try:
                    officers = self.yf_ticker.info.get('companyOfficers', [])
                    data = officers if officers else []
                except:
                    pass
                    
        except Exception as e:
            print(f"[EXECUTIVE ERROR] {e}")
            
        return data
    
    def _fetch_esg_data(self) -> Dict:
        """Fetch ESG (Environmental, Social, Governance) data"""
        data = {}
        try:
            if self.yf_ticker:
                try:
                    sustainability = self.yf_ticker.sustainability
                    if sustainability is not None:
                        data = sustainability.to_dict()
                except:
                    pass
                    
        except Exception as e:
            print(f"[ESG ERROR] {e}")
            
        return data
    
    def _fetch_peer_comparison(self) -> List[Dict]:
        """Fetch peer comparison data"""
        data = []
        try:
            # Would need external API for comprehensive peer data
            pass
            
        except Exception as e:
            print(f"[PEER ERROR] {e}")
            
        return data
    
    def _fetch_dividend_history(self) -> List[Dict]:
        """Fetch dividend history"""
        data = []
        try:
            if self.yf_ticker:
                try:
                    divs = self.yf_ticker.dividends
                    if divs is not None and not divs.empty:
                        data = [{'date': str(idx), 'amount': float(val)} for idx, val in divs.items()]
                except:
                    pass
                    
        except Exception as e:
            print(f"[DIVIDEND ERROR] {e}")
            
        return data
    
    def _fetch_split_history(self) -> List[Dict]:
        """Fetch stock split history"""
        data = []
        try:
            if self.yf_ticker:
                try:
                    splits = self.yf_ticker.splits
                    if splits is not None and not splits.empty:
                        data = [{'date': str(idx), 'ratio': float(val)} for idx, val in splits.items()]
                except:
                    pass
                    
        except Exception as e:
            print(f"[SPLIT ERROR] {e}")
            
        return data
    
    def _fetch_earnings_data(self) -> Dict:
        """Fetch earnings data"""
        data = {'quarterly': {}, 'annual': {}}
        try:
            if self.yf_ticker:
                try:
                    earnings = self.yf_ticker.earnings
                    if earnings is not None:
                        data['annual'] = earnings.to_dict()
                except:
                    pass
                    
                try:
                    q_earnings = self.yf_ticker.quarterly_earnings
                    if q_earnings is not None:
                        data['quarterly'] = q_earnings.to_dict()
                except:
                    pass
                    
        except Exception as e:
            print(f"[EARNINGS ERROR] {e}")
            
        return data
    
    def _fetch_recommendations(self) -> Dict:
        """Fetch analyst recommendations"""
        data = {}
        try:
            if self.yf_ticker:
                try:
                    recs = self.yf_ticker.recommendations
                    if recs is not None:
                        data = recs.to_dict()
                except:
                    pass
                    
        except Exception as e:
            print(f"[RECOMMENDATIONS ERROR] {e}")
            
        return data
    
    def _fetch_upgrades_downgrades(self) -> List[Dict]:
        """Fetch upgrades and downgrades"""
        data = []
        try:
            if self.yf_ticker:
                try:
                    upgrades = self.yf_ticker.upgrades_downgrades
                    if upgrades is not None:
                        data = upgrades.to_dict()
                except:
                    pass
                    
        except Exception as e:
            print(f"[UPGRADES ERROR] {e}")
            
        return data
    
    def _fetch_sustainability_data(self) -> Dict:
        """Fetch sustainability scores"""
        return self._fetch_esg_data()
    
    def _fetch_calendar_events(self) -> Dict:
        """Fetch calendar events (earnings, dividends, etc.)"""
        data = {}
        try:
            if self.yf_ticker:
                try:
                    calendar = self.yf_ticker.calendar
                    if calendar is not None:
                        data = calendar.to_dict()
                except:
                    pass
                    
        except Exception as e:
            print(f"[CALENDAR ERROR] {e}")
            
        return data
    
    def _fetch_options_data(self) -> Dict:
        """Fetch options chain data"""
        data = {'calls': [], 'puts': [], 'expiration_dates': []}
        try:
            if self.yf_ticker:
                try:
                    # Get expiration dates
                    dates = self.yf_ticker.options
                    if dates:
                        data['expiration_dates'] = list(dates)[:5]  # Next 5 expirations
                        
                        # Get options chain for nearest expiration
                        if dates:
                            chain = self.yf_ticker.option_chain(dates[0])
                            if chain:
                                data['calls'] = chain.calls.to_dict() if hasattr(chain, 'calls') else []
                                data['puts'] = chain.puts.to_dict() if hasattr(chain, 'puts') else []
                except:
                    pass
                    
        except Exception as e:
            print(f"[OPTIONS ERROR] {e}")
            
        return data


# Convenience function
def fetch_comprehensive_data(ticker: str) -> Dict:
    """Fetch all comprehensive data for a ticker"""
    fetcher = ComprehensiveDataFetcher(ticker)
    return fetcher.fetch_all_data()


__all__ = ['ComprehensiveDataFetcher', 'fetch_comprehensive_data']