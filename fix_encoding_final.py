#!/usr/bin/env python3
"""
Fix the multi-layered emoji encoding corruption
"""

def fix_file(filename):
    """Fix corrupted emojis using direct string replacement"""
    try:
        print(f"\nProcessing {filename}...")

        # Read file as UTF-8 (the corrupted text is valid UTF-8, just wrong characters)
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Build comprehensive replacement map
        # Format: corrupted_string -> correct_emoji
        replacements = {}

        # Method 1: Direct mappings from analysis
        replacements['ÃƒÂ¢Ã‚Â\xadÃ‚Â\x90'] = '⭐'  # Star (from analysis)

        # Method 2: Test decoding corruption layers
        # The corruption appears to be: UTF-8 bytes -> interpreted as CP1252 -> UTF-8 encoded again -> interpreted as CP1252 -> UTF-8 encoded

        # Let's generate mappings for common emojis
        emojis = {
            '\u26a0\ufe0f': '⚠️',  # Warning
            '\u26a0': '⚠',
            '\u2b50': '⭐',  # Star
            '\U0001f4ca': '📊',  # Bar chart
            '\U0001f534': '🔴',  # Red circle
            '\U0001f7e2': '🟢',  # Green circle
            '\U0001f7e1': '🟡',  # Yellow circle
            '\U0001f3f7\ufe0f': '🏷️',  # Label
            '\u2b06\ufe0f': '⬆️',  # Up arrow
            '\u2b06': '⬆',
            '\U0001f3e2': '🏢',  # Building
            '\U0001f525': '🔥',  # Fire
            '\u2728': '✨',  # Sparkles
            '\U0001f3f8': '🏸',  # Shuttlecock
            '\u27a1': '➡',  # Right arrow
            '\U0001f4a1': '💡',  # Light bulb
            '\U0001f4c5': '📅',  # Calendar
            '\U0001f517': '🔗',  # Link
            '\u2500': '─',  # Box drawing
            '\U0001f48e': '💎',  # Gem
            '\u2705': '✅',  # Check
            '\u274c': '❌',  # Cross
            '\U0001f3ef': '🏯',  # Castle
            '\U0001f531': '🔱',  # Trident
            '\U0001f4c9': '📉',  # Chart decreasing
            '\U0001f4c8': '📈',  # Chart increasing
            '\U0001f4ac': '💬',  # Speech balloon
            '\U0001f4b5': '💵',  # Dollar
            '\U0001f4b0': '💰',  # Money bag
            '\U0001f4a6': '📦',  # Package
        }

        # Generate corrupted versions by simulating the encoding error
        def corrupt_emoji(emoji):
            """Simulate the corruption: UTF-8 -> CP1252 misinterpret -> UTF-8 -> repeat"""
            try:
                # Get UTF-8 bytes
                utf8_bytes = emoji.encode('utf-8')

                # Interpret as CP1252 (latin-1) and encode as UTF-8
                step1 = utf8_bytes.decode('latin-1').encode('utf-8')

                # Repeat: interpret as CP1252 and encode as UTF-8
                step2 = step1.decode('latin-1').encode('utf-8')

                # Decode as UTF-8 to get the corrupted string
                corrupted = step2.decode('utf-8')

                return corrupted
            except:
                return None

        # Generate corruption map
        for emoji_code, emoji in emojis.items():
            corrupted = corrupt_emoji(emoji)
            if corrupted and corrupted != emoji:
                replacements[corrupted] = emoji

        # Apply all replacements
        replacement_count = 0
        for corrupted, correct in replacements.items():
            if corrupted in content:
                count = content.count(corrupted)
                content = content.replace(corrupted, correct)
                replacement_count += count
                print(f"  Replaced {count}x: {correct}")

        if content == original_content:
            print(f"  No changes made")
            return False

        # Write back
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  Total replacements: {replacement_count}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    files = ['discord_embed.py', 'discord_sender.py']

    print("="*60)
    print("Fixing Emoji Encoding Corruption")
    print("="*60)

    for f in files:
        fix_file(f)

    print("\n" + "="*60)
    print("Verification")
    print("="*60)

    # Test
    with open('discord_embed.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if len(lines) >= 95:
            line95 = lines[94]
            print(f"\nLine 95: {line95.strip()[:80]}...")
            if '⭐' in line95:
                print("✓ Fixed successfully!")
            else:
                print("✗ Still needs fixing")
