"""
Ticker Report Builder - Generates 3 COMPREHENSIVE Discord embeds with ALL stock data.
Each embed is packed with real live data from APIs.
"""

import sys
import io
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import yfinance as yf

from config import (
    ENABLE_BACKTEST, ENABLE_MOMENTUM_SCORE, ENABLE_PRICE_ALERTS_IN_EMBED,
    ENABLE_ENHANCED_TECHNICALS, ENABLE_ML_PREDICTION, ENABLE_OPTIONS_FLOW,
    ENABLE_INSIDER_DATA, ENABLE_CONGRESS_TRACKER, BACKTEST_YEARS,
    CONGRESS_LOOKBACK_DAYS,
    COLOR_REPORT_OVERVIEW, COLOR_REPORT_SIGNALS, COLOR_REPORT_INSIDER,
)
from database import DatabaseManager
from stock_data import StockDataFetcher
from analysis import AnalysisEngine
from backtesting import EnhancedBacktester
from congress_tracker import CongressTracker
from ml_predictor import PricePredictor


class TickerReportBuilder:
    """Builds 3 COMPREHENSIVE embeds with ALL stock data - no missing info!"""

    def __init__(self):
        self.db = DatabaseManager()
        self.stock_fetcher = StockDataFetcher(self.db)
        self.analysis = AnalysisEngine()
        self.backtester = EnhancedBacktester()
        self.congress_tracker = CongressTracker(self.db)
        self.ml_predictor = PricePredictor()

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def _fmt_num(val, prefix='$', suffix='', decimals=2):
        """Format a number with magnitude suffix."""
        if val is None:
            return 'N/A'
        try:
            val = float(val)
        except (TypeError, ValueError):
            return 'N/A'
        if val != val:  # NaN
            return 'N/A'
        neg = val < 0
        av = abs(val)
        if av >= 1e12:
            s = f"{av / 1e12:.{decimals}f}T"
        elif av >= 1e9:
            s = f"{av / 1e9:.{decimals}f}B"
        elif av >= 1e6:
            s = f"{av / 1e6:.{decimals}f}M"
        elif av >= 1e3:
            s = f"{av / 1e3:.{decimals}f}K"
        else:
            s = f"{av:,.{decimals}f}"
        sign = '-' if neg else ''
        return f"{sign}{prefix}{s}{suffix}"

    @staticmethod
    def _fmt_pct(val, decimals=2):
        """Format a ratio (0.15) as percentage (15.00%)."""
        if val is None:
            return 'N/A'
        try:
            val = float(val)
        except (TypeError, ValueError):
            return 'N/A'
        if val != val:
            return 'N/A'
        return f"{val * 100:.{decimals}f}%"

    @staticmethod
    def _safe_df_val(df, row_names, col_idx=0):
        """Safely extract a value from a DataFrame given possible row name variants."""
        if df is None or df.empty:
            return None
        for name in row_names:
            if name in df.index:
                try:
                    val = df.loc[name].iloc[col_idx]
                    if val is not None and val == val:  # not NaN
                        return float(val)
                except (IndexError, TypeError, ValueError):
                    continue
        return None

    # -- extra data fetching ---------------------------------------------------

    def _fetch_extra_data(self, symbol: str, valid_ticker: str) -> Dict:
        """Fetch financial statements, recommendations, institutional holders, earnings dates."""
        extra = {}
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            stock = yf.Ticker(valid_ticker)
            for attr in [
                'financials', 'quarterly_financials',
                'balance_sheet', 'quarterly_balance_sheet',
                'cashflow', 'quarterly_cashflow',
                'recommendations', 'institutional_holders', 'earnings_dates',
            ]:
                try:
                    extra[attr] = getattr(stock, attr)
                except Exception:
                    extra[attr] = None
        finally:
            sys.stderr = old_stderr
        return extra

    # -- main build method -----------------------------------------------------

    def build_report_sync(self, symbol: str) -> Tuple[Optional[List[Dict]], Optional[str], Optional[List[str]]]:
        """
        Build 3 COMPREHENSIVE embeds with ALL the data.
        Returns (list_of_embeds, chart_path, chart_paths) or (None, None, None) on failure.
        """
        symbol = symbol.upper().strip()

        # 1. Fetch base stock data (includes chart, options, insider, technicals)
        stock_data = self.stock_fetcher.get_stock_data(symbol)
        if not stock_data:
            return None, None, None

        ticker = stock_data['ticker']

        # 2. Run analysis that main.py normally does
        if ENABLE_BACKTEST:
            backtest = self.backtester.backtest_ticker_history(ticker, years=BACKTEST_YEARS)
            if backtest:
                stock_data['backtest'] = backtest

        mtf_performance = self.backtester.get_multi_timeframe_performance(ticker)
        stock_data['mtf_performance'] = mtf_performance

        if ENABLE_MOMENTUM_SCORE and mtf_performance:
            stock_data['momentum'] = self.analysis.calculate_momentum_score(stock_data)

        if ENABLE_PRICE_ALERTS_IN_EMBED:
            stock_data['price_alerts'] = self.analysis.generate_price_alerts(
                stock_data, stock_data.get('backtest')
            )

        if stock_data.get('backtest'):
            rr = self.analysis.calculate_risk_reward_ratio(stock_data, stock_data['backtest'])
            if rr:
                stock_data['risk_reward'] = rr

        if ENABLE_ENHANCED_TECHNICALS and stock_data.get('technical_indicators'):
            signal_summary = self.analysis.generate_signal_summary(stock_data)
            stock_data['signal_summary'] = signal_summary
            fib = self.analysis.calculate_fibonacci_levels(stock_data)
            if fib:
                stock_data['fibonacci'] = fib

        if ENABLE_ML_PREDICTION:
            try:
                ml_result = self.ml_predictor.predict(ticker)
                if ml_result:
                    stock_data['ml_prediction'] = PricePredictor.format_for_embed(ml_result)
            except Exception as e:
                print(f"[ML] Prediction error for {ticker}: {e}")

        if ENABLE_OPTIONS_FLOW and stock_data.get('options_data'):
            stock_data['options_flow'] = self.analysis.analyze_options_flow(
                stock_data['options_data'], stock_data['price']
            )

        if ENABLE_CONGRESS_TRACKER:
            congress_trades = self.congress_tracker.check_congress_trades(ticker)
            if congress_trades:
                stock_data['congress_data'] = CongressTracker.format_for_embed(congress_trades)

        # 3. Fetch extra financial data
        valid_ticker = self.stock_fetcher._valid_ticker_cache.get(symbol, symbol)
        extra = self._fetch_extra_data(symbol, valid_ticker)

        # 5. Build 5 COMPREHENSIVE embeds - wrapped in try/except to NEVER fail
        try:
            embeds = [
                self._embed_company_info(stock_data, extra),      # Embed 1: Company Overview FIRST
                self._embed_sentiment_ml(stock_data, extra),      # Embed 2: Sentiment + ML + Prediction
                self._embed_insider_congress(stock_data, extra),  # Embed 3: Insider + Congress
                self._embed_charts(stock_data),                   # Embed 4: Charts & Visuals
                self._embed_actions(stock_data),                 # Embed 5: Actions & Commands
            ]
        except Exception as e:
            print(f"[TickerReport] Error building embeds: {e}")
            # Return basic embed as fallback
            embeds = [{
                "title": f"📊 {ticker} - {stock_data.get('name', ticker)}",
                "color": COLOR_REPORT_OVERVIEW,
                "fields": [{"name": "Data", "value": f"Price: ${stock_data.get('price', 'N/A')}", "inline": True}],
                "footer": {"text": "Turd News Network v6.0"},
                "timestamp": datetime.utcnow().isoformat(),
            }]

        chart_path = stock_data.get('chart_path')
        chart_paths = stock_data.get('chart_paths', [])
        
        # Debug logging
        print(f"[TickerReport] chart_path: {chart_path}")
        print(f"[TickerReport] chart_paths: {chart_paths}")
        
        # Return both - tuple of (embeds, single_chart_path, all_chart_paths)
        return embeds, chart_path, chart_paths

    # -- EMBED 1: SENTIMENT + ML + PREDICTION ---------------------------------

    def _embed_sentiment_ml(self, sd: Dict, extra: Dict) -> Dict:
        """Embed 1: COMPLETE Sentiment, ML, Signals, and Prediction data"""
        ticker = sd['ticker']
        price = sd.get('price', 0)
        change = sd.get('change_pct', 0)
        fields = []

        # ===== SENTIMENT & SIGNALS =====
        signal_summary = sd.get('signal_summary')
        if signal_summary and isinstance(signal_summary, dict):
            signal = signal_summary.get('signal', 'HOLD')
            if signal and isinstance(signal, str) and hasattr(signal, 'upper'):
                signal = signal.upper()
            else:
                signal = 'HOLD'
            confidence = signal_summary.get('confidence', 0)
            bullish_count = signal_summary.get('bullish_count', 0)
            bearish_count = signal_summary.get('bearish_count', 0)
            
            if signal == 'BUY':
                sig_emoji = '🟢'
            elif signal == 'SELL':
                sig_emoji = '🔴'
            else:
                sig_emoji = '🟡'
            
            fields.append({
                "name": f"{sig_emoji} UNIFIED SIGNAL",
                "value": f"**{signal}** ({confidence}% confidence)\nBullish: {bullish_count} | Bearish: {bearish_count}",
                "inline": False
            })

        # ===== MOMENTUM =====
        momentum = sd.get('momentum')
        if momentum:
            mom_emoji = momentum.get('emoji', '')
            mom_class = momentum.get('classification', 'NEUTRAL')
            mom_score = momentum.get('score', 50)
            trend = momentum.get('trend', '')
            mom_str = f"{mom_emoji} **{mom_class}** ({mom_score:.0f}/100)"
            if trend and trend != 'UNKNOWN':
                mom_str += f" | Trend: {trend}"
            fields.append({"name": "📊 MOMENTUM", "value": mom_str, "inline": True})

        # ===== RISK ASSESSMENT =====
        risk = self.analysis.get_risk_assessment(sd)
        if risk:
            risk_str = f"**{risk['risk_level']}** (Score: {risk['risk_score']})"
            factors = risk.get('risk_factors', [])
            if factors:
                risk_str += "\n" + " | ".join(factors[:3])
            fields.append({"name": "⚠️ RISK LEVEL", "value": risk_str[:1024], "inline": True})

        # ===== RISK/REWARD =====
        rr = sd.get('risk_reward')
        if rr:
            rr_str = f"**{rr['ratio']:.2f}:1** ({rr['rating']})\nUpside: {rr['upside_pct']:+.1f}% | Downside: -{rr['downside_pct']:.1f}%"
            fields.append({"name": "📈 RISK/REWARD", "value": rr_str, "inline": True})

        # ===== ML PREDICTION =====
        ml = sd.get('ml_prediction')
        if ml:
            ml_emoji = ml.get('emoji', '🟡')
            direction = ml.get('direction', 'FLAT')
            conf = ml.get('confidence', 0)
            days = ml.get('days', 5)
            probs = ml.get('probabilities', {})
            
            ml_str = f"{ml_emoji} **{direction}** ({conf}% conf, {days}-day)"
            if probs:
                prob_parts = [f"{k}: {v}%" for k, v in probs.items()]
                ml_str += "\n" + " | ".join(prob_parts)
            ml_str += "\n*Experimental - not financial advice*"
            fields.append({"name": "🤖 ML PREDICTION", "value": ml_str[:1024], "inline": False})

        # ===== BACKTEST PERFORMANCE =====
        backtest = sd.get('backtest')
        if backtest:
            sharpe_emoji = '🟢' if backtest['sharpe_ratio'] > 1 else '🟡' if backtest['sharpe_ratio'] > 0 else '🔴'
            vs_spy = '🟢' if backtest['excess_return'] > 0 else '🔴'
            bt_str = (
                f"3Y Return: **{backtest['total_return']:+.1f}%**\n"
                f"vs SPY: {vs_spy} {backtest['excess_return']:+.1f}%\n"
                f"Sharpe: {sharpe_emoji} {backtest['sharpe_ratio']:.2f} | Max DD: {backtest['max_drawdown']:.1f}%\n"
                f"Win Rate: {backtest['win_rate']:.0f}% | Profit Factor: {backtest['profit_factor']:.2f}"
            )
            fields.append({"name": "📊 BACKTEST (3Y)", "value": bt_str, "inline": False})

        # ===== PERFORMANCE TIMELINE =====
        mtf = sd.get('mtf_performance', {})
        if mtf:
            period_order = ['1M', '3M', '6M', '1Y', '2Y', '3Y']
            parts = []
            for p in period_order:
                v = mtf.get(p)
                if v is not None:
                    emoji = '🟢' if v > 0 else '🔴'
                    parts.append(f"**{p}:** {emoji} {v:+.1f}%")
            if parts:
                fields.append({"name": "📈 PERFORMANCE TIMELINE", "value": " | ".join(parts), "inline": False})

        # ===== PRICE ALERTS =====
        alerts = sd.get('price_alerts', [])
        if alerts:
            alert_str = "\n".join(alerts[:5])
            fields.append({"name": "🔔 PRICE ALERTS", "value": alert_str, "inline": False})

        return {
            "title": f"🤖 {ticker} - Sentiment & ML Prediction",
            "color": COLOR_REPORT_SIGNALS,
            "fields": fields,
            "footer": {"text": "Turd News Network v6.0 | Sentiment & ML"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    # -- EMBED 2: INSIDER + CONGRESS -------------------------------------------

    def _embed_insider_congress(self, sd: Dict, extra: Dict) -> Dict:
        """Embed 2: COMPLETE Insider and Congressional Trading data"""
        ticker = sd['ticker']
        fields = []

        # ===== INSIDER TRANSACTIONS =====
        insider = sd.get('insider_data')
        if insider:
            buys = insider.get('buys', 0)
            sells = insider.get('sells', 0)
            lookback = insider.get('lookback_days', 90)
            net = buys - sells

            if net > 0:
                net_emoji = '🟢'
            elif net < 0:
                net_emoji = '🔴'
            else:
                net_emoji = '🟡'

            ins_str = f"{net_emoji} **{buys} Buys** / **{sells} Sells** ({lookback}d)"

            # Show recent transactions
            txns = insider.get('transactions', [])
            if txns:
                ins_str += "\n"
                for t in txns[:8]:
                    tname = t.get('name', 'Unknown')[:25]
                    txn_type = t.get('type', '')
                    shares = t.get('shares', 0)
                    value = t.get('value', 0)
                    date = t.get('date', '')
                    type_emoji = '🟢' if txn_type == 'BUY' else '🔴' if txn_type == 'SELL' else '🟡'
                    val_str = self._fmt_num(value) if value else ''
                    ins_str += f"\n{type_emoji} {tname} - {txn_type} {shares:,} {val_str} ({date})"

            fields.append({"name": "👀 INSIDER TRANSACTIONS", "value": ins_str[:2000], "inline": False})

            # ===== OWNERSHIP =====
            inst_pct = insider.get('institutional_pct')
            insider_pct = insider.get('insider_pct')
            own_parts = []
            if inst_pct is not None:
                own_parts.append(f"Institutional: **{inst_pct:.1f}%**")
            if insider_pct is not None:
                own_parts.append(f"Insider: **{insider_pct:.1f}%**")
            if own_parts:
                fields.append({"name": "🏢 OWNERSHIP", "value": " | ".join(own_parts), "inline": True})

        # ===== CONGRESS TRADES =====
        congress = sd.get('congress_data')
        if congress and congress.get('trades'):
            c_buys = congress.get('buys', 0)
            c_sells = congress.get('sells', 0)
            total = congress.get('total', 0)

            parts = []
            if c_buys > 0:
                parts.append(f"🟢 **{c_buys} Buys**")
            if c_sells > 0:
                parts.append(f"🔴 **{c_sells} Sells**")
            if not parts:
                parts.append(f"{total} Trades")

            cong_str = " / ".join(parts) + f" ({CONGRESS_LOOKBACK_DAYS}d)\n"

            for t in congress['trades'][:8]:
                cname = t.get('politician_name', 'Unknown')
                if len(cname) > 22:
                    cname = cname[:20] + '..'
                txn = t.get('transaction_type', '')
                amount = t.get('amount_range', '')
                date_str = t.get('transaction_date', '')
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    date_str = dt.strftime('%b %d')
                except (ValueError, TypeError):
                    pass
                chamber = t.get('chamber', '')
                chamber_tag = f" ({chamber})" if chamber else ""
                emoji = '🟢' if 'PURCHASE' in txn else '🔴'
                cong_str += f"\n{emoji} {cname}{chamber_tag} {txn} {amount} ({date_str})"

            fields.append({"name": "🏛️ CONGRESS TRADING", "value": cong_str[:2000], "inline": False})

        # ===== INSTITUTIONAL HOLDERS =====
        inst_holders = extra.get('institutional_holders')
        if inst_holders is not None and not inst_holders.empty:
            try:
                top_holders = inst_holders.head(5)
                holder_lines = []
                for _, row in top_holders.iterrows():
                    name = str(row.get('Holder', ''))[:25]
                    shares = row.get('Shares', 0)
                    pct = row.get('pctTotal', 0)
                    if shares:
                        holder_lines.append(f"• {name}: {shares:,} ({pct:.1f}%)")
                if holder_lines:
                    fields.append({"name": "🏦 TOP INSTITUTIONAL HOLDERS", "value": "\n".join(holder_lines), "inline": False})
            except:
                pass

        if not fields:
            fields.append({"name": "No insider or Congress data", "value": "No transactions found in lookback period", "inline": False})

        return {
            "title": f"👀 {ticker} - Insider & Congress",
            "color": COLOR_REPORT_INSIDER,
            "fields": fields,
            "footer": {"text": "Turd News Network v6.0 | Insider & Congress"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    # -- EMBED 3: COMPANY INFO - ALL DATA -------------------------------------

    def _embed_company_info(self, sd: Dict, extra: Dict) -> Dict:
        """Embed 3: COMPLETE Company Information - Overview, Financials, Technicals"""
        ticker = sd['ticker']
        name = sd.get('name', ticker)
        price = sd.get('price', 0)
        fields = []

        # ===== COMPANY OVERVIEW =====
        sector = sd.get('sector', 'N/A')
        industry = sd.get('industry', 'N/A')
        employees = sd.get('employees')
        emp_str = f"{employees:,}" if employees else 'N/A'
        
        overview = f"**{name}**\n"
        overview += f"Sector: {sector} | Industry: {industry}\n"
        overview += f"Employees: {emp_str}"
        fields.append({"name": "🏢 COMPANY OVERVIEW", "value": overview, "inline": False})
        
        # ===== COMPANY DESCRIPTION =====
        description = sd.get('description', '')
        if description:
            # Truncate to fit in embed
            if len(description) > 500:
                description = description[:497] + "..."
            fields.append({"name": "📋 ABOUT", "value": description, "inline": False})

        # ===== PRICE & MARKET DATA =====
        change = sd.get('change_pct', 0)
        change_emoji = '🟢' if change >= 0 else '🔴'
        
        price_data = f"**${price:,.2f}** {change_emoji} {change:+.2f}%\n"
        
        # 52W range
        w52h = sd.get('52w_high')
        w52l = sd.get('52w_low')
        if w52h and w52l:
            price_data += f"52W Range: ${w52l:.2f} - ${w52h:.2f}\n"
            pct_from_low = ((price - w52l) / w52l) * 100
            pct_from_high = ((price - w52h) / w52h) * 100
            price_data += f"From Low: {pct_from_low:+.1f}% | From High: {pct_from_high:.1f}%\n"
        
        # Volume
        vol = sd.get('volume')
        avg_vol = sd.get('avg_volume')
        if vol:
            vol_str = self._fmt_num(vol, prefix='')
            if avg_vol and avg_vol > 0:
                ratio = vol / avg_vol
                fire = ' 🔥' if ratio > 1.5 else ''
                vol_str += f" ({ratio:.1f}x avg){fire}"
            price_data += f"Volume: {vol_str}"
        
        fields.append({"name": "💰 PRICE & VOLUME", "value": price_data, "inline": False})

        # ===== MARKET CAP & VALUATION =====
        mc = sd.get('market_cap')
        mc_str = self._fmt_num(mc) if mc else 'N/A'
        
        pe = sd.get('pe_ratio')
        fpe = sd.get('forward_pe')
        peg = sd.get('peg_ratio')
        pb = sd.get('price_to_book')
        
        # Safe formatting for each value
        try:
            pe_str = f"{float(pe):.2f}" if pe is not None else 'N/A'
        except (TypeError, ValueError):
            pe_str = 'N/A'
        
        try:
            fpe_str = f"{float(fpe):.2f}" if fpe is not None else 'N/A'
        except (TypeError, ValueError):
            fpe_str = 'N/A'
        
        try:
            peg_str = f"{float(peg):.2f}" if peg is not None else 'N/A'
        except (TypeError, ValueError):
            peg_str = 'N/A'
        
        try:
            pb_str = f"{float(pb):.2f}" if pb is not None else 'N/A'
        except (TypeError, ValueError):
            pb_str = 'N/A'
        
        val_data = f"Market Cap: **{mc_str}**\n"
        val_data += f"P/E: {pe_str} | Fwd P/E: {fpe_str}\n"
        val_data += f"PEG: {peg_str} | P/B: {pb_str}"
        
        fields.append({"name": "📊 VALUATION", "value": val_data, "inline": True})

        # ===== EPS & TARGETS =====
        eps = sd.get('eps')
        feps = sd.get('forward_eps')
        target = sd.get('price_target')
        
        try:
            eps_str = f"${float(eps):.2f}" if eps is not None else 'N/A'
        except (TypeError, ValueError):
            eps_str = 'N/A'
        
        try:
            if feps is not None:
                eps_str += f" (Fwd: ${float(feps):.2f})"
        except (TypeError, ValueError):
            pass
        
        try:
            target_str = f"${float(target):.2f}" if target else 'N/A'
            if target and price:
                upside = ((float(target) - float(price)) / float(price)) * 100
                target_str += f" ({upside:+.1f}%)"
        except (TypeError, ValueError):
            target_str = 'N/A'
        
        beta = sd.get('beta')
        si = sd.get('short_interest')
        
        try:
            beta_str = f"{float(beta):.2f}" if beta is not None else 'N/A'
        except (TypeError, ValueError):
            beta_str = 'N/A'
        
        eps_data = f"EPS: {eps_str}\nTarget: {target_str}\n"
        eps_data += f"Beta: {beta_str} | Short: {self._fmt_pct(si) if si else 'N/A'}"
        
        fields.append({"name": "📈 EPS & TARGETS", "value": eps_data, "inline": True})

        # ===== MARGINS =====
        pm = sd.get('profit_margin')
        om = sd.get('operating_margin')
        gm = sd.get('gross_margin')
        
        margin_data = f"Gross: {self._fmt_pct(gm) if gm else 'N/A'}\n"
        margin_data += f"Operating: {self._fmt_pct(om) if om else 'N/A'}\n"
        margin_data += f"Profit: {self._fmt_pct(pm) if pm else 'N/A'}"
        
        fields.append({"name": "💵 MARGINS", "value": margin_data, "inline": True})

        # ===== FINANCIAL HEALTH =====
        roe = sd.get('roe')
        roa = sd.get('roa')
        de = sd.get('debt_to_equity')
        cr = sd.get('current_ratio')
        
        try:
            de_str = f"{float(de):.2f}" if de is not None else 'N/A'
        except (TypeError, ValueError):
            de_str = 'N/A'
        
        try:
            cr_str = f"{float(cr):.2f}" if cr is not None else 'N/A'
        except (TypeError, ValueError):
            cr_str = 'N/A'
        
        health_data = f"ROE: {self._fmt_pct(roe) if roe else 'N/A'}\n"
        health_data += f"ROA: {self._fmt_pct(roa) if roa else 'N/A'}\n"
        health_data += f"D/E: {de_str} | Current: {cr_str}"
        
        fields.append({"name": "🏥 FINANCIAL HEALTH", "value": health_data, "inline": True})

        # ===== TECHNICALS =====
        indicators = sd.get('technical_indicators', {})
        
        # RSI
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi < 30:
                rsi_label = "OVERSOLD"
                rsi_emoji = '🟢'
            elif rsi > 70:
                rsi_label = "OVERBOUGHT"
                rsi_emoji = '🔴'
            else:
                rsi_label = "NEUTRAL"
                rsi_emoji = '🟡'
            fields.append({"name": f"{rsi_emoji} RSI (14)", "value": f"**{rsi:.1f}** - {rsi_label}", "inline": True})

        # MACD
        macd = indicators.get('macd')
        if macd is not None:
            macd_emoji = '🟢' if macd > 0 else '🔴'
            fields.append({"name": f"{macd_emoji} MACD", "value": f"**{macd:.4f}**", "inline": True})

        # ADX
        adx = indicators.get('adx')
        if adx is not None:
            trend_str = "Trending" if adx >= 25 else "Ranging"
            adx_emoji = '🟢' if adx >= 25 else '🟡'
            fields.append({"name": f"{adx_emoji} ADX", "value": f"**{adx:.1f}** ({trend_str})", "inline": True})

        # Moving Averages
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        
        ma_parts = []
        if sma_20:
            ma_parts.append(f"20: ${sma_20:.2f}")
        if sma_50:
            ma_parts.append(f"50: ${sma_50:.2f}")
        if sma_200:
            ma_parts.append(f"200: ${sma_200:.2f}")
        
        if ma_parts:
            fields.append({"name": "📉 MOVING AVERAGES", "value": " | ".join(ma_parts), "inline": True})

        # ===== ANALYST RATINGS =====
        rating = sd.get('analyst_rating')
        recs = extra.get('recommendations')
        if recs is not None and not recs.empty:
            try:
                latest = recs.iloc[0]
                sb = int(latest.get('strongBuy', 0) or 0)
                b = int(latest.get('buy', 0) or 0)
                h = int(latest.get('hold', 0) or 0)
                s = int(latest.get('sell', 0) or 0)
                ss = int(latest.get('strongSell', 0) or 0)
                total = sb + b + h + s + ss
                
                if total > 0:
                    buy_pct = (sb + b) / total * 100
                    if buy_pct >= 70:
                        consensus = '🟢 Strong Buy'
                    elif buy_pct >= 50:
                        consensus = '🟢 Buy'
                    elif (sb + b) >= (s + ss):
                        consensus = '🟡 Hold'
                    else:
                        consensus = '🔴 Sell'
                    
                    rec_str = f"**{consensus}** ({buy_pct:.0f}% bullish)\n"
                    rec_str += f"Strong Buy: {sb} | Buy: {b} | Hold: {h}\n"
                    rec_str += f"Sell: {s} | Strong Sell: {ss}"
                    fields.append({"name": "🎯 ANALYST RATINGS", "value": rec_str, "inline": False})
            except:
                pass

        # ===== OPTIONS DATA =====
        options_data = sd.get('options_data')
        if options_data:
            pc = options_data.get('pc_ratio')
            if pc is not None:
                if pc < 0.5:
                    pc_label = "Heavy Calls 🟢"
                elif pc > 1.5:
                    pc_label = "Heavy Puts 🔴"
                else:
                    pc_label = "Balanced 🟡"
                fields.append({"name": "📊 PUT/CALL RATIO", "value": f"**{pc:.2f}** - {pc_label}", "inline": True})

        # ===== DIVIDEND & EARNINGS =====
        div = sd.get('dividend_yield')
        div_str = self._fmt_pct(div) if div else 'None'
        
        earnings = sd.get('earnings_date')
        if earnings:
            if isinstance(earnings, (list, tuple)):
                earnings = earnings[0] if earnings else None
            try:
                if hasattr(earnings, 'strftime'):
                    earnings_str = earnings.strftime('%b %d, %Y')
                else:
                    earnings_str = str(earnings)
            except:
                earnings_str = str(earnings) if earnings else 'N/A'
        else:
            earnings_str = 'N/A'
        
        fields.append({"name": "💵 DIVIDEND & EARNINGS", "value": f"Yield: {div_str}\nEarnings: {earnings_str}", "inline": True})

        # ===== QUICK LINKS =====
        links = []
        for label, key in [
            ('Yahoo', 'yahoo_link'), ('Finviz', 'finviz_link'), ('SEC', 'sec_filings'),
        ]:
            url = sd.get(key)
            if url:
                links.append(f"[{label}]({url})")
        if links:
            fields.append({"name": "🔗 RESEARCH LINKS", "value": " | ".join(links), "inline": False})

        return {
            "title": f"📊 {ticker} - {name} | Complete Company Info",
            "color": COLOR_REPORT_OVERVIEW,
            "fields": fields,
            "footer": {"text": "Turd News Network v6.0 | Company Intelligence"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    # -- EMBED 4: CHARTS & IMAGES ---------------------------------------------

    def _embed_charts(self, sd: Dict) -> Dict:
        """Embed 4: Charts and Visualizations"""
        ticker = sd['ticker']
        name = sd.get('name', ticker)
        price = sd.get('price', 0)
        fields = []
        
        # ===== CHART INFO =====
        chart_path = sd.get('chart_path')
        
        chart_info = "📈 **Charts Generated:**\n"
        
        if chart_path and os.path.exists(chart_path):
            chart_info += "• ✅ Candlestick + Moving Averages\n"
            chart_info += "• ✅ Bollinger Bands\n"
            chart_info += "• ✅ 52W High/Low Lines\n"
        else:
            chart_info += "• ⏳ Price Chart (generating...)\n"
        
        # Technical indicators
        indicators = sd.get('technical_indicators', {})
        if indicators:
            chart_info += "\n📊 **Technical Indicators:**\n"
            
            if indicators.get('rsi') is not None:
                rsi = indicators['rsi']
                rsi_status = "Oversold 🟢" if rsi < 30 else "Overbought 🔴" if rsi > 70 else "Neutral 🟡"
                chart_info += f"• RSI (14): {rsi:.1f} - {rsi_status}\n"
            
            if indicators.get('macd') is not None:
                macd = indicators['macd']
                macd_status = "Bullish 🟢" if macd > 0 else "Bearish 🔴"
                chart_info += f"• MACD: {macd:.4f} - {macd_status}\n"
        
        fields.append({"name": "📈 PRICE CHART", "value": chart_info, "inline": False})
        
        # ===== FIBONACCI LEVELS =====
        fib = sd.get('fibonacci')
        if fib:
            levels = fib.get('levels', {})
            if levels:
                fib_info = "🎯 **Fibonacci Retracement:**\n"
                for level, price_val in levels.items():
                    pct_from = ((price_val - price) / price) * 100
                    emoji = "🟢" if pct_from > 0 else "🔴"
                    fib_info += f"• {level}: ${price_val:.2f} {emoji} {pct_from:+.1f}%\n"
                
                nearest = fib.get('nearest_level', '')
                if nearest:
                    fib_info += f"\n📍 Nearest: **{nearest}** (${fib.get('nearest_level_price', 0):.2f})"
                
                fields.append({"name": "🎯 FIBONACCI", "value": fib_info, "inline": False})
        
        # ===== PERFORMANCE VS SPY =====
        backtest = sd.get('backtest')
        if backtest:
            perf_info = f"📊 **3-Year Performance:**\n"
            perf_info += f"• Stock: **{backtest.get('total_return', 0):+.1f}%**\n"
            perf_info += f"• vs SPY: {backtest.get('excess_return', 0):+.1f}%\n"
            perf_info += f"• Sharpe: {backtest.get('sharpe_ratio', 'N/A')}\n"
            perf_info += f"• Max DD: {backtest.get('max_drawdown', 'N/A')}%"
            
            fields.append({"name": "📈 PERFORMANCE VS SPY", "value": perf_info, "inline": False})
        
        # ===== OPTIONS FLOW =====
        options_data = sd.get('options_data')
        if options_data:
            pc = options_data.get('pc_ratio')
            if pc is not None:
                opt_info = "📊 **Options Flow:**\n"
                if pc < 0.5:
                    opt_info += "• 🟢 Heavy Calls (bullish)\n"
                elif pc > 1.5:
                    opt_info += "• 🔴 Heavy Puts (bearish)\n"
                else:
                    opt_info += "• 🟡 Balanced\n"
                
                opt_info += f"• P/C Ratio: **{pc:.2f}**"
                fields.append({"name": "📊 OPTIONS FLOW", "value": opt_info, "inline": False})
        
        # ===== CHART LINKS =====
        links_info = "🔗 **Chart Links:**\n"
        links_info += f"• [TradingView](https://www.tradingview.com/symbols/{ticker})\n"
        links_info += f"• [StockAnalysis](https://stockanalysis.com/stocks/{ticker}/charts)"
        
        fields.append({"name": "📈 CHART LINKS", "value": links_info, "inline": False})
        
        return {
            "title": f"📈 {ticker} - Charts & Visuals",
            "color": COLOR_REPORT_OVERVIEW,
            "fields": fields,
            "footer": {"text": "Turd News Network v6.0 | Charts"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    # -- EMBED 5: LIVE MARKET DATA ---------------------------------------------

    def _embed_actions(self, sd: Dict) -> Dict:
        """Embed 5: Comprehensive Live Market Data - All in one place"""
        ticker = sd['ticker']
        price = sd.get('price', 0)
        change = sd.get('change_pct', 0)
        w52h = sd.get('52w_high')
        w52l = sd.get('52w_low')
        fields = []
        
        # ===== ANALYST PRICE TARGETS =====
        target = sd.get('price_target')
        rating = sd.get('analyst_rating')
        
        if target and price:
            upside = ((float(target) - float(price)) / float(price)) * 100
            upside_emoji = '🟢' if upside > 0 else '🔴'
            
            target_str = f"🎯 **${float(target):.2f}** {upside_emoji} {upside:+.1f}%\n"
            
            if rating:
                rating_emoji = '🟢' if rating in ['buy', 'strongBuy'] else '🔴' if rating in ['sell', 'strongSell'] else '🟡'
                target_str += f"Consensus: {rating_emoji} {rating.title()}"
            
            fields.append({"name": "📊 PRICE TARGET", "value": target_str, "inline": True})
        
        # ===== 52W POSITION =====
        if w52h and w52l and price:
            pct_from_low = ((price - w52l) / w52l) * 100
            pct_from_high = ((price - w52h) / w52h) * 100
            
            # Visual progress bar
            total_range = w52h - w52l
            if total_range > 0:
                position = (price - w52l) / total_range
                bar_len = 10
                filled = int(position * bar_len)
                bar = '█' * filled + '░' * (bar_len - filled)
                pos_emoji = '🔥' if position > 0.8 else '🚀' if position > 0.5 else '📍'
            else:
                bar = '░' * 10
                pos_emoji = '📍'
            
            pos_str = f"{pos_emoji} **{position*100:.0f}%** of range\n"
            pos_str += f"{bar}\n"
            pos_str += f"Low: ${w52l:.2f} | High: ${w52h:.2f}"
            
            fields.append({"name": "📈 52W POSITION", "value": pos_str, "inline": True})
        
        # ===== VOLUME ANALYSIS =====
        vol = sd.get('volume')
        avg_vol = sd.get('avg_volume')
        
        if vol and avg_vol:
            vol_ratio = vol / avg_vol if avg_vol > 0 else 1
            vol_emoji = '🔥' if vol_ratio > 1.5 else '📊'
            vol_status = 'HIGH' if vol_ratio > 1.5 else 'NORMAL' if vol_ratio > 0.8 else 'LOW'
            
            vol_str = f"{vol_emoji} **{vol_ratio:.1f}x** avg volume\n"
            vol_str += f"Status: **{vol_status}**\n"
            vol_str += f"Today: {self._fmt_num(vol, prefix='')}\n"
            vol_str += f"Avg: {self._fmt_num(avg_vol, prefix='')}"
            
            fields.append({"name": "📊 VOLUME", "value": vol_str, "inline": True})
        
        # ===== EARNINGS & DIVIDENDS =====
        earnings = sd.get('earnings_date')
        div_yield = sd.get('dividend_yield')
        
        earnings_str = ""
        if earnings:
            if isinstance(earnings, (list, tuple)):
                earnings = earnings[0] if earnings else None
            
            if earnings:
                try:
                    if hasattr(earnings, 'date'):
                        days_until = (earnings.date() - datetime.now().date()).days
                    else:
                        # Try parsing string
                        earnings_dt = datetime.strptime(str(earnings)[:10], '%Y-%m-%d')
                        days_until = (earnings_dt.date() - datetime.now().date()).days
                    
                    if days_until > 0:
                        earnings_str = f"📅 **{days_until} days**\n"
                        earnings_str += f"Earnings: {str(earnings)[:10]}"
                    elif days_until == 0:
                        earnings_str = "📅 **TODAY**"
                    else:
                        earnings_str = f"📅 Past"
                except:
                    earnings_str = f"📅 {str(earnings)[:10]}"
            else:
                earnings_str = "📅 N/A"
        else:
            earnings_str = "📅 N/A"
        
        if div_yield:
            div_str = f"\n💵 **{self._fmt_pct(div_yield)}** yield"
        else:
            div_str = "\n💵 None"
        
        earnings_str += div_str
        fields.append({"name": "📅 EARNINGS & DIVIDENDS", "value": earnings_str, "inline": True})
        
        # ===== OPTIONS DATA =====
        options_data = sd.get('options_data')
        
        if options_data:
            pc_ratio = options_data.get('pc_ratio')
            max_pain = options_data.get('max_pain')
            total_call_vol = options_data.get('total_call_vol', 0)
            total_put_vol = options_data.get('total_put_vol', 0)
            
            if pc_ratio is not None:
                if pc_ratio < 0.5:
                    pc_emoji = '🟢'
                    pc_status = 'Bullish'
                elif pc_ratio > 1.5:
                    pc_emoji = '🔴'
                    pc_status = 'Bearish'
                else:
                    pc_emoji = '🟡'
                    pc_status = 'Neutral'
                
                opt_str = f"📊 P/C: **{pc_ratio:.2f}** {pc_emoji}\n"
                opt_str += f"Signal: **{pc_status}**\n"
                
                if max_pain:
                    opt_str += f"Max Pain: ${max_pain:.2f}\n"
                
                opt_str += f"Vol: {self._fmt_num(total_call_vol + total_put_vol, prefix='')}"
                
                fields.append({"name": "🎰 OPTIONS", "value": opt_str, "inline": True})
        
        # ===== TECHNICAL SIGNALS =====
        indicators = sd.get('technical_indicators', {})
        
        tech_signals = []
        
        # RSI
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi < 30:
                rsi_signal = '🟢 Oversold'
            elif rsi > 70:
                rsi_signal = '🔴 Overbought'
            else:
                rsi_signal = '🟡 Neutral'
            tech_signals.append(f"RSI: {rsi:.0f} {rsi_signal}")
        
        # MACD
        macd = indicators.get('macd')
        if macd is not None:
            macd_signal = '🟢 Bullish' if macd > 0 else '🔴 Bearish'
            tech_signals.append(f"MACD {macd_signal}")
        
        # Price vs MAs
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        
        if sma_20 and price:
            if price > sma_20:
                tech_signals.append(f"🟢 Price > SMA20")
            else:
                tech_signals.append(f"🔴 Price < SMA20")
        
        if sma_50 and price:
            if price > sma_50:
                tech_signals.append(f"🟢 Price > SMA50")
            else:
                tech_signals.append(f"🔴 Price < SMA50")
        
        # ADX
        adx = indicators.get('adx')
        if adx is not None:
            if adx >= 25:
                tech_signals.append(f"🟢 ADX: {adx:.0f} (Trending)")
            else:
                tech_signals.append(f"🟡 ADX: {adx:.0f} (Ranging)")
        
        if tech_signals:
            tech_str = "\n".join(tech_signals[:6])
            fields.append({"name": "📈 TECHNICALS", "value": tech_str, "inline": False})
        
        # ===== KEY LEVELS =====
        levels = []
        
        # Fibonacci levels from stock_data if available
        fib = sd.get('fibonacci')
        if fib and fib.get('levels'):
            fib_levels = fib.get('levels', {})
            if 'R1' in fib_levels:
                levels.append(f"🔴 R1: ${fib_levels['R1']:.2f}")
            if 'S1' in fib_levels:
                levels.append(f"🟢 S1: ${fib_levels['S1']:.2f}")
        
        # Add pivot if available
        if indicators.get('sma_20'):
            levels.append(f"📊 SMA20: ${indicators['sma_20']:.2f}")
        
        if levels:
            levels_str = "\n".join(levels[:4])
            fields.append({"name": "🎯 KEY LEVELS", "value": levels_str, "inline": True})
        
        return {
            "title": f"⚡ {ticker} - Live Market Data",
            "color": COLOR_REPORT_OVERVIEW,
            "fields": fields,
            "footer": {"text": "Turd News Network v6.0 | Live Data"},
            "timestamp": datetime.utcnow().isoformat(),
        }
