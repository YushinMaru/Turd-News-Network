
# Script to update main.py to send all chart files

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the chart sending section
old_chart_section = '''                            if chart_path and os.path.exists(chart_path):
                                try:
                                    chart_file = discord.File(chart_path, filename=f"{ticker}_chart.png")
                                    await stonks_channel.send(file=chart_file)
                                except:
                                    pass'''

new_chart_section = '''                            # Send all chart files (1 week, 3 month, 1 year)
                            chart_paths = sd.get('chart_paths', [])
                            if chart_paths:
                                for cp in chart_paths:
                                    if cp and os.path.exists(cp):
                                        try:
                                            # Extract period from filename (e.g., "NVDA_chart_1w.png")
                                            import os
                                            basename = os.path.basename(cp)
                                            chart_file = discord.File(cp, filename=basename)
                                            await stonks_channel.send(file=chart_file)
                                        except Exception as e:
                                            print(f"[DD] Error sending chart {cp}: {e}")
                                            pass
                            elif chart_path and os.path.exists(chart_path):
                                # Fallback to single chart
                                try:
                                    chart_file = discord.File(chart_path, filename=f"{ticker}_chart.png")
                                    await stonks_channel.send(file=chart_file)
                                except:
                                    pass'''

content = content.replace(old_chart_section, new_chart_section)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - updated main.py to send all chart files')
