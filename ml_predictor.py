"""
ML Predictor - Machine Learning prediction module
Provides price direction predictions based on technical indicators
"""

import numpy as np
from typing import Dict, Optional
from datetime import datetime
import yfinance as yf


class MLPredictor:
    """Simple ML-based price direction predictor"""
    
    def __init__(self):
        self.model_version = "1.0.0"
    
    def predict(self, ticker: str, days: int = 5) -> Optional[Dict]:
        """
        Predict price direction for a ticker
        Returns dict with direction, confidence, and features used
        """
        try:
            # Fetch historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period='3mo')
            
            if hist.empty or len(hist) < 30:
                return None
            
            # Calculate technical features
            closes = hist['Close'].values
            volumes = hist['Volume'].values
            
            # Feature extraction
            features = self._extract_features(closes, volumes)
            
            # Simple rule-based prediction (can be replaced with actual ML model)
            direction, confidence = self._make_prediction(features)
            
            return {
                'ticker': ticker,
                'direction': direction,
                'confidence': confidence,
                'days': days,
                'features_used': features['summary'],
                'model_version': self.model_version,
                'prediction_date': datetime.now().isoformat(),
                'probabilities': {
                    'UP': round(confidence * 100, 1) if direction == 'UP' else round((1 - confidence) * 50, 1),
                    'DOWN': round(confidence * 100, 1) if direction == 'DOWN' else round((1 - confidence) * 50, 1),
                    'FLAT': round((1 - confidence) * 100, 1) if direction == 'NEUTRAL' else round((1 - confidence) * 30, 1)
                }
            }
            
        except Exception as e:
            print(f"[ML] Prediction error for {ticker}: {e}")
            return None
    
    def _extract_features(self, closes: np.ndarray, volumes: np.ndarray) -> Dict:
        """Extract technical features from price data"""
        features = {}
        
        # Price momentum
        if len(closes) >= 20:
            features['price_change_5d'] = (closes[-1] - closes[-6]) / closes[-6] if len(closes) >= 6 else 0
            features['price_change_20d'] = (closes[-1] - closes[-21]) / closes[-21] if len(closes) >= 21 else 0
            
            # Moving averages
            features['sma_20'] = np.mean(closes[-20:])
            features['sma_50'] = np.mean(closes[-50:]) if len(closes) >= 50 else features['sma_20']
            
            # Trend
            features['above_sma20'] = closes[-1] > features['sma_20']
            features['above_sma50'] = closes[-1] > features['sma_50']
            
            # Volume trend
            if len(volumes) >= 20:
                features['volume_ratio'] = volumes[-1] / np.mean(volumes[-20:])
            else:
                features['volume_ratio'] = 1.0
            
            # RSI approximation
            deltas = np.diff(closes[-15:])
            gains = np.sum(deltas[deltas > 0])
            losses = -np.sum(deltas[deltas < 0])
            if losses != 0:
                rs = gains / losses
                features['rsi'] = 100 - (100 / (1 + rs))
            else:
                features['rsi'] = 50
        else:
            features['price_change_5d'] = 0
            features['price_change_20d'] = 0
            features['rsi'] = 50
            features['volume_ratio'] = 1.0
            features['above_sma20'] = True
            features['above_sma50'] = True
        
        # Create summary string
        summary_parts = []
        if features.get('price_change_5d', 0) > 0.02:
            summary_parts.append("5d+")
        elif features.get('price_change_5d', 0) < -0.02:
            summary_parts.append("5d-")
        
        if features.get('rsi', 50) > 70:
            summary_parts.append("RSI>70")
        elif features.get('rsi', 50) < 30:
            summary_parts.append("RSI<30")
        
        if features.get('volume_ratio', 1.0) > 1.5:
            summary_parts.append("HighVol")
        
        features['summary'] = ", ".join(summary_parts) if summary_parts else "Neutral"
        
        return features
    
    def _make_prediction(self, features: Dict) -> tuple:
        """
        Make prediction based on features
        Returns (direction, confidence)
        """
        score = 0
        
        # Price momentum scoring
        if features.get('price_change_5d', 0) > 0.03:
            score += 2
        elif features.get('price_change_5d', 0) > 0.01:
            score += 1
        elif features.get('price_change_5d', 0) < -0.03:
            score -= 2
        elif features.get('price_change_5d', 0) < -0.01:
            score -= 1
        
        # Trend scoring
        if features.get('above_sma20', True):
            score += 1
        else:
            score -= 1
        
        if features.get('above_sma50', True):
            score += 1
        else:
            score -= 1
        
        # RSI scoring
        rsi = features.get('rsi', 50)
        if rsi > 70:
            score -= 1  # Overbought
        elif rsi < 30:
            score += 1  # Oversold
        
        # Volume scoring
        if features.get('volume_ratio', 1.0) > 1.5:
            score += 1  # High volume confirms move
        
        # Determine direction and confidence
        if score >= 2:
            direction = 'UP'
            confidence = min(0.5 + (score - 2) * 0.1, 0.9)
        elif score <= -2:
            direction = 'DOWN'
            confidence = min(0.5 + (abs(score) - 2) * 0.1, 0.9)
        else:
            direction = 'NEUTRAL'
            confidence = 0.5
        
        return direction, round(confidence, 2)


# Alias for compatibility with ticker_report.py
PricePredictor = MLPredictor


# Convenience function
def predict_ticker(ticker: str, days: int = 5) -> Optional[Dict]:
    """Quick prediction for a ticker"""
    predictor = MLPredictor()
    return predictor.predict(ticker, days)
