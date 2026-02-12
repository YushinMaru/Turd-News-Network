"""
Congress & Political Trading Tracker
Fetches recent Congressional stock trades via Finnhub free tier API.
Cross-references mentioned tickers with politician trades.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config import (
    FINNHUB_API_KEY, CONGRESS_LOOKBACK_DAYS, CONGRESS_CACHE_HOURS,
    USER_AGENT, API_DELAY
)


class CongressTracker:
    """Tracks Congressional stock trades using Finnhub API"""

    FINNHUB_BASE = 'https://finnhub.io/api/v1'

    def __init__(self, db_manager):
        self.db = db_manager
        self.enabled = bool(FINNHUB_API_KEY)
        if not self.enabled:
            print("   [i] Congress tracker disabled: no FINNHUB_API_KEY set")

    def _finnhub_get(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make an authenticated GET request to Finnhub"""
        params['token'] = FINNHUB_API_KEY
        headers = {'User-Agent': USER_AGENT}
        try:
            resp = requests.get(
                f'{self.FINNHUB_BASE}{endpoint}',
                params=params,
                headers=headers,
                timeout=15
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                print("   [!] Finnhub rate limit hit, backing off...")
                time.sleep(API_DELAY * 3)
                return None
            return None
        except Exception as e:
            print(f"   [X] Finnhub request failed: {e}")
            return None

    def refresh_congress_data(self, ticker: str) -> List[Dict]:
        """Fetch fresh Congress trade data from Finnhub for a ticker"""
        if not self.enabled:
            return []

        data = self._finnhub_get('/stock/congressional-trading', {'symbol': ticker})
        if not data or 'data' not in data:
            return []

        cutoff = datetime.now() - timedelta(days=CONGRESS_LOOKBACK_DAYS)
        trades = []

        for entry in data['data']:
            txn_date_str = entry.get('transactionDate', '')
            if not txn_date_str:
                continue

            try:
                txn_date = datetime.strptime(txn_date_str, '%Y-%m-%d')
            except ValueError:
                continue

            if txn_date < cutoff:
                continue

            amount_from = entry.get('amountFrom', 0) or 0
            amount_to = entry.get('amountTo', 0) or 0
            amount_range = self._format_amount_range(amount_from, amount_to)

            raw_type = (entry.get('transactionType') or '').strip()
            txn_type = self._normalize_transaction_type(raw_type)

            chamber = self._guess_chamber(entry.get('position', ''))

            trade = {
                'ticker': ticker,
                'politician_name': entry.get('name', 'Unknown'),
                'party': '',
                'chamber': chamber,
                'transaction_type': txn_type,
                'amount_range': amount_range,
                'transaction_date': txn_date_str,
                'disclosure_date': entry.get('filingDate', ''),
            }
            trades.append(trade)

        if trades:
            self.db.save_congress_trades(trades)

        return trades

    def check_congress_trades(self, ticker: str) -> List[Dict]:
        """Get recent Congress trades for a ticker (cache-aware)"""
        if not self.enabled:
            return []

        cached = self.db.get_congress_trades(ticker, days=CONGRESS_LOOKBACK_DAYS)
        if cached:
            return cached

        cache_age = self.db.get_congress_cache_age_hours()
        if cache_age is not None and cache_age < CONGRESS_CACHE_HOURS:
            return []

        trades = self.refresh_congress_data(ticker)
        return trades

    @staticmethod
    def _format_amount_range(amount_from: float, amount_to: float) -> str:
        """Format dollar amount range into readable string"""
        def fmt(val):
            if val >= 1_000_000:
                return f"${val / 1_000_000:.1f}M"
            if val >= 1_000:
                return f"${val / 1_000:.0f}K"
            if val > 0:
                return f"${val:,.0f}"
            return ""

        low = fmt(amount_from)
        high = fmt(amount_to)
        if low and high and low != high:
            return f"{low}-{high}"
        return high or low or "N/A"

    @staticmethod
    def _normalize_transaction_type(raw: str) -> str:
        """Normalize transaction type strings"""
        lower = raw.lower()
        if 'purchase' in lower or 'buy' in lower:
            return 'PURCHASE'
        if 'sale' in lower and 'partial' in lower:
            return 'SALE (PARTIAL)'
        if 'sale' in lower or 'sold' in lower:
            return 'SALE'
        if 'exchange' in lower:
            return 'EXCHANGE'
        return raw.upper() if raw else 'UNKNOWN'

    @staticmethod
    def _guess_chamber(position: str) -> str:
        """Try to determine chamber from position field"""
        if not position:
            return ''
        lower = position.lower()
        if 'senator' in lower or 'senate' in lower:
            return 'Senate'
        if 'representative' in lower or 'rep.' in lower or 'house' in lower:
            return 'House'
        return ''

    @staticmethod
    def format_for_embed(trades: List[Dict]) -> Optional[Dict]:
        """Format Congress trades into an embed-ready dict"""
        if not trades:
            return None

        buys = [t for t in trades if 'PURCHASE' in t.get('transaction_type', '')]
        sells = [t for t in trades if 'SALE' in t.get('transaction_type', '')]

        return {
            'total': len(trades),
            'buys': len(buys),
            'sells': len(sells),
            'trades': trades[:5],
        }
