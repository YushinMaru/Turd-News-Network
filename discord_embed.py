"""
NEW Enhanced Discord embed builder - REORGANIZED LAYOUT
1. Company Info (name, description, what they produce)
2. Sentiment Analysis
3. Reddit Post Info
4. All Market Data (price, technicals, ml, options, insider, congress)
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import *
from analysis import AnalysisEngine
from discord_sender import DiscordSender


class DiscordEmbedBuilder:
    """Builds beautiful Discord embeds with organized layout"""
    
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
        if len(str(field['name'])) > 256:
            field['name'] = str(field['name'])[:253] + '...'
        if len(value_str) > 1024:
            field['value'] = value_str[:1021] + '...'
        return True
    
    def send_discord_embed(self, post_data: Dict, stock_data_list: List[Dict]) -> bool:
        """Send formatted embed to Discord"""
        try:
            MAX_STOCKS_PER_EMBED = 2
            if len(stock_data_list) > MAX_STOCKS_PER_EMBED:
                print(f"   [WARNING]  Limiting to {MAX_STOCKS_PER_EMBED} stocks")
                stock_data_list = stock_data_list[:MAX_STOCKS_PER_EMBED]

            quality_score = post_data.get('quality_score', 0)
            
            # Collect chart paths
            chart_paths = []
            chart_filename = None
            for sd in stock_data_list:
                cp = sd.get('chart_path')
                if cp and os.path.exists(cp):
                    chart_paths.append(cp)
                    if chart_filename is None:
                        chart_filename = os.path.basename(cp)

            # Build the embed with new organized structure
            main_embed = self._build_organized_embed(post_data, stock_data_list, quality_score)

            if chart_filename:
                main_embed['image'] = {'url': f'attachment://{chart_filename}'}

            embeds = [main_embed]

            if chart_paths:
                return self.sender.send_embeds_with_files(embeds, post_data['title'], chart_paths)
            else:
                return self.sender.send_embeds(embeds, post_data['title'])
                
        except Exception as e:
            print(f"Error sending to Discord: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _build_organized_embed(self, post_data: Dict, stock_data_list: List[Dict], quality_score: float) -> Dict:
        """Build embed with organized layout:
        1. Company Info (name, description, business)
        2. Sentiment Analysis  
        3. Reddit Post Details
        4. All Market Data
        """
        
        # Quality badge
        if quality_score >= PREMIUM_DD_SCORE:
            quality_emoji, quality_text = "💎", "PREMIUM DD"
        elif quality_score >= QUALITY_DD_SCORE:
            quality_emoji, quality_text = "⭐", "QUALITY DD"
        else:
            quality_emoji, quality_text = "📊", "Standard DD"
        
        color = self._determine_embed_color(post_data, stock_data_list, quality_score)
        
        # Get sentiment data
        sentiment = post_data.get('sentiment', {})
        sentiment_text = sentiment.get('sentiment', 'NEUTRAL')
        sentiment_confidence = sentiment.get('confidence', 0)
        
        fields = []
        
        # Process each stock
        for i, stock_data in enumerate(stock_data_list):
            if not stock_data:
                continue
            
            if i > 0:
                fields.append({
                    "name": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    "value": "\u200b",
                    "inline": False
                })
            
            # ========== SECTION 1: COMPANY INFO + PRICE ==========
            fields.extend(self._build_company_info_section(stock_data))
            
            # ========== SECTION 2: SENTIMENT + ML + SIGNAL ==========
            fields.extend(self._build_sentiment_section(sentiment_text, sentiment_confidence, post_data, stock_data))
            
            # ========== SECTION 3: MARKET DATA ==========
            fields.extend(self._build_market_data_section(stock_data))
            
            # ========== SECTION 4: REDDIT POST INFO (BOTTOM) ==========
            fields.extend(self._build_reddit_section(post_data, quality_score))
        
        # Filter valid fields
        fields = [f for f in fields if self._validate_field(f)]
        
        embed = {
            "title": f"{quality_emoji} {quality_text}: {post_data['title'][:150]}",
            "url": post_data['url'],
            "color": color,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"💎 Turd News Network v5.0 | {len(stock_data_list)} stock(s) analyzed"}
        }
        
        # Add company logo
        if stock_data_list:
            thumb_url = self._get_logo_thumbnail(stock_data_list[0])
            if thumb_url:
                embed['thumbnail'] = {'url': thumb_url}
        
        return embed
    
    def _build_company_info_section(self, sd: Dict) -> List[Dict]:
        """Build Section 1: Company Info + Price/Volume"""
        fields = []
        ticker = sd.get('ticker', '')
        name = sd.get('name', '')
        description = sd.get('description', '')
        sector = sd.get('sector', '')
        industry = sd.get('industry', '')
        
        # Header with company name
        header_value = f"**{name}** (${ticker})"
        if sector and industry:
            header_value += f"\n{sector} • {industry}"
        
        # Add key metrics
        employees = sd.get('employees')
        if employees:
            header_value += f"\n👥 {employees:,} employees"
        
        website = sd.get('website', '')
        if website:
            header_value += f"\n🌐 [Website]({website})"
        
        fields.append({
            "name": "🏢 COMPANY INFO",
            "value": header_value,
            "inline": False
        })
        
        # Description/Business summary
        if description:
            # Truncate if too long
            desc = description[:500] + "..." if len(description) > 500 else description
            fields.append({
                "name": "📄 Business Description",
                "value": desc,
                "inline": False
            })
        
        # ===== PRICE & VOLUME (moved here from market data) =====
        price = sd.get('price', 0)
        change_pct = sd.get('change_pct', 0)
        volume = sd.get('volume', 0)
        avg_volume = sd.get('avg_volume', 0)
        market_cap = sd.get('market_cap', 0)
        
        change_emoji = "📈" if change_pct >= 0 else "📉"
        change_color = "🟢" if change_pct >= 0 else "🔴"
        
        price_value = f"💰 **${price:,.2f}** {change_color} {change_emoji} **{change_pct:+.2f}%**"
        
        if market_cap:
            price_value += f"\n🏢 Market Cap: {self._format_number(market_cap)}"
        
        # 52-week range
        w52_high = sd.get('52w_high')
        w52_low = sd.get('52w_low')
        if w52_high and w52_low:
            pct_from_high = ((price - w52_high) / w52_high) * 100
            pct_from_low = ((price - w52_low) / w52_low) * 100
            price_value += f"\n📊 52W Range: ${w52_low:,.2f} - ${w52_high:,.2f}"
            price_value += f"\n   {pct_from_low:+.1f}% from low | {pct_from_high:.1f}% from high"
        
        if volume and avg_volume:
            vol_ratio = volume / avg_volume
            fire = ' 🔥' if vol_ratio > 1.5 else ''
            price_value += f"\n📦 Volume: {self._format_number(volume)} ({vol_ratio:.1f}x avg){fire}"
        
        # Beta
        beta = sd.get('beta')
        if beta:
            price_value += f"\n📉 Beta: {beta:.2f}"
        
        # Short Interest
        short_int = sd.get('short_interest')
        if short_int:
            price_value += f"\n🎯 Short Interest: {short_int*100:.1f}%"
        
        fields.append({
            "name": "💵 PRICE & VOLUME",
            "value": price_value,
            "inline": False
        })
        
        return fields
    
    def _build_sentiment_section(self, sentiment_text: str, confidence: float, post_data: Dict, stock_data: Dict) -> List[Dict]:
        """Build Section 2: Sentiment Analysis with ML and Signal"""
        fields = []
        
        if sentiment_text == 'BULLISH':
            emoji = "🟢"
        elif sentiment_text == 'BEARISH':
            emoji = "🔴"
        else:
            emoji = "🟡"
        
        # Centered sentiment with emojis framing
        full_line = emoji * 12
        centered_text = f"**{sentiment_text}** — {confidence:.0%} confidence"
        sentiment_value = f"{full_line}\n{centered_text}\n{full_line}"
        
        # Add ML Prediction if available
        ml_prediction = stock_data.get('ml_prediction', {})
        if ml_prediction:
            direction = ml_prediction.get('direction', 'NEUTRAL')
            ml_conf = ml_prediction.get('confidence', 0)
            ml_emoji = "🟢" if direction == 'UP' else "🔴" if direction == 'DOWN' else "🟡"
            sentiment_value += f"\n\n🤖 **ML Prediction**: {ml_emoji} **{direction}** ({ml_conf}% confidence)"
        
        # Add Signal if available
        signal_summary = stock_data.get('signal_summary', {})
        if signal_summary:
            signal = signal_summary.get('signal', 'HOLD')
            sig_conf = signal_summary.get('confidence', 0)
            sig_emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "🟡"
            sentiment_value += f"\n📊 **Technical Signal**: {sig_emoji} **{signal}** ({sig_conf}% confidence)"
        
        # Add post quality context
        quality_score = post_data.get('quality_score', 0)
        upvotes = post_data.get('score', 0)
        comments = post_data.get('num_comments', 0)
        
        sentiment_value += f"\n\n📋 Post Quality: **{quality_score:.0f}/100**"
        sentiment_value += f"\n⬆️ {upvotes:,} upvotes • 💬 {comments:,} comments"
        
        fields.append({
            "name": "💭 SENTIMENT & SIGNALS",
            "value": sentiment_value,
            "inline": False
        })
        
        return fields
    
    def _build_reddit_section(self, post_data: Dict, quality_score: float) -> List[Dict]:
        """Build Section 3: Reddit Post Information"""
        fields = []
        
        subreddit = post_data.get('subreddit', '')
        author = post_data.get('author', 'Unknown')
        flair = post_data.get('flair', '')
        upvote_ratio = post_data.get('upvote_ratio', 0)
        post_length = post_data.get('post_length', 0)
        
        reddit_value = f"📰 r/{subreddit}\n👤 u/{author}"
        
        if flair:
            reddit_value += f"\n🏷️ {flair}"
        
        reddit_value += f"\n📈 {upvote_ratio*100:.0f}% upvote ratio"
        reddit_value += f"\n📝 {post_length:,} characters"
        
        fields.append({
            "name": "📱 REDDIT POST DETAILS",
            "value": reddit_value,
            "inline": False
        })
        
        return fields
    
    def _build_market_data_section(self, sd: Dict) -> List[Dict]:
        """Build Section 4: All Market Data - Financials, Technicals, ML, Options, Insider, Congress, News"""
        fields = []
        ticker = sd.get('ticker', '')
        
        # Get all available data
        technical_indicators = sd.get('technical_indicators', {})
        signal_summary = sd.get('signal_summary', {})
        ml_prediction = sd.get('ml_prediction', {})
        options_flow = sd.get('options_flow', {})
        insider_data = sd.get('insider_data', {})
        congress_data = sd.get('congress_data', {})
        backtest = sd.get('backtest', {})
        stats = self.db.get_stock_stats(ticker)
        risk_assessment = self.analysis.get_risk_assessment(sd)
        
        # ===== FINANCIAL METRICS (3 columns) =====
        fin_parts = []
        
        # Valuation
        pe = sd.get('pe_ratio')
        peg = sd.get('peg_ratio')
        pb = sd.get('price_to_book')
        if pe:
            fin_parts.append(f"P/E: {pe:.1f}")
        if peg:
            fin_parts.append(f"PEG: {peg:.2f}")
        if pb:
            fin_parts.append(f"P/B: {pb:.2f}")
        
        if fin_parts:
            fields.append({
                "name": "📊 Valuation",
                "value": " | ".join(fin_parts),
                "inline": True
            })
        
        # Profitability
        prof_parts = []
        margin = sd.get('profit_margin')
        roe = sd.get('roe')
        if margin is not None:
            prof_parts.append(f"Margin: {margin*100:.1f}%")
        if roe is not None:
            prof_parts.append(f"ROE: {roe*100:.1f}%")
        
        if prof_parts:
            fields.append({
                "name": "💰 Profitability",
                "value": " | ".join(prof_parts),
                "inline": True
            })
        
        # Health
        health_parts = []
        de = sd.get('debt_to_equity')
        cr = sd.get('current_ratio')
        if de is not None:
            health_parts.append(f"D/E: {de:.2f}")
        if cr is not None:
            health_parts.append(f"CR: {cr:.2f}")
        
        if health_parts:
            fields.append({
                "name": "💡 Health",
                "value": " | ".join(health_parts),
                "inline": True
            })
        
        # ===== TECHNICAL ANALYSIS =====
        if technical_indicators:
            rsi = technical_indicators.get('rsi')
            macd = technical_indicators.get('macd')
            sma_20 = technical_indicators.get('sma_20')
            sma_50 = technical_indicators.get('sma_50')
            adx = technical_indicators.get('adx')
            
            tech_parts = []
            if rsi:
                tech_parts.append(f"RSI: {rsi:.0f}")
            if macd:
                tech_parts.append(f"MACD: {macd:+.2f}")
            if adx:
                tech_parts.append(f"ADX: {adx:.0f}")
            
            if tech_parts:
                tech_value = " | ".join(tech_parts)
                
                # Add signal summary if available
                if signal_summary:
                    signal = signal_summary.get('signal', 'HOLD')
                    conf = signal_summary.get('confidence', 0)
                    reasons = signal_summary.get('reasons', [])
                    
                    sig_emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "🟡"
                    tech_value += f"\n\n{sig_emoji} **Signal: {signal}** ({conf}% confidence)"
                    if reasons:
                        tech_value += f"\n• " + "\n• ".join(reasons[:3])
                
                fields.append({
                    "name": "📈 TECHNICAL ANALYSIS",
                    "value": tech_value,
                    "inline": False
                })
        
        # ===== ML PREDICTION =====
        if ml_prediction:
            direction = ml_prediction.get('direction', 'NEUTRAL')
            ml_conf = ml_prediction.get('confidence', 0)
            features = ml_prediction.get('features', '')
            
            ml_emoji = "🟢" if direction == 'UP' else "🔴" if direction == 'DOWN' else "🟡"
            
            ml_value = f"{ml_emoji} **{direction}** ({ml_conf}% confidence)"
            if features:
                ml_value += f"\nFeatures: {features}"
            ml_value += "\n*⚠️ Experimental - not financial advice*"
            
            fields.append({
                "name": "🤖 ML PREDICTION",
                "value": ml_value,
                "inline": False
            })
        
        # ===== OPTIONS FLOW =====
        if options_flow:
            flow = options_flow.get('flow', 'NEUTRAL')
            pc_ratio = options_flow.get('pc_ratio')
            max_pain = options_flow.get('max_pain')
            unusual = options_flow.get('unusual_strikes', [])
            expiry = options_flow.get('expiry', '')
            
            flow_emoji = "🟢" if 'BULLISH' in flow else "🔴" if 'BEARISH' in flow else "🟡"
            
            options_value = f"{flow_emoji} **{flow.replace('_', ' ')}**"
            if expiry:
                options_value += f" (Exp: {expiry})"
            
            opts_parts = []
            if pc_ratio is not None:
                opts_parts.append(f"P/C Ratio: {pc_ratio:.2f}")
            if max_pain:
                opts_parts.append(f"Max Pain: ${max_pain:.0f}")
            
            if opts_parts:
                options_value += "\n" + " | ".join(opts_parts)
            
            if unusual:
                top = unusual[0]
                strike_type = 'Call' if top['type'] == 'CALL' else 'Put'
                options_value += f"\n🔥 Unusual: ${top['strike']:.0f} {strike_type} ({top['ratio']:.1f}x OI)"
            
            fields.append({
                "name": "📊 OPTIONS FLOW",
                "value": options_value,
                "inline": False
            })
        
        # ===== INSIDER ACTIVITY =====
        if insider_data:
            buys = insider_data.get('buys', 0)
            sells = insider_data.get('sells', 0)
            inst_pct = insider_data.get('institutional_pct')
            insider_pct = insider_data.get('insider_pct')
            
            if buys > 0 or sells > 0 or inst_pct is not None:
                net = buys - sells
                insider_emoji = "🟢" if net > 0 else "🔴" if net < 0 else "🟡"
                
                insider_value = f"{insider_emoji} **Insider Trading**\n"
                insider_value += f"Buys: {buys} | Sells: {sells} (90d)"
                
                if inst_pct is not None:
                    insider_value += f"\nInstitutional: {inst_pct:.1f}%"
                if insider_pct is not None:
                    insider_value += f" | Insider: {insider_pct:.1f}%"
                
                fields.append({
                    "name": "👔 INSIDER ACTIVITY",
                    "value": insider_value,
                    "inline": False
                })
        
        # ===== CONGRESS TRADES =====
        if congress_data:
            buys = congress_data.get('buys', 0)
            sells = congress_data.get('sells', 0)
            trades = congress_data.get('trades', [])
            
            if buys > 0 or sells > 0:
                congress_value = ""
                if buys > 0:
                    congress_value += f"🟢 **{buys} Purchase{'s' if buys != 1 else ''}**\n"
                if sells > 0:
                    congress_value += f"🔴 **{sells} Sale{'s' if sells != 1 else ''}**\n"
                
                # Show recent trades
                for t in trades[:2]:
                    name = t.get('politician_name', 'Unknown')[:20]
                    txn = t.get('transaction_type', '')
                    amount = t.get('amount_range', '')
                    date = t.get('transaction_date', '')
                    emoji = "🟢" if 'PURCHASE' in txn else "🔴"
                    congress_value += f"\n{emoji} {name}: {txn} {amount} ({date})"
                
                fields.append({
                    "name": "🏛️ CONGRESS TRADES (90d)",
                    "value": congress_value,
                    "inline": False
                })
        
        # ===== NEWS ARTICLES =====
        news = sd.get('recent_news', [])
        if news:
            news_lines = []
            for article in news[:3]:
                title = article.get('title', '')[:80]
                source = article.get('source', 'News')
                date = article.get('date', '')
                url = article.get('url', '')
                if url:
                    news_lines.append(f"• [{title}]({url})\n  *{source} - {date}*")
                else:
                    news_lines.append(f"• {title}\n  *{source} - {date}*")
            
            if news_lines:
                fields.append({
                    "name": "📰 RECENT NEWS",
                    "value": "\n".join(news_lines)[:1024],
                    "inline": False
                })
        
        # ===== SEC & PATENTS LINKS =====
        sec_link = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=&dateb=&owner=include&count=40&search_text="
        patents_link = f"https://patents.google.com/?assignee={ticker}&type=PATENT"
        
        links_value = f"[📋 SEC Filings]({sec_link}) • [🔬 Patents]({patents_link})"
        
        # Add standard research links
        links_value += f"\n[📊 Yahoo]({sd.get('yahoo_link', '#')}) • [📈 TradingView]({sd.get('tradingview_link', '#')}) • [📉 Finviz]({sd.get('finviz_link', '#')})"
        
        fields.append({
            "name": "🔗 RESEARCH LINKS",
            "value": links_value,
            "inline": False
        })
        
        # ===== BACKTEST & RISK =====
        extras = []
        
        if backtest:
            total_ret = backtest.get('total_return', 0)
            sharpe = backtest.get('sharpe_ratio', 0)
            extras.append(f"📈 3Y Return: {total_ret:+.1f}% | Sharpe: {sharpe:.2f}")
        
        if risk_assessment:
            risk_level = risk_assessment.get('risk_level', '')
            risk_factors = risk_assessment.get('risk_factors', [])
            if risk_factors:
                extras.append(f"⚠️ Risk: {risk_factors[0]}")
        
        if stats:
            win_rate = stats.get('win_rate', 0)
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            extras.append(f"📊 Track Record: {wins}W-{losses}L ({win_rate:.0f}% win rate)")
        
        if extras:
            fields.append({
                "name": "📋 ADDITIONAL DATA",
                "value": "\n".join(extras),
                "inline": False
            })
        
        return fields
    
    def _determine_embed_color(self, post_data: Dict, stock_data_list: List[Dict], quality_score: float) -> int:
        """Determine embed color"""
        if quality_score >= PREMIUM_DD_SCORE:
            return COLOR_PREMIUM
        
        if stock_data_list:
            sd = stock_data_list[0]
            signal = sd.get('signal_summary', {})
            sig_type = signal.get('signal', '')
            if sig_type == 'BUY':
                return COLOR_BULLISH
            elif sig_type == 'SELL':
                return COLOR_BEARISH
        
        sentiment = post_data.get('sentiment', {})
        sent_text = sentiment.get('sentiment', 'NEUTRAL')
        if sent_text == 'BULLISH':
            return COLOR_BULLISH
        elif sent_text == 'BEARISH':
            return COLOR_BEARISH
        
        return COLOR_STANDARD
    
    @staticmethod
    def _get_logo_thumbnail(stock_data: Dict) -> Optional[str]:
        """Get company logo URL"""
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
        except:
            pass
        return None
    
    @staticmethod
    def _format_number(num):
        """Format large numbers"""
        if num is None:
            return 'N/A'
        if num >= 1e12:
            return f"${num/1e12:.2f}T"
        elif num >= 1e9:
            return f"${num/1e9:.2f}B"
        elif num >= 1e6:
            return f"${num/1e6:.2f}M"
        elif num >= 1e3:
            return f"${num/1e3:.2f}K"
        return f"${num:,.2f}"
