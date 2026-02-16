
# Script to add multiple timeframe chart generation to stock_data.py

import re

# Read the current stock_data.py
with open('stock_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the _generate_chart method and add a new method after it
new_method = '''
    def _generate_multi_timeframe_charts(self, ticker: str, valid_ticker: str, w52_high=None, w52_low=None) -> list:
        """
        Generate multiple timeframe charts: 1 week, 3 month, 1 year.
        Returns a list of chart file paths.
        """
        import yfinance as yf
        
        chart_periods = [
            ('1w', '7d'),   # 1 week
            ('3m', '3mo'),  # 3 month  
            ('1y', '1y'),   # 1 year
        ]
        
        chart_paths = []
        
        for period_name, yf_period in chart_periods:
            try:
                # Fetch data for this period
                stock = yf.Ticker(valid_ticker)
                hist = stock.history(period=yf_period)
                
                if hist.empty or len(hist) < 5:
                    continue
                
                # Generate chart with specific period
                chart_path = self._generate_single_chart(ticker, hist, w52_high, w52_low, period_name)
                if chart_path:
                    chart_paths.append(chart_path)
                    print(f"   [CHART] Generated {period_name} chart for {ticker}")
                    
            except Exception as e:
                print(f"   [!] Error generating {period_name} chart for {ticker}: {e}")
                continue
        
        return chart_paths

    def _generate_single_chart(self, ticker: str, hist_data, w52_high=None, w52_low=None, period_name='3m') -> Optional[str]:
        """
        Generate a single candlestick chart with technical overlays.
        Returns the file path to the saved PNG or None on failure.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import mplfinance as mpf
        except ImportError as e:
            print(f"   [!] mplfinance not installed: {e}")
            return None

        try:
            # Work on a copy to avoid modifying original data
            hist_copy = hist_data.copy()
            
            # Ensure proper column names for mplfinance
            column_mapping = {
                'Open': 'Open',
                'High': 'High', 
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            }
            
            # Rename columns if needed
            for old_col, new_col in column_mapping.items():
                if old_col in hist_copy.columns and new_col not in hist_copy.columns:
                    hist_copy = hist_copy.rename(columns={old_col: new_col})
            
            # Verify required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close']
            for col in required_cols:
                if col not in hist_copy.columns:
                    return None

            # Calculate moving averages
            hist_copy['SMA20'] = hist_copy['Close'].rolling(window=20).mean()
            hist_copy['SMA50'] = hist_copy['Close'].rolling(window=50).mean()
            if len(hist_copy) >= 200:
                hist_copy['SMA200'] = hist_copy['Close'].rolling(window=200).mean()

            # Use all available data
            chart_data = hist_copy.copy()
            if len(chart_data) < 10:
                return None

            # Build overlay plots
            addplots = []
            if 'SMA20' in chart_data.columns and not chart_data['SMA20'].isna().all():
                addplots.append(mpf.make_addplot(chart_data['SMA20'], color='#2196F3', width=0.8))
            if 'SMA50' in chart_data.columns and not chart_data['SMA50'].isna().all():
                addplots.append(mpf.make_addplot(chart_data['SMA50'], color='#FF9800', width=0.8))
            if 'SMA200' in chart_data.columns and not chart_data['SMA200'].isna().all():
                addplots.append(mpf.make_addplot(chart_data['SMA200'], color='#9C27B0', width=0.8))

            # Bollinger Bands
            if ENABLE_CHART_BOLLINGER and 'SMA20' in chart_data.columns:
                std20 = hist_copy['Close'].rolling(window=20).std()
                bb_upper = hist_copy['SMA20'] + 2 * std20
                bb_lower = hist_copy['SMA20'] - 2 * std20
                if not bb_upper.isna().all():
                    addplots.append(mpf.make_addplot(bb_upper, color='#9E9E9E', linestyle='--', width=0.5))
                    addplots.append(mpf.make_addplot(bb_lower, color='#9E9E9E', linestyle='--', width=0.5))

            # 52-week high/low horizontal lines
            hlines_vals = []
            hlines_colors = []
            if w52_high and w52_high > 0:
                hlines_vals.append(w52_high)
                hlines_colors.append('#4CAF50')
            if w52_low and w52_low > 0:
                hlines_vals.append(w52_low)
                hlines_colors.append('#F44336')

            hlines_dict = None
            if hlines_vals:
                hlines_dict = dict(hlines=hlines_vals, colors=hlines_colors, linestyle='-.', linewidths=0.7)

            # Chart directory
            chart_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), CHART_DIR)
            os.makedirs(chart_dir, exist_ok=True)

            # Create filename with period
            filepath = os.path.join(chart_dir, f"{ticker}_chart_{period_name}.png")

            # Custom style
            mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
            period_labels = {'1w': '1 Week', '3m': '3 Month', '1y': '1 Year'}
            style = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='#e0e0e0',
                facecolor='#fafafa'
            )

            # Plot
            kwargs = dict(
                type='candle',
                style=style,
                volume=True,
                title=f'\\n${ticker} - {period_labels.get(period_name, period_name)} Chart',
                savefig=dict(fname=filepath, dpi=120, bbox_inches='tight'),
                figsize=(10, 8),
            )
            if addplots:
                kwargs['addplot'] = addplots
            if hlines_dict:
                kwargs['hlines'] = hlines_dict

            mpf.plot(chart_data, **kwargs)
            plt.close('all')

            if os.path.exists(filepath):
                return filepath
            return None

        except Exception as e:
            print(f"   [!] Chart generation failed for {ticker}: {e}")
            try:
                import matplotlib.pyplot as plt
                plt.close('all')
            except Exception:
                pass
            return None

'''

# Find where to insert the new methods (after _generate_chart method)
# Look for the get_options_data method which comes after _generate_chart
pattern = r'(    def get_options_data\(self, ticker: str, valid_ticker: str\))'
replacement = new_method + r'\n\1'

content = re.sub(pattern, replacement, content)

# Now update get_stock_data to generate multiple charts
# Find the chart generation section
old_chart_section = '''            # Generate chart image if enabled
            if ENABLE_CHARTS:
                try:
                    chart_path = self._generate_chart(
                        display_ticker, hist,
                        w52_high=data.get('52w_high'),
                        w52_low=data.get('52w_low')
                    )
                    if chart_path and os.path.exists(chart_path):
                        data['chart_path'] = chart_path
                        print(f"   [CHART] Generated chart for {ticker}: {chart_path}")
                    else:
                        print(f"   [!] Chart generation returned None or file not found for {ticker}")
                except Exception as e:
                    print(f"   [!] Chart generation error for {ticker}: {e}")'''

new_chart_section = '''            # Generate multiple timeframe charts if enabled
            if ENABLE_CHARTS:
                try:
                    chart_paths = self._generate_multi_timeframe_charts(
                        display_ticker, valid_ticker,
                        w52_high=data.get('52w_high'),
                        w52_low=data.get('52w_low')
                    )
                    if chart_paths:
                        data['chart_paths'] = chart_paths
                        # Keep the main 3-month chart for backward compatibility
                        data['chart_path'] = chart_paths[0] if len(chart_paths) > 0 else None
                        print(f"   [CHART] Generated {len(chart_paths)} charts for {ticker}")
                    else:
                        print(f"   [!] Chart generation returned no charts for {ticker}")
                except Exception as e:
                    print(f"   [!] Chart generation error for {ticker}: {e}")'''

content = content.replace(old_chart_section, new_chart_section)

# Write the modified content
with open('stock_data.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - added multiple timeframe chart generation')
