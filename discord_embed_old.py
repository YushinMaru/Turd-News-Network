"""
Enhanced Discord embed builder with COMPACT horizontal formatting
Version 2.0 - Focus on width over height for better readability
FIXED: Discord 400 errors, embed size validation, field limits
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import *
from analysis import AnalysisEngine
from discord_sender import DiscordSender


class DiscordEmbedBuilder:
    """Builds beautiful, COMPACT Discord embeds with horizontal layout"""
    
    def __init__(self, webhook_url: str, db_manager):
        self.webhook_url = webhook_url
        self.db = db_manager
        self.analysis = AnalysisEngine()
        self.sender = DiscordSender(webhook_url)
    
    def _validate_field(self, field):
        """Validate Discord embed field to prevent 400 errors"""
        if not field:
            return False
        if not field.get('name') or not field.get('value'):
            return False
        value_str = str(field['value']).strip()
        if len(value_str) == 0 or value_str == 'N/A':
            return False
        # Discord limits
        if len(str(field['name'])) > 256:
            field['name'] = str(field['name'])[:253] + '...'
        if len(value_str) > 1024:
            field['value'] = value_str[:1021] + '...'
        return True
    
    def _count_embed_chars(self, embed: Dict) -> int:
        """Count total characters in embed"""
        total = 0
        if 'title' in embed:
            total += len(str(embed['title']))
        if 'description' in embed:
            total += len(str(embed['description']))
        if 'footer' in embed and 'text' in embed['footer']:
            total += len(str(embed['footer']['text']))
        for field in embed.get('fields', []):
            total += len(str(field.get('name', '')))
            total += len(str(field.get('value', '')))
        return total
    
    def send_discord_embed(self, post_data: Dict, stock_data_list: List[Dict]) -> bool:
        """Send COMPACT formatted embed to Discord - with size limits and optional chart"""
        try:
            # Limit stocks to prevent embed overflow (Discord 400 errors)
            # Multiple stocks can cause total char count > 6000
            MAX_STOCKS_PER_EMBED = 2  # Reduced from unlimited to prevent 400 errors

            if len(stock_data_list) > MAX_STOCKS_PER_EMBED:
                print(f"   [WARNING]  Limiting to {MAX_STOCKS_PER_EMBED} stocks (found {len(stock_data_list)})")
                stock_data_list = stock_data_list[:MAX_STOCKS_PER_EMBED]

            embeds = []
            quality_score = post_data.get('quality_score', 0)

            # Collect chart file paths from stock data (use first stock's chart for the embed image)
            chart_paths = []
            chart_filename = None
            for sd in stock_data_list:
                cp = sd.get('chart_path')
                if cp and os.path.exists(cp):
                    chart_paths.append(cp)
                    if chart_filename is None:
                        chart_filename = os.path.basename(cp)

            # Build single comprehensive embed with post + stocks
            main_embed = self._build_unified_embed(post_data, stock_data_list, quality_score)

            # Attach chart image reference to the embed if available
            if chart_filename:
                main_embed['image'] = {'url': f'attachment://{chart_filename}'}

            # Validate embed size
            char_count = self._count_embed_chars(main_embed)
            if char_count > 5500:  # Leave buffer under 6000 limit
                print(f"   [WARNING]  Embed too large ({char_count} chars), using fallback format...")
                # Fallback: Reduce to 1 stock only
                main_embed = self._build_unified_embed(post_data, stock_data_list[:1], quality_score)
                if chart_filename:
                    main_embed['image'] = {'url': f'attachment://{chart_filename}'}

            embeds.append(main_embed)

            # Send with file attachments if we have charts, otherwise plain embeds
            if chart_paths:
                return self.sender.send_embeds_with_files(embeds, post_data['title'], chart_paths)
            else:
                return self.sender.send_embeds(embeds, post_data['title'])
                
        except Exception as e:
            # Strip emojis from error message for Windows console compatibility
            error_msg = str(e).replace('\U0001f7e2', '[GREEN]').replace('\U0001f534', '[RED]').replace('\U0001f7e1', '[YELLOW]').replace('\U0001f504', '[ROTATING]').replace('\u2705', '[CHECK]')
            print(f"Error sending to Discord: {error_msg}")
            import traceback
            traceback.print_exc()
            return False
    
    def _build_unified_embed(self, post_data: Dict, stock_data_list: List[Dict], quality_score: float) -> Dict:
        """Build SINGLE unified embed with post header + all stocks (COMPACT)"""

        # Determine quality badge
        if quality_score >= PREMIUM_DD_SCORE:
            quality_emoji, quality_text = "💎", "PREMIUM DD"
        elif quality_score >= QUALITY_DD_SCORE:
            quality_emoji, quality_text = "⭐", "QUALITY DD"
        else:
            quality_emoji, quality_text = "📊", "Standard DD"

        # Dynamic color: override based on strongest signal/sentiment
        color = self._determine_embed_color(post_data, stock_data_list, quality_score)

        # Get sentiment data
        sentiment = post_data.get('sentiment', {})
        sentiment_text = sentiment.get('sentiment', 'NEUTRAL')
        sentiment_confidence = sentiment.get('confidence', 0)

        # Sentiment emoji
        if sentiment_text == 'BULLISH':
            sentiment_emoji = '\U0001f7e2'
        elif sentiment_text == 'BEARISH':
            sentiment_emoji = '\U0001f534'
        else:
            sentiment_emoji = '\U0001f7e1'

        # Build compact description
        time_ago = self._get_time_ago(datetime.now())

        description = f"""**📉 r/{post_data['subreddit']}** • {post_data.get('score', 0):,}⬆️ {post_data.get('num_comments', 0):,}💬 • {post_data.get('upvote_ratio', 0)*100:.0f}% upvoted • Quality: **{quality_score:.0f}/100**
**{sentiment_emoji} Sentiment:** {sentiment_text} ({sentiment_confidence:.0%} confidence) • {time_ago}"""

        if post_data.get('flair'):
            description = f"**🏷️ {post_data['flair']}**\n{description}"

        # Build fields for all stocks
        fields = []

        for i, stock_data in enumerate(stock_data_list):
            if not stock_data:
                continue

            ticker = stock_data['ticker']

            # Add separator between stocks (except first)
            if i > 0:
                fields.append({
                    "name": "──────────────────────────────────────",
                    "value": "\u200b",  # Zero-width space
                    "inline": False
                })

            # Quick Stats one-liner at top of each stock section
            quick_stats = self._build_quick_stats_line(stock_data)
            if quick_stats:
                fields.append(quick_stats)
            else:
                # Fallback to old stock header
                fields.append({
                    "name": f"${ticker} \u2022 {stock_data['name'][:50]}",
                    "value": f"**{stock_data['sector']}** \u2022 {stock_data['industry'][:40]}",
                    "inline": False
                })

            # Build compact stock fields
            stock_fields = self._build_compact_stock_fields(stock_data)
            fields.extend(stock_fields)

        # Filter valid fields
        fields = [f for f in fields if self._validate_field(f)]

        # Add big sentiment banner at the bottom
        sentiment_banner = self._build_sentiment_banner(sentiment_text, sentiment_confidence)
        if sentiment_banner:
            fields.append(sentiment_banner)

        embed = {
            "title": f"{quality_emoji} {quality_text}: {post_data['title'][:150]}",
            "url": post_data['url'],
            "color": color,
            "description": description,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"💎 Turd News Network Enhanced v5.0 | {len(stock_data_list)} stock{'s' if len(stock_data_list) != 1 else ''} analyzed"}
        }

        # Add company logo thumbnail via Clearbit
        if stock_data_list:
            thumb_url = self._get_logo_thumbnail(stock_data_list[0])
            if thumb_url:
                embed['thumbnail'] = {'url': thumb_url}

        return embed

    def _determine_embed_color(self, post_data: Dict, stock_data_list: List[Dict], quality_score: float) -> int:
        """Determine embed color dynamically from signal strength and sentiment"""
        # Premium DD gets gold regardless
        if quality_score >= PREMIUM_DD_SCORE:
            return COLOR_PREMIUM

        # Check for signal-based color from first stock
        if stock_data_list:
            sd = stock_data_list[0]
            signal = sd.get('signal_summary', {})
            sig_type = signal.get('signal', '')
            confidence = signal.get('confidence', 0)
            if sig_type == 'BUY' and confidence >= 60:
                return COLOR_STRONG_BULLISH
            elif sig_type == 'BUY':
                return COLOR_BULLISH
            elif sig_type == 'SELL' and confidence >= 60:
                return COLOR_STRONG_BEARISH
            elif sig_type == 'SELL':
                return COLOR_BEARISH

        # Fall back to sentiment-based color
        sentiment = post_data.get('sentiment', {})
        sent_text = sentiment.get('sentiment', 'NEUTRAL')
        if sent_text == 'BULLISH':
            return COLOR_BULLISH
        elif sent_text == 'BEARISH':
            return COLOR_BEARISH

        # Default by quality tier
        if quality_score >= QUALITY_DD_SCORE:
            return COLOR_QUALITY
        return COLOR_STANDARD

    @staticmethod
    def _get_logo_thumbnail(stock_data: Dict) -> Optional[str]:
        """Get company logo URL from Clearbit via the company website domain"""
        website = stock_data.get('website', '')
        if not website:
            return None
        try:
            from urllib.parse import urlparse
            domain = urlparse(website).netloc
            if not domain:
                domain = website.replace('https://', '').replace('http://', '').split('/')[0]
            if domain:
                return f"https://logo.clearbit.com/{domain}"
        except Exception:
            pass
        return None
    
    def _build_quick_stats_line(self, sd: Dict) -> Optional[Dict]:
        """Build Quick Stats one-liner at top of each stock section"""
        ticker = sd.get('ticker', '')
        name = sd.get('name', '')[:30]
        price = sd.get('price', 0)
        change = sd.get('change_pct', 0)
        mcap = sd.get('market_cap')
        rsi = (sd.get('technical_indicators') or {}).get('rsi')

        if not price:
            return None

        change_emoji = '\U0001f7e2' if change >= 0 else '\U0001f534'
        parts = [f"**${ticker}** {name} \u2022 ${price:,.2f} {change_emoji} {change:+.2f}%"]

        if mcap:
            parts.append(f"MC: {self.analysis.format_number(mcap)}")
        pe = sd.get('pe_ratio')
        if pe and pe > 0:
            parts.append(f"P/E: {pe:.1f}")
        if rsi is not None:
            parts.append(f"RSI: {rsi:.0f}")

        sector = sd.get('sector', '')
        industry = sd.get('industry', '')[:30]

        value = " | ".join(parts)
        if sector:
            value += f"\n**{sector}** \u2022 {industry}"

        return {"name": "\u200b", "value": value, "inline": False}

    @staticmethod
    def _build_sparkline(values: List[float]) -> str:
        """Build a Unicode sparkline text chart from a list of values"""
        if not values or len(values) < 2:
            return ""

        blocks = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
        v_min = min(values)
        v_max = max(values)
        v_range = v_max - v_min

        if v_range == 0:
            return blocks[4] * len(values)

        spark = ""
        for v in values:
            idx = int((v - v_min) / v_range * 7)
            idx = max(0, min(7, idx))
            spark += blocks[idx]
        return spark

    def _build_compact_stock_fields(self, sd: Dict) -> List[Dict]:
        """Build COMPACT horizontal fields for a single stock"""
        fields = []
        ticker = sd['ticker']
        
        # Get all analysis data
        stats = self.db.get_stock_stats(ticker)
        risk_assessment = self.analysis.get_risk_assessment(sd)
        technical_indicators = sd.get('technical_indicators', {})
        tech_analysis = self.analysis.get_technical_analysis_summary(technical_indicators, sd['price'])
        backtest = sd.get('backtest')
        mtf_performance = sd.get('mtf_performance', {})
        
        # Row 1: Price, Volume, Market Cap (3 columns)
        price_field = self._build_price_compact(sd)
        volume_field = self._build_volume_compact(sd)
        mcap_field = self._build_mcap_compact(sd)
        
        if price_field: fields.append(price_field)
        if volume_field: fields.append(volume_field)
        if mcap_field: fields.append(mcap_field)
        
        # Row 2: Valuation, Profitability, Health (3 columns)
        val_field = self._build_valuation_compact(sd)
        prof_field = self._build_profitability_compact(sd)
        health_field = self._build_health_compact(sd)
        
        if val_field: fields.append(val_field)
        if prof_field: fields.append(prof_field)
        if health_field: fields.append(health_field)
        
        # Row 3: Performance Timeline (full width)
        perf_field = self._build_performance_timeline(mtf_performance)
        if perf_field: fields.append(perf_field)
        
        # Row 4: Backtest Summary (full width) - SIMPLIFIED to save space
        if backtest:
            backtest_field = self._build_backtest_compact(backtest, sd['price'])
            if backtest_field: fields.append(backtest_field)
        
        # Row 5: Risk & Technical Signal (2 columns side by side)
        risk_field = self._build_risk_compact(risk_assessment)
        tech_field = self._build_technical_compact(tech_analysis)

        if risk_field: fields.append(risk_field)
        if tech_field: fields.append(tech_field)

        # Row 5a: Unified Signal Summary (if available, full width)
        signal_summary = sd.get('signal_summary')
        fib_data = sd.get('fibonacci')
        if signal_summary:
            signal_field = self._build_signal_summary_compact(signal_summary, technical_indicators, fib_data)
            if signal_field: fields.append(signal_field)

        # Row 5a2: ML Prediction (if available, full width)
        ml_prediction = sd.get('ml_prediction')
        if ml_prediction:
            ml_field = self._build_ml_prediction_compact(ml_prediction)
            if ml_field: fields.append(ml_field)

        # Row 5b: Options Flow (if available, full width)
        options_flow = sd.get('options_flow')
        if options_flow:
            options_field = self._build_options_compact(options_flow)
            if options_field: fields.append(options_field)

        # Row 5c: Insider/Institutional data (if available, full width)
        insider_data = sd.get('insider_data')
        if insider_data:
            insider_field = self._build_insider_compact(insider_data)
            if insider_field: fields.append(insider_field)

        # Row 5d: Congress trades (if available, full width)
        congress_data = sd.get('congress_data')
        if congress_data:
            congress_field = self._build_congress_compact(congress_data)
            if congress_field: fields.append(congress_field)

        # Row 6: Track Record (if exists, full width)
        if stats:
            track_field = self._build_track_record_compact(stats)
            if track_field: fields.append(track_field)
        
        # Row 7: Quick Links (full width, single row) - REMOVED news to save space
        links_field = self._build_quick_links(sd)
        if links_field: fields.append(links_field)
        
        return fields
    
    def _build_price_compact(self, sd: Dict) -> Dict:
        """Compact price field"""
        change_emoji = "📈" if sd['change_pct'] >= 0 else "📉"
        change_color = "🟢" if sd['change_pct'] >= 0 else "🔴"
        
        value = f"**${sd['price']:,.2f}** {change_color}\n{change_emoji} **{sd['change_pct']:+.2f}%**"
        
        if sd['52w_high'] and sd['52w_low']:
            value += f"\n52W: ${sd['52w_low']:.0f}-${sd['52w_high']:.0f}"
        
        return {"name": "💵 Price", "value": value, "inline": True}
    
    def _build_volume_compact(self, sd: Dict) -> Optional[Dict]:
        """Compact volume field"""
        if not sd['volume']:
            return None
        
        volume_str = self._format_volume(sd['volume'])
        
        lines = [f"**{volume_str}**"]
        
        if sd['avg_volume']:
            ratio = sd['volume'] / sd['avg_volume']
            if ratio > HIGH_VOLUME_THRESHOLD:
                lines.append(f"🔥 **{ratio:.1f}x** avg")
            elif ratio < LOW_VOLUME_THRESHOLD:
                lines.append(f"⚠️ **{ratio:.1f}x** avg")
            else:
                lines.append(f"**{ratio:.1f}x** avg")
        
        return {"name": "📦 Volume", "value": "\n".join(lines), "inline": True}
    
    def _build_mcap_compact(self, sd: Dict) -> Optional[Dict]:
        """Compact market cap field"""
        if not sd['market_cap']:
            return None
        
        mcap_str = self.analysis.format_number(sd['market_cap'])
        
        # Market cap category
        mcap = sd['market_cap']
        if mcap < 300_000_000:
            category = "Micro 🔴"
        elif mcap < 2_000_000_000:
            category = "Small ⚠️"
        elif mcap < 10_000_000_000:
            category = "Mid 🟡"
        else:
            category = "Large 🟢"
        
        return {"name": "🏢 Market Cap", "value": f"**{mcap_str}**\n{category}", "inline": True}
    
    def _build_valuation_compact(self, sd: Dict) -> Optional[Dict]:
        """Compact valuation metrics - horizontal format"""
        parts = []
        
        if sd['pe_ratio'] and sd['pe_ratio'] > 0:
            parts.append(f"P/E: **{sd['pe_ratio']:.1f}**")
        
        if sd['peg_ratio']:
            emoji = "✨" if sd['peg_ratio'] < 1 else "⚠️" if sd['peg_ratio'] > 2 else "✨"
            parts.append(f"PEG: **{sd['peg_ratio']:.2f}** {emoji}")
        
        if sd['price_to_book']:
            parts.append(f"P/B: **{sd['price_to_book']:.2f}**")
        
        if not parts:
            return None
        
        return {"name": "📊 Valuation", "value": " | ".join(parts), "inline": True}
    
    def _build_profitability_compact(self, sd: Dict) -> Optional[Dict]:
        """Compact profitability metrics"""
        parts = []
        
        if sd['profit_margin'] is not None:
            emoji = "🟢" if sd['profit_margin'] > 0.15 else "🟡" if sd['profit_margin'] > 0 else "🔴"
            parts.append(f"Margin: **{sd['profit_margin']*100:.1f}%** {emoji}")
        
        if sd['roe'] is not None:
            emoji = "🟢" if sd['roe'] > 0.15 else "🟡" if sd['roe'] > 0 else "🔴"
            parts.append(f"ROE: **{sd['roe']*100:.1f}%** {emoji}")
        
        if not parts:
            return None
        
        return {"name": "💰 Profitability", "value": "\n".join(parts), "inline": True}
    
    def _build_health_compact(self, sd: Dict) -> Optional[Dict]:
        """Compact financial health metrics"""
        parts = []
        
        if sd['debt_to_equity'] is not None:
            emoji = "🟢" if sd['debt_to_equity'] < 1 else "🟡" if sd['debt_to_equity'] < 2 else "🔴"
            parts.append(f"D/E: **{sd['debt_to_equity']:.2f}** {emoji}")
        
        if sd['current_ratio'] is not None:
            emoji = "🟢" if sd['current_ratio'] > 1.5 else "🟡" if sd['current_ratio'] > 1 else "🔴"
            parts.append(f"CR: **{sd['current_ratio']:.2f}** {emoji}")
        
        if not parts:
            return None
        
        return {"name": "💡 Health", "value": "\n".join(parts), "inline": True}
    
    def _build_performance_timeline(self, mtf: Dict) -> Optional[Dict]:
        """Build compact performance timeline with sparkline"""
        if not mtf:
            return None

        # Filter and sort periods
        period_order = ['1M', '3M', '6M', '1Y']
        available = [(p, mtf[p]) for p in period_order if p in mtf and mtf[p] is not None]

        if not available:
            return None

        # Build horizontal bar
        parts = []
        values = []
        for period, value in available:
            emoji = "\U0001f7e2" if value > 0 else "\U0001f534"
            parts.append(f"**{period}:** {emoji} {value:+.1f}%")
            values.append(value)

        line = " \u27a1 ".join(parts)

        # Add sparkline if we have enough data points
        spark = self._build_sparkline(values)
        if spark:
            line += f"\n`{spark}`"

        return {
            "name": "\U0001f4c5 Performance Timeline",
            "value": line,
            "inline": False
        }
    
    def _build_backtest_compact(self, backtest: Dict, current_price: float) -> Optional[Dict]:
        """Ultra compact backtest summary - single line"""
        if not backtest:
            return None
        
        sharpe_emoji = "🟢" if backtest['sharpe_ratio'] > 1 else "🟡" if backtest['sharpe_ratio'] > 0 else "🔴"
        vs_spy = "📈" if backtest['excess_return'] > 0 else "📉"
        
        value = (f"**3Y:** {backtest['total_return']:+.1f}% ➡ "
                f"**vs SPY:** {vs_spy} {backtest['excess_return']:+.1f}% ➡ "
                f"**Sharpe:** {sharpe_emoji} {backtest['sharpe_ratio']:.2f}")
        
        return {
            "name": "📈 3-Year Backtest",
            "value": value,
            "inline": False
        }
    
    def _build_risk_compact(self, risk: Dict) -> Dict:
        """Compact risk assessment"""
        # Take top 2 risk factors to save space
        factors = risk['risk_factors'][:2]
        value = risk['risk_level'] + "\n" + " • ".join(factors)
        
        return {"name": "⚠️ Risk Profile", "value": value[:400], "inline": False}
    
    def _build_technical_compact(self, tech: Dict) -> Optional[Dict]:
        """Compact technical analysis - horizontal"""
        if not tech.get('details'):
            return None

        signal = tech['signal']
        emoji = "🟢" if signal == "BULLISH" else "🔴" if signal == "BEARISH" else "🟡"

        # Get key indicators only (first 2)
        indicators = []
        for detail in tech['details'][:2]:
            if 'RSI' in detail or 'MA' in detail or 'MACD' in detail:
                indicators.append(detail.split('**')[1] if '**' in detail else detail[:20])

        value = f"**Signal: {emoji} {signal}**\n" + " \u2022 ".join(indicators[:2])

        return {"name": "\U0001f4ca Technicals", "value": value, "inline": False}

    def _build_signal_summary_compact(self, signal_summary: Dict, indicators: Dict, fib_data=None) -> Optional[Dict]:
        """Compact unified signal summary with confidence score"""
        if not signal_summary:
            return None

        signal = signal_summary.get('signal', 'HOLD')
        confidence = signal_summary.get('confidence', 0)
        reasons = signal_summary.get('reasons', [])

        if signal == 'BUY':
            emoji = '\U0001f7e2'
        elif signal == 'SELL':
            emoji = '\U0001f534'
        else:
            emoji = '\U0001f7e1'

        header = f"{emoji} **SIGNAL: {signal}** ({confidence}% confidence)"

        parts = []
        # Top reasons (max 3)
        if reasons:
            parts.append(" \u2022 ".join(reasons[:3]))

        # ADX trend strength
        adx = indicators.get('adx')
        if adx is not None:
            if adx >= 25:
                parts.append(f"ADX: **{adx:.0f}** (Trending)")
            else:
                parts.append(f"ADX: **{adx:.0f}** (Ranging)")

        # Ichimoku summary
        senkou_a = indicators.get('ichimoku_senkou_a')
        senkou_b = indicators.get('ichimoku_senkou_b')
        if senkou_a is not None and senkou_b is not None:
            cloud_top = max(senkou_a, senkou_b)
            cloud_bottom = min(senkou_a, senkou_b)
            parts.append(f"Cloud: ${cloud_bottom:.0f}-${cloud_top:.0f}")

        # VWAP
        vwap = indicators.get('vwap')
        if vwap is not None:
            parts.append(f"VWAP: ${vwap:.2f}")

        # Fibonacci nearest level
        if fib_data and fib_data.get('nearest_level'):
            lvl = fib_data['nearest_level']
            lvl_price = fib_data.get('nearest_level_price', 0)
            dist = fib_data.get('distance_pct', 0)
            if dist < 3:
                parts.append(f"Fib {lvl}% (${lvl_price:.0f})")

        value = header
        if parts:
            value += "\n" + " | ".join(parts[:4])

        return {"name": "\U0001f3af Signal Summary", "value": value[:1024], "inline": False}

    def _build_ml_prediction_compact(self, ml_data: Dict) -> Optional[Dict]:
        """Compact ML prediction field with disclaimer"""
        if not ml_data:
            return None

        emoji = ml_data.get('emoji', '\U0001f7e1')
        direction = ml_data.get('direction', 'FLAT')
        confidence = ml_data.get('confidence', 0)
        days = ml_data.get('days', 5)
        features = ml_data.get('features', '')

        header = f"{emoji} **{direction}** ({confidence}% conf, {days}-day)"
        parts = []
        if features:
            parts.append(features)

        probs = ml_data.get('probabilities', {})
        if probs:
            prob_parts = [f"{k}: {v}%" for k, v in probs.items()]
            parts.append(" | ".join(prob_parts))

        value = header
        if parts:
            value += "\n" + " | ".join(parts[:2])
        value += "\n*Experimental - not financial advice*"

        return {"name": "\U0001f916 ML Prediction", "value": value[:1024], "inline": False}

    def _build_options_compact(self, options_flow: Dict) -> Optional[Dict]:
        """Compact options flow summary"""
        if not options_flow:
            return None

        parts = []
        emoji = options_flow.get('emoji', '\U0001f7e1')
        flow = options_flow.get('flow', 'NEUTRAL')

        pc_ratio = options_flow.get('pc_ratio')
        if pc_ratio is not None:
            parts.append(f"P/C: **{pc_ratio:.2f}**")

        max_pain = options_flow.get('max_pain')
        if max_pain:
            parts.append(f"Max Pain: **${max_pain:.0f}**")

        # Show top unusual strike
        unusual = options_flow.get('unusual_strikes', [])
        if unusual:
            top = unusual[0]
            strike_type = 'C' if top['type'] == 'CALL' else 'P'
            parts.append(f"Unusual: ${top['strike']:.0f}{strike_type} {top['ratio']:.1f}x OI")

        if not parts:
            return None

        expiry = options_flow.get('expiry', '')
        header = f"{emoji} **{flow.replace('_', ' ')}**"
        if expiry:
            header += f" (exp {expiry})"
        value = header + "\n" + " | ".join(parts)

        return {"name": "\U0001f4c8 Options Flow", "value": value, "inline": False}

    def _build_insider_compact(self, insider_data: Dict) -> Optional[Dict]:
        """Compact insider/institutional ownership summary"""
        if not insider_data:
            return None

        parts = []

        buys = insider_data.get('buys', 0)
        sells = insider_data.get('sells', 0)
        lookback = insider_data.get('lookback_days', 90)

        if buys > 0 or sells > 0:
            net = buys - sells
            if net > 0:
                emoji = '\U0001f7e2'
            elif net < 0:
                emoji = '\U0001f534'
            else:
                emoji = '\U0001f7e1'
            parts.append(f"{emoji} Insiders: **{buys} buy{'s' if buys != 1 else ''}** / **{sells} sell{'s' if sells != 1 else ''}** ({lookback}d)")

        inst_pct = insider_data.get('institutional_pct')
        insider_pct = insider_data.get('insider_pct')

        ownership_parts = []
        if inst_pct is not None:
            ownership_parts.append(f"Inst: **{inst_pct:.1f}%**")
        if insider_pct is not None:
            ownership_parts.append(f"Insider: **{insider_pct:.1f}%**")
        if ownership_parts:
            parts.append(" | ".join(ownership_parts))

        if not parts:
            return None

        return {"name": "\U0001f575 Insider Activity", "value": "\n".join(parts), "inline": False}

    def _build_congress_compact(self, congress_data: Dict) -> Optional[Dict]:
        """Compact Congress trading activity summary"""
        if not congress_data or not congress_data.get('trades'):
            return None

        buys = congress_data.get('buys', 0)
        sells = congress_data.get('sells', 0)
        total = congress_data.get('total', 0)

        parts = []

        if buys > 0:
            parts.append(f"\U0001f7e2 **{buys} purchase{'s' if buys != 1 else ''}**")
        if sells > 0:
            parts.append(f"\U0001f534 **{sells} sale{'s' if sells != 1 else ''}**")
        if not parts:
            parts.append(f"{total} trade{'s' if total != 1 else ''}")

        summary = " / ".join(parts) + f" ({CONGRESS_LOOKBACK_DAYS}d)"

        # Show up to 2 individual trades
        details = []
        for t in congress_data['trades'][:2]:
            name = t.get('politician_name', 'Unknown')
            # Shorten name if too long
            if len(name) > 25:
                name = name[:23] + '..'
            txn = t.get('transaction_type', '')
            amount = t.get('amount_range', '')
            date_str = t.get('transaction_date', '')
            # Format date as Mon DD
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                date_str = dt.strftime('%b %d')
            except (ValueError, TypeError):
                pass
            chamber = t.get('chamber', '')
            chamber_tag = f" ({chamber})" if chamber else ""
            emoji = '\U0001f7e2' if 'PURCHASE' in txn else '\U0001f534'
            line = f"{emoji} {name}{chamber_tag} {txn} {amount} ({date_str})"
            details.append(line)

        value = summary
        if details:
            value += "\n" + "\n".join(details)

        return {"name": "\U0001f3db Congress Trades", "value": value[:1024], "inline": False}

    def _build_track_record_compact(self, stats: Dict) -> Dict:
        """Compact track record - single line"""
        win_emoji = "🟢" if stats['win_rate'] >= 50 else "🔴"
        
        value = (f"**{stats['wins']}W-{stats['losses']}L** ({win_emoji} {stats['win_rate']:.0f}%) ➡ "
                f"**Avg:** {stats['avg_change']:+.1f}% ➡ "
                f"**Best:** +{stats['best_gain']:.1f}%")
        
        return {
            "name": "🏯 Reddit DD Track Record",
            "value": value,
            "inline": False
        }
    
    def _build_quick_links(self, sd: Dict) -> Dict:
        """Compact quick links - single row"""
        ticker = sd['ticker']
        
        links = (f"[📊 Yahoo]({sd['yahoo_link']}) • "
                f"[📈 TradingView]({sd['tradingview_link']}) • "
                f"[📉 Finviz]({sd['finviz_link']})")
        
        return {
            "name": "🔗 Quick Links",
            "value": links,
            "inline": False
        }
    
    def _format_volume(self, volume: int) -> str:
        """Format volume for readability"""
        if volume >= 1_000_000_000:
            return f"{volume/1_000_000_000:.2f}B"
        elif volume >= 1_000_000:
            return f"{volume/1_000_000:.2f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.2f}K"
        else:
            return f"{volume:,}"
    
    def _get_time_ago(self, dt: datetime) -> str:
        """Get human-readable time ago string"""
        now = datetime.now()
        diff = now - dt
        
        if diff.total_seconds() < 60:
            return "Just now"
        elif diff.total_seconds() < 3600:
            mins = int(diff.total_seconds() / 60)
            return f"{mins} min{'s' if mins != 1 else ''} ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            return dt.strftime('%b %d, %Y')

    def _build_sentiment_banner(self, sentiment_text: str, confidence: float) -> Optional[Dict]:
        """Build a big, eye-catching sentiment banner for the bottom of the embed"""
        if sentiment_text == 'BULLISH':
            emoji_row = "🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢"
            label = "BULLISH"
            if confidence >= 0.8:
                emoji_row = "🟢🟢🟢🟢🟢🚀🚀🚀🟢🟢🟢🟢🟢"
                label = "STRONGLY BULLISH"
        elif sentiment_text == 'BEARISH':
            emoji_row = "🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴"
            label = "BEARISH"
            if confidence >= 0.8:
                emoji_row = "🔴🔴🔴🔴🔴💀💀💀🔴🔴🔴🔴🔴"
                label = "STRONGLY BEARISH"
        else:
            emoji_row = "🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡"
            label = "NEUTRAL"
            if confidence < 0.3:
                emoji_row = "🟡🟡🟡🟡⚪⚪⚪🟡🟡🟡🟡"
                label = "NEUTRAL / LOW CONVICTION"

        value = f"{emoji_row}\n**{label}** — {confidence:.0%} CONFIDENCE\n{emoji_row}"

        return {
            "name": f"{'━' * 20} SENTIMENT {'━' * 20}",
            "value": value,
            "inline": False
        }
