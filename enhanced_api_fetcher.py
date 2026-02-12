"""
Enhanced API Fetcher - Integrates Alpha Vantage, SEC EDGAR, Google Search, and Twikit
Extends comprehensive_data_fetcher with additional API sources
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
from bs4 import BeautifulSoup
import yfinance as yf

# Import API configurations
from config import (
    ALPHA_VANTAGE_API_KEY, ENABLE_ALPHA_VANTAGE,
    SEC_EDGAR_API_KEY, SEC_EDGAR_EMAIL, ENABLE_SEC_EDGAR,
    GOOGLE_API_KEY, GOOGLE_CSE_ID, ENABLE_GOOGLE_SEARCH,
    ENABLE_TWITTER, TWITTER_USERNAME, TWITTER_EMAIL, TWITTER_PASSWORD,
    USER_AGENT, API_DELAY
)


class EnhancedAPIFetcher:
    """Fetches enhanced data using Alpha Vantage, SEC EDGAR, Google, and Twikit"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT
        })
        
    def fetch_all_enhanced_data(self) -> Dict:
        """Fetch all enhanced data from new APIs"""
        print(f"[ENHANCED API] Fetching enhanced data for {self.ticker}...")
        
        data = {
            'alpha_vantage': self._fetch_alpha_vantage(),
            'sec_edgar': self._fetch_sec_edgar(),
            'google_search': self._fetch_google_search(),
            'twitter': self._fetch_twitter_data(),
        }
        
        print(f"[ENHANCED API] ✓ Enhanced data fetch complete for {self.ticker}")
        return data
    
    # -------------------------------------------------------------------------
    # Alpha Vantage Integration
    # -------------------------------------------------------------------------
    
    def _fetch_alpha_vantage(self) -> Dict:
        """Fetch data from Alpha Vantage API"""
        if not ENABLE_ALPHA_VANTAGE or not ALPHA_VANTAGE_API_KEY:
            return {'error': 'Alpha Vantage not enabled'}
        
        data = {}
        
        # Company Overview
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'OVERVIEW',
                'symbol': self.ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                overview = response.json()
                if overview and 'Symbol' in overview:
                    data['overview'] = overview
                    print(f"[ALPHA VANTAGE] ✓ Company overview fetched")
        except Exception as e:
            print(f"[ALPHA VANTAGE ERROR] Overview: {e}")
        
        time.sleep(12)  # Rate limit: 5 calls per minute
        
        # Income Statement
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'INCOME_STATEMENT',
                'symbol': self.ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                income = response.json()
                if income and 'annualReports' in income:
                    data['income_statement'] = income
                    print(f"[ALPHA VANTAGE] ✓ Income statement fetched")
        except Exception as e:
            print(f"[ALPHA VANTAGE ERROR] Income: {e}")
        
        time.sleep(12)  # Rate limit
        
        # Balance Sheet
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'BALANCE_SHEET',
                'symbol': self.ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                balance = response.json()
                if balance and 'annualReports' in balance:
                    data['balance_sheet'] = balance
                    print(f"[ALPHA VANTAGE] ✓ Balance sheet fetched")
        except Exception as e:
            print(f"[ALPHA VANTAGE ERROR] Balance: {e}")
        
        time.sleep(12)  # Rate limit
        
        # Cash Flow
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'CASH_FLOW',
                'symbol': self.ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                cashflow = response.json()
                if cashflow and 'annualReports' in cashflow:
                    data['cash_flow'] = cashflow
                    print(f"[ALPHA VANTAGE] ✓ Cash flow fetched")
        except Exception as e:
            print(f"[ALPHA VANTAGE ERROR] Cash Flow: {e}")
        
        time.sleep(12)  # Rate limit
        
        # Earnings
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'EARNINGS',
                'symbol': self.ticker,
                'apikey': ALPHA_VANTAGE_API_KEY
            }
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                earnings = response.json()
                if earnings and 'annualEarnings' in earnings:
                    data['earnings'] = earnings
                    print(f"[ALPHA VANTAGE] ✓ Earnings fetched")
        except Exception as e:
            print(f"[ALPHA VANTAGE ERROR] Earnings: {e}")
        
        return data
    
    # -------------------------------------------------------------------------
    # SEC EDGAR Integration
    # -------------------------------------------------------------------------
    
    def _fetch_sec_edgar(self) -> Dict:
        """Fetch data from SEC EDGAR API"""
        if not ENABLE_SEC_EDGAR or not SEC_EDGAR_API_KEY:
            return {'error': 'SEC EDGAR not enabled'}
        
        data = {
            'filings': [],
            'submissions': {},
            'company_info': {}
        }
        
        try:
            # First, get CIK from ticker
            headers = {
                'User-Agent': f'{USER_AGENT} {SEC_EDGAR_EMAIL}',
                'Authorization': f'Bearer {SEC_EDGAR_API_KEY}'
            }
            
            # SEC requires email in User-Agent
            search_url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={self.ticker}&output=json'
            
            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                company_data = response.json()
                if company_data:
                    data['company_info'] = company_data
                    print(f"[SEC EDGAR] ✓ Company info fetched")
            
            # Get recent filings
            time.sleep(API_DELAY)
            
            # Get submissions (recent filings)
            cik = self._get_cik_from_ticker(self.ticker)
            if cik:
                submissions_url = f'https://data.sec.gov/submissions/CIK{cik}.json'
                headers['User-Agent'] = f'TurdNewsNetwork {SEC_EDGAR_EMAIL}'
                
                response = self.session.get(submissions_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    submissions = response.json()
                    data['submissions'] = submissions
                    
                    # Extract recent 10-K, 10-Q, 8-K
                    recent_filings = submissions.get('filings', {}).get('recent', {})
                    if recent_filings:
                        forms = recent_filings.get('form', [])
                        filing_dates = recent_filings.get('filingDate', [])
                        primary_docs = recent_filings.get('primaryDocument', [])
                        accession_nums = recent_filings.get('accessionNumber', [])
                        
                        filings_list = []
                        for i, form in enumerate(forms[:20]):  # Last 20 filings
                            if form in ['10-K', '10-Q', '8-K', 'DEF 14A', '4']:
                                filings_list.append({
                                    'form': form,
                                    'date': filing_dates[i] if i < len(filing_dates) else '',
                                    'document': primary_docs[i] if i < len(primary_docs) else '',
                                    'accession': accession_nums[i] if i < len(accession_nums) else ''
                                })
                        
                        data['filings'] = filings_list
                        print(f"[SEC EDGAR] ✓ {len(filings_list)} filings fetched")
                        
        except Exception as e:
            print(f"[SEC EDGAR ERROR] {e}")
        
        return data
    
    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK number from ticker symbol"""
        try:
            # SEC tickers JSON
            url = 'https://www.sec.gov/files/company_tickers.json'
            headers = {'User-Agent': f'TurdNewsNetwork {SEC_EDGAR_EMAIL}'}
            
            response = self.session.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                tickers_data = response.json()
                for entry in tickers_data.values():
                    if entry.get('ticker', '').upper() == ticker.upper():
                        cik = str(entry.get('cik_str', ''))
                        # Pad with zeros to 10 digits
                        return cik.zfill(10)
        except Exception as e:
            print(f"[CIK LOOKUP ERROR] {e}")
        return None
    
    # -------------------------------------------------------------------------
    # Google Custom Search Integration
    # -------------------------------------------------------------------------
    
    def _fetch_google_search(self) -> Dict:
        """Fetch data from Google Custom Search API"""
        if not ENABLE_GOOGLE_SEARCH or not GOOGLE_API_KEY:
            return {'error': 'Google Search not enabled'}
        
        data = {
            'company_images': [],
            'product_images': [],
            'recent_news': []
        }
        
        try:
            # Search for company images
            search_url = 'https://www.googleapis.com/customsearch/v1'
            
            # Get company logo and images
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID if GOOGLE_CSE_ID else '017576662512468239146:omuauf_lfve',  # Default CSE
                'q': f'{self.ticker} company logo',
                'searchType': 'image',
                'num': 3
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                image_results = response.json()
                if 'items' in image_results:
                    data['company_images'] = [
                        {
                            'link': item.get('link'),
                            'thumbnail': item.get('image', {}).get('thumbnailLink'),
                            'title': item.get('title')
                        }
                        for item in image_results['items']
                    ]
                    print(f"[GOOGLE SEARCH] ✓ {len(data['company_images'])} images found")
            
            time.sleep(API_DELAY)
            
            # Search for recent news
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID if GOOGLE_CSE_ID else '017576662512468239146:omuauf_lfve',
                'q': f'{self.ticker} stock news',
                'dateRestrict': 'd7',  # Last 7 days
                'num': 5
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            if response.status_code == 200:
                news_results = response.json()
                if 'items' in news_results:
                    data['recent_news'] = [
                        {
                            'title': item.get('title'),
                            'link': item.get('link'),
                            'snippet': item.get('snippet'),
                            'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', '')
                        }
                        for item in news_results['items']
                    ]
                    print(f"[GOOGLE SEARCH] ✓ {len(data['recent_news'])} news items found")
                    
        except Exception as e:
            print(f"[GOOGLE SEARCH ERROR] {e}")
        
        return data
    
    # -------------------------------------------------------------------------
    # Twikit/Twitter Integration
    # -------------------------------------------------------------------------
    
    def _fetch_twitter_data(self) -> Dict:
        """Fetch Twitter data using twikit (scraping library)"""
        if not ENABLE_TWITTER:
            return {'error': 'Twitter not enabled'}
        
        data = {
            'mentions': [],
            'sentiment_summary': {},
            'trending_hashtags': []
        }
        
        try:
            # Try to import twikit
            try:
                from twikit import Client
            except ImportError:
                print("[TWITTER] twikit not installed. Run: pip install twikit")
                return {'error': 'twikit not installed'}
            
            # Initialize client
            client = Client()
            
            # Search for ticker mentions
            search_query = f"${self.ticker} OR #{self.ticker}"
            
            try:
                # Get tweets (this uses web scraping, no API key needed)
                # Note: search_tweet is async, need to handle it properly
                import asyncio
                
                async def fetch_tweets():
                    return await client.search_tweet(search_query, 'Latest')
                
                tweets = asyncio.run(fetch_tweets())
                
                mentions = []
                sentiments = []
                hashtags = []
                
                for tweet in tweets[:20]:  # Last 20 tweets
                    mentions.append({
                        'text': tweet.text[:280],
                        'author': tweet.user.name,
                        'date': tweet.created_at,
                        'likes': tweet.favorite_count,
                        'retweets': tweet.retweet_count
                    })
                    
                    # Extract hashtags
                    if hasattr(tweet, 'hashtags'):
                        hashtags.extend(tweet.hashtags)
                
                data['mentions'] = mentions
                data['trending_hashtags'] = list(set(hashtags))[:10]
                
                print(f"[TWITTER] ✓ {len(mentions)} mentions found")
                
            except Exception as e:
                print(f"[TWITTER SEARCH ERROR] {e}")
                
        except Exception as e:
            print(f"[TWITTER ERROR] {e}")
        
        return data
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def get_enhanced_financials(self) -> Dict:
        """Get enhanced financial data from Alpha Vantage"""
        av_data = self._fetch_alpha_vantage()
        
        enhanced = {
            'revenue_growth': '',
            'profit_margin': '',
            'operating_margin': '',
            'ebitda': '',
            'eps_growth': '',
            'return_on_equity': '',
            'return_on_assets': '',
            'debt_to_equity': '',
            'current_ratio': '',
            'quick_ratio': ''
        }
        
        overview = av_data.get('overview', {})
        if overview:
            enhanced = {
                'revenue_growth': overview.get('QuarterlyRevenueGrowthYOY', 'N/A'),
                'profit_margin': overview.get('ProfitMargin', 'N/A'),
                'operating_margin': overview.get('OperatingMarginTTM', 'N/A'),
                'ebitda': overview.get('EBITDA', 'N/A'),
                'eps_growth': overview.get('QuarterlyEarningsGrowthYOY', 'N/A'),
                'return_on_equity': overview.get('ReturnOnEquityTTM', 'N/A'),
                'return_on_assets': overview.get('ReturnOnAssetsTTM', 'N/A'),
                'debt_to_equity': overview.get('DebtToEquityRatio', 'N/A'),
                'current_ratio': overview.get('CurrentRatio', 'N/A'),
                'quick_ratio': overview.get('QuickRatio', 'N/A'),
                'sector': overview.get('Sector', 'N/A'),
                'industry': overview.get('Industry', 'N/A'),
                'market_cap': overview.get('MarketCapitalization', 'N/A'),
                'pe_ratio': overview.get('PERatio', 'N/A'),
                'peg_ratio': overview.get('PEGRatio', 'N/A'),
                'book_value': overview.get('BookValue', 'N/A'),
                'dividend_yield': overview.get('DividendYield', 'N/A'),
                'eps': overview.get('EPS', 'N/A'),
                'beta': overview.get('Beta', 'N/A'),
                '52_week_high': overview.get('52WeekHigh', 'N/A'),
                '52_week_low': overview.get('52WeekLow', 'N/A'),
                '50_day_ma': overview.get('50DayMovingAverage', 'N/A'),
                '200_day_ma': overview.get('200DayMovingAverage', 'N/A'),
                'shares_outstanding': overview.get('SharesOutstanding', 'N/A'),
                'dividend_date': overview.get('DividendDate', 'N/A'),
                'ex_dividend_date': overview.get('ExDividendDate', 'N/A'),
                'description': overview.get('Description', ''),
                'asset_type': overview.get('AssetType', ''),
                'name': overview.get('Name', self.ticker),
                'exchange': overview.get('Exchange', 'N/A'),
                'currency': overview.get('Currency', 'USD'),
                'country': overview.get('Country', 'USA'),
                'full_time_employees': overview.get('FullTimeEmployees', 'N/A'),
                'fiscal_year_end': overview.get('FiscalYearEnd', 'N/A'),
                'latest_quarter': overview.get('LatestQuarter', 'N/A')
            }
        
        return enhanced
    
    def get_sec_filings_detailed(self) -> List[Dict]:
        """Get detailed SEC filings"""
        sec_data = self._fetch_sec_edgar()
        return sec_data.get('filings', [])
    
    def get_company_images(self) -> List[Dict]:
        """Get company images from Google Search"""
        google_data = self._fetch_google_search()
        return google_data.get('company_images', [])


# Convenience function
def fetch_enhanced_data(ticker: str) -> Dict:
    """Fetch all enhanced data for a ticker"""
    fetcher = EnhancedAPIFetcher(ticker)
    return fetcher.fetch_all_enhanced_data()


__all__ = ['EnhancedAPIFetcher', 'fetch_enhanced_data']