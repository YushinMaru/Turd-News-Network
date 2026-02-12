"""
Analysis, scoring, and assessment module - ENHANCED VERSION
New features: Momentum scoring, Price alerts, Social sentiment integration
"""

from typing import Dict, List, Optional, Tuple
from config import *


class AnalysisEngine:
    """Handles quality scoring, risk assessment, technical analysis, and momentum detection"""
    
    def calculate_quality_score(self, post: Dict) -> float:
        """Calculate quality score for DD post based on multiple factors (0-100)"""
        score = 0
        
        # Length score (max 25 points)
        length = post.get('post_length', 0)
        if length > 2000:
            score += 25
        elif length > 1000:
            score += 20
        elif length > 500:
            score += 15
        elif length > 200:
            score += 10
        
        # Engagement score (max 35 points)
        upvotes = post.get('score', 0)
        comments = post.get('num_comments', 0)
        ratio = post.get('upvote_ratio', 0)
        
        if upvotes > 500:
            score += 15
        elif upvotes > 100:
            score += 10
        elif upvotes > 50:
            score += 5
        
        if comments > 100:
            score += 10
        elif comments > 50:
            score += 7
        elif comments > 20:
            score += 5
        
        score += ratio * 10
        
        # Flair score (max 15 points)
        flair = post.get('flair', '') or ''
        flair_lower = flair.lower()
        if 'dd' in flair_lower or 'due diligence' in flair_lower:
            score += 15
        elif 'analysis' in flair_lower:
            score += 10
        elif 'discussion' in flair_lower:
            score += 5
        
        # Subreddit credibility (max 15 points)
        subreddit = post.get('subreddit', '') or ''
        subreddit_lower = subreddit.lower()
        if subreddit_lower in ['wallstreetbets', 'stocks', 'investing']:
            score += 15
        elif subreddit_lower in ['options', 'securityanalysis', 'valueinvesting']:
            score += 12
        else:
            score += 8
        
        # Time relevance (max 10 points)
        score += 10
        
        return min(score, 100)
    
    def get_risk_assessment(self, stock_data: Dict) -> Dict:
        """Generate risk assessment based on multiple factors"""
        risk_factors = []
        risk_score = 0  # 0 = low risk, 100 = high risk
        
        # Volatility (Beta)
        beta = stock_data.get('beta')
        if beta:
            if beta > 2:
                risk_factors.append("🔴 Very High Vol (β > 2.0)")
                risk_score += 30
            elif beta > 1.5:
                risk_factors.append("⚠️ High Vol (β > 1.5)")
                risk_score += 20
            elif beta < 0.5:
                risk_factors.append("🟢 Low Vol (β < 0.5)")
                risk_score += 5
            else:
                risk_factors.append(f"🟡 Moderate Vol (β = {beta:.2f})")
                risk_score += 10
        
        # Debt levels
        debt_to_equity = stock_data.get('debt_to_equity')
        if debt_to_equity:
            if debt_to_equity > 2:
                risk_factors.append(f"🔴 High Debt (D/E = {debt_to_equity:.2f})")
                risk_score += 25
            elif debt_to_equity > 1:
                risk_factors.append(f"⚠️ Moderate Debt (D/E = {debt_to_equity:.2f})")
                risk_score += 15
            else:
                risk_factors.append(f"[+] Low Debt (D/E = {debt_to_equity:.2f})")
                risk_score += 5
        
        # Liquidity
        current_ratio = stock_data.get('current_ratio')
        if current_ratio:
            if current_ratio < 1:
                risk_factors.append(f"🔴 Liquidity Risk (CR = {current_ratio:.2f})")
                risk_score += 20
            elif current_ratio < 1.5:
                risk_factors.append(f"⚠️ Tight Liquidity (CR = {current_ratio:.2f})")
                risk_score += 10
            else:
                risk_factors.append(f"[+] Good Liquidity (CR = {current_ratio:.2f})")
                risk_score += 3
        
        # Profitability
        profit_margin = stock_data.get('profit_margin')
        if profit_margin:
            if profit_margin < 0:
                risk_factors.append("[-] Unprofitable (Negative margins)")
                risk_score += 25
            elif profit_margin < 0.05:
                risk_factors.append(f"⚠️ Low Margins ({profit_margin*100:.1f}%)")
                risk_score += 15
            else:
                risk_factors.append(f"[+] Profitable ({profit_margin*100:.1f}% margin)")
                risk_score += 5
        
        # Market cap
        market_cap = stock_data.get('market_cap')
        if market_cap:
            if market_cap < 300_000_000:
                risk_factors.append("🔴 Micro Cap (Extreme Risk)")
                risk_score += 25
            elif market_cap < 2_000_000_000:
                risk_factors.append("⚠️ Small Cap (High Risk)")
                risk_score += 15
            elif market_cap < 10_000_000_000:
                risk_factors.append("[~] Mid Cap (Moderate Risk)")
                risk_score += 8
            else:
                risk_factors.append("[+] Large Cap (Lower Risk)")
                risk_score += 3
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "🔴 **VERY HIGH RISK**"
            color = COLOR_RISK_VERY_HIGH
        elif risk_score >= 50:
            risk_level = "⚠️ **HIGH RISK**"
            color = COLOR_RISK_HIGH
        elif risk_score >= 30:
            risk_level = "🟡 **MODERATE RISK**"
            color = COLOR_RISK_MODERATE
        else:
            risk_level = "🟢 **LOWER RISK**"
            color = COLOR_RISK_LOW
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'color': color
        }
    
    def get_valuation_assessment(self, stock_data: Dict) -> str:
        """Assess if stock is overvalued/undervalued"""
        signals = []
        
        pe_ratio = stock_data.get('pe_ratio')
        peg_ratio = stock_data.get('peg_ratio')
        price_to_book = stock_data.get('price_to_book')
        
        if pe_ratio:
            if pe_ratio < 0:
                signals.append("⚠️ Negative P/E (Unprofitable)")
            elif pe_ratio < 15:
                signals.append(f"[OK] Low P/E ({pe_ratio:.1f}) - Potentially undervalued")
            elif pe_ratio > 40:
                signals.append(f"⚠️ High P/E ({pe_ratio:.1f}) - Potentially overvalued")
        
        if peg_ratio:
            if peg_ratio < 1:
                signals.append(f"[OK] PEG < 1.0 ({peg_ratio:.2f}) - Growth undervalued")
            elif peg_ratio > 2:
                signals.append(f"⚠️ PEG > 2.0 ({peg_ratio:.2f}) - Growth overvalued")
        
        if price_to_book:
            if price_to_book < 1:
                signals.append(f"[OK] P/B < 1.0 ({price_to_book:.2f}) - Trading below book value")
            elif price_to_book > 5:
                signals.append(f"⚠️ P/B > 5.0 ({price_to_book:.2f}) - High premium to book")
        
        return "\n".join(signals) if signals else "No clear valuation signal"
    
    def get_technical_analysis_summary(self, indicators: Dict, current_price: float) -> Dict:
        """Generate human-readable technical analysis summary"""
        summary = {
            'signal': 'NEUTRAL',
            'strength': 0,
            'details': []
        }
        
        if not indicators:
            return summary
        
        signals = []
        
        # RSI analysis
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < RSI_OVERSOLD:
                signals.append(('BULLISH', 2, f"RSI oversold at {rsi:.1f}"))
                summary['details'].append(f"📊 **RSI: {rsi:.1f}** - Oversold (Bullish)")
            elif rsi > RSI_OVERBOUGHT:
                signals.append(('BEARISH', 2, f"RSI overbought at {rsi:.1f}"))
                summary['details'].append(f"📊 **RSI: {rsi:.1f}** - Overbought (Bearish)")
            else:
                summary['details'].append(f"📊 **RSI: {rsi:.1f}** - Neutral")
        
        # Moving average analysis
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        
        if sma_20 and sma_50:
            if current_price > sma_20 > sma_50:
                signals.append(('BULLISH', 2, "Price above 20 & 50 SMA"))
                summary['details'].append("📈 **MA Signal:** Bullish (Price > 20 SMA > 50 SMA)")
            elif current_price < sma_20 < sma_50:
                signals.append(('BEARISH', 2, "Price below 20 & 50 SMA"))
                summary['details'].append("📉 **MA Signal:** Bearish (Price < 20 SMA < 50 SMA)")
        
        if sma_200:
            if current_price > sma_200:
                signals.append(('BULLISH', 1, f"Above 200 SMA"))
                summary['details'].append(f"[OK] **Long-term:** Above 200 SMA (${sma_200:.2f})")
            else:
                signals.append(('BEARISH', 1, f"Below 200 SMA"))
                summary['details'].append(f"❌ **Long-term:** Below 200 SMA (${sma_200:.2f})")
        
        # MACD analysis
        macd = indicators.get('macd')
        if macd:
            if macd > 0:
                signals.append(('BULLISH', 1, "MACD positive"))
                summary['details'].append(f"⬆️ **MACD:** Positive momentum")
            else:
                signals.append(('BEARISH', 1, "MACD negative"))
                summary['details'].append(f"⬇️ **MACD:** Negative momentum")
        
        # Bollinger Bands
        bb_upper = indicators.get('bollinger_upper')
        bb_lower = indicators.get('bollinger_lower')
        if bb_upper and bb_lower:
            if current_price >= bb_upper:
                signals.append(('BEARISH', 1, "At upper Bollinger Band"))
                summary['details'].append("[-] **Bollinger:** At upper band (Overbought)")
            elif current_price <= bb_lower:
                signals.append(('BULLISH', 1, "At lower Bollinger Band"))
                summary['details'].append("[+] **Bollinger:** At lower band (Oversold)")
        
        # Volume analysis
        volume_ratio = indicators.get('volume_ratio')
        if volume_ratio:
            if volume_ratio > HIGH_VOLUME_THRESHOLD:
                summary['details'].append(f"📊 **Volume:** {volume_ratio:.1f}x average 🔥 (High interest)")
            elif volume_ratio < LOW_VOLUME_THRESHOLD:
                summary['details'].append(f"📊 **Volume:** {volume_ratio:.1f}x average ⚠️ (Low interest)")
        
        # Calculate overall signal
        bullish_score = sum(strength for signal, strength, _ in signals if signal == 'BULLISH')
        bearish_score = sum(strength for signal, strength, _ in signals if signal == 'BEARISH')
        
        if bullish_score > bearish_score + 2:
            summary['signal'] = 'BULLISH'
            summary['strength'] = bullish_score - bearish_score
        elif bearish_score > bullish_score + 2:
            summary['signal'] = 'BEARISH'
            summary['strength'] = bearish_score - bullish_score
        else:
            summary['signal'] = 'NEUTRAL'
            summary['strength'] = abs(bullish_score - bearish_score)
        
        return summary
    
    def calculate_momentum_score(self, stock_data: Dict) -> Dict:
        """
        NEW FEATURE: Calculate momentum score based on multiple timeframe returns
        Returns score 0-100 and momentum classification
        """
        mtf = stock_data.get('mtf_performance', {})
        
        if not mtf:
            return {'score': 50, 'classification': 'NEUTRAL', 'trend': 'UNKNOWN', 'emoji': '[~]'}

        # Weight different timeframes
        weights = {
            '1M': 0.30,   # Recent performance most important
            '3M': 0.25,
            '6M': 0.20,
            '1Y': 0.15,
            '2Y': 0.05,
            '3Y': 0.05
        }
        
        weighted_score = 0
        total_weight = 0
        
        for period, weight in weights.items():
            if period in mtf and mtf[period] is not None:
                # Convert return to score (0-100 scale)
                # -50% = 0, 0% = 50, +100% = 100
                period_score = min(max((mtf[period] + 50), 0), 100)
                weighted_score += period_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return {'score': 50, 'classification': 'NEUTRAL', 'trend': 'UNKNOWN', 'emoji': '[~]'}

        final_score = weighted_score / total_weight
        
        # Classify momentum
        if final_score >= 75:
            classification = 'STRONG_BULLISH'
            emoji = '[++]'  # Strong bullish
        elif final_score >= 60:
            classification = 'BULLISH'
            emoji = '[+]'   # Bullish
        elif final_score >= 40:
            classification = 'NEUTRAL'
            emoji = '[~]'   # Neutral
        elif final_score >= 25:
            classification = 'BEARISH'
            emoji = '[-]'   # Bearish
        else:
            classification = 'STRONG_BEARISH'
            emoji = '[--]'   # Strong bearish
        
        # Determine trend (improving vs deteriorating)
        if '1M' in mtf and '3M' in mtf and mtf['1M'] and mtf['3M']:
            if mtf['1M'] > mtf['3M'] * 1.2:
                trend = 'ACCELERATING'
            elif mtf['1M'] < mtf['3M'] * 0.8:
                trend = 'DECELERATING'
            else:
                trend = 'STABLE'
        else:
            trend = 'UNKNOWN'
        
        return {
            'score': round(final_score, 1),
            'classification': classification,
            'emoji': emoji,
            'trend': trend
        }
    
    def generate_price_alerts(self, stock_data: Dict, backtest: Optional[Dict]) -> List[str]:
        """
        NEW FEATURE: Generate intelligent price alerts based on technical levels
        """
        alerts = []
        price = stock_data['price']
        
        # 52-week high/low alerts
        if stock_data['52w_high']:
            pct_from_high = ((price - stock_data['52w_high']) / stock_data['52w_high']) * 100
            if pct_from_high > -5:
                alerts.append(f"[HOT] Near 52W high! Only {abs(pct_from_high):.1f}% away")
            elif pct_from_high > -10:
                alerts.append(f"[~] Approaching 52W high ({abs(pct_from_high):.1f}% away)")
        
        if stock_data['52w_low']:
            pct_from_low = ((price - stock_data['52w_low']) / stock_data['52w_low']) * 100
            if pct_from_low < 5:
                alerts.append(f"[!] Near 52W low! Only {pct_from_low:.1f}% above")
        
        # Moving average alerts
        indicators = stock_data.get('technical_indicators', {})
        sma_200 = indicators.get('sma_200')
        if sma_200:
            pct_from_200 = ((price - sma_200) / sma_200) * 100
            if -2 < pct_from_200 < 2:
                alerts.append(f"[*] Testing 200 SMA support/resistance at ${sma_200:.2f}")
        
        # Volume alert
        if stock_data.get('volume') and stock_data.get('avg_volume'):
            ratio = stock_data['volume'] / stock_data['avg_volume']
            if ratio > 3:
                alerts.append(f"[!!!] EXTREME volume! {ratio:.1f}x average - unusual activity")
            elif ratio > 2:
                alerts.append(f"[!!] High volume: {ratio:.1f}x average")
        
        # Backtest-based alerts
        if backtest:
            if backtest.get('max_drawdown', 0) < -40:
                alerts.append(f"[!] Historical max drawdown: {backtest['max_drawdown']:.1f}% - high volatility expected")
        
        return alerts
    
    def calculate_risk_reward_ratio(self, stock_data: Dict, backtest: Optional[Dict]) -> Optional[Dict]:
        """
        NEW FEATURE: Calculate potential risk/reward based on historical data
        """
        if not backtest:
            return None
        
        price_target = stock_data.get('price_target')
        current_price = stock_data['price']
        max_drawdown = abs(backtest.get('max_drawdown', 0))
        
        if not price_target or price_target <= 0:
            return None
        
        # Calculate potential upside
        upside = ((price_target - current_price) / current_price) * 100
        
        # Use historical max drawdown as potential downside
        downside = max_drawdown
        
        # Calculate risk/reward ratio
        if downside > 0:
            ratio = upside / downside
        else:
            ratio = 0
        
        # Rating
        if ratio > 3:
            rating = 'EXCELLENT'
            emoji = '[+]'
        elif ratio > 2:
            rating = 'GOOD'
            emoji = '[+]'
        elif ratio > 1:
            rating = 'FAIR'
            emoji = '[~]'
        else:
            rating = 'POOR'
            emoji = '[-]'
        
        return {
            'ratio': round(ratio, 2),
            'upside_pct': round(upside, 1),
            'downside_pct': round(downside, 1),
            'rating': rating,
            'emoji': emoji
        }
    
    def analyze_options_flow(self, options_data: Dict, current_price: float) -> Dict:
        """
        Analyze options flow data and classify as BULLISH_FLOW, BEARISH_FLOW, or NEUTRAL.
        Returns flow classification, signals, and a compact summary string.
        """
        pc_ratio = options_data.get('pc_ratio')
        max_pain = options_data.get('max_pain')
        unusual = options_data.get('unusual_strikes', [])
        total_call_vol = options_data.get('total_call_vol', 0)
        total_put_vol = options_data.get('total_put_vol', 0)

        signals = []
        bullish_points = 0
        bearish_points = 0

        # Put/Call ratio analysis
        if pc_ratio is not None:
            if pc_ratio < OPTIONS_EXTREME_PC_LOW:
                signals.append(f"P/C {pc_ratio:.2f} (heavy call buying)")
                bullish_points += 2
            elif pc_ratio > OPTIONS_EXTREME_PC_HIGH:
                signals.append(f"P/C {pc_ratio:.2f} (heavy put buying)")
                bearish_points += 2
            else:
                signals.append(f"P/C {pc_ratio:.2f}")

        # Max pain vs current price
        if max_pain and current_price:
            pain_diff_pct = ((max_pain - current_price) / current_price) * 100
            if pain_diff_pct > 5:
                signals.append(f"Max Pain ${max_pain:.0f} ({pain_diff_pct:+.1f}% above)")
                bullish_points += 1
            elif pain_diff_pct < -5:
                signals.append(f"Max Pain ${max_pain:.0f} ({pain_diff_pct:+.1f}% below)")
                bearish_points += 1
            else:
                signals.append(f"Max Pain ${max_pain:.0f}")

        # Unusual activity analysis
        unusual_calls = [u for u in unusual if u['type'] == 'CALL']
        unusual_puts = [u for u in unusual if u['type'] == 'PUT']

        if unusual_calls:
            top = unusual_calls[0]
            signals.append(f"${top['strike']:.0f}C {top['ratio']:.1f}x OI")
            bullish_points += 1
        if unusual_puts:
            top = unusual_puts[0]
            signals.append(f"${top['strike']:.0f}P {top['ratio']:.1f}x OI")
            bearish_points += 1

        # Large single-strike bets (volume > 1000 and ratio > threshold)
        for u in unusual:
            if u['volume'] > 1000 and u['ratio'] >= OPTIONS_UNUSUAL_VOLUME_THRESHOLD:
                if u['type'] == 'CALL':
                    bullish_points += 1
                else:
                    bearish_points += 1

        # Classify overall flow
        if bullish_points > bearish_points + 1:
            flow = 'BULLISH_FLOW'
            emoji = '\U0001f7e2'
        elif bearish_points > bullish_points + 1:
            flow = 'BEARISH_FLOW'
            emoji = '\U0001f534'
        else:
            flow = 'NEUTRAL'
            emoji = '\U0001f7e1'

        return {
            'flow': flow,
            'emoji': emoji,
            'pc_ratio': pc_ratio,
            'max_pain': max_pain,
            'unusual_strikes': unusual,
            'signals': signals,
            'expiry': options_data.get('expiry', ''),
            'bullish_points': bullish_points,
            'bearish_points': bearish_points
        }

    def calculate_fibonacci_levels(self, stock_data: Dict) -> Optional[Dict]:
        """
        Calculate Fibonacci retracement levels from recent swing high/low.
        Returns levels and which level the current price is nearest.
        """
        high_52 = stock_data.get('52w_high')
        low_52 = stock_data.get('52w_low')
        price = stock_data.get('price')

        if not high_52 or not low_52 or not price or high_52 <= low_52:
            return None

        diff = high_52 - low_52
        levels = {
            '0.0': high_52,
            '23.6': high_52 - diff * 0.236,
            '38.2': high_52 - diff * 0.382,
            '50.0': high_52 - diff * 0.500,
            '61.8': high_52 - diff * 0.618,
            '78.6': high_52 - diff * 0.786,
            '100.0': low_52,
        }

        # Find nearest level
        nearest_level = None
        nearest_dist = float('inf')
        for label, level_price in levels.items():
            dist = abs(price - level_price)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_level = label

        nearest_pct = (nearest_dist / price * 100) if price > 0 else 0

        return {
            'levels': {k: round(v, 2) for k, v in levels.items()},
            'nearest_level': nearest_level,
            'nearest_level_price': round(levels.get(nearest_level, 0), 2),
            'distance_pct': round(nearest_pct, 2),
        }

    def calculate_unified_signal(self, indicators: Dict, current_price: float) -> Dict:
        """
        Calculate unified trading signal from technical indicators.
        Wrapper that calls generate_signal_summary with proper parameter format.
        """
        # Create a compatible stock_data dict from indicators and price
        stock_data = {
            'price': current_price,
            'technical_indicators': indicators
        }
        return self.generate_signal_summary(stock_data)

    def generate_signal_summary(self, stock_data: Dict) -> Dict:
        """
        Combine RSI, MACD, Bollinger, moving averages, ADX, Ichimoku, VWAP,
        and Fibonacci into a single BUY/SELL/HOLD signal with confidence score.
        """
        indicators = stock_data.get('technical_indicators', {})
        price = stock_data.get('price', 0)

        if not indicators or not price:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reasons': [],
                'bullish_count': 0,
                'bearish_count': 0,
                'total_checks': 0
            }

        bullish = 0
        bearish = 0
        total_weight = 0
        reasons = []

        # RSI (weight 2)
        rsi = indicators.get('rsi')
        if rsi is not None:
            total_weight += 2
            if rsi < RSI_OVERSOLD:
                bullish += 2
                reasons.append(f"RSI oversold ({rsi:.0f})")
            elif rsi > RSI_OVERBOUGHT:
                bearish += 2
                reasons.append(f"RSI overbought ({rsi:.0f})")

        # MACD (weight 2)
        macd = indicators.get('macd')
        if macd is not None:
            total_weight += 2
            if macd > 0:
                bullish += 2
                reasons.append("MACD bullish")
            else:
                bearish += 2
                reasons.append("MACD bearish")

        # Moving average alignment (weight 2)
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        if sma_20 and sma_50:
            total_weight += 2
            if price > sma_20 > sma_50:
                bullish += 2
                reasons.append("Above 20/50 SMA")
            elif price < sma_20 < sma_50:
                bearish += 2
                reasons.append("Below 20/50 SMA")

        # 200 SMA trend (weight 1)
        sma_200 = indicators.get('sma_200')
        if sma_200:
            total_weight += 1
            if price > sma_200:
                bullish += 1
                reasons.append("Above 200 SMA")
            else:
                bearish += 1
                reasons.append("Below 200 SMA")

        # Bollinger Bands (weight 1)
        bb_upper = indicators.get('bollinger_upper')
        bb_lower = indicators.get('bollinger_lower')
        if bb_upper and bb_lower:
            total_weight += 1
            if price <= bb_lower:
                bullish += 1
                reasons.append("At lower Bollinger")
            elif price >= bb_upper:
                bearish += 1
                reasons.append("At upper Bollinger")

        # ADX + DI (weight 2) - confirms trend direction when trending
        adx = indicators.get('adx')
        plus_di = indicators.get('plus_di')
        minus_di = indicators.get('minus_di')
        if adx is not None and plus_di is not None and minus_di is not None:
            if adx >= ADX_TRENDING_THRESHOLD:
                total_weight += 2
                if plus_di > minus_di:
                    bullish += 2
                    reasons.append(f"ADX trending bullish ({adx:.0f})")
                else:
                    bearish += 2
                    reasons.append(f"ADX trending bearish ({adx:.0f})")

        # Ichimoku Cloud (weight 2)
        senkou_a = indicators.get('ichimoku_senkou_a')
        senkou_b = indicators.get('ichimoku_senkou_b')
        if senkou_a is not None and senkou_b is not None:
            cloud_top = max(senkou_a, senkou_b)
            cloud_bottom = min(senkou_a, senkou_b)
            total_weight += 2
            if price > cloud_top:
                bullish += 2
                reasons.append("Above Ichimoku cloud")
            elif price < cloud_bottom:
                bearish += 2
                reasons.append("Below Ichimoku cloud")

        # VWAP (weight 1)
        vwap = indicators.get('vwap')
        if vwap is not None:
            total_weight += 1
            if price > vwap:
                bullish += 1
                reasons.append("Above VWAP")
            else:
                bearish += 1
                reasons.append("Below VWAP")

        # Calculate confidence and signal
        if total_weight == 0:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reasons': [],
                'bullish_count': 0,
                'bearish_count': 0,
                'total_checks': 0
            }

        net = bullish - bearish
        max_possible = total_weight
        confidence = abs(net) / max_possible if max_possible > 0 else 0
        confidence = min(confidence, 1.0)
        confidence_pct = round(confidence * 100)

        if net >= 3:
            signal = 'BUY'
        elif net <= -3:
            signal = 'SELL'
        else:
            signal = 'HOLD'

        return {
            'signal': signal,
            'confidence': confidence_pct,
            'reasons': reasons[:5],
            'bullish_count': bullish,
            'bearish_count': bearish,
            'total_checks': total_weight
        }

    def format_number(self, num):
        """Format large numbers for readability"""
        if num is None or num == 'N/A':
            return 'N/A'
        if isinstance(num, (int, float)):
            if num >= 1e12:
                return f"${num/1e12:.2f}T"
            elif num >= 1e9:
                return f"${num/1e9:.2f}B"
            elif num >= 1e6:
                return f"${num/1e6:.2f}M"
            elif num >= 1e3:
                return f"${num/1e3:.2f}K"
            else:
                return f"${num:,.2f}"
        return str(num)
    
    def format_percent(self, num):
        """Format percentages"""
        if num is None or num == 'N/A':
            return 'N/A'
        if isinstance(num, (int, float)):
            return f"{num*100:.2f}%"
        return str(num)
