import sys
import io
import os
import logging
"""
Stock data fetching and analysis module - IMPROVED NEWS PARSING
"""

import yfinance as yf
import statistics
from typing import Dict, Optional, List, Set
from datetime import datetime, timedelta
from database import DatabaseManager
import requests
from bs4 import BeautifulSoup
from config import (
    USER_AGENT, ENABLE_CHARTS, CHART_DIR, CHART_PERIOD, ENABLE_CHART_BOLLINGER,
    ENABLE_OPTIONS_FLOW, OPTIONS_UNUSUAL_VOLUME_THRESHOLD,
    ENABLE_INSIDER_DATA, INSIDER_LOOKBACK_DAYS, FINNHUB_API_KEY,
    ENABLE_ENHANCED_TECHNICALS, ICHIMOKU_TENKAN_PERIOD, ICHIMOKU_KIJUN_PERIOD,
    ICHIMOKU_SENKOU_B_PERIOD
)

# Suppress noisy yfinance/urllib3 error logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('peewee').setLevel(logging.CRITICAL)

# Common international exchange suffixes to try as fallback
EXCHANGE_SUFFIXES = ['', '.TO', '.L', '.AX', '.DE', '.PA', '.HK', '.T', '.NS', '.SI']


class StockDataFetcher:
    """Handles fetching and processing stock data"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._invalid_ticker_cache: Set[str] = set()  # Cache of known-invalid tickers
        self._valid_ticker_cache: Dict[str, str] = {}  # Cache of validated ticker -> actual symbol

    def _validate_ticker(self, ticker: str) -> Optional[str]:
        """
        Validate that a ticker symbol actually exists on an exchange.
        Returns the valid ticker symbol (possibly with exchange suffix) or None.
        Uses a quick Yahoo Finance quote lookup instead of full data fetch.
        """
        # Check caches first
        if ticker in self._invalid_ticker_cache:
            return None
        if ticker in self._valid_ticker_cache:
            return self._valid_ticker_cache[ticker]

        # Try the ticker with different exchange suffixes
        for suffix in EXCHANGE_SUFFIXES:
            test_ticker = f"{ticker}{suffix}"
            try:
                # Quick validation: use a lightweight Yahoo Finance quote check
                # Suppress stderr to avoid noisy 404 error output
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                try:
                    stock = yf.Ticker(test_ticker)
                    # Fast check: get just 5 days of history (minimal data)
                    fast_hist = stock.history(period='5d')
                    info = stock.info
                finally:
                    sys.stderr = old_stderr

                # Validate we got real data back
                if fast_hist.empty:
                    continue

                # Check for the "delisted" or error response from Yahoo
                quote_type = info.get('quoteType', '')
                if not quote_type or quote_type == 'NONE':
                    continue

                # Reject non-equity types that slip through (like currency pairs, indices)
                if quote_type not in ('EQUITY', 'ETF', 'MUTUALFUND'):
                    continue

                # Check if we have a valid price
                if len(fast_hist) < 1:
                    continue

                last_price = fast_hist['Close'].iloc[-1]
                if not last_price or last_price <= 0 or last_price != last_price:
                    continue

                # Valid ticker found!
                self._valid_ticker_cache[ticker] = test_ticker
                if suffix:
                    print(f"   [i]  Found {ticker} on exchange: {test_ticker}")
                return test_ticker

            except Exception:
                continue

        # No valid exchange found
        self._invalid_ticker_cache.add(ticker)
        return None

    def _generate_chart(self, ticker: str, hist_data, w52_high=None, w52_low=None) -> Optional[str]:
        """
        Generate a candlestick chart with technical overlays.
        Returns the file path to the saved PNG or None on failure.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import mplfinance as mpf
        except ImportError:
            return None

        try:
            # Work on a copy to avoid modifying original data
            hist_copy = hist_data.copy()

            # Calculate moving averages on full history
            hist_copy['SMA20'] = hist_copy['Close'].rolling(window=20).mean()
            hist_copy['SMA50'] = hist_copy['Close'].rolling(window=50).mean()
            if len(hist_copy) >= 200:
                hist_copy['SMA200'] = hist_copy['Close'].rolling(window=200).mean()

            # Slice to chart period
            chart_data = hist_copy.tail(CHART_PERIOD).copy()
            if len(chart_data) < 10:
                return None

            # Build overlay plots
            addplots = []
            if 'SMA20' in chart_data.columns and not chart_data['SMA20'].isna().all():
                addplots.append(mpf.make_addplot(chart_data['SMA20'], color='#2196F3', width=0.8))
            if 'SMA50' in chart_data.columns and not chart_data['SMA50'].isna().all():
                addplots.append(mpf.make_addplot(chart_data['SMA50'], color='#FF9800', width=0.8))
            if 'SMA200' in chart_data.columns and not chart_data['SMA200'].isna().all():
                addplots.append(mpf.make_addplot(chart_data['SMA200'], color='#9C27B0', width=0.8))

            # Bollinger Bands
            if ENABLE_CHART_BOLLINGER and 'SMA20' in chart_data.columns:
                std20 = hist_copy['Close'].rolling(window=20).std()
                bb_upper = (hist_copy['SMA20'] + 2 * std20).tail(CHART_PERIOD)
                bb_lower = (hist_copy['SMA20'] - 2 * std20).tail(CHART_PERIOD)
                if not bb_upper.isna().all():
                    addplots.append(mpf.make_addplot(bb_upper, color='#9E9E9E', linestyle='--', width=0.5))
                    addplots.append(mpf.make_addplot(bb_lower, color='#9E9E9E', linestyle='--', width=0.5))

            # 52-week high/low horizontal lines
            hlines_vals = []
            hlines_colors = []
            if w52_high and w52_high > 0:
                hlines_vals.append(w52_high)
                hlines_colors.append('#4CAF50')
            if w52_low and w52_low > 0:
                hlines_vals.append(w52_low)
                hlines_colors.append('#F44336')

            hlines_dict = None
            if hlines_vals:
                hlines_dict = dict(hlines=hlines_vals, colors=hlines_colors, linestyle='-.', linewidths=0.7)

            # Chart directory
            chart_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), CHART_DIR)
            os.makedirs(chart_dir, exist_ok=True)

            # Clean old charts (older than 1 hour)
            import glob as glob_mod
            import time as time_mod
            now = time_mod.time()
            for old_file in glob_mod.glob(os.path.join(chart_dir, '*.png')):
                if now - os.path.getmtime(old_file) > 3600:
                    try:
                        os.remove(old_file)
                    except OSError:
                        pass

            filepath = os.path.join(chart_dir, f"{ticker}_chart.png")

            # Custom style
            mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
            style = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='#e0e0e0',
                facecolor='#fafafa'
            )

            # Plot
            kwargs = dict(
                type='candle',
                style=style,
                volume=True,
                title=f'\n${ticker} - 3 Month Chart',
                savefig=dict(fname=filepath, dpi=120, bbox_inches='tight'),
                figsize=(10, 6),
            )
            if addplots:
                kwargs['addplot'] = addplots
            if hlines_dict:
                kwargs['hlines'] = hlines_dict

            mpf.plot(chart_data, **kwargs)
            plt.close('all')

            if os.path.exists(filepath):
                return filepath
            return None

        except Exception as e:
            print(f"   [!] Chart generation failed for {ticker}: {e}")
            try:
                import matplotlib.pyplot as plt
                plt.close('all')
            except Exception:
                pass
            return None

    def get_options_data(self, ticker: str, valid_ticker: str) -> Optional[Dict]:
        """
        Fetch options chain data for the nearest expiry.
        Returns put/call ratio, max pain, and unusual activity or None.
        """
        if not ENABLE_OPTIONS_FLOW:
            return None

        try:
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                stock = yf.Ticker(valid_ticker)
                expiry_dates = stock.options
            finally:
                sys.stderr = old_stderr

            if not expiry_dates:
                return None

            # Use nearest expiry
            nearest_expiry = expiry_dates[0]

            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                chain = stock.option_chain(nearest_expiry)
            finally:
                sys.stderr = old_stderr

            calls = chain.calls
            puts = chain.puts

            if calls.empty and puts.empty:
                return None

            # Total call/put volume
            total_call_vol = int(calls['volume'].sum()) if 'volume' in calls.columns else 0
            total_put_vol = int(puts['volume'].sum()) if 'volume' in puts.columns else 0
            total_call_oi = int(calls['openInterest'].sum()) if 'openInterest' in calls.columns else 0
            total_put_oi = int(puts['openInterest'].sum()) if 'openInterest' in puts.columns else 0

            # Put/Call ratio (by volume)
            if total_call_vol > 0:
                pc_ratio = round(total_put_vol / total_call_vol, 2)
            else:
                pc_ratio = None

            # Max Pain calculation: strike where total $ value of expiring options is minimized
            max_pain = self._calculate_max_pain(calls, puts)

            # Detect unusual activity: strikes where volume >> open interest
            unusual_strikes = []

            for _, row in calls.iterrows():
                oi = row.get('openInterest', 0)
                vol = row.get('volume', 0)
                if oi and oi > 0 and vol and vol > 0:
                    ratio = vol / oi
                    if ratio >= OPTIONS_UNUSUAL_VOLUME_THRESHOLD:
                        unusual_strikes.append({
                            'strike': row['strike'],
                            'type': 'CALL',
                            'volume': int(vol),
                            'oi': int(oi),
                            'ratio': round(ratio, 1)
                        })

            for _, row in puts.iterrows():
                oi = row.get('openInterest', 0)
                vol = row.get('volume', 0)
                if oi and oi > 0 and vol and vol > 0:
                    ratio = vol / oi
                    if ratio >= OPTIONS_UNUSUAL_VOLUME_THRESHOLD:
                        unusual_strikes.append({
                            'strike': row['strike'],
                            'type': 'PUT',
                            'volume': int(vol),
                            'oi': int(oi),
                            'ratio': round(ratio, 1)
                        })

            # Sort unusual strikes by ratio descending, keep top 3
            unusual_strikes.sort(key=lambda x: x['ratio'], reverse=True)
            unusual_strikes = unusual_strikes[:3]

            return {
                'expiry': nearest_expiry,
                'pc_ratio': pc_ratio,
                'total_call_vol': total_call_vol,
                'total_put_vol': total_put_vol,
                'total_call_oi': total_call_oi,
                'total_put_oi': total_put_oi,
                'max_pain': max_pain,
                'unusual_strikes': unusual_strikes
            }

        except Exception:
            return None

    def _calculate_max_pain(self, calls, puts) -> Optional[float]:
        """
        Calculate max pain price: the strike at which the total dollar value
        of all in-the-money options is minimized (options writers profit most).
        """
        try:
            all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
            if not all_strikes:
                return None

            min_pain = float('inf')
            max_pain_strike = None

            for test_strike in all_strikes:
                total_pain = 0

                # Pain for call holders: calls ITM if strike < test_strike
                for _, row in calls.iterrows():
                    oi = row.get('openInterest', 0) or 0
                    if row['strike'] < test_strike:
                        total_pain += (test_strike - row['strike']) * oi * 100

                # Pain for put holders: puts ITM if strike > test_strike
                for _, row in puts.iterrows():
                    oi = row.get('openInterest', 0) or 0
                    if row['strike'] > test_strike:
                        total_pain += (row['strike'] - test_strike) * oi * 100

                if total_pain < min_pain:
                    min_pain = total_pain
                    max_pain_strike = test_strike

            return max_pain_strike

        except Exception:
            return None

    def get_insider_data(self, ticker: str, valid_ticker: str) -> Optional[Dict]:
        """
        Fetch insider transaction data and institutional ownership info.
        Uses yfinance as primary source, SEC EDGAR EFTS as supplement.
        Returns aggregated insider activity or None.
        """
        if not ENABLE_INSIDER_DATA:
            return None

        buys = 0
        sells = 0
        transactions = []
        inst_pct = None
        insider_pct = None

        try:
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                stock = yf.Ticker(valid_ticker)

                # Major holders: insider % and institutional %
                try:
                    major = stock.major_holders
                    if major is not None and not major.empty:
                        for idx, row in major.iterrows():
                            val_str = str(row.iloc[0]).replace('%', '').strip()
                            label = str(row.iloc[1]).lower() if len(row) > 1 else ''
                            try:
                                val = float(val_str)
                            except (ValueError, TypeError):
                                continue
                            if 'insider' in label:
                                insider_pct = val
                            elif 'institution' in label and 'float' not in label:
                                inst_pct = val
                except Exception:
                    pass

                # Insider transactions
                try:
                    it = stock.insider_transactions
                    if it is not None and not it.empty:
                        cutoff = datetime.now() - timedelta(days=INSIDER_LOOKBACK_DAYS)
                        for _, row in it.iterrows():
                            txn_text = str(row.get('Text', row.get('Transaction', ''))).lower()
                            shares = row.get('Shares', row.get('#Shares', 0))
                            value = row.get('Value', row.get('Value ($)', 0))
                            date_val = row.get('Start Date', row.get('Date', None))
                            name = str(row.get('Insider Trading', row.get('Insider', 'Unknown')))

                            # Parse date
                            txn_date = None
                            if date_val is not None:
                                try:
                                    if hasattr(date_val, 'to_pydatetime'):
                                        txn_date = date_val.to_pydatetime()
                                    elif isinstance(date_val, str):
                                        txn_date = datetime.strptime(date_val, '%Y-%m-%d')
                                except Exception:
                                    txn_date = None

                            # Filter by lookback window
                            if txn_date and txn_date.replace(tzinfo=None) < cutoff:
                                continue

                            # Classify transaction
                            if 'purchase' in txn_text or 'buy' in txn_text or 'acquisition' in txn_text:
                                txn_type = 'BUY'
                                buys += 1
                            elif 'sale' in txn_text or 'sell' in txn_text or 'disposition' in txn_text:
                                txn_type = 'SELL'
                                sells += 1
                            else:
                                txn_type = 'OTHER'

                            try:
                                shares_int = int(float(str(shares).replace(',', ''))) if shares else 0
                            except (ValueError, TypeError):
                                shares_int = 0
                            try:
                                value_float = float(str(value).replace(',', '').replace('$', '')) if value else 0
                            except (ValueError, TypeError):
                                value_float = 0

                            transactions.append({
                                'name': name[:50],
                                'title': '',
                                'type': txn_type,
                                'shares': shares_int,
                                'value': value_float,
                                'date': txn_date.strftime('%Y-%m-%d') if txn_date else ''
                            })
                except Exception:
                    pass

            finally:
                sys.stderr = old_stderr

        except Exception:
            pass

        # Supplement with Finnhub if API key provided
        if FINNHUB_API_KEY and inst_pct is None:
            try:
                url = f'https://finnhub.io/api/v1/stock/institutional-ownership?symbol={ticker}&token={FINNHUB_API_KEY}'
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    ownership = data.get('ownership', [])
                    if ownership:
                        latest = ownership[0]
                        inst_pct = latest.get('ownershipPercent')
            except Exception:
                pass

        # Only return if we have any useful data
        if buys == 0 and sells == 0 and inst_pct is None and insider_pct is None:
            return None

        return {
            'buys': buys,
            'sells': sells,
            'net': buys - sells,
            'transactions': transactions[:10],
            'institutional_pct': inst_pct,
            'insider_pct': insider_pct,
            'lookback_days': INSIDER_LOOKBACK_DAYS
        }

    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Get comprehensive stock data from Yahoo Finance with validation"""
        display_ticker = ticker  # Keep original for display
        try:
            # Pre-validate ticker to avoid 404 errors
            valid_ticker = self._validate_ticker(ticker)
            if not valid_ticker:
                print(f"   [!]  ${ticker}: not found on any exchange - skipping")
                return None

            # Suppress stderr during yfinance calls to hide HTTP error noise
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                stock = yf.Ticker(valid_ticker)
                info = stock.info
                hist = stock.history(period='1y')
            finally:
                sys.stderr = old_stderr

            if hist.empty:
                print(f"   [!]  No historical data for {display_ticker}")
                return None
            
            # CRITICAL: Validate we have valid price data
            if len(hist) < 2:
                print(f"   [!]  Insufficient historical data for {display_ticker}")
                return None

            current_price = hist['Close'].iloc[-1]

            # CRITICAL: Reject invalid prices
            if not current_price or current_price <= 0 or current_price != current_price:  # NaN check
                print(f"   [!]  Invalid current price for {display_ticker}: {current_price}")
                return None

            # Save historical data using display ticker (original ticker without exchange suffix)
            self.db.save_price_history(display_ticker, hist)

            # Calculate technical indicators
            technical_indicators = self.calculate_technical_indicators(display_ticker, hist)
            self.db.save_technical_indicators(display_ticker, technical_indicators)
            
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            # CRITICAL: Validate prev_price before division
            if not prev_price or prev_price <= 0:
                prev_price = current_price
                change_pct = 0
            else:
                change_pct = ((current_price - prev_price) / prev_price * 100)
            
            # Validate and sanitize data
            def safe_get(key, default=None):
                value = info.get(key, default)
                if value is None:
                    return default
                if isinstance(value, (int, float)):
                    # Check for invalid float values
                    if value == float('inf') or value == float('-inf') or value != value:
                        return default
                    # Reject unrealistic P/E ratios
                    if key in ['trailingPE', 'forwardPE'] and (value < 0 or value > 10000):
                        return default
                    # Reject unrealistic beta values
                    if key in ['beta'] and (value < -5 or value > 5):
                        return default
                    # Reject zero or negative market caps
                    if key == 'marketCap' and value <= 0:
                        return default
                return value
            
            # Get market cap (optional - some securities don't have this)
            market_cap = safe_get('marketCap')
            if not market_cap or market_cap <= 0:
                # Just use 0 instead of failing - some securities don't have market cap
                market_cap = 0

            # Build comprehensive data (use display_ticker for consistency)
            data = {
                'ticker': display_ticker,
                'name': safe_get('longName', ticker),
                'price': round(current_price, 2),
                'change_pct': round(change_pct, 2),
                'market_cap': market_cap,
                'pe_ratio': safe_get('trailingPE'),
                'forward_pe': safe_get('forwardPE'),
                'peg_ratio': safe_get('pegRatio'),
                'price_to_book': safe_get('priceToBook'),
                'revenue': safe_get('totalRevenue'),
                'revenue_growth': safe_get('revenueGrowth'),
                'profit_margin': safe_get('profitMargins'),
                'operating_margin': safe_get('operatingMargins'),
                'roe': safe_get('returnOnEquity'),
                'roa': safe_get('returnOnAssets'),
                'debt_to_equity': safe_get('debtToEquity'),
                'current_ratio': safe_get('currentRatio'),
                'quick_ratio': safe_get('quickRatio'),
                'eps': safe_get('trailingEps'),
                'forward_eps': safe_get('forwardEps'),
                'dividend_yield': safe_get('dividendYield'),
                'payout_ratio': safe_get('payoutRatio'),
                '52w_high': safe_get('fiftyTwoWeekHigh'),
                '52w_low': safe_get('fiftyTwoWeekLow'),
                'avg_volume': safe_get('averageVolume'),
                'volume': safe_get('volume'),
                'beta': safe_get('beta'),
                'sector': safe_get('sector', 'N/A'),
                'industry': safe_get('industry', 'N/A'),
                'employees': safe_get('fullTimeEmployees'),
                'website': safe_get('website'),
                'description': safe_get('longBusinessSummary', '')[:200],
                'short_interest': safe_get('shortPercentOfFloat'),
                'short_ratio': safe_get('shortRatio'),
                'institutional_ownership': safe_get('heldPercentInstitutions'),
                'insider_ownership': safe_get('heldPercentInsiders'),
                'earnings_date': safe_get('earningsDate'),
                'analyst_rating': safe_get('recommendationKey'),
                'price_target': safe_get('targetMeanPrice'),
                'technical_indicators': technical_indicators,
                # Research Links (use valid_ticker for Yahoo, display_ticker for others)
                'yahoo_link': f"https://finance.yahoo.com/quote/{valid_ticker}",
                'yahoo_financials': f"https://finance.yahoo.com/quote/{valid_ticker}/financials",
                'yahoo_analysis': f"https://finance.yahoo.com/quote/{valid_ticker}/analysis",
                'yahoo_statistics': f"https://finance.yahoo.com/quote/{valid_ticker}/key-statistics",
                'yahoo_profile': f"https://finance.yahoo.com/quote/{valid_ticker}/profile",
                'yahoo_holders': f"https://finance.yahoo.com/quote/{valid_ticker}/holders",
                'yahoo_news': f"https://finance.yahoo.com/quote/{valid_ticker}/news",
                'finviz_link': f"https://finviz.com/quote.ashx?t={display_ticker}",
                'marketwatch_link': f"https://www.marketwatch.com/investing/stock/{display_ticker}",
                'seekingalpha_link': f"https://seekingalpha.com/symbol/{display_ticker}",
                'tradingview_link': f"https://www.tradingview.com/symbols/{display_ticker}",
                'gurufocus_link': f"https://www.gurufocus.com/stock/{display_ticker}",
                'stockanalysis_link': f"https://stockanalysis.com/stocks/{display_ticker}",
                'tipranks_link': f"https://www.tipranks.com/stocks/{display_ticker}",
                'google_finance': f"https://www.google.com/finance/quote/{display_ticker}:NASDAQ",
                'sec_filings': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={display_ticker}&type=&dateb=&owner=exclude&count=40",
                'openinsider': f"http://openinsider.com/screener?s={display_ticker}",
                'reddit_search': f"https://www.reddit.com/search/?q={display_ticker}&type=link&sort=new",
                'twitter_search': f"https://twitter.com/search?q=%24{display_ticker}&src=typed_query&f=live"
            }
            
            # Save metadata
            self.db.save_stock_metadata(display_ticker, data)

            # Fetch and save recent news
            news_articles = self.get_recent_news(display_ticker, data['name'])
            if news_articles:
                self.db.save_news_articles(display_ticker, news_articles)
                data['recent_news'] = news_articles
            else:
                data['recent_news'] = []

            # Generate chart image if enabled
            if ENABLE_CHARTS:
                chart_path = self._generate_chart(
                    display_ticker, hist,
                    w52_high=data.get('52w_high'),
                    w52_low=data.get('52w_low')
                )
                if chart_path:
                    data['chart_path'] = chart_path

            # Fetch options data if enabled
            if ENABLE_OPTIONS_FLOW:
                options_data = self.get_options_data(display_ticker, valid_ticker)
                if options_data:
                    data['options_data'] = options_data

            # Fetch insider/institutional data if enabled
            if ENABLE_INSIDER_DATA:
                insider_data = self.get_insider_data(display_ticker, valid_ticker)
                if insider_data:
                    data['insider_data'] = insider_data

            return data
        except Exception as e:
            print(f"   [X] Error getting data for {display_ticker}: {e}")
            return None
    
    def calculate_technical_indicators(self, ticker: str, hist_data) -> Dict:
        """Calculate technical indicators from historical data"""
        try:
            if len(hist_data) < 50:
                return {}
            
            close_prices = hist_data['Close'].values
            
            # RSI calculation
            def calculate_rsi(prices, period=14):
                deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
                gains = [d if d > 0 else 0 for d in deltas]
                losses = [-d if d < 0 else 0 for d in deltas]
                
                avg_gain = sum(gains[:period]) / period
                avg_loss = sum(losses[:period]) / period
                
                if avg_loss == 0:
                    return 100
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            # Moving averages
            sma_20 = sum(close_prices[-20:]) / 20 if len(close_prices) >= 20 else None
            sma_50 = sum(close_prices[-50:]) / 50 if len(close_prices) >= 50 else None
            sma_200 = sum(close_prices[-200:]) / 200 if len(close_prices) >= 200 else None
            
            # EMA calculation
            def calculate_ema(prices, period):
                multiplier = 2 / (period + 1)
                ema = prices[0]
                for price in prices[1:]:
                    ema = (price - ema) * multiplier + ema
                return ema
            
            ema_12 = calculate_ema(close_prices[-26:], 12) if len(close_prices) >= 26 else None
            ema_26 = calculate_ema(close_prices[-26:], 26) if len(close_prices) >= 26 else None
            
            # MACD
            macd = (ema_12 - ema_26) if ema_12 and ema_26 else None
            
            # Bollinger Bands
            if sma_20:
                std_dev = statistics.stdev(close_prices[-20:])
                bollinger_upper = sma_20 + (2 * std_dev)
                bollinger_lower = sma_20 - (2 * std_dev)
            else:
                bollinger_upper = None
                bollinger_lower = None
            
            # Volume ratio
            avg_volume = hist_data['Volume'].mean()
            current_volume = hist_data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # RSI
            rsi = calculate_rsi(close_prices) if len(close_prices) >= 15 else None

            result = {
                'rsi': rsi,
                'macd': macd,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'sma_200': sma_200,
                'ema_12': ema_12,
                'ema_26': ema_26,
                'bollinger_upper': bollinger_upper,
                'bollinger_lower': bollinger_lower,
                'volume_ratio': volume_ratio
            }

            # Enhanced technicals: VWAP, ADX, Ichimoku
            if ENABLE_ENHANCED_TECHNICALS:
                high_prices = hist_data['High'].values
                low_prices = hist_data['Low'].values
                volumes = hist_data['Volume'].values

                # VWAP (20-day rolling)
                try:
                    period = min(20, len(close_prices))
                    typical = [(high_prices[-i] + low_prices[-i] + close_prices[-i]) / 3 for i in range(period, 0, -1)]
                    vols = [volumes[-i] for i in range(period, 0, -1)]
                    cum_tp_vol = sum(t * v for t, v in zip(typical, vols))
                    cum_vol = sum(vols)
                    result['vwap'] = cum_tp_vol / cum_vol if cum_vol > 0 else None
                except Exception:
                    result['vwap'] = None

                # ADX (14-period)
                try:
                    if len(close_prices) >= 28:
                        adx_period = 14
                        tr_list = []
                        plus_dm_list = []
                        minus_dm_list = []
                        for i in range(1, len(close_prices)):
                            h = high_prices[i]
                            l = low_prices[i]
                            pc = close_prices[i - 1]
                            tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))
                            up_move = high_prices[i] - high_prices[i - 1]
                            down_move = low_prices[i - 1] - low_prices[i]
                            plus_dm_list.append(up_move if up_move > down_move and up_move > 0 else 0)
                            minus_dm_list.append(down_move if down_move > up_move and down_move > 0 else 0)

                        # Wilder smoothing (initial sum then recursive)
                        atr = sum(tr_list[:adx_period]) / adx_period
                        plus_dm_smooth = sum(plus_dm_list[:adx_period]) / adx_period
                        minus_dm_smooth = sum(minus_dm_list[:adx_period]) / adx_period
                        dx_list = []

                        for i in range(adx_period, len(tr_list)):
                            atr = (atr * (adx_period - 1) + tr_list[i]) / adx_period
                            plus_dm_smooth = (plus_dm_smooth * (adx_period - 1) + plus_dm_list[i]) / adx_period
                            minus_dm_smooth = (minus_dm_smooth * (adx_period - 1) + minus_dm_list[i]) / adx_period

                            plus_di = (plus_dm_smooth / atr * 100) if atr > 0 else 0
                            minus_di = (minus_dm_smooth / atr * 100) if atr > 0 else 0
                            di_sum = plus_di + minus_di
                            dx = abs(plus_di - minus_di) / di_sum * 100 if di_sum > 0 else 0
                            dx_list.append(dx)

                        if len(dx_list) >= adx_period:
                            adx = sum(dx_list[:adx_period]) / adx_period
                            for i in range(adx_period, len(dx_list)):
                                adx = (adx * (adx_period - 1) + dx_list[i]) / adx_period
                            result['adx'] = round(adx, 2)
                            result['plus_di'] = round(plus_di, 2)
                            result['minus_di'] = round(minus_di, 2)
                        else:
                            result['adx'] = None
                            result['plus_di'] = None
                            result['minus_di'] = None
                    else:
                        result['adx'] = None
                        result['plus_di'] = None
                        result['minus_di'] = None
                except Exception:
                    result['adx'] = None
                    result['plus_di'] = None
                    result['minus_di'] = None

                # Ichimoku Cloud
                try:
                    if len(close_prices) >= ICHIMOKU_SENKOU_B_PERIOD:
                        tenkan = (max(high_prices[-ICHIMOKU_TENKAN_PERIOD:]) + min(low_prices[-ICHIMOKU_TENKAN_PERIOD:])) / 2
                        kijun = (max(high_prices[-ICHIMOKU_KIJUN_PERIOD:]) + min(low_prices[-ICHIMOKU_KIJUN_PERIOD:])) / 2
                        senkou_a = (tenkan + kijun) / 2
                        senkou_b = (max(high_prices[-ICHIMOKU_SENKOU_B_PERIOD:]) + min(low_prices[-ICHIMOKU_SENKOU_B_PERIOD:])) / 2
                        result['ichimoku_tenkan'] = round(tenkan, 2)
                        result['ichimoku_kijun'] = round(kijun, 2)
                        result['ichimoku_senkou_a'] = round(senkou_a, 2)
                        result['ichimoku_senkou_b'] = round(senkou_b, 2)
                    else:
                        result['ichimoku_tenkan'] = None
                        result['ichimoku_kijun'] = None
                        result['ichimoku_senkou_a'] = None
                        result['ichimoku_senkou_b'] = None
                except Exception:
                    result['ichimoku_tenkan'] = None
                    result['ichimoku_kijun'] = None
                    result['ichimoku_senkou_a'] = None
                    result['ichimoku_senkou_b'] = None

            return result
        except Exception as e:
            print(f"   [!]  Error calculating technical indicators: {e}")
            return {}
    
    def get_recent_news(self, ticker: str, company_name: str, limit: int = 6) -> List[Dict]:
        """Fetch recent news articles about the company"""
        try:
            # Try Yahoo Finance news first
            articles = self.get_yahoo_finance_news(ticker, limit)
            
            # If not enough articles, try Google News
            if len(articles) < 3:
                google_articles = self.get_google_news(ticker, company_name, limit)
                articles.extend(google_articles)
                
                # Remove duplicates by URL
                seen_urls = set()
                unique_articles = []
                for article in articles:
                    if article['url'] not in seen_urls:
                        seen_urls.add(article['url'])
                        unique_articles.append(article)
                articles = unique_articles[:limit]
            
            return articles
            
        except Exception as e:
            print(f"   [!]  Error fetching news for {ticker}: {e}")
            return []
    
    def get_yahoo_finance_news(self, ticker: str, limit: int = 6) -> List[Dict]:
        """Fetch news from Yahoo Finance with improved parsing"""
        try:
            stock = yf.Ticker(ticker)
            
            # Try to get news
            try:
                news = stock.news
            except:
                news = []
            
            if not news or len(news) == 0:
                return []
            
            articles = []
            for item in news[:limit]:
                try:
                    # Extract title - try multiple fields
                    title = item.get('title', item.get('headline', 'No title'))
                    
                    # Extract source/publisher - handle dict and string types
                    publisher_field = item.get('publisher', {})
                    if isinstance(publisher_field, dict):
                        source = publisher_field.get('title', publisher_field.get('name', 'Unknown'))
                    else:
                        source = str(publisher_field) if publisher_field else item.get('source', 'Unknown')
                    
                    # Extract URL - try multiple fields  
                    url = item.get('link', item.get('url', ''))
                    
                    # If source is still Unknown or empty, extract from URL
                    if (not source or source == 'Unknown') and url:
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(url).netloc.replace('www.', '')
                            # Map common domains to readable names
                            domain_map = {
                                'reuters.com': 'Reuters',
                                'bloomberg.com': 'Bloomberg',
                                'wsj.com': 'Wall Street Journal',
                                'ft.com': 'Financial Times',
                                'cnbc.com': 'CNBC',
                                'marketwatch.com': 'MarketWatch',
                                'seekingalpha.com': 'Seeking Alpha',
                                'barrons.com': "Barron's",
                                'fool.com': 'Motley Fool',
                                'benzinga.com': 'Benzinga',
                                'investing.com': 'Investing.com',
                                'finance.yahoo.com': 'Yahoo Finance',
                                'zacks.com': 'Zacks',
                                'thestreet.com': 'TheStreet'
                            }
                            source = domain_map.get(domain, domain.split('.')[0].title())
                        except:
                            source = 'Financial News'
                    
                    # Extract timestamp - try multiple fields
                    timestamp = item.get('providerPublishTime', item.get('publishTime', 0))
                    
                    if timestamp and timestamp > 0:
                        try:
                            # yfinance returns Unix timestamp in seconds
                            date_obj = datetime.fromtimestamp(timestamp)
                            # Calculate time difference
                            time_diff = datetime.now() - date_obj
                            days_ago = time_diff.days
                            hours_ago = time_diff.seconds // 3600
                            
                            if days_ago == 0:
                                if hours_ago == 0:
                                    date = 'Just now'
                                elif hours_ago == 1:
                                    date = '1 hour ago'
                                else:
                                    date = f'{hours_ago} hours ago'
                            elif days_ago == 1:
                                date = 'Yesterday'
                            elif days_ago < 7:
                                date = f'{days_ago} days ago'
                            elif days_ago < 30:
                                weeks = days_ago // 7
                                date = f'{weeks} week{"s" if weeks > 1 else ""} ago'
                            else:
                                date = date_obj.strftime('%b %d, %Y')
                        except Exception:
                            date = 'Recent'
                    else:
                        date = 'Recent'
                    
                    # Only add if we have valid data
                    if title and url and title != 'No title' and source and source != 'Unknown':
                        articles.append({
                            'title': title,
                            'source': source,
                            'date': date,
                            'url': url
                        })
                except Exception:
                    continue
            
            return articles
            
        except Exception as e:
            print(f"   [!]  Yahoo news error for {ticker}: {e}")
            return []
    
    def get_google_news(self, ticker: str, company_name: str, limit: int = 6) -> List[Dict]:
        """Fetch news from Google News"""
        try:
            search_query = f"{ticker} {company_name} stock"
            url = f"https://www.google.com/search?q={search_query}&tbm=nws&num=10"
            
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            news_items = soup.find_all('div', {'class': 'SoaBEf'})
            
            for item in news_items[:limit]:
                try:
                    title_elem = item.find('div', {'class': 'MBeuO'})
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    link_elem = item.find('a')
                    url = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''
                    source_elem = item.find('div', {'class': 'CEMjEf'})
                    source = source_elem.get_text(strip=True) if source_elem else 'News'
                    date_elem = item.find('span', {'class': 'OSrXXb'})
                    date = date_elem.get_text(strip=True) if date_elem else 'Recent'
                    
                    if title and url:
                        articles.append({
                            'title': title,
                            'source': source,
                            'date': date,
                            'url': url
                        })
                
                except Exception:
                    continue
            
            return articles
            
        except Exception as e:
            return []
