#!/usr/bin/env python3
"""
Fix corrupted emoji encoding - the file was saved with wrong encoding
Strategy: Read as latin-1, then re-encode properly as UTF-8
"""

def fix_file(filename):
    """Fix encoding by reading as latin-1 and saving as UTF-8"""
    try:
        print(f"Processing {filename}...")

        # Read as bytes
        with open(filename, 'rb') as f:
            raw_bytes = f.read()

        # Try to decode as latin-1 (this will succeed even with mojibake)
        try:
            content = raw_bytes.decode('latin-1')
        except:
            print(f"  Could not decode as latin-1, trying utf-8...")
            content = raw_bytes.decode('utf-8', errors='ignore')

        # Now we have the text with the mojibake characters as-is
        # We need to fix the double-encoding issue
        # The problem: UTF-8 bytes were interpreted as latin-1 and re-encoded as UTF-8

        # To fix: decode the UTF-8 bytes back to latin-1, then encode as latin-1 to get original bytes,
        # then decode as UTF-8 to get correct text

        # Actually, simpler approach: just find and replace the specific mojibake patterns
        original_content = content

        replacements = {
            # Based on hex dump: line 95 shows the corrupted star emoji
            '\u00c3\u0083\u00c6\u0092\u00c3\u0082\u00c2\u00a2\u00c3\u0083\u00e2\u0080\u009a\u00c3\u0082\u00c2\u00ad\u00c3\u0083\u00e2\u0080\u009a\u00c3\u0082\u00c2\u0090': '\u2b50',  # ⭐
        }

        # Try a more general approach - look for common mojibake patterns
        # If text was UTF-8 but saved as latin-1 then re-read as UTF-8, we get double encoding

        # Let me try repairing by converting back through the encoding chain
        try:
            # Encode to latin-1 to get original UTF-8 bytes, then decode as UTF-8
            fixed_content = content.encode('latin-1').decode('utf-8')
            print(f"  Successfully repaired encoding!")

            # Write back
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

            print(f"  Fixed {filename}")
            return True

        except Exception as e2:
            print(f"  Encoding repair failed: {e2}")
            print(f"  File may already be correct or has a different issue")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    files = ['discord_embed.py', 'discord_sender.py']

    print("Fixing encoding issues...")
    print("="*60)

    for filename in files:
        fix_file(filename)

    print("="*60)
    print("Done!")
