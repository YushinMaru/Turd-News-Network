"""
Configuration and constants for Turd News Network Enhanced v4.0
SECURE: Uses environment variables for secrets
"""

import os
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# ============== REQUIRED ENVIRONMENT VARIABLES ==============
# Set these before running the bot:
# - DISCORD_BOT_TOKEN: Your Discord bot token
# - DISCORD_WEBHOOK_URL: Your Discord webhook URL

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
ALERT_ROLE_ID = os.environ.get('ALERT_ROLE_ID', '<@&1315430425388789881>')

# Discord Bot Configuration for Interactive Dashboard
ENABLE_DASHBOARD = True  # Enable interactive dashboard
DASHBOARD_CHANNEL_NAME = "stonk-bot"  # Channel name for dashboard
DASHBOARD_REFRESH_INTERVAL = 30  # seconds between dashboard updates

# Database Configuration
DB_PATH = 'wsb_tracker_enhanced.db'

# Scraping Configuration - OPTIMIZED SUBREDDIT LIST
SUBREDDITS = [
    'wallstreetbets', 'stocks', 'investing', 'options', 'thetagang',
    'smallstreetbets', 'pennystocks', 'Daytrading', 'StockMarket',
    'SecurityAnalysis', 'ValueInvesting', 'SwingTrading', 'algotrading',
    'dividends', 'dividendinvesting', 'personalfinance', 'financialindependence',
    'cryptocurrency', 'forex', 'FuturesTrading', 'RealDayTrading',
    'investing_discussion', 'Pennystock', 'algorithmictrading', 'quantfinance',
    'educatedinvesting', 'MillennialBets', 'MoonGangCapital', 'SwaggyStocks',
    'thecorporation', 'Stocks_Advice', 'AsymmetricAlpha', 'Bogleheads',
    'RobinHoodPennyStocks', 'Canadapennystocks', 'weedstocks', 'biotech_stocks',
    'greeninvestor', 'greenstocks', 'personalfinancecanada', 'trading212',
    'UKInvesting', 'IndiaInvestments', 'AusFinance', 'StockMarketIndia',
    'Baystreetbets', 'FatFIRE', 'LeanFIRE', 'ChubbyFIRE', 'stocks_india',
    'Shortsqueeze', 'SqueezePlays', 'Market_Sentiment', 'technicalanalysis',
    'swingtrading', 'StockMarketNews', 'StocksToBuy', 'InvestmentClub',
    'CryptoMarkets', 'Altcoins', 'DeFi',
    'EarningsReports', 'Macroeconomics', 'Economics', 'GlobalMarkets',
    'ETF', 'IndexFunds', 'MutualFunds', 'RealEstateInvesting',
    'Wallstreetbetsnew', 'UndervaluedStonks', 'PennyStockSpeculation',
    'HedgeFunds', 'Trading', 'InvestmentStrategies', 'FinancialNews',
    'Superstonk', 'GME', 'AMCSTOCK', 'Semiconductors', 'Techstocks',
    'RenewableEnergy', 'EVstock', 'CannabisStock', 'DueDiligence',
    'MarketResearch', 'WallStreetAnalysis', 'ThetaGang', 'CoveredCall',
    'WheelStrategy',
]

# DD Detection Configuration
DD_FLAIRS = ['DD', 'Due Diligence', 'Technical Analysis', 'Fundamental Analysis', 'Discussion', 'News', 'Catalyst', 'YOLO', 'Gain']

DD_KEYWORDS = [
    'DD:', 'DD -', 'Due Diligence', 'Analysis', 'Deep Dive', 'Research', 'Detailed Analysis',
    'My DD on', 'DD on', "Here's my DD", 'Bull Case', 'Bear Case', 'Bullish Thesis',
    'Bearish Thesis', 'Investment Thesis', 'Undervalued', 'Overvalued', 'Opportunity',
    'Hidden Gem', 'Sleeper Stock', 'PT:', 'Price Target', 'Earnings', 'Revenue Growth',
    'Short Squeeze', 'Squeeze Play', 'High Short Interest', 'Technical Analysis',
]

EXCLUDE_KEYWORDS = [
    'loss', 'losses', 'lost everything', 'down', 'rip', 'fucked', 'rekt', 'wiped out',
    'obliterated', 'destroyed', 'crushed', 'bag holder', 'bagholder', 'rug pull', 'scam',
    'pump and dump', 'worthless', 'garbage', 'trash', 'fraud', 'ponzi', 'blown account',
    'blew up', 'margin call', 'liquidated', 'bankruptcy', 'bankrupt', 'panic sold',
    'paper hands', 'to the moon', 'diamond hands', 'ape', 'meme', 'joke',
]

# Ticker Filtering - Comprehensive
IGNORE_TICKERS = {
    'CEO', 'CFO', 'CTO', 'COO', 'EVP', 'SVP', 'VP', 'CMO', 'CDO',
    'USA', 'NYSE', 'NASDAQ', 'SEC', 'FDA', 'EPA', 'FBI', 'DOJ', 'IMF', 'WHO',
    'UK', 'EU', 'CSE', 'TSX', 'LSE', 'OTCQX', 'CAD', 'USD', 'GBP', 'EUR', 'JPY', 'CNY',
    'BTC', 'ETH', 'USDT', 'USDC', 'BNB', 'XRP', 'ADA', 'DOGE', 'SOL',
    'THE', 'FOR', 'AND', 'ALL', 'NEW', 'NOW', 'OUT', 'SEE', 'CAN', 'MAY', 'NEXT',
    'EDIT', 'GO', 'AT', 'BY', 'ON', 'OR', 'IT', 'BE', 'TO', 'OF', 'IN', 'IS',
    'WAS', 'AS', 'ARE', 'SO', 'AN', 'NO', 'YES', 'MY', 'ME', 'US', 'IF', 'HE',
    'SHE', 'WE', 'THEY', 'BUT', 'NOT', 'HAS', 'HAD', 'DO', 'DOES', 'DID', 'WILL',
    'WOULD', 'SHOULD', 'COULD', 'HAVE', 'FROM', 'THAT', 'WITH', 'THIS', 'WHAT',
    'WHEN', 'WHERE', 'WHY', 'HOW', 'WHO', 'WHICH', 'BEEN', 'WERE', 'THAN', 'THEN',
    'I', 'A', 'S', 'P', 'F', 'T', 'E', 'D', 'R', 'M', 'K', 'L', 'O', 'H',
    'WSB', 'DD', 'TA', 'IMO', 'TLDR', 'LMAO', 'FOMO', 'YOLO', 'OMG', 'FYI',
    'LOVE', 'BABY', 'LIFE', 'HOPE', 'CASH', 'MOON', 'BEST', 'GOOD', 'NICE', 'HUGE',
    'SAFE', 'RARE', 'REAL', 'TRUE', 'FAST', 'EASY', 'HARD', 'FREE', 'COOL', 'PUMP',
    'DUMP', 'REKT', 'RIP', 'LOL', 'WOW', 'DAMN', 'SICK', 'LLC', 'INC', 'CORP', 'LTD',
    'IPO', 'ETF', 'REIT', 'ADR', 'SPAC', 'GAAP', 'EBITDA', 'CAPEX', 'OPEX', 'ROI',
    'KPI', 'PE', 'PB', 'PS', 'EV', 'ROIC', 'FCF', 'EPS', 'PEG', 'DCF', 'NAV',
    'RSI', 'MACD', 'SMA', 'EMA', 'BBANDS', 'ADX', 'ATR', 'OBV', 'CCI', 'CFA',
    'MBA', 'PHD', 'CPA', 'CFP', 'LEAP', 'LEAPS', 'DELTA', 'GAMMA', 'THETA', 'VEGA',
    'RHO', 'AI', 'AWS', 'API', 'SDK', 'IoT', 'SaaS', 'PaaS', 'IaaS', 'JAN', 'FEB',
    'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
    'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN', 'OK', 'BUY', 'SELL', 'HOLD',
    'LONG', 'SHORT', 'CALL', 'PUT', 'OTM', 'ITM', 'ATM', 'DTE', 'GTC', 'IOC',
    'FOK', 'VWAP', 'TWAP', 'HIGH', 'LOW', 'MID', 'MAX', 'MIN', 'AVG', 'SUM',
    'TOTAL', 'TOP', 'END', 'START', 'BEGIN', 'OPEN', 'CLOSE', 'SHUT', 'ONE', 'TWO',
    'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN', 'ZERO',
    'RED', 'BLUE', 'GREEN', 'YELLOW', 'ORANGE', 'PURPLE', 'PINK', 'BLACK', 'WHITE',
    'NORTH', 'SOUTH', 'EAST', 'WEST', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'RAIN', 'SNOW',
    'WIND', 'STORM', 'SUNNY', 'CLOUDY', 'HOT', 'COLD', 'WARM', 'COOL', 'HAPPY',
    'SAD', 'ANGRY', 'MAD', 'GLAD', 'SURE', 'GAIN', 'GAINS', 'LOSS', 'PROFIT',
    'REVENUE', 'INCOME', 'COST', 'PRICE', 'VALUE', 'WORTH', 'BULL', 'BEAR',
}

# Performance Thresholds
WINNER_THRESHOLD = 20.0
LOSER_THRESHOLD = -20.0
HIGH_VOLUME_THRESHOLD = 1.5
LOW_VOLUME_THRESHOLD = 0.5

# Quality Score Thresholds
PREMIUM_DD_SCORE = 80
QUALITY_DD_SCORE = 60

# Momentum Thresholds
STRONG_MOMENTUM_THRESHOLD = 75
WEAK_MOMENTUM_THRESHOLD = 25

# Alert Configuration
ENABLE_PRICE_ALERTS = True
ENABLE_MOMENTUM_ALERTS = True
ENABLE_VOLUME_ALERTS = True
ENABLE_ROLE_PING_ON_ALERTS = True
NEAR_52W_HIGH_PCT = 3.0
NEAR_52W_LOW_PCT = 3.0
EXTREME_VOLUME_THRESHOLD = 3.0
MIN_MOMENTUM_FOR_ALERT = 70
RISK_REWARD_MIN_RATIO = 2.0

# Scheduling
RUN_TIMES = ["06:00", "12:00", "18:00", "00:00"]
CHECK_INTERVAL = 30

# Daily Digest
DAILY_DIGEST_TIME = "08:00"
ENABLE_DAILY_DIGEST = True

# Rate Limiting
SCRAPE_DELAY = 2
API_DELAY = 2
DISCORD_DELAY = 1

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Embed Colors
COLOR_PREMIUM = 0xFFD700
COLOR_QUALITY = 0x00FF00
COLOR_STANDARD = 0x3498DB
COLOR_BULLISH = 0x00FF00
COLOR_BEARISH = 0xFF0000
COLOR_NEUTRAL = 0xFFCC00
COLOR_ALERT = 0xFF0000

# News Sources
NEWS_SOURCES = ['Reuters', 'Bloomberg', 'Wall Street Journal', 'Financial Times', 'CNBC', 'MarketWatch', 'Seeking Alpha', "Barron's", 'Yahoo Finance', 'Motley Fool', 'Zacks', 'Business Insider']

# Alert System
ENABLE_ALERT_SYSTEM = True
ALERT_VOLUME_THRESHOLD = 2.0
ALERT_PRICE_CHANGE_THRESHOLD = 0.05
ALERT_SENTIMENT_THRESHOLD = 0.6
ALERT_COOLDOWN_MINUTES = 30
ALERT_SCHEDULE_TIMES = ["06:30", "09:30", "12:30", "15:30", "18:30"]
ALERT_TRACKED_STOCKS_LIMIT = 50

# Stock Config
STOCK_CONFIG = {
    'default_stocks': ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'DIS', 'V', 'JPM', 'BAC', 'XOM', 'CVX'],
    'max_tracking_age_days': 7,
    'min_mention_count': 2
}

# Technical Indicators
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
RSI_PERIOD = 14

# Feature Toggles
ENABLE_BACKTEST = True
ENABLE_SENTIMENT = True
ENABLE_TECHNICAL_ANALYSIS = True
ENABLE_RISK_ASSESSMENT = True
ENABLE_MOMENTUM_SCORE = True
ENABLE_PRICE_ALERTS_IN_EMBED = True
ENABLE_AI_SUMMARY = True

# API Keys (Free tier keys - replace with your own for production)
FINNHUB_API_KEY = 'd63vua1r01ql6dj1m3sgd63vua1r01ql6dj1m3t0'
ALPHA_VANTAGE_API_KEY = '4CSJY4GHM8L2EEU2'
SEC_EDGAR_API_KEY = 'fbc9348314fe4b67f39d999344a5656023aa3341e826234216ef1282eb6f2115'
SEC_EDGAR_EMAIL = 'user@example.com'

ENABLE_INSIDER_DATA = True
INSIDER_LOOKBACK_DAYS = 90

ENABLE_OPTIONS_FLOW = True
OPTIONS_UNUSUAL_VOLUME_THRESHOLD = 5.0

ENABLE_CONGRESS_TRACKER = True
CONGRESS_LOOKBACK_DAYS = 60
CONGRESS_CACHE_HOURS = 24

ENABLE_ENHANCED_TECHNICALS = True

ENABLE_ML_PREDICTION = True
ML_MIN_TRAINING_SAMPLES = 30
ML_PREDICTION_DAYS = 5

ENABLE_CHARTS = True
CHART_DIR = 'charts'
CHART_PERIOD = 63

ENABLE_FINBERT = True

BACKTEST_YEARS = 3
BACKTEST_BENCHMARK = 'SPY'

STATS_REPORT_SCHEDULE = "daily"
STATS_TOP_N = 10

# Additional config values needed
ENABLE_CHART_BOLLINGER = True
ENABLE_TWITTER = False
NEWSAPI_KEY = ''
TWITTER_USERNAME = ''
TWITTER_EMAIL = ''
TWITTER_PASSWORD = ''
GOOGLE_API_KEY = ''
GOOGLE_CSE_ID = ''
ENABLE_GOOGLE_SEARCH = True
PDF_OUTPUT_DIR = 'reports'
REPORTS_DIR = 'reports'
PDF_DPI = 150
PDF_MAX_PAGES = 50
PDF_INCLUDE_ALL_SECTIONS = True
PDF_GENERATION_TIMEOUT = 300
PDF_RATE_LIMIT_DELAY = 5
ENABLE_SEC_EDGAR = True
ENABLE_ALPHA_VANTAGE = True

# Technical Analysis
ICHIMOKU_TENKAN_PERIOD = 9
ICHIMOKU_KIJUN_PERIOD = 26
ICHIMOKU_SENKOU_B_PERIOD = 52
FIBONACCI_LOOKBACK_DAYS = 60
ADX_TRENDING_THRESHOLD = 25
ADX_RANGING_THRESHOLD = 20
SMA_SHORT = 20
SMA_MEDIUM = 50
SMA_LONG = 200
EMA_SHORT = 12
EMA_LONG = 26
BOLLINGER_BANDS_PERIOD = 20
BOLLINGER_BANDS_STD = 2
ML_MODEL_PATH = 'ml_model.joblib'
ML_RETRAIN_DAYS = 7
ML_UP_THRESHOLD = 3.0
ML_DOWN_THRESHOLD = -3.0
MTF_PERIODS = ['1M', '3M', '6M', '1Y', '2Y', '3Y']
OPTIONS_EXTREME_PC_LOW = 0.5
OPTIONS_EXTREME_PC_HIGH = 1.5

# FinBERT
FINBERT_MODEL = 'ProsusAI/finbert'
FINBERT_DEVICE = 'cpu'
FINBERT_MAX_LENGTH = 512
FINBERT_BATCH_SIZE = 8

# Dashboard Colors
DASHBOARD_BG_PRIMARY = "#0f1117"
DASHBOARD_BG_SECONDARY = "#1a1d29"
DASHBOARD_BG_CARD = "#232636"
DASHBOARD_ACCENT_BLUE = "#3b82f6"
DASHBOARD_ACCENT_CYAN = "#06b6d4"
DASHBOARD_ACCENT_PURPLE = "#8b5cf6"
DASHBOARD_TEXT_PRIMARY = "#ffffff"
DASHBOARD_TEXT_SECONDARY = "#94a3b8"
DASHBOARD_BORDER = "#2d3748"
DASHBOARD_SUCCESS = "#10b981"
DASHBOARD_DANGER = "#ef4444"
DASHBOARD_WARNING = "#f59e0b"

# Report Colors
COLOR_REPORT_OVERVIEW = 0x3498DB
COLOR_REPORT_PRICE = 0x2ECC71
COLOR_REPORT_VALUATION = 0x9B59B6
COLOR_REPORT_INCOME = 0xE67E22
COLOR_REPORT_BALANCE = 0x1ABC9C
COLOR_REPORT_TECHNICAL = 0x34495E
COLOR_REPORT_SIGNALS = 0xF1C40F
COLOR_REPORT_OPTIONS = 0xE74C3C
COLOR_REPORT_INSIDER = 0x95A5A6
COLOR_REPORT_ANALYST = 0x16A085

# Risk Colors
COLOR_RISK_LOW = 0x00FF00
COLOR_RISK_MODERATE = 0xFFCC00
COLOR_RISK_HIGH = 0xFF6600
COLOR_RISK_VERY_HIGH = 0xFF0000
COLOR_STRONG_BULLISH = 0x00CC00
COLOR_STRONG_BEARISH = 0xCC0000

# Embed Formatting
COMPACT_MODE = True
MAX_FIELDS_PER_STOCK = 12
SHOW_COMPANY_OVERVIEW = False
SHOW_FULL_RESEARCH_LINKS = False
MAX_NEWS_ARTICLES = 3
MAX_RELATED_POSTS = 2
DUPLICATE_DETECTION_HOURS = 48
NEWS_SOURCES_PRIORITY = ['Reuters', 'Bloomberg', 'Wall Street Journal', 'Financial Times', 'CNBC', 'MarketWatch', 'Seeking Alpha', "Barron's"]
ENABLE_SECTOR_COMPARISON = True
ENABLE_TRENDING_STOCKS = True
ENABLE_RISK_ADJUSTED_LEADERBOARD = True
