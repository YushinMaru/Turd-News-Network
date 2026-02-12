"""
Enhanced Backtesting Module - Track historical performance with detailed metrics
"""

import yfinance as yf
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import DB_PATH, WINNER_THRESHOLD, LOSER_THRESHOLD
import statistics


class EnhancedBacktester:
    """Advanced backtesting with multi-year tracking and benchmark comparison"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def backtest_ticker_history(self, ticker: str, years: int = 3) -> Optional[Dict]:
        """
        Backtest ticker performance over historical period
        
        Returns comprehensive metrics including:
        - Total return
        - Annualized return
        - Volatility
        - Sharpe ratio
        - Max drawdown
        - Win rate
        - Profit factor
        - Benchmark comparison (SPY)
        """
        try:
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years*365)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty or len(hist) < 50:
                return None
            
            # Fetch SPY benchmark
            spy = yf.Ticker('SPY')
            spy_hist = spy.history(start=start_date, end=end_date)
            
            # Calculate returns
            returns = hist['Close'].pct_change().dropna()
            spy_returns = spy_hist['Close'].pct_change().dropna()
            
            # Align dates
            common_dates = returns.index.intersection(spy_returns.index)
            returns = returns[common_dates]
            spy_returns = spy_returns[common_dates]
            
            # Performance metrics
            total_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
            spy_total_return = ((spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0]) - 1) * 100
            
            # Annualized return
            days = len(hist)
            years_actual = days / 252  # Trading days
            annualized_return = ((1 + total_return/100) ** (1/years_actual) - 1) * 100 if years_actual > 0 else 0
            
            # Volatility (annualized)
            volatility = returns.std() * (252 ** 0.5) * 100
            
            # Sharpe Ratio (assuming 4% risk-free rate)
            risk_free_rate = 0.04
            sharpe_ratio = (annualized_return/100 - risk_free_rate) / (volatility/100) if volatility > 0 else 0
            
            # Max Drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            # Win Rate
            positive_days = (returns > 0).sum()
            total_days = len(returns)
            win_rate = (positive_days / total_days * 100) if total_days > 0 else 0
            
            # Profit Factor
            gains = returns[returns > 0].sum()
            losses = abs(returns[returns < 0].sum())
            profit_factor = (gains / losses) if losses > 0 else 0
            
            # Alpha & Beta vs SPY
            covariance = returns.cov(spy_returns)
            spy_variance = spy_returns.var()
            beta = covariance / spy_variance if spy_variance > 0 else 1
            
            alpha = annualized_return - (risk_free_rate * 100 + beta * (spy_returns.mean() * 252 * 100 - risk_free_rate * 100))
            
            # Sortino Ratio (downside deviation)
            downside_returns = returns[returns < 0]
            downside_std = downside_returns.std() * (252 ** 0.5) if len(downside_returns) > 0 else 0
            sortino_ratio = (annualized_return/100 - risk_free_rate) / (downside_std) if downside_std > 0 else 0
            
            # Calmar Ratio
            calmar_ratio = (annualized_return / abs(max_drawdown)) if max_drawdown != 0 else 0
            
            return {
                'ticker': ticker,
                'period_years': years,
                'total_return': round(total_return, 2),
                'annualized_return': round(annualized_return, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'sortino_ratio': round(sortino_ratio, 2),
                'calmar_ratio': round(calmar_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 1),
                'profit_factor': round(profit_factor, 2),
                'alpha': round(alpha, 2),
                'beta': round(beta, 2),
                'spy_return': round(spy_total_return, 2),
                'excess_return': round(total_return - spy_total_return, 2),
                'trading_days': len(hist)
            }
            
        except Exception as e:
            print(f"Backtest error for {ticker}: {e}")
            return None
    
    def get_multi_timeframe_performance(self, ticker: str) -> Dict:
        """Get performance across multiple timeframes"""
        timeframes = {
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365,
            '2Y': 730,
            '3Y': 1095
        }
        
        results = {}
        
        for period, days in timeframes.items():
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                
                if not hist.empty and len(hist) >= 2:
                    total_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
                    results[period] = round(total_return, 2)
                else:
                    results[period] = None
                    
            except Exception:
                results[period] = None
        
        return results
    
    def save_backtest_results(self, ticker: str, backtest_data: Dict):
        """Save backtest results to database"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS backtest_results
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      ticker TEXT,
                      backtest_date TEXT,
                      period_years INTEGER,
                      total_return REAL,
                      annualized_return REAL,
                      volatility REAL,
                      sharpe_ratio REAL,
                      sortino_ratio REAL,
                      calmar_ratio REAL,
                      max_drawdown REAL,
                      win_rate REAL,
                      profit_factor REAL,
                      alpha REAL,
                      beta REAL,
                      spy_return REAL,
                      excess_return REAL,
                      UNIQUE(ticker, backtest_date))''')
        
        c.execute('''INSERT OR REPLACE INTO backtest_results
                     (ticker, backtest_date, period_years, total_return, annualized_return,
                      volatility, sharpe_ratio, sortino_ratio, calmar_ratio, max_drawdown,
                      win_rate, profit_factor, alpha, beta, spy_return, excess_return)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (ticker, datetime.now().isoformat(), backtest_data['period_years'],
                   backtest_data['total_return'], backtest_data['annualized_return'],
                   backtest_data['volatility'], backtest_data['sharpe_ratio'],
                   backtest_data['sortino_ratio'], backtest_data['calmar_ratio'],
                   backtest_data['max_drawdown'], backtest_data['win_rate'],
                   backtest_data['profit_factor'], backtest_data['alpha'],
                   backtest_data['beta'], backtest_data['spy_return'],
                   backtest_data['excess_return']))
        
        conn.commit()
        conn.close()
    
    def get_sector_comparison(self, ticker: str, sector: str) -> Optional[Dict]:
        """Compare ticker performance to sector ETF"""
        sector_etfs = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financial Services': 'XLF',
            'Consumer Cyclical': 'XLY',
            'Communication Services': 'XLC',
            'Industrials': 'XLI',
            'Consumer Defensive': 'XLP',
            'Energy': 'XLE',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE',
            'Basic Materials': 'XLB'
        }
        
        sector_etf = sector_etfs.get(sector)
        if not sector_etf:
            return None
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            stock = yf.Ticker(ticker)
            etf = yf.Ticker(sector_etf)
            
            stock_hist = stock.history(start=start_date, end=end_date)
            etf_hist = etf.history(start=start_date, end=end_date)
            
            if stock_hist.empty or etf_hist.empty:
                return None
            
            stock_return = ((stock_hist['Close'].iloc[-1] / stock_hist['Close'].iloc[0]) - 1) * 100
            etf_return = ((etf_hist['Close'].iloc[-1] / etf_hist['Close'].iloc[0]) - 1) * 100
            
            return {
                'sector': sector,
                'sector_etf': sector_etf,
                'stock_return': round(stock_return, 2),
                'sector_return': round(etf_return, 2),
                'relative_performance': round(stock_return - etf_return, 2),
                'outperforming': stock_return > etf_return
            }
            
        except Exception:
            return None
    
    def get_risk_adjusted_metrics(self, ticker: str) -> Optional[Dict]:
        """Calculate advanced risk-adjusted performance metrics"""
        try:
            backtest = self.backtest_ticker_history(ticker, years=3)
            if not backtest:
                return None
            
            # Risk classification
            if backtest['sharpe_ratio'] > 2:
                risk_rating = 'EXCELLENT'
            elif backtest['sharpe_ratio'] > 1:
                risk_rating = 'GOOD'
            elif backtest['sharpe_ratio'] > 0:
                risk_rating = 'FAIR'
            else:
                risk_rating = 'POOR'
            
            # Drawdown classification
            if abs(backtest['max_drawdown']) < 15:
                drawdown_rating = 'LOW'
            elif abs(backtest['max_drawdown']) < 30:
                drawdown_rating = 'MODERATE'
            elif abs(backtest['max_drawdown']) < 50:
                drawdown_rating = 'HIGH'
            else:
                drawdown_rating = 'EXTREME'
            
            return {
                'sharpe_ratio': backtest['sharpe_ratio'],
                'sortino_ratio': backtest['sortino_ratio'],
                'calmar_ratio': backtest['calmar_ratio'],
                'risk_rating': risk_rating,
                'max_drawdown': backtest['max_drawdown'],
                'drawdown_rating': drawdown_rating,
                'win_rate': backtest['win_rate'],
                'profit_factor': backtest['profit_factor']
            }
            
        except Exception:
            return None
