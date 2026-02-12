"""
AI Summary Generator - Provides trading recommendations based on analysis
"""

from typing import Dict, List, Optional
from datetime import datetime


class AISummaryGenerator:
    """Generates AI-powered trading recommendations based on stock analysis"""
    
    def generate_trading_recommendations(self, all_stocks_data: List[Dict]) -> Dict:
        """
        Generate comprehensive trading recommendations
        
        Returns:
            Dict with 'strong_buys', 'buys', 'holds', 'sells', 'avoid' lists
        """
        if not all_stocks_data:
            return self._empty_recommendations()
        
        strong_buys = []
        buys = []
        holds = []
        sells = []
        avoid = []
        
        for stock in all_stocks_data:
            recommendation = self._analyze_stock(stock)
            
            if recommendation['action'] == 'STRONG_BUY':
                strong_buys.append(recommendation)
            elif recommendation['action'] == 'BUY':
                buys.append(recommendation)
            elif recommendation['action'] == 'HOLD':
                holds.append(recommendation)
            elif recommendation['action'] == 'SELL':
                sells.append(recommendation)
            else:  # AVOID
                avoid.append(recommendation)
        
        return {
            'strong_buys': strong_buys[:5],  # Top 5
            'buys': buys[:5],
            'holds': holds[:3],
            'sells': sells[:3],
            'avoid': avoid[:3],
            'generated_at': datetime.now().isoformat()
        }
    
    def _analyze_stock(self, stock_data: Dict) -> Dict:
        """Analyze individual stock and return recommendation"""
        ticker = stock_data.get('ticker', 'UNKNOWN')
        score = 0
        reasons = []
        
        # Momentum Analysis (weight: 25%)
        momentum = stock_data.get('momentum', {})
        if momentum:
            mom_score = momentum.get('score', 50)
            if mom_score >= 75:
                score += 25
                reasons.append(f"🚀 Strong bullish momentum ({mom_score}/100)")
            elif mom_score >= 60:
                score += 15
                reasons.append(f"📈 Bullish momentum ({mom_score}/100)")
            elif mom_score <= 30:
                score -= 20
                reasons.append(f"📉 Weak momentum ({mom_score}/100)")
        
        # Technical Analysis (weight: 20%)
        tech_analysis = stock_data.get('technical_analysis', {})
        if tech_analysis:
            signal = tech_analysis.get('signal', 'NEUTRAL')
            if signal == 'BULLISH':
                score += 20
                reasons.append("✅ Bullish technical signals")
            elif signal == 'BEARISH':
                score -= 15
                reasons.append("⚠️ Bearish technical signals")
        
        # Risk/Reward (weight: 20%)
        risk_reward = stock_data.get('risk_reward')
        if risk_reward:
            ratio = risk_reward.get('ratio', 0)
            if ratio >= 3:
                score += 20
                reasons.append(f"💎 Excellent R/R ({ratio:.1f}:1)")
            elif ratio >= 2:
                score += 15
                reasons.append(f"✅ Good R/R ({ratio:.1f}:1)")
            elif ratio < 1:
                score -= 15
                reasons.append(f"⚠️ Poor R/R ({ratio:.1f}:1)")
        
        # Backtest Performance (weight: 15%)
        backtest = stock_data.get('backtest')
        if backtest:
            sharpe = backtest.get('sharpe_ratio', 0)
            total_return = backtest.get('total_return', 0)
            
            if sharpe > 1.5 and total_return > 50:
                score += 15
                reasons.append(f"📊 Strong historical performance (Sharpe: {sharpe:.2f})")
            elif sharpe < 0.5:
                score -= 10
                reasons.append(f"⚠️ Weak historical performance (Sharpe: {sharpe:.2f})")
        
        # Risk Assessment (weight: 10%)
        risk_assessment = stock_data.get('risk_assessment', {})
        if risk_assessment:
            risk_level = risk_assessment.get('risk_level', '')
            if 'VERY HIGH' in risk_level:
                score -= 15
                reasons.append("🔴 Very high risk profile")
            elif 'HIGH' in risk_level:
                score -= 10
                reasons.append("🟠 High risk profile")
            elif 'LOW' in risk_level:
                score += 10
                reasons.append("🟢 Low risk profile")
        
        # Actionable Alerts (weight: 10%)
        alerts = stock_data.get('price_alerts', [])
        actionable_alerts = [a for a in alerts if isinstance(a, dict) and a.get('actionable')]
        if actionable_alerts:
            score += 10
            reasons.append(f"🎯 {len(actionable_alerts)} actionable alert(s)")
        
        # Sentiment (weight: 10%)
        sentiment = stock_data.get('sentiment', {})
        if sentiment:
            sent_text = sentiment.get('sentiment', 'NEUTRAL')
            confidence = sentiment.get('confidence', 0)
            if sent_text == 'BULLISH' and confidence > 0.7:
                score += 10
                reasons.append(f"💬 Strong bullish sentiment ({confidence:.0%})")
            elif sent_text == 'BEARISH' and confidence > 0.7:
                score -= 10
                reasons.append(f"💬 Strong bearish sentiment ({confidence:.0%})")
        
        # Determine action based on score
        if score >= 60:
            action = 'STRONG_BUY'
            emoji = '🟢'
        elif score >= 35:
            action = 'BUY'
            emoji = '🟢'
        elif score >= -20:
            action = 'HOLD'
            emoji = '🟡'
        elif score >= -40:
            action = 'SELL'
            emoji = '🟠'
        else:
            action = 'AVOID'
            emoji = '🔴'
        
        return {
            'ticker': ticker,
            'name': stock_data.get('name', ticker),
            'action': action,
            'emoji': emoji,
            'score': score,
            'reasons': reasons[:5],  # Top 5 reasons
            'price': stock_data.get('price'),
            'market_cap': stock_data.get('market_cap')
        }
    
    def _empty_recommendations(self) -> Dict:
        """Return empty recommendations"""
        return {
            'strong_buys': [],
            'buys': [],
            'holds': [],
            'sells': [],
            'avoid': [],
            'generated_at': datetime.now().isoformat()
        }
    
    def format_recommendations_embed(self, recommendations: Dict) -> Dict:
        """Format recommendations as Discord embed"""
        if not any([recommendations['strong_buys'], recommendations['buys'], 
                   recommendations['holds'], recommendations['sells'], recommendations['avoid']]):
            return None
        
        fields = []
        
        # Strong Buys
        if recommendations['strong_buys']:
            strong_buy_lines = []
            for rec in recommendations['strong_buys']:
                reasons_str = " • ".join(rec['reasons'][:2])  # Top 2 reasons
                strong_buy_lines.append(
                    f"{rec['emoji']} **${rec['ticker']}** (${rec['price']:.2f})\n   {reasons_str}"
                )
            
            fields.append({
                "name": "🚀 STRONG BUYS - High Conviction Plays",
                "value": "\n\n".join(strong_buy_lines),
                "inline": False
            })
        
        # Buys
        if recommendations['buys']:
            buy_lines = []
            for rec in recommendations['buys']:
                reasons_str = " • ".join(rec['reasons'][:2])
                buy_lines.append(
                    f"{rec['emoji']} **${rec['ticker']}** (${rec['price']:.2f})\n   {reasons_str}"
                )
            
            fields.append({
                "name": "✅ BUYS - Solid Opportunities",
                "value": "\n\n".join(buy_lines),
                "inline": False
            })
        
        # Avoid
        if recommendations['avoid']:
            avoid_lines = []
            for rec in recommendations['avoid']:
                reasons_str = " • ".join(rec['reasons'][:2])
                avoid_lines.append(
                    f"{rec['emoji']} **${rec['ticker']}** - {reasons_str}"
                )
            
            fields.append({
                "name": "⚠️ AVOID - High Risk / Poor Setup",
                "value": "\n".join(avoid_lines),
                "inline": False
            })
        
        return {
            "title": "🤖 AI Trading Recommendations",
            "description": "Algorithmic analysis of Reddit DD picks with risk-adjusted scoring",
            "color": 0x00FF00,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "💎 Turd News Network AI • Scores based on momentum, technicals, risk/reward, backtest, sentiment"}
        }
