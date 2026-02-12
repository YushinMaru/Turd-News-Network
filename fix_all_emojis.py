#!/usr/bin/env python3
"""
Comprehensive emoji encoding fix - mapping all corrupted patterns
"""

def generate_corruption_map():
    """Generate mappings from correct emojis to their corrupted versions"""
    mappings = {}

    # Common emojis used in the Discord bot
    emojis = [
        ('⚠️', 'warning with variation selector'),
        ('⚠', 'warning'),
        ('⭐', 'star'),
        ('📊', 'bar chart'),
        ('📈', 'chart increasing'),
        ('📉', 'chart decreasing'),
        ('🔴', 'red circle'),
        ('🟢', 'green circle'),
        ('🟡', 'yellow circle'),
        ('🏷️', 'label'),
        ('⬆️', 'up arrow'),
        ('⬆', 'up arrow no variant'),
        ('🏢', 'office building'),
        ('🔥', 'fire'),
        ('✨', 'sparkles'),
        ('🏸', 'badminton'),
        ('➡', 'right arrow'),
        ('💡', 'light bulb'),
        ('📅', 'calendar'),
        ('🔗', 'link'),
        ('─', 'box drawing horizontal'),
        ('💎', 'gem stone'),
        ('✅', 'check mark button'),
        ('❌', 'cross mark'),
        ('🏯', 'Japanese castle'),
        ('🔱', 'trident emblem'),
        ('💬', 'speech balloon'),
        ('💵', 'dollar banknote'),
        ('💰', 'money bag'),
        ('📦', 'package'),
        ('🎯', 'bullseye'),
    ]

    for emoji, desc in emojis:
        try:
            # Simulate double-encoding corruption:
            # UTF-8 bytes -> interpreted as Latin-1 -> encoded as UTF-8 -> repeated
            utf8_bytes = emoji.encode('utf-8')
            step1 = utf8_bytes.decode('latin-1')
            step1_utf8 = step1.encode('utf-8')
            corrupted = step1_utf8.decode('latin-1')

            mappings[corrupted] = emoji
        except:
            pass

    return mappings

def fix_file(filename, mappings):
    """Fix file using the corruption mappings"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        replacement_count = {}

        # Apply all mappings
        for corrupted, correct in mappings.items():
            if corrupted in content:
                count = content.count(corrupted)
                content = content.replace(corrupted, correct)
                replacement_count[correct] = count

        if content == original:
            return 0, {}

        # Save
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        return sum(replacement_count.values()), replacement_count

    except Exception as e:
        print(f"Error in {filename}: {e}")
        return 0, {}

if __name__ == '__main__':
    print("="*60)
    print("Comprehensive Emoji Encoding Fix")
    print("="*60)

    # Generate corruption mappings
    print("\nGenerating corruption mappings...")
    mappings = generate_corruption_map()
    print(f"Generated {len(mappings)} mappings")

    # Fix files
    files = ['discord_embed.py', 'discord_sender.py']

    total_fixes = 0
    for filename in files:
        print(f"\nProcessing {filename}...")
        count, replacements = fix_file(filename, mappings)

        if count > 0:
            print(f"  Made {count} replacements:")
            for emoji, cnt in replacements.items():
                print(f"    {cnt}x {emoji}")
            total_fixes += count
        else:
            print(f"  No changes")

    print("\n" + "="*60)
    print(f"Total fixes: {total_fixes}")
    print("="*60)

    # Verify
    print("\nVerification:")
    with open('discord_embed.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for remaining corruption patterns
    import re
    remaining = re.findall(r'Ã[ƒƒ]|ð|â€|Å|Â[^\s]', content)

    if remaining:
        print(f"⚠  Still {len(remaining)} potentially corrupted characters")
        print(f"  Sample: {remaining[:5]}")
    else:
        print("✓ No obvious corruption patterns detected")

    # Check for correct emojis
    if '📊' in content and '🔴' in content and '⚠' in content:
        print("✓ Correct emojis detected in file")
    else:
        print("✗ Expected emojis not found")
