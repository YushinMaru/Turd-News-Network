"""
Ticker Report Builder - Generates 10 themed Discord embeds for comprehensive stock analysis.
Used by the interactive !ticker command in discord_bot.py.
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
    COLOR_REPORT_OVERVIEW, COLOR_REPORT_PRICE, COLOR_REPORT_VALUATION,
    COLOR_REPORT_INCOME, COLOR_REPORT_BALANCE, COLOR_REPORT_TECHNICAL,
    COLOR_REPORT_SIGNALS, COLOR_REPORT_OPTIONS, COLOR_REPORT_INSIDER,
    COLOR_REPORT_ANALYST,
)
from database import DatabaseManager
from stock_data import StockDataFetcher
from analysis import AnalysisEngine
from backtesting import EnhancedBacktester
from congress_tracker import CongressTracker
from ml_predictor import PricePredictor


class TickerReportBuilder:
    """Builds a comprehensive 10-embed stock report for the interactive !ticker command."""

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

    @staticmethod
    def _get_logo_url(stock_data: Dict) -> Optional[str]:
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

    @staticmethod
    def _build_sparkline(values: List[float]) -> str:
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

    def build_report_sync(self, symbol: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Build the full 10-embed report synchronously.
        Returns (list_of_embeds, chart_path) or (None, None) on failure.
        """
        symbol = symbol.upper().strip()

        # 1. Fetch base stock data (includes chart, options, insider, technicals)
        stock_data = self.stock_fetcher.get_stock_data(symbol)
        if not stock_data:
            return None, None

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
            ml_result = self.ml_predictor.predict(stock_data)
            if ml_result:
                stock_data['ml_prediction'] = PricePredictor.format_for_embed(ml_result)

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

        # 4. Build the 10 embeds
        embeds = [
            self._embed_overview(stock_data),
            self._embed_price_action(stock_data),
            self._embed_valuation(stock_data),
            self._embed_income(stock_data, extra),
            self._embed_balance_cashflow(stock_data, extra),
            self._embed_technical(stock_data),
            self._embed_signals_ml(stock_data),
            self._embed_options(stock_data),
            self._embed_insider(stock_data),
            self._embed_analyst_news(stock_data, extra),
        ]

        chart_path = stock_data.get('chart_path')
        return embeds, chart_path

    # -- embed builders (1-10) -------------------------------------------------

    def _embed_overview(self, sd: Dict) -> Dict:
        """Embed 1: Company Overview"""
        ticker = sd['ticker']
        name = sd.get('name', ticker)

        desc_parts = []
        biz = sd.get('description', '')
        if biz:
            desc_parts.append(biz)

        fields = []

        # Row 1: Sector | Industry | Employees
        sector = sd.get('sector', 'N/A')
        industry = sd.get('industry', 'N/A')
        employees = sd.get('employees')
        emp_str = f"{employees:,}" if employees else 'N/A'
        fields.append({"name": "Sector", "value": sector, "inline": True})
        fields.append({"name": "Industry", "value": industry, "inline": True})
        fields.append({"name": "Employees", "value": emp_str, "inline": True})

        # Row 2: Market Cap | Beta | Short Interest
        fields.append({"name": "Market Cap", "value": self._fmt_num(sd.get('market_cap')), "inline": True})
        beta = sd.get('beta')
        beta_str = f"{beta:.2f}" if beta is not None else 'N/A'
        fields.append({"name": "Beta", "value": beta_str, "inline": True})
        si = sd.get('short_interest')
        si_str = self._fmt_pct(si) if si is not None else 'N/A'
        fields.append({"name": "Short Interest", "value": si_str, "inline": True})

        # Row 3: Dividend | Earnings Date
        div = sd.get('dividend_yield')
        div_str = self._fmt_pct(div) if div is not None else 'None'
        fields.append({"name": "Dividend Yield", "value": div_str, "inline": True})

        earnings = sd.get('earnings_date')
        if earnings:
            if isinstance(earnings, (list, tuple)):
                earnings = earnings[0] if earnings else None
            try:
                if hasattr(earnings, 'strftime'):
                    earnings_str = earnings.strftime('%b %d, %Y')
                else:
                    earnings_str = str(earnings)
            except Exception:
                earnings_str = str(earnings)
        else:
            earnings_str = 'N/A'
        fields.append({"name": "Earnings Date", "value": earnings_str, "inline": True})

        # Quick links
        links = []
        for label, key in [
            ('Yahoo', 'yahoo_link'), ('TradingView', 'tradingview_link'),
            ('Finviz', 'finviz_link'), ('SEC', 'sec_filings'),
            ('StockAnalysis', 'stockanalysis_link'),
        ]:
            url = sd.get(key)
            if url:
                links.append(f"[{label}]({url})")
        if links:
            fields.append({"name": "Research Links", "value": " | ".join(links), "inline": False})

        embed = {
            "title": f"${ticker} \u2022 {name}",
            "description": "\n".join(desc_parts) if desc_parts else None,
            "color": COLOR_REPORT_OVERVIEW,
            "fields": fields,
            "footer": {"text": "1/10 Company Overview \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        logo = self._get_logo_url(sd)
        if logo:
            embed['thumbnail'] = {'url': logo}
        return embed

    def _embed_price_action(self, sd: Dict) -> Dict:
        """Embed 2: Price Action"""
        ticker = sd['ticker']
        price = sd['price']
        change = sd.get('change_pct', 0)
        change_emoji = '\U0001f7e2' if change >= 0 else '\U0001f534'

        fields = []

        # Price + change
        price_val = f"**${price:,.2f}** {change_emoji} {change:+.2f}%"
        fields.append({"name": "Current Price", "value": price_val, "inline": True})

        # 52W range
        w52h = sd.get('52w_high')
        w52l = sd.get('52w_low')
        if w52h and w52l:
            pct_from_high = ((price - w52h) / w52h) * 100
            pct_from_low = ((price - w52l) / w52l) * 100
            range_str = f"${w52l:,.2f} - ${w52h:,.2f}\n{pct_from_low:+.1f}% from low | {pct_from_high:.1f}% from high"
            fields.append({"name": "52-Week Range", "value": range_str, "inline": True})

        # Volume
        vol = sd.get('volume')
        avg_vol = sd.get('avg_volume')
        if vol:
            vol_str = self._fmt_num(vol, prefix='')
            if avg_vol and avg_vol > 0:
                ratio = vol / avg_vol
                fire = ' \U0001f525' if ratio > 1.5 else ''
                vol_str += f"\n{ratio:.1f}x avg{fire}"
            fields.append({"name": "Volume", "value": vol_str, "inline": True})

        # Performance timeline
        mtf = sd.get('mtf_performance', {})
        if mtf:
            period_order = ['1M', '3M', '6M', '1Y', '2Y', '3Y']
            parts = []
            values = []
            for p in period_order:
                v = mtf.get(p)
                if v is not None:
                    emoji = '\U0001f7e2' if v > 0 else '\U0001f534'
                    parts.append(f"**{p}:** {emoji} {v:+.1f}%")
                    values.append(v)
            if parts:
                line = " | ".join(parts)
                spark = self._build_sparkline(values)
                if spark:
                    line += f"\n`{spark}`"
                fields.append({"name": "Performance Timeline", "value": line, "inline": False})

        # Momentum
        momentum = sd.get('momentum')
        if momentum:
            mom_emoji = momentum.get('emoji', '')
            mom_class = momentum.get('classification', 'NEUTRAL')
            mom_score = momentum.get('score', 50)
            trend = momentum.get('trend', '')
            mom_str = f"{mom_emoji} **{mom_class}** ({mom_score:.0f}/100)"
            if trend and trend != 'UNKNOWN':
                mom_str += f" | Trend: {trend}"
            fields.append({"name": "Momentum", "value": mom_str, "inline": False})

        # Alerts
        alerts = sd.get('price_alerts', [])
        if alerts:
            alert_str = "\n".join(alerts[:5])
            fields.append({"name": "Alerts", "value": alert_str, "inline": False})

        embed = {
            "title": f"${ticker} \u2022 Price Action",
            "color": COLOR_REPORT_PRICE,
            "fields": fields,
            "footer": {"text": "2/10 Price Action \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Attach chart to this embed
        chart_path = sd.get('chart_path')
        if chart_path and os.path.exists(chart_path):
            filename = os.path.basename(chart_path)
            embed['image'] = {'url': f'attachment://{filename}'}

        return embed

    def _embed_valuation(self, sd: Dict) -> Dict:
        """Embed 3: Valuation Deep Dive"""
        ticker = sd['ticker']
        fields = []

        # Row 1: P/E | Forward P/E | PEG
        pe = sd.get('pe_ratio')
        fpe = sd.get('forward_pe')
        peg = sd.get('peg_ratio')
        pb = sd.get('price_to_book')

        pe_str = f"{pe:.2f}" if pe is not None else 'N/A'
        fpe_str = f"{fpe:.2f}" if fpe is not None else 'N/A'
        peg_str = f"{peg:.2f}" if peg is not None else 'N/A'
        pb_str = f"{pb:.2f}" if pb is not None else 'N/A'

        fields.append({"name": "P/E (TTM)", "value": pe_str, "inline": True})
        fields.append({"name": "Forward P/E", "value": fpe_str, "inline": True})
        fields.append({"name": "PEG Ratio", "value": peg_str, "inline": True})

        # Row 2: P/B | EPS | Analyst Target
        eps = sd.get('eps')
        feps = sd.get('forward_eps')
        target = sd.get('price_target')

        eps_str = f"${eps:.2f}" if eps is not None else 'N/A'
        if feps is not None:
            eps_str += f" (Fwd: ${feps:.2f})"

        target_str = f"${target:.2f}" if target is not None else 'N/A'
        if target and sd.get('price'):
            upside = ((target - sd['price']) / sd['price']) * 100
            target_str += f" ({upside:+.1f}%)"

        fields.append({"name": "P/B Ratio", "value": pb_str, "inline": True})
        fields.append({"name": "EPS", "value": eps_str, "inline": True})
        fields.append({"name": "Analyst Target", "value": target_str, "inline": True})

        # Row 3: Margins
        pm = sd.get('profit_margin')
        om = sd.get('operating_margin')
        pm_str = self._fmt_pct(pm) if pm is not None else 'N/A'
        om_str = self._fmt_pct(om) if om is not None else 'N/A'
        fields.append({"name": "Profit Margin", "value": pm_str, "inline": True})
        fields.append({"name": "Operating Margin", "value": om_str, "inline": True})

        # Row 4: ROE | ROA | D/E | Current Ratio
        roe = sd.get('roe')
        roa = sd.get('roa')
        de = sd.get('debt_to_equity')
        cr = sd.get('current_ratio')

        roe_str = self._fmt_pct(roe) if roe is not None else 'N/A'
        roa_str = self._fmt_pct(roa) if roa is not None else 'N/A'
        de_str = f"{de:.2f}" if de is not None else 'N/A'
        cr_str = f"{cr:.2f}" if cr is not None else 'N/A'

        fields.append({"name": "ROE", "value": roe_str, "inline": True})
        fields.append({"name": "ROA", "value": roa_str, "inline": True})
        fields.append({"name": "D/E Ratio", "value": de_str, "inline": True})
        fields.append({"name": "Current Ratio", "value": cr_str, "inline": True})

        # Valuation assessment
        val_text = self.analysis.get_valuation_assessment(sd)
        if val_text and val_text != "No clear valuation signal":
            fields.append({"name": "Valuation Assessment", "value": val_text[:1024], "inline": False})

        return {
            "title": f"${ticker} \u2022 Valuation Deep Dive",
            "color": COLOR_REPORT_VALUATION,
            "fields": fields,
            "footer": {"text": "3/10 Valuation \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_income(self, sd: Dict, extra: Dict) -> Dict:
        """Embed 4: Income Statement"""
        ticker = sd['ticker']
        fields = []

        fin = extra.get('financials')
        qfin = extra.get('quarterly_financials')

        # Row names to try for each metric
        revenue_names = ['Total Revenue', 'Revenue', 'Operating Revenue']
        gross_profit_names = ['Gross Profit']
        operating_income_names = ['Operating Income', 'EBIT', 'Operating Profit']
        net_income_names = ['Net Income', 'Net Income Common Stockholders',
                            'Net Income From Continuing Operations']
        ebitda_names = ['EBITDA', 'Normalized EBITDA']

        # Annual financials (up to 2 years)
        if fin is not None and not fin.empty:
            cols = min(2, len(fin.columns))
            for col_idx in range(cols):
                try:
                    date_label = fin.columns[col_idx].strftime('%Y') if hasattr(fin.columns[col_idx], 'strftime') else str(fin.columns[col_idx])[:4]
                except Exception:
                    date_label = f"Year {col_idx + 1}"

                rev = self._safe_df_val(fin, revenue_names, col_idx)
                gp = self._safe_df_val(fin, gross_profit_names, col_idx)
                oi = self._safe_df_val(fin, operating_income_names, col_idx)
                ni = self._safe_df_val(fin, net_income_names, col_idx)
                ebitda = self._safe_df_val(fin, ebitda_names, col_idx)

                lines = [
                    f"Revenue: **{self._fmt_num(rev)}**",
                    f"Gross Profit: **{self._fmt_num(gp)}**",
                    f"Operating Inc: **{self._fmt_num(oi)}**",
                    f"Net Income: **{self._fmt_num(ni)}**",
                    f"EBITDA: **{self._fmt_num(ebitda)}**",
                ]

                if rev and gp and rev > 0:
                    gm = gp / rev * 100
                    lines.append(f"Gross Margin: {gm:.1f}%")

                fields.append({"name": f"FY {date_label}", "value": "\n".join(lines), "inline": True})

        # Most recent quarter
        if qfin is not None and not qfin.empty:
            try:
                date_label = qfin.columns[0].strftime('%b %Y') if hasattr(qfin.columns[0], 'strftime') else str(qfin.columns[0])[:10]
            except Exception:
                date_label = "Latest Q"

            rev = self._safe_df_val(qfin, revenue_names, 0)
            gp = self._safe_df_val(qfin, gross_profit_names, 0)
            oi = self._safe_df_val(qfin, operating_income_names, 0)
            ni = self._safe_df_val(qfin, net_income_names, 0)
            ebitda = self._safe_df_val(qfin, ebitda_names, 0)

            lines = [
                f"Revenue: **{self._fmt_num(rev)}**",
                f"Gross Profit: **{self._fmt_num(gp)}**",
                f"Operating Inc: **{self._fmt_num(oi)}**",
                f"Net Income: **{self._fmt_num(ni)}**",
                f"EBITDA: **{self._fmt_num(ebitda)}**",
            ]
            fields.append({"name": f"Q {date_label}", "value": "\n".join(lines), "inline": True})

        if not fields:
            fields.append({"name": "Income Statement", "value": "Financial data not available for this ticker.", "inline": False})

        # Revenue growth
        rg = sd.get('revenue_growth')
        if rg is not None:
            fields.append({"name": "Revenue Growth (YoY)", "value": self._fmt_pct(rg), "inline": True})

        return {
            "title": f"${ticker} \u2022 Income Statement",
            "color": COLOR_REPORT_INCOME,
            "fields": fields,
            "footer": {"text": "4/10 Income Statement \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_balance_cashflow(self, sd: Dict, extra: Dict) -> Dict:
        """Embed 5: Balance Sheet & Cash Flow"""
        ticker = sd['ticker']
        fields = []

        bs = extra.get('balance_sheet')
        cf = extra.get('cashflow')

        # Balance sheet
        if bs is not None and not bs.empty:
            try:
                date_label = bs.columns[0].strftime('%b %Y') if hasattr(bs.columns[0], 'strftime') else str(bs.columns[0])[:10]
            except Exception:
                date_label = "Latest"

            total_assets = self._safe_df_val(bs, ['Total Assets'])
            total_liab = self._safe_df_val(bs, [
                'Total Liabilities Net Minority Interest', 'Total Liab', 'Total Liabilities'])
            total_equity = self._safe_df_val(bs, [
                'Stockholders Equity', 'Total Equity Gross Minority Interest',
                'Total Stockholder Equity', 'Common Stock Equity'])
            cash = self._safe_df_val(bs, [
                'Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments',
                'Cash Financial'])
            total_debt = self._safe_df_val(bs, [
                'Total Debt', 'Long Term Debt', 'Long Term Debt And Capital Lease Obligation'])

            lines = [
                f"Total Assets: **{self._fmt_num(total_assets)}**",
                f"Total Liabilities: **{self._fmt_num(total_liab)}**",
                f"Stockholder Equity: **{self._fmt_num(total_equity)}**",
                f"Cash & Equivalents: **{self._fmt_num(cash)}**",
                f"Total Debt: **{self._fmt_num(total_debt)}**",
            ]

            if total_assets and total_liab and total_assets > 0:
                leverage = total_liab / total_assets * 100
                lines.append(f"Leverage: {leverage:.1f}%")

            fields.append({"name": f"Balance Sheet ({date_label})", "value": "\n".join(lines), "inline": True})

        # Cash flow
        if cf is not None and not cf.empty:
            try:
                date_label = cf.columns[0].strftime('%Y') if hasattr(cf.columns[0], 'strftime') else str(cf.columns[0])[:4]
            except Exception:
                date_label = "Latest"

            op_cf = self._safe_df_val(cf, [
                'Operating Cash Flow', 'Total Cash From Operating Activities',
                'Cash Flow From Continuing Operating Activities'])
            capex = self._safe_df_val(cf, ['Capital Expenditure', 'Capital Expenditures'])
            free_cf = self._safe_df_val(cf, ['Free Cash Flow'])

            # Calculate FCF if not directly available
            if free_cf is None and op_cf is not None and capex is not None:
                free_cf = op_cf + capex  # capex is typically negative

            lines = [
                f"Operating CF: **{self._fmt_num(op_cf)}**",
                f"Capital Expenditure: **{self._fmt_num(capex)}**",
                f"Free Cash Flow: **{self._fmt_num(free_cf)}**",
            ]

            if free_cf is not None:
                fcf_emoji = '\U0001f7e2' if free_cf > 0 else '\U0001f534'
                lines.append(f"{fcf_emoji} FCF {'Positive' if free_cf > 0 else 'Negative'}")

            fields.append({"name": f"Cash Flow (FY {date_label})", "value": "\n".join(lines), "inline": True})

        if not fields:
            fields.append({"name": "Balance Sheet & Cash Flow", "value": "Financial data not available for this ticker.", "inline": False})

        return {
            "title": f"${ticker} \u2022 Balance Sheet & Cash Flow",
            "color": COLOR_REPORT_BALANCE,
            "fields": fields,
            "footer": {"text": "5/10 Balance Sheet & Cash Flow \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_technical(self, sd: Dict) -> Dict:
        """Embed 6: Technical Analysis"""
        ticker = sd['ticker']
        indicators = sd.get('technical_indicators', {})
        price = sd.get('price', 0)
        fields = []

        # RSI
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi < 30:
                rsi_label = "Oversold"
                rsi_emoji = '\U0001f7e2'
            elif rsi > 70:
                rsi_label = "Overbought"
                rsi_emoji = '\U0001f534'
            else:
                rsi_label = "Neutral"
                rsi_emoji = '\U0001f7e1'
            fields.append({"name": "RSI (14)", "value": f"{rsi_emoji} **{rsi:.1f}** - {rsi_label}", "inline": True})

        # MACD
        macd = indicators.get('macd')
        if macd is not None:
            macd_emoji = '\U0001f7e2' if macd > 0 else '\U0001f534'
            fields.append({"name": "MACD", "value": f"{macd_emoji} **{macd:.4f}**", "inline": True})

        # ADX + DI
        adx = indicators.get('adx')
        plus_di = indicators.get('plus_di')
        minus_di = indicators.get('minus_di')
        if adx is not None:
            trend_str = "Trending" if adx >= 25 else "Ranging"
            lines = [f"ADX: **{adx:.1f}** ({trend_str})"]
            if plus_di is not None and minus_di is not None:
                di_emoji = '\U0001f7e2' if plus_di > minus_di else '\U0001f534'
                lines.append(f"{di_emoji} +DI: {plus_di:.1f} | -DI: {minus_di:.1f}")
            fields.append({"name": "ADX / Directional", "value": "\n".join(lines), "inline": True})

        # Moving Averages
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        ema_12 = indicators.get('ema_12')
        ema_26 = indicators.get('ema_26')
        ma_lines = []
        if sma_20:
            pos = '\U0001f7e2' if price > sma_20 else '\U0001f534'
            ma_lines.append(f"SMA 20: {pos} ${sma_20:.2f}")
        if sma_50:
            pos = '\U0001f7e2' if price > sma_50 else '\U0001f534'
            ma_lines.append(f"SMA 50: {pos} ${sma_50:.2f}")
        if sma_200:
            pos = '\U0001f7e2' if price > sma_200 else '\U0001f534'
            ma_lines.append(f"SMA 200: {pos} ${sma_200:.2f}")
        if ema_12:
            ma_lines.append(f"EMA 12: ${ema_12:.2f}")
        if ema_26:
            ma_lines.append(f"EMA 26: ${ema_26:.2f}")
        if ma_lines:
            fields.append({"name": "Moving Averages", "value": "\n".join(ma_lines), "inline": True})

        # VWAP
        vwap = indicators.get('vwap')
        if vwap is not None:
            vwap_emoji = '\U0001f7e2' if price > vwap else '\U0001f534'
            fields.append({"name": "VWAP", "value": f"{vwap_emoji} ${vwap:.2f}", "inline": True})

        # Bollinger Bands
        bb_upper = indicators.get('bollinger_upper')
        bb_lower = indicators.get('bollinger_lower')
        if bb_upper and bb_lower:
            if price >= bb_upper:
                bb_label = "At Upper Band"
            elif price <= bb_lower:
                bb_label = "At Lower Band"
            else:
                bb_label = "Within Bands"
            fields.append({"name": "Bollinger Bands", "value": f"${bb_lower:.2f} - ${bb_upper:.2f}\n{bb_label}", "inline": True})

        # Ichimoku Cloud
        senkou_a = indicators.get('ichimoku_senkou_a')
        senkou_b = indicators.get('ichimoku_senkou_b')
        tenkan = indicators.get('ichimoku_tenkan')
        kijun = indicators.get('ichimoku_kijun')
        if senkou_a is not None and senkou_b is not None:
            cloud_top = max(senkou_a, senkou_b)
            cloud_bottom = min(senkou_a, senkou_b)
            if price > cloud_top:
                cloud_pos = '\U0001f7e2 Above Cloud'
            elif price < cloud_bottom:
                cloud_pos = '\U0001f534 Below Cloud'
            else:
                cloud_pos = '\U0001f7e1 Inside Cloud'
            lines = [f"Cloud: ${cloud_bottom:.2f} - ${cloud_top:.2f}", cloud_pos]
            if tenkan is not None:
                lines.append(f"Tenkan: ${tenkan:.2f}")
            if kijun is not None:
                lines.append(f"Kijun: ${kijun:.2f}")
            fields.append({"name": "Ichimoku Cloud", "value": "\n".join(lines), "inline": True})

        # Fibonacci Levels
        fib = sd.get('fibonacci')
        if fib:
            levels = fib.get('levels', {})
            nearest = fib.get('nearest_level')
            dist = fib.get('distance_pct', 0)
            fib_lines = []
            for level_pct in ['0.0', '23.6', '38.2', '50.0', '61.8', '78.6', '100.0']:
                lp = levels.get(level_pct)
                if lp is not None:
                    marker = ' \u25c0' if level_pct == nearest else ''
                    fib_lines.append(f"{level_pct}%: ${lp:.2f}{marker}")
            if dist < 3 and nearest:
                fib_lines.append(f"Near {nearest}% ({dist:.1f}% away)")
            fields.append({"name": "Fibonacci Levels", "value": "\n".join(fib_lines[:8]), "inline": True})

        if not fields:
            fields.append({"name": "Technical Analysis", "value": "Insufficient data for technical analysis.", "inline": False})

        return {
            "title": f"${ticker} \u2022 Technical Analysis",
            "color": COLOR_REPORT_TECHNICAL,
            "fields": fields,
            "footer": {"text": "6/10 Technical Analysis \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_signals_ml(self, sd: Dict) -> Dict:
        """Embed 7: Signals & ML"""
        ticker = sd['ticker']
        fields = []

        # Unified Signal
        signal_summary = sd.get('signal_summary')
        if signal_summary:
            signal = signal_summary.get('signal', 'HOLD')
            confidence = signal_summary.get('confidence', 0)
            reasons = signal_summary.get('reasons', [])
            bullish_count = signal_summary.get('bullish_count', 0)
            bearish_count = signal_summary.get('bearish_count', 0)

            if signal == 'BUY':
                sig_emoji = '\U0001f7e2'
            elif signal == 'SELL':
                sig_emoji = '\U0001f534'
            else:
                sig_emoji = '\U0001f7e1'

            sig_str = f"{sig_emoji} **{signal}** ({confidence}% confidence)\nBullish: {bullish_count} | Bearish: {bearish_count}"
            if reasons:
                sig_str += "\n" + " | ".join(reasons[:4])
            fields.append({"name": "Unified Signal", "value": sig_str, "inline": False})

        # Risk Assessment
        risk = self.analysis.get_risk_assessment(sd)
        if risk:
            risk_str = risk['risk_level'] + f" (Score: {risk['risk_score']})"
            factors = risk.get('risk_factors', [])
            if factors:
                risk_str += "\n" + "\n".join(factors[:4])
            fields.append({"name": "Risk Assessment", "value": risk_str[:1024], "inline": False})

        # Risk/Reward Ratio
        rr = sd.get('risk_reward')
        if rr:
            rr_str = f"**{rr['ratio']:.2f}:1** ({rr['rating']})\nUpside: {rr['upside_pct']:+.1f}% | Downside: -{rr['downside_pct']:.1f}%"
            fields.append({"name": "Risk/Reward Ratio", "value": rr_str, "inline": True})

        # ML Prediction
        ml = sd.get('ml_prediction')
        if ml:
            ml_emoji = ml.get('emoji', '\U0001f7e1')
            direction = ml.get('direction', 'FLAT')
            conf = ml.get('confidence', 0)
            days = ml.get('days', 5)
            features = ml.get('features', '')

            ml_str = f"{ml_emoji} **{direction}** ({conf}% conf, {days}-day)"
            probs = ml.get('probabilities', {})
            if probs:
                prob_parts = [f"{k}: {v}%" for k, v in probs.items()]
                ml_str += "\n" + " | ".join(prob_parts)
            if features:
                ml_str += f"\nFeatures: {features}"
            ml_str += "\n*Experimental - not financial advice*"
            fields.append({"name": "ML Prediction", "value": ml_str[:1024], "inline": True})

        # Backtest
        backtest = sd.get('backtest')
        if backtest:
            sharpe_emoji = '\U0001f7e2' if backtest['sharpe_ratio'] > 1 else '\U0001f7e1' if backtest['sharpe_ratio'] > 0 else '\U0001f534'
            vs_spy = '\U0001f7e2' if backtest['excess_return'] > 0 else '\U0001f534'
            bt_str = (
                f"3Y Return: **{backtest['total_return']:+.1f}%**\n"
                f"vs SPY: {vs_spy} {backtest['excess_return']:+.1f}%\n"
                f"Sharpe: {sharpe_emoji} {backtest['sharpe_ratio']:.2f} | "
                f"Max DD: {backtest['max_drawdown']:.1f}%\n"
                f"Win Rate: {backtest['win_rate']:.0f}% | "
                f"Profit Factor: {backtest['profit_factor']:.2f}"
            )
            fields.append({"name": "3-Year Backtest", "value": bt_str, "inline": False})

        if not fields:
            fields.append({"name": "Signals", "value": "Insufficient data for signal generation.", "inline": False})

        return {
            "title": f"${ticker} \u2022 Signals & ML",
            "color": COLOR_REPORT_SIGNALS,
            "fields": fields,
            "footer": {"text": "7/10 Signals & ML \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_options(self, sd: Dict) -> Dict:
        """Embed 8: Options"""
        ticker = sd['ticker']
        fields = []

        options_data = sd.get('options_data')
        options_flow = sd.get('options_flow')

        if options_data:
            # P/C Ratio
            pc = options_data.get('pc_ratio')
            if pc is not None:
                if pc < 0.5:
                    pc_label = "Heavy Call Buying"
                    pc_emoji = '\U0001f7e2'
                elif pc > 1.5:
                    pc_label = "Heavy Put Buying"
                    pc_emoji = '\U0001f534'
                else:
                    pc_label = "Balanced"
                    pc_emoji = '\U0001f7e1'
                fields.append({"name": "Put/Call Ratio", "value": f"{pc_emoji} **{pc:.2f}** - {pc_label}", "inline": True})

            # Max Pain
            mp = options_data.get('max_pain')
            if mp:
                diff = ((mp - sd['price']) / sd['price']) * 100
                fields.append({"name": "Max Pain", "value": f"**${mp:.2f}** ({diff:+.1f}% from price)", "inline": True})

            # Volume / OI
            call_vol = options_data.get('total_call_vol', 0)
            put_vol = options_data.get('total_put_vol', 0)
            call_oi = options_data.get('total_call_oi', 0)
            put_oi = options_data.get('total_put_oi', 0)
            expiry = options_data.get('expiry', '')

            vol_str = f"Call Vol: **{call_vol:,}** | Put Vol: **{put_vol:,}**\nCall OI: **{call_oi:,}** | Put OI: **{put_oi:,}**"
            if expiry:
                vol_str += f"\nExpiry: {expiry}"
            fields.append({"name": "Volume & Open Interest", "value": vol_str, "inline": False})

            # Unusual activity (top 5)
            unusual = options_data.get('unusual_strikes', [])
            if unusual:
                lines = []
                for u in unusual[:5]:
                    strike_type = 'CALL' if u['type'] == 'CALL' else 'PUT'
                    lines.append(f"${u['strike']:.0f} {strike_type} - Vol: {u['volume']:,} | OI: {u['oi']:,} | **{u['ratio']:.1f}x** OI")
                fields.append({"name": "Unusual Activity", "value": "\n".join(lines), "inline": False})

        # Flow analysis summary
        if options_flow:
            flow = options_flow.get('flow', 'NEUTRAL')
            flow_emoji = options_flow.get('emoji', '\U0001f7e1')
            signals = options_flow.get('signals', [])
            flow_str = f"{flow_emoji} **{flow.replace('_', ' ')}**"
            if signals:
                flow_str += "\n" + " | ".join(signals[:4])
            fields.append({"name": "Flow Analysis", "value": flow_str, "inline": False})

        if not fields:
            fields.append({"name": "Options", "value": "No options data available for this ticker.", "inline": False})

        return {
            "title": f"${ticker} \u2022 Options Analysis",
            "color": COLOR_REPORT_OPTIONS,
            "fields": fields,
            "footer": {"text": "8/10 Options \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_insider(self, sd: Dict) -> Dict:
        """Embed 9: Insider/Institutional/Congress"""
        ticker = sd['ticker']
        fields = []

        # Insider activity
        insider = sd.get('insider_data')
        if insider:
            buys = insider.get('buys', 0)
            sells = insider.get('sells', 0)
            lookback = insider.get('lookback_days', 90)
            net = buys - sells

            if net > 0:
                net_emoji = '\U0001f7e2'
            elif net < 0:
                net_emoji = '\U0001f534'
            else:
                net_emoji = '\U0001f7e1'

            ins_str = f"{net_emoji} **{buys} buy{'s' if buys != 1 else ''}** / **{sells} sell{'s' if sells != 1 else ''}** ({lookback}d)"

            # Show recent transactions
            txns = insider.get('transactions', [])
            if txns:
                for t in txns[:5]:
                    tname = t.get('name', 'Unknown')[:30]
                    txn_type = t.get('type', '')
                    shares = t.get('shares', 0)
                    value = t.get('value', 0)
                    date = t.get('date', '')
                    type_emoji = '\U0001f7e2' if txn_type == 'BUY' else '\U0001f534' if txn_type == 'SELL' else '\U0001f7e1'
                    val_str = self._fmt_num(value) if value else ''
                    ins_str += f"\n{type_emoji} {tname} - {txn_type} {shares:,} shares {val_str} ({date})"

            fields.append({"name": "Insider Transactions", "value": ins_str[:1024], "inline": False})

            # Ownership percentages
            inst_pct = insider.get('institutional_pct')
            insider_pct = insider.get('insider_pct')
            own_parts = []
            if inst_pct is not None:
                own_parts.append(f"Institutional: **{inst_pct:.1f}%**")
            if insider_pct is not None:
                own_parts.append(f"Insider: **{insider_pct:.1f}%**")
            if own_parts:
                fields.append({"name": "Ownership", "value": " | ".join(own_parts), "inline": True})

        # Institutional holders from extra data (handled by bot if needed)

        # Congress trades
        congress = sd.get('congress_data')
        if congress and congress.get('trades'):
            c_buys = congress.get('buys', 0)
            c_sells = congress.get('sells', 0)
            total = congress.get('total', 0)

            parts = []
            if c_buys > 0:
                parts.append(f"\U0001f7e2 **{c_buys} purchase{'s' if c_buys != 1 else ''}**")
            if c_sells > 0:
                parts.append(f"\U0001f534 **{c_sells} sale{'s' if c_sells != 1 else ''}**")
            if not parts:
                parts.append(f"{total} trade{'s' if total != 1 else ''}")

            cong_str = " / ".join(parts) + f" ({CONGRESS_LOOKBACK_DAYS}d)"

            for t in congress['trades'][:3]:
                cname = t.get('politician_name', 'Unknown')
                if len(cname) > 25:
                    cname = cname[:23] + '..'
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
                emoji = '\U0001f7e2' if 'PURCHASE' in txn else '\U0001f534'
                cong_str += f"\n{emoji} {cname}{chamber_tag} {txn} {amount} ({date_str})"

            fields.append({"name": "Congress Trades", "value": cong_str[:1024], "inline": False})

        if not fields:
            fields.append({"name": "Insider/Institutional", "value": "No insider or Congressional trading data available.", "inline": False})

        return {
            "title": f"${ticker} \u2022 Insider / Institutional / Congress",
            "color": COLOR_REPORT_INSIDER,
            "fields": fields,
            "footer": {"text": "9/10 Insider & Congress \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _embed_analyst_news(self, sd: Dict, extra: Dict) -> Dict:
        """Embed 10: Analyst/News/Track Record"""
        ticker = sd['ticker']
        fields = []

        # Analyst consensus (from recommendations)
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
                    lines = [
                        f"Strong Buy: **{sb}** | Buy: **{b}** | Hold: **{h}**",
                        f"Sell: **{s}** | Strong Sell: **{ss}**",
                    ]
                    buy_pct = (sb + b) / total * 100
                    if buy_pct >= 70:
                        consensus = '\U0001f7e2 Strong Buy'
                    elif buy_pct >= 50:
                        consensus = '\U0001f7e2 Buy'
                    elif (sb + b) >= (s + ss):
                        consensus = '\U0001f7e1 Hold'
                    else:
                        consensus = '\U0001f534 Sell'
                    lines.append(f"Consensus: **{consensus}** ({buy_pct:.0f}% bullish)")
                    fields.append({"name": "Analyst Ratings", "value": "\n".join(lines), "inline": False})
            except Exception:
                pass

        # Analyst rating & target from stock info
        rating = sd.get('analyst_rating')
        target = sd.get('price_target')
        if rating or target:
            parts = []
            if rating:
                parts.append(f"Rating: **{rating.upper()}**")
            if target:
                upside = ((target - sd['price']) / sd['price']) * 100
                parts.append(f"Target: **${target:.2f}** ({upside:+.1f}%)")
            fields.append({"name": "Analyst Summary", "value": " | ".join(parts), "inline": True})

        # News headlines
        news = sd.get('recent_news', [])
        if news:
            lines = []
            for article in news[:5]:
                title = article.get('title', '')[:80]
                source = article.get('source', 'News')
                date = article.get('date', '')
                url = article.get('url', '')
                if url:
                    lines.append(f"[{title}]({url})\n*{source} - {date}*")
                else:
                    lines.append(f"{title}\n*{source} - {date}*")
            if lines:
                fields.append({"name": "Recent News", "value": "\n".join(lines)[:1024], "inline": False})

        # Bot track record for this ticker
        stats = self.db.get_stock_stats(ticker)
        if stats and stats.get('total_mentions', 0) > 0:
            win_emoji = '\U0001f7e2' if stats['win_rate'] >= 50 else '\U0001f534'
            tr_str = (
                f"**{stats['wins']}W-{stats['losses']}L** ({win_emoji} {stats['win_rate']:.0f}%)\n"
                f"Avg Change: {stats['avg_change']:+.1f}% | "
                f"Best: +{stats['best_gain']:.1f}% | Worst: {stats['worst_loss']:.1f}%\n"
                f"Mentions: {stats['total_mentions']} | Avg Days Tracked: {stats['avg_days']:.0f}"
            )
            fields.append({"name": "Bot Track Record", "value": tr_str, "inline": False})

        if not fields:
            fields.append({"name": "Analyst/News", "value": "No analyst or news data available.", "inline": False})

        return {
            "title": f"${ticker} \u2022 Analyst / News / Track Record",
            "color": COLOR_REPORT_ANALYST,
            "fields": fields,
            "footer": {"text": "10/10 Analyst & News \u2022 Stonk Bot v5.0"},
            "timestamp": datetime.utcnow().isoformat(),
        }
