# Patch to be applied to main.py
# This adds the stats summary and changes channel name

# After line: print(f"[COMPLETE] Scan complete! Processed: {processed_count}/{len(all_posts)}")
# Add these lines:
        
        # Send stats summary to Discord
        if processed_count > 0:
            print("[SUMMARY] Sending performance stats to Discord...")
            try:
                embeds = self.stats_reporter.generate_performance_embed()
                for guild in self.guilds:
                    for channel in guild.text_channels:
                        if channel.name == "📉stonks":
                            for embed_dict in embeds:
                                embed = discord.Embed(
                                    title=embed_dict.get('title'),
                                    description=embed_dict.get('description'),
                                    color=embed_dict.get('color', 0x3498DB),
                                    timestamp=datetime.now()
                                )
                                for field in embed_dict.get('fields', []):
                                    embed.add_field(
                                        name=field.get('name', '')[:256],
                                        value=str(field.get('value', ''))[:1024],
                                        inline=field.get('inline', False)
                                    )
                                if embed_dict.get('footer', {}).get('text'):
                                    embed.set_footer(text=embed_dict['footer']['text'])
                                await channel.send(embed=embed)
                            print(f"[SUMMARY] ✅ Stats sent to #{channel.name} in {guild.name}")
                            break
            except Exception as e:
                print(f"[SUMMARY] ❌ Error sending stats: {e}")

# Change: stonks_channel_name = "stonks"
# To: stonks_channel_name = "📉stonks"
