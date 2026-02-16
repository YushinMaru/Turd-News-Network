"""
Congressional Trading Tracker
Fetches live congressional trading data from the Senate Stock Watcher API
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Use the publicly available Senate Stock Watcher API
SENATE_API_URL = "https://senatestockwatcher.com/backend/api/trades"
HOUSE_API_URL = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"

def fetch_senate_trades(days_back: int = 90) -> List[Dict]:
    """Fetch recent Senate trading activity"""
    trades = []
    
    try:
        # Try the Senate Stock Watcher API
        response = requests.get(
            SENATE_API_URL,
            params={"days": days_back},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            for item in data:
                if item.get("ticker"):
                    trades.append({
                        'ticker': item.get('ticker', '').upper(),
                        'member': item.get('member', 'Unknown'),
                        'type': item.get('transaction_type', 'N/A'),
                        'amount': item.get('amount', 'N/A'),
                        'date': item.get('transaction_date', ''),
                        'chamber': 'Senate'
                    })
    except Exception as e:
        print(f"[CONGRESS] Error fetching Senate data: {e}")
    
    return trades

def fetch_house_trades(days_back: int = 90) -> List[Dict]:
    """Fetch recent House trading activity"""
    trades = []
    
    try:
        response = requests.get(HOUSE_API_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for item in data:
                try:
                    date_str = item.get('transaction_date', '')
                    if date_str:
                        trans_date = datetime.strptime(date_str, '%Y-%m-%d')
                        if trans_date < cutoff_date:
                            continue
                    
                    if item.get("ticker"):
                        trades.append({
                            'ticker': item.get('ticker', '').upper(),
                            'member': item.get('member', 'Unknown'),
                            'type': item.get('transaction_type', 'N/A'),
                            'amount': item.get('amount', 'N/A'),
                            'date': date_str,
                            'chamber': 'House'
                        })
                except:
                    continue
    except Exception as e:
        print(f"[CONGRESS] Error fetching House data: {e}")
    
    return trades

def fetch_all_congress_trades(days_back: int = 90) -> List[Dict]:
    """Fetch all recent congressional trades (Senate + House)"""
    all_trades = []
    
    senate_trades = fetch_senate_trades(days_back)
    print(f"[CONGRESS] Fetched {len(senate_trades)} Senate trades")
    
    house_trades = fetch_house_trades(days_back)
    print(f"[CONGRESS] Fetched {len(house_trades)} House trades")
    
    all_trades.extend(senate_trades)
    all_trades.extend(house_trades)
    
    # Sort by date, most recent first
    all_trades.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return all_trades

# Cache for storing fetched data
_trades_cache = None
_cache_time = None
CACHE_DURATION = 300  # 5 minutes

def get_congress_trades_cached(days_back: int = 90) -> List[Dict]:
    """Get congress trades with caching"""
    global _trades_cache, _cache_time
    
    now = datetime.now()
    
    if _trades_cache is None or _cache_time is None or (now - _cache_time).seconds > CACHE_DURATION:
        print("[CONGRESS] Refreshing congress trades cache...")
        _trades_cache = fetch_all_congress_trades(days_back)
        _cache_time = now
    
    return _trades_cache

if __name__ == "__main__":
    # Test the fetcher
    trades = fetch_all_congress_trades(90)
    print(f"Total trades: {len(trades)}")
    
    # Show sample
    for trade in trades[:5]:
        print(f"  {trade}")
