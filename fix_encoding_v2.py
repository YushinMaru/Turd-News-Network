#!/usr/bin/env python3
"""
Fix emoji encoding using direct byte replacements
Based on actual hex analysis of the corrupted file
"""

def fix_file(filename):
    """Fix file using byte-level find and replace"""
    try:
        print(f"\nProcessing {filename}...")

        # Read as raw bytes
        with open(filename, 'rb') as f:
            content = f.read()

        original_size = len(content)

        # Direct byte replacements based on hex analysis
        # Format: (corrupted_bytes, correct_emoji_utf8_bytes, description)
        replacements = [
            # Star emoji ⭐ (from line 95)
            (b'\xc3\x83\xc6\x92\xc3\x82\xc2\xa2\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\xad\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\x90', b'\xe2\xad\x90', 'star'),
        ]

        # Also try common patterns - these are UTF-8 bytes that were double-encoded
        # The pattern: Each UTF-8 byte got interpreted as Windows-1252 and re-encoded as UTF-8

        # Let's try to find patterns programmatically
        # Common emoji starting bytes in UTF-8:
        # F0 9F (4-byte emojis like 📊 🔴 etc.)
        # E2 (3-byte symbols like ⚠ ⭐ ➡)

        # When F0 is interpreted as Windows-1252 char 0xF0 (ð) and encoded to UTF-8: C3 B0
        # When 9F is interpreted as Windows-1252 and  encoded: C5 B8
        # etc.

        total_replacements = 0
        for corrupted, correct, desc in replacements:
            count = content.count(corrupted)
            if count > 0:
                print(f"  Replacing {count}x {desc}")
                content = content.replace(corrupted, correct)
                total_replacements += count

        if total_replacements == 0:
            print(f"  No direct replacements found. Trying algorithmic approach...")

            # Try fixing UTF-8 -> Windows-1252 -> UTF-8 double encoding
            try:
                # Decode current UTF-8 to string
                text = content.decode('utf-8')

                # Encode back to latin-1 (this treats each char as a byte)
                # This should give us the original corrupted UTF-8 bytes
                raw_bytes = text.encode('latin-1')

                # Now decode as UTF-8 to get correct text
                fixed_text = raw_bytes.decode('utf-8')

                # Write back
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(fixed_text)

                print(f"  Applied algorithmic fix")
                return True

            except Exception as e:
                print(f"  Algorithmic approach failed: {e}")
                return False

        else:
            # Write back the byte-replaced content
            with open(filename, 'wb') as f:
                f.write(content)

            print(f"  Made {total_replacements} replacements")
            return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    import sys

    files = ['discord_embed.py', 'discord_sender.py']

    print("="*60)
    print("Emoji Encoding Fix - Direct Byte Replacement")
    print("="*60)

    for f in files:
        fix_file(f)

    print("\n" + "="*60)
    print("Testing the fix...")
    print("="*60)

    # Test by reading line 95 of discord_embed.py
    try:
        with open('discord_embed.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 95:
                line95 = lines[94]  # 0-indexed
                print(f"\nLine 95 content:")
                print(f"  {line95.strip()}")

                # Check if it contains the correct emoji
                if '⭐' in line95 or '\u2b50' in line95:
                    print("\n✓ SUCCESS! Emoji fixed correctly")
                else:
                    print("\n✗ FAILED: Still showing corrupted text")
                    print(f"  Expected ⭐ (U+2B50)")

    except Exception as e:
        print(f"Test failed: {e}")
