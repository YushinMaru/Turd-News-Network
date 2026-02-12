"""
Enhanced Data Enrichment Module
Combines Twitter sentiment, SEC EDGAR, Economic Calendar, and advanced ML features
"""

import asyncio
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from bs4 import BeautifulSoup
import numpy as np
from scipy import stats

from config import (
    USER_AGENT, ENABLE_TWITTER, TWITTER_BEARER_TOKEN,
    SEC_EDGAR_EMAIL, ALPHA_VANTAGE_API_KEY,
    FINNHUB_API_KEY, ECONOMIC_CALENDAR_API_KEY
)
from database import DatabaseManager


class EnhancedDataEnrichment:
    """Enriches stock data with Twitter, SEC, Economic Calendar, and ML features"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    # =========================================================================
    # TWITTER/X SENTIMENT SCRAPER
    # =========================================================================
    
    def fetch_twitter_sentiment(self, ticker: str, limit: int = 100) -> Dict:
        """Fetch recent Twitter sentiment for a ticker"""
        if not ENABLE_TWITTER or not TWITTER_BEARER_TOKEN:
            return {'sentiment': 'NEUTRAL', 'score': 0, 'tweet_count': 0}
        
        try:
            headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}
            query = f"${ticker} -is:retweet lang:en"
            
            url = 'https://api.twitter.com/2/tweets/search/recent'
            params = {
                'query': query,
                'max_results': min(limit, 100),
                'tweet.fields': 'created_at,public_metrics,author_id',
                'user.fields': 'public_metrics,verified'
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return {'sentiment': 'NEUTRAL', 'score': 0, 'tweet_count': 0}
            
            data = response.json()
            tweets = data.get('data', [])
            
            if not tweets:
                return {'sentiment': 'NEUTRAL', 'score': 0, 'tweet_count': 0}
            
            # Analyze sentiment using basic keyword analysis
            bullish_keywords = ['buy', 'long', 'bull', 'moon', 'rocket', '🚀', '💰', 'calls', 'cheap', 'undervalued']
            bearish_keywords = ['sell', 'short', 'bear', 'crash', 'dump', '💩', 'puts', 'overvalued', 'bubble']
            
            bullish_count = 0
            bearish_count = 0
            total_engagement = 0
            
            for tweet in tweets:
                text = tweet.get('text', '').lower()
                metrics = tweet.get('public_metrics', {})
                engagement = metrics.get('like_count', 0) + metrics.get('retweet_count', 0)
                total_engagement += engagement
                
                # Weight by engagement
                weight = 1 + (engagement / 100)
                
                if any(kw in text for kw in bullish_keywords):
                    bullish_count += weight
                elif any(kw in text for kw in bearish_keywords):
                    bearish_count += weight
            
            # Calculate sentiment
            total = bullish_count + bearish_count
            if total == 0:
                sentiment = 'NEUTRAL'
                score = 0
            else:
                score = (bullish_count - bearish_count) / total
                if score > 0.2:
                    sentiment = 'BULLISH'
                elif score < -0.2:
                    sentiment = 'BEARISH'
                else:
                    sentiment = 'NEUTRAL'
            
            result = {
                'sentiment': sentiment,
                'score': round(score, 2),
                'tweet_count': len(tweets),
                'bullish_count': int(bullish_count),
                'bearish_count': int(bearish_count),
                'total_engagement': total_engagement
            }
            
            # Save to database
            self._save_twitter_sentiment(ticker, tweets, result)
            
            return result
            
        except Exception as e:
            print(f"[TWITTER] Error fetching sentiment for {ticker}: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0, 'tweet_count': 0}
    
    def _save_twitter_sentiment(self, ticker: str, tweets: List[Dict], analysis: Dict):
        """Save Twitter sentiment to database"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            for tweet in tweets:
                try:
                    c.execute('''INSERT OR IGNORE INTO twitter_sentiment
                                 (ticker, tweet_date, tweet_id, tweet_text, author,
                                  sentiment, sentiment_score, likes, retweets, replies)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (ticker, tweet.get('created_at', ''), tweet.get('id', ''),
                               tweet.get('text', '')[:500], tweet.get('author_id', ''),
                               analysis['sentiment'], analysis['score'],
                               tweet.get('public_metrics', {}).get('like_count', 0),
                               tweet.get('public_metrics', {}).get('retweet_count', 0),
                               tweet.get('public_metrics', {}).get('reply_count', 0)))
                except:
                    continue
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[TWITTER] Error saving sentiment: {e}")
    
    # =========================================================================
    # SEC EDGAR INSIDER TRADING
    # =========================================================================
    
    def fetch_sec_insider_trades(self, ticker: str) -> List[Dict]:
        """Fetch recent SEC EDGAR Form 4 insider transactions"""
        try:
            # Use SEC EDGAR full-text search
            cik = self._get_cik_from_ticker(ticker)
            if not cik:
                return []
            
            # Get recent Form 4 filings
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4&dateb=&owner=only&count=10&output=atom"
            headers = {'User-Agent': f'{USER_AGENT} {SEC_EDGAR_EMAIL}'}
            
            response = self.session.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                return []
            
            # Parse XML
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('entry')
            
            trades = []
            for entry in entries:
                try:
                    filing_url = entry.find('link')['href'] if entry.find('link') else ''
                    filing_date = entry.find('updated').text[:10] if entry.find('updated') else ''
                    
                    # Get transaction details from filing
                    if filing_url:
                        trade_details = self._parse_form4_filing(filing_url)
                        if trade_details:
                            trade_details['filing_date'] = filing_date
                            trades.append(trade_details)
                except:
                    continue
            
            # Save to database
            self._save_sec_insider_trades(ticker, trades)
            
            return trades
            
        except Exception as e:
            print(f"[SEC EDGAR] Error fetching insider trades for {ticker}: {e}")
            return []
    
    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK number from ticker"""
        try:
            url = 'https://www.sec.gov/files/company_tickers.json'
            headers = {'User-Agent': f'{USER_AGENT} {SEC_EDGAR_EMAIL}'}
            
            response = self.session.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for entry in data.values():
                    if entry.get('ticker', '').upper() == ticker.upper():
                        return str(entry.get('cik_str', '')).zfill(10)
        except:
            pass
        return None
    
    def _parse_form4_filing(self, filing_url: str) -> Optional[Dict]:
        """Parse Form 4 XML for transaction details"""
        try:
            # Get the actual filing document
            headers = {'User-Agent': f'{USER_AGENT} {SEC_EDGAR_EMAIL}'}
            
            # Fetch the filing index page
            response = self.session.get(filing_url, headers=headers, timeout=30)
            if response.status_code != 200:
                return None
            
            # Find the XML document link
            soup = BeautifulSoup(response.content, 'html.parser')
            xml_link = None
            for link in soup.find_all('a'):
                if link.get('href', '').endswith('.xml'):
                    xml_link = link['href']
                    break
            
            if not xml_link:
                return None
            
            # Fetch the XML document
            if not xml_link.startswith('http'):
                xml_link = f"https://www.sec.gov{xml_link}"
            
            xml_response = self.session.get(xml_link, headers=headers, timeout=30)
            if xml_response.status_code != 200:
                return None
            
            # Parse the XML
            xml_soup = BeautifulSoup(xml_response.content, 'xml')
            
            # Extract insider info
            insider_name = xml_soup.find('rptOwnerName')
            insider_name = insider_name.text if insider_name else 'Unknown'
            
            insider_title = xml_soup.find('officerTitle')
            insider_title = insider_title.text if insider_title else ''
            
            # Extract transaction details
            trans_shares = xml_soup.find('transactionShares')
            trans_price = xml_soup.find('transactionPricePerShare')
            trans_type = xml_soup.find('transactionCode')
            
            if not trans_shares:
                return None
            
            shares = int(float(trans_shares.text)) if trans_shares.text else 0
            price = float(trans_price.text) if trans_price and trans_price.text else 0
            txn_type = trans_type.text if trans_type else 'A'
            
            # Determine buy/sell
            if txn_type in ['P', 'A']:
                trans_type_desc = 'PURCHASE'
            elif txn_type in ['S', 'D']:
                trans_type_desc = 'SALE'
            else:
                trans_type_desc = 'OTHER'
            
            return {
                'insider_name': insider_name,
                'insider_title': insider_title,
                'transaction_type': trans_type_desc,
                'shares': shares,
                'price_per_share': price,
                'total_value': shares * price,
                'form_type': '4',
                'filing_url': filing_url
            }
            
        except Exception as e:
            print(f"[SEC EDGAR] Error parsing Form 4: {e}")
            return None
    
    def _save_sec_insider_trades(self, ticker: str, trades: List[Dict]):
        """Save SEC insider trades to database"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            for trade in trades:
                try:
                    c.execute('''INSERT OR IGNORE INTO sec_insider_filings
                                 (ticker, filing_date, transaction_date, insider_name,
                                  insider_title, transaction_type, shares, price_per_share,
                                  total_value, form_type, filing_url)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (ticker, trade.get('filing_date'), trade.get('transaction_date'),
                               trade.get('insider_name'), trade.get('insider_title'),
                               trade.get('transaction_type'), trade.get('shares'),
                               trade.get('price_per_share'), trade.get('total_value'),
                               trade.get('form_type'), trade.get('filing_url')))
                except:
                    continue
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SEC EDGAR] Error saving trades: {e}")
    
    # =========================================================================
    # ECONOMIC CALENDAR
    # =========================================================================
    
    def fetch_economic_calendar(self, days_ahead: int = 7) -> List[Dict]:
        """Fetch upcoming economic events from ForexFactory or similar"""
        try:
            # Use ForexFactory calendar (free, no API key needed)
            today = datetime.now()
            events = []
            
            for day_offset in range(days_ahead):
                date = today + timedelta(days=day_offset)
                date_str = date.strftime('%Y-%m-%d')
                
                # Try to fetch from ForexFactory
                url = f"https://www.forexfactory.com/calendar?day={date.strftime('%b')}{date.day}.{date.year}"
                
                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Parse events from the table
                        rows = soup.find_all('tr', class_='calendar_row')
                        
                        for row in rows:
                            try:
                                time_elem = row.find('td', class_='calendar__time')
                                currency_elem = row.find('td', class_='calendar__currency')
                                event_elem = row.find('td', class_='calendar__event')
                                impact_elem = row.find('td', class_='calendar__impact')
                                
                                if event_elem:
                                    event_name = event_elem.text.strip()
                                    currency = currency_elem.text.strip() if currency_elem else 'USD'
                                    
                                    # Determine impact level
                                    impact = 'MEDIUM'
                                    if impact_elem:
                                        if 'high' in str(impact_elem).lower():
                                            impact = 'HIGH'
                                        elif 'low' in str(impact_elem).lower():
                                            impact = 'LOW'
                                    
                                    events.append({
                                        'event_date': date_str,
                                        'event_time': time_elem.text.strip() if time_elem else '',
                                        'country': currency,
                                        'event_name': event_name,
                                        'impact_level': impact
                                    })
                            except:
                                continue
                except:
                    continue
            
            # Save to database
            self._save_economic_calendar(events)
            
            return events
            
        except Exception as e:
            print(f"[ECONOMIC CALENDAR] Error fetching: {e}")
            return []
    
    def _save_economic_calendar(self, events: List[Dict]):
        """Save economic calendar events to database"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            for event in events:
                try:
                    c.execute('''INSERT OR IGNORE INTO economic_calendar
                                 (event_date, event_time, country, event_name, impact_level)
                                 VALUES (?, ?, ?, ?, ?)''',
                              (event['event_date'], event['event_time'], event['country'],
                               event['event_name'], event['impact_level']))
                except:
                    continue
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ECONOMIC CALENDAR] Error saving: {e}")
    
    # =========================================================================
    # CORRELATION ANALYSIS
    # =========================================================================
    
    def calculate_ticker_correlation(self, ticker_a: str, ticker_b: str, period: str = '1y') -> Optional[Dict]:
        """Calculate price correlation between two tickers"""
        try:
            # Fetch price history for both tickers
            stock_a = yf.Ticker(ticker_a)
            stock_b = yf.Ticker(ticker_b)
            
            hist_a = stock_a.history(period=period)
            hist_b = stock_b.history(period=period)
            
            if hist_a.empty or hist_b.empty:
                return None
            
            # Align dates
            combined = hist_a['Close'].rename('a').to_frame().join(
                hist_b['Close'].rename('b'), how='inner'
            )
            
            if len(combined) < 30:
                return None
            
            # Calculate returns
            returns_a = combined['a'].pct_change().dropna()
            returns_b = combined['b'].pct_change().dropna()
            
            # Calculate correlation
            if len(returns_a) != len(returns_b):
                min_len = min(len(returns_a), len(returns_b))
                returns_a = returns_a[-min_len:]
                returns_b = returns_b[-min_len:]
            
            correlation, p_value = stats.pearsonr(returns_a, returns_b)
            
            result = {
                'ticker_a': ticker_a,
                'ticker_b': ticker_b,
                'correlation_coefficient': round(correlation, 4),
                'correlation_period': period,
                'p_value': round(p_value, 6),
                'is_significant': p_value < 0.05,
                'calculation_date': datetime.now().isoformat()
            }
            
            # Save to database
            self._save_correlation(result)
            
            return result
            
        except Exception as e:
            print(f"[CORRELATION] Error calculating: {e}")
            return None
    
    def _save_correlation(self, correlation: Dict):
        """Save correlation to database"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''INSERT OR REPLACE INTO ticker_correlations
                         (ticker_a, ticker_b, correlation_coefficient, correlation_period,
                          calculation_date, p_value, is_significant)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (correlation['ticker_a'], correlation['ticker_b'],
                       correlation['correlation_coefficient'], correlation['correlation_period'],
                       correlation['calculation_date'], correlation['p_value'],
                       correlation['is_significant']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[CORRELATION] Error saving: {e}")
    
    # =========================================================================
    # ML FEATURE GENERATION
    # =========================================================================
    
    def generate_ml_features(self, ticker: str, hist_data=None) -> Dict:
        """Generate comprehensive ML features for a ticker"""
        try:
            if hist_data is None:
                stock = yf.Ticker(ticker)
                hist_data = stock.history(period='6mo')
            
            if hist_data.empty or len(hist_data) < 50:
                return {}
            
            close_prices = hist_data['Close'].values
            high_prices = hist_data['High'].values
            low_prices = hist_data['Low'].values
            volumes = hist_data['Volume'].values
            
            features = {
                'ticker': ticker,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Price changes
            features['price_change_1d'] = self._calculate_return(close_prices, 1)
            features['price_change_5d'] = self._calculate_return(close_prices, 5)
            features['price_change_20d'] = self._calculate_return(close_prices, 20)
            
            # Moving averages
            features['sma_20'] = np.mean(close_prices[-20:]) if len(close_prices) >= 20 else None
            features['sma_50'] = np.mean(close_prices[-50:]) if len(close_prices) >= 50 else None
            features['sma_200'] = np.mean(close_prices[-200:]) if len(close_prices) >= 200 else None
            
            # EMA
            features['ema_12'] = self._calculate_ema(close_prices, 12)
            features['ema_26'] = self._calculate_ema(close_prices, 26)
            
            # RSI
            features['rsi'] = self._calculate_rsi(close_prices)
            
            # MACD
            ema_12 = features['ema_12']
            ema_26 = features['ema_26']
            if ema_12 and ema_26:
                features['macd'] = ema_12 - ema_26
                features['macd_signal'] = self._calculate_ema(
                    [features['macd']] * 9, 9
                ) if features['macd'] else None
            
            # Bollinger Bands
            if len(close_prices) >= 20:
                sma_20 = features['sma_20']
                std_20 = np.std(close_prices[-20:])
                features['bollinger_upper'] = sma_20 + (2 * std_20)
                features['bollinger_lower'] = sma_20 - (2 * std_20)
            
            # Volume ratio
            if len(volumes) >= 20:
                features['volume_ratio'] = volumes[-1] / np.mean(volumes[-20:])
            
            # ADX and DI
            adx_data = self._calculate_adx(high_prices, low_prices, close_prices)
            if adx_data:
                features.update(adx_data)
            
            # VWAP
            features['vwap'] = self._calculate_vwap(high_prices, low_prices, close_prices, volumes)
            
            # Save to feature store
            self._save_ml_features(features)
            
            return features
            
        except Exception as e:
            print(f"[ML FEATURES] Error generating for {ticker}: {e}")
            return {}
    
    def _calculate_return(self, prices: np.ndarray, days: int) -> float:
        """Calculate return over N days"""
        if len(prices) < days + 1:
            return 0
        return round((prices[-1] - prices[-(days+1)]) / prices[-(days+1)] * 100, 2)
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return None
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return round(ema, 2)
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    def _calculate_adx(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict:
        """Calculate ADX and DI"""
        try:
            if len(closes) < 28:
                return {}
            
            period = 14
            tr_list = []
            plus_dm_list = []
            minus_dm_list = []
            
            for i in range(1, len(closes)):
                h, l, pc = highs[i], lows[i], closes[i-1]
                tr = max(h - l, abs(h - pc), abs(l - pc))
                tr_list.append(tr)
                
                up = h - highs[i-1]
                down = lows[i-1] - l
                plus_dm = up if up > down and up > 0 else 0
                minus_dm = down if down > up and down > 0 else 0
                plus_dm_list.append(plus_dm)
                minus_dm_list.append(minus_dm)
            
            # Smooth
            atr = sum(tr_list[:period]) / period
            plus_dm_smooth = sum(plus_dm_list[:period]) / period
            minus_dm_smooth = sum(minus_dm_list[:period]) / period
            
            for i in range(period, len(tr_list)):
                atr = (atr * (period-1) + tr_list[i]) / period
                plus_dm_smooth = (plus_dm_smooth * (period-1) + plus_dm_list[i]) / period
                minus_dm_smooth = (minus_dm_smooth * (period-1) + minus_dm_list[i]) / period
            
            plus_di = (plus_dm_smooth / atr * 100) if atr > 0 else 0
            minus_di = (minus_dm_smooth / atr * 100) if atr > 0 else 0
            
            di_sum = plus_di + minus_di
            dx = abs(plus_di - minus_di) / di_sum * 100 if di_sum > 0 else 0
            
            return {
                'adx': round(dx, 2),
                'plus_di': round(plus_di, 2),
                'minus_di': round(minus_di, 2)
            }
        except:
            return {}
    
    def _calculate_vwap(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray) -> float:
        """Calculate VWAP"""
        try:
            period = min(20, len(closes))
            typical = (highs[-period:] + lows[-period:] + closes[-period:]) / 3
            vols = volumes[-period:]
            return round(np.sum(typical * vols) / np.sum(vols), 2)
        except:
            return None
    
    def _save_ml_features(self, features: Dict):
        """Save ML features to database"""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            
            c.execute('''INSERT OR REPLACE INTO ml_feature_store
                         (ticker, date, rsi, macd, macd_signal, bollinger_upper, bollinger_lower,
                          sma_20, sma_50, sma_200, ema_12, ema_26, volume_ratio,
                          adx, plus_di, minus_di, vwap, price_change_1d, price_change_5d, price_change_20d)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (features['ticker'], features['date'],
                       features.get('rsi'), features.get('macd'), features.get('macd_signal'),
                       features.get('bollinger_upper'), features.get('bollinger_lower'),
                       features.get('sma_20'), features.get('sma_50'), features.get('sma_200'),
                       features.get('ema_12'), features.get('ema_26'), features.get('volume_ratio'),
                       features.get('adx'), features.get('plus_di'), features.get('minus_di'),
                       features.get('vwap'), features.get('price_change_1d'),
                       features.get('price_change_5d'), features.get('price_change_20d')))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ML FEATURES] Error saving: {e}")


# Convenience function
def enrich_stock_data(ticker: str, db: DatabaseManager) -> Dict:
    """Enrich stock data with all enhanced sources"""
    enricher = EnhancedDataEnrichment(db)
    
    return {
        'twitter_sentiment': enricher.fetch_twitter_sentiment(ticker),
        'sec_insider_trades': enricher.fetch_sec_insider_trades(ticker),
        'ml_features': enricher.generate_ml_features(ticker)
    }