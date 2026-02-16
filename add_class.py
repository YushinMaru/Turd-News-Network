
# Add CongressTracker class wrapper to congress_tracker.py

class_code = '''

class CongressTracker:
    """Wrapper class for compatibility with existing code"""
    
    def __init__(self, db=None):
        self.db = db
    
    def check_congress_trades(self, ticker):
        trades = get_congress_trades_cached(90)
        ticker_trades = [t for t in trades if t.get('ticker', '').upper() == ticker.upper()]
        return ticker_trades
    
    @staticmethod
    def format_for_embed(trades):
        if not trades:
            return None
        
        buys = sum(1 for t in trades if 'PURCHASE' in str(t.get('type', '')).upper())
        sells = sum(1 for t in trades if 'SALE' in str(t.get('type', '')).upper())
        
        return {
            'trades': trades[:10],
            'buys': buys,
            'sells': sells,
            'total': len(trades)
        }
'''

with open('congress_tracker.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the if __name__ == "__main__" section
if 'if __name__ == "__main__"' in content:
    content = content.split('if __name__ == "__main__"')[0]

# Add the class at the end
content = content.rstrip() + class_code + '\n'

with open('congress_tracker.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - added CongressTracker class')
