"""
Alert Manager - Manages stock alerts with sentiment validation
Integrates with existing sentiment analyzer, stock data fetcher, and Reddit scraper
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum

from config import (
    NEWS_SOURCES,
    SUBREDDITS,
    STOCK_CONFIG
)
from sentiment import SentimentAnalyzer
from stock_data import StockDataFetcher
from scraper import RedditScraper


class AlertType(Enum):
    """Types of alerts that can be generated"""
    PRICE_TARGET_HIT = "price_target_hit"
    UNUSUAL_VOLUME = "unusual_volume"
    SENTIMENT_CHANGE = "sentiment_change"
    BREAKOUT = "breakout"
    DROP = "drop"
    GAP_UP = "gap_up"
    GAP_DOWN = "gap_down"


@dataclass
class Alert:
    """Represents a stock alert"""
    ticker: str
    alert_type: AlertType
    price: float
    timestamp: datetime
    confidence: float
    details: Dict
    sentiment_score: Optional[float] = None
    news_articles: Optional[List[Dict]] = None
    reddit_posts: Optional[List[Dict]] = None


class AlertManager:
    """Manages stock alerts with sentiment validation"""
    
    def __init__(self, db_manager=None, discord_webhook: Optional[str] = None):
        """
        Initialize Alert Manager
        
        Args:
            db_manager: Database manager instance
            discord_webhook: Optional Discord webhook URL for sending alerts
        """
        from database import DatabaseManager
        self.db = db_manager if db_manager else DatabaseManager()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.stock_fetcher = StockDataFetcher(self.db)
        self.reddit_scraper = RedditScraper()
        self.discord_webhook = discord_webhook
        
        # Alert thresholds
        self.volume_threshold = 2.0  # 2x average volume
        self.price_change_threshold = 0.05  # 5% price change
        self.sentiment_threshold = 0.6  # 60% confidence
        
        # Track alerts to avoid duplicates
        self.recent_alerts = {}
        self.alert_cooldown = timedelta(minutes=30)
    
    async def check_alerts(self, ticker: str, data: Optional[Dict] = None) -> List[Alert]:
        """
        Check for alerts for a given ticker
        
        Args:
            ticker: Stock ticker symbol
            data: Optional pre-fetched stock data
            
        Returns:
            List of alerts found
        """
        alerts = []
        
        try:
            # Fetch stock data if not provided
            if data is None:
                data = await self._fetch_stock_data(ticker)
                if not data:
                    return alerts
            
            # Check for different alert types
            if self._check_volume_alert(data):
                alert = await self._create_volume_alert(ticker, data)
                if alert:
                    alerts.append(alert)
            
            if self._check_price_change_alert(data):
                alert = await self._create_price_change_alert(ticker, data)
                if alert:
                    alerts.append(alert)
            
            if self._check_gap_alert(data):
                alert = await self._create_gap_alert(ticker, data)
                if alert:
                    alerts.append(alert)
            
            # Fetch and validate with sentiment
            if alerts:
                for alert in alerts:
                    await self._validate_with_sentiment(alert)
                
                # Filter alerts based on cooldown and sentiment
                alerts = self._filter_alerts(alerts)
        
        except Exception as e:
            print(f"[!] Error checking alerts for {ticker}: {e}")
        
        return alerts
    
    async def _fetch_stock_data(self, ticker: str) -> Optional[Dict]:
        """Fetch stock data for ticker"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d", interval="1d")
            
            if hist.empty:
                return None
            
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else latest
            
            # Calculate average volume
            avg_volume = hist['Volume'].mean()
            
            return {
                'ticker': ticker,
                'current_price': latest['Close'],
                'previous_close': previous['Close'],
                'volume': latest['Volume'],
                'avg_volume': avg_volume,
                'high': latest['High'],
                'low': latest['Low'],
                'open': latest['Open'],
                'timestamp': hist.index[-1]
            }
        
        except Exception as e:
            print(f"[!] Error fetching stock data for {ticker}: {e}")
            return None
    
    def _check_volume_alert(self, data: Dict) -> bool:
        """Check if volume is unusually high"""
        volume_ratio = data['volume'] / data['avg_volume']
        return volume_ratio >= self.volume_threshold
    
    def _check_price_change_alert(self, data: Dict) -> bool:
        """Check if price changed significantly"""
        price_change = abs(data['current_price'] - data['previous_close']) / data['previous_close']
        return price_change >= self.price_change_threshold
    
    def _check_gap_alert(self, data: Dict) -> bool:
        """Check if stock gapped up or down"""
        gap = abs(data['open'] - data['previous_close']) / data['previous_close']
        return gap >= self.price_change_threshold
    
    async def _create_volume_alert(self, ticker: str, data: Dict) -> Optional[Alert]:
        """Create a volume alert"""
        volume_ratio = data['volume'] / data['avg_volume']
        direction = "UP" if data['current_price'] > data['previous_close'] else "DOWN"
        
        return Alert(
            ticker=ticker,
            alert_type=AlertType.UNUSUAL_VOLUME,
            price=data['current_price'],
            timestamp=datetime.now(),
            confidence=min(0.5 + (volume_ratio - self.volume_threshold) * 0.1, 0.9),
            details={
                'volume_ratio': volume_ratio,
                'volume': data['volume'],
                'avg_volume': data['avg_volume'],
                'direction': direction
            }
        )
    
    async def _create_price_change_alert(self, ticker: str, data: Dict) -> Optional[Alert]:
        """Create a price change alert"""
        price_change = (data['current_price'] - data['previous_close']) / data['previous_close']
        
        if price_change > 0:
            alert_type = AlertType.BREAKOUT
        else:
            alert_type = AlertType.DROP
        
        return Alert(
            ticker=ticker,
            alert_type=alert_type,
            price=data['current_price'],
            timestamp=datetime.now(),
            confidence=min(0.5 + abs(price_change) * 10, 0.9),
            details={
                'price_change': price_change,
                'previous_close': data['previous_close'],
                'high': data['high'],
                'low': data['low']
            }
        )
    
    async def _create_gap_alert(self, ticker: str, data: Dict) -> Optional[Alert]:
        """Create a gap alert"""
        gap = (data['open'] - data['previous_close']) / data['previous_close']
        
        if gap > 0:
            alert_type = AlertType.GAP_UP
        else:
            alert_type = AlertType.GAP_DOWN
        
        return Alert(
            ticker=ticker,
            alert_type=alert_type,
            price=data['current_price'],
            timestamp=datetime.now(),
            confidence=min(0.5 + abs(gap) * 10, 0.9),
            details={
                'gap': gap,
                'previous_close': data['previous_close'],
                'open': data['open']
            }
        )
    
    async def _validate_with_sentiment(self, alert: Alert):
        """Validate alert with sentiment analysis"""
        try:
            # Analyze news sentiment
            news_data = await self.stock_fetcher.fetch_news(alert.ticker, limit=3)
            if news_data:
                sentiment_scores = []
                for article in news_data:
                    try:
                        score = self.sentiment_analyzer.analyze(article.get('title', ''))['sentiment_score']
                        sentiment_scores.append(score)
                        if 'news_articles' not in alert.details:
                            alert.details['news_articles'] = []
                        alert.details['news_articles'].append({
                            'title': article.get('title', ''),
                            'url': article.get('link', ''),
                            'sentiment': score
                        })
                    except:
                        pass
                
                if sentiment_scores:
                    alert.sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
            
            # Analyze Reddit sentiment
            reddit_data = await self.reddit_scraper.search_alerts(alert.ticker, limit=3)
            if reddit_data:
                reddit_scores = []
                for post in reddit_data:
                    try:
                        score = self.sentiment_analyzer.analyze(post.get('title', ''))['sentiment_score']
                        reddit_scores.append(score)
                        if 'reddit_posts' not in alert.details:
                            alert.details['reddit_posts'] = []
                        alert.details['reddit_posts'].append({
                            'title': post.get('title', ''),
                            'url': post.get('url', ''),
                            'subreddit': post.get('subreddit', ''),
                            'sentiment': score
                        })
                    except:
                        pass
                
                if reddit_scores and alert.sentiment_score:
                    # Weight news and Reddit equally
                    alert.sentiment_score = (alert.sentiment_score + sum(reddit_scores) / len(reddit_scores)) / 2
                elif reddit_scores:
                    alert.sentiment_score = sum(reddit_scores) / len(reddit_scores)
        
        except Exception as e:
            print(f"[!] Error validating sentiment for {alert.ticker}: {e}")
    
    def _filter_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """Filter alerts based on cooldown and sentiment"""
        filtered = []
        now = datetime.now()
        
        for alert in alerts:
            # Check cooldown
            alert_key = f"{alert.ticker}_{alert.alert_type.value}"
            if alert_key in self.recent_alerts:
                last_time = self.recent_alerts[alert_key]
                if now - last_time < self.alert_cooldown:
                    continue
            
            # Check sentiment if available
            if alert.sentiment_score is not None:
                # For bullish alerts, require bullish sentiment
                if alert.alert_type in [AlertType.BREAKOUT, AlertType.GAP_UP]:
                    if alert.sentiment_score < -self.sentiment_threshold:
                        continue
                # For bearish alerts, require bearish sentiment
                elif alert.alert_type in [AlertType.DROP, AlertType.GAP_DOWN]:
                    if alert.sentiment_score > self.sentiment_threshold:
                        continue
            
            filtered.append(alert)
            self.recent_alerts[alert_key] = now
        
        return filtered
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert to Discord
        
        Args:
            alert: Alert to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.discord_webhook:
            print(f"[ALERT] {alert.ticker}: {alert.alert_type.value} @ ${alert.price:.2f}")
            return False
        
        try:
            import requests
            
            # Format alert type
            alert_type_emoji = {
                AlertType.UNUSUAL_VOLUME: "📊",
                AlertType.BREAKOUT: "🚀",
                AlertType.DROP: "📉",
                AlertType.GAP_UP: "⬆️",
                AlertType.GAP_DOWN: "⬇️"
            }.get(alert.alert_type, "⚠️")
            
            # Build embed
            embed = {
                "title": f"{alert_type_emoji} {alert.ticker} Alert",
                "color": self._get_alert_color(alert),
                "fields": [],
                "timestamp": alert.timestamp.isoformat()
            }
            
            # Add alert type
            embed["fields"].append({
                "name": "Alert Type",
                "value": alert.alert_type.value.replace("_", " ").title(),
                "inline": True
            })
            
            # Add price
            embed["fields"].append({
                "name": "Price",
                "value": f"${alert.price:.2f}",
                "inline": True
            })
            
            # Add confidence
            embed["fields"].append({
                "name": "Confidence",
                "value": f"{alert.confidence * 100:.0f}%",
                "inline": True
            })
            
            # Add sentiment if available
            if alert.sentiment_score is not None:
                sentiment_emoji = "🐂" if alert.sentiment_score > 0 else "🐻"
                sentiment_text = "Bullish" if alert.sentiment_score > 0 else "Bearish"
                embed["fields"].append({
                    "name": "Sentiment",
                    "value": f"{sentiment_emoji} {sentiment_text} ({abs(alert.sentiment_score) * 100:.0f}%)",
                    "inline": True
                })
            
            # Add details
            for key, value in alert.details.items():
                if key not in ['news_articles', 'reddit_posts']:
                    if isinstance(value, float):
                        if abs(value) < 1:
                            value = f"{value * 100:.2f}%"
                        else:
                            value = f"{value:.2f}"
                    embed["fields"].append({
                        "name": key.replace("_", " ").title(),
                        "value": str(value),
                        "inline": True
                    })
            
            # Add news articles
            if 'news_articles' in alert.details and alert.details['news_articles']:
                news_text = "\n".join([
                    f"[{article['title'][:50]}...]({article['url']})"
                    for article in alert.details['news_articles'][:3]
                ])
                embed["fields"].append({
                    "name": "📰 News",
                    "value": news_text,
                    "inline": False
                })
            
            # Add Reddit posts
            if 'reddit_posts' in alert.details and alert.details['reddit_posts']:
                reddit_text = "\n".join([
                    f"[{post['title'][:50]}...]({post['url']})"
                    for post in alert.details['reddit_posts'][:3]
                ])
                embed["fields"].append({
                    "name": "💬 Reddit",
                    "value": reddit_text,
                    "inline": False
                })
            
            # Send to Discord
            response = requests.post(
                self.discord_webhook,
                json={"embeds": [embed]},
                timeout=10
            )
            
            return response.status_code == 204
        
        except Exception as e:
            print(f"[!] Error sending alert to Discord: {e}")
            return False
    
    def _get_alert_color(self, alert: Alert) -> int:
        """Get color for alert embed"""
        if alert.alert_type in [AlertType.BREAKOUT, AlertType.GAP_UP]:
            return 5763719  # Green
        elif alert.alert_type in [AlertType.DROP, AlertType.GAP_DOWN]:
            return 15548997  # Red
        else:
            return 16776960  # Yellow
    
    async def scan_for_alerts(self, tickers: List[str]) -> List[Alert]:
        """
        Scan multiple tickers for alerts
        
        Args:
            tickers: List of ticker symbols to scan
            
        Returns:
            List of alerts found
        """
        all_alerts = []
        
        for ticker in tickers:
            alerts = await self.check_alerts(ticker)
            all_alerts.extend(alerts)
        
        return all_alerts