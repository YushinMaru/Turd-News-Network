#!/usr/bin/env python3
"""
Search the error.log file for specific terms.
Usage: python search_errors.py <search_term> [--stats] [--limit N]
"""

import sys
import os

ERROR_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'error.log')


def search_errors(search_term: str, limit: int = 100) -> list:
    """Search the error log for matching entries"""
    matches = []
    try:
        if not os.path.exists(ERROR_LOG_FILE):
            return ["Error log file not found"]
        
        with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        search_lower = search_term.lower()
        for line in reversed(lines):  # Most recent first
            if search_lower in line.lower():
                matches.append(line.strip())
                if len(matches) >= limit:
                    break
    except Exception as e:
        return [f"Error reading log: {e}"]
    
    return matches


def get_error_stats() -> dict:
    """Get statistics about logged errors"""
    stats = {
        'total_errors': 0,
        'by_type': {},
        'by_category': {},
        'recent': []
    }
    
    try:
        if not os.path.exists(ERROR_LOG_FILE):
            return stats
        
        with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            if '| ERROR |' in line or '| EXCEPTION |' in line:
                stats['total_errors'] += 1
                
                # Parse type
                parts = line.split('|')
                if len(parts) >= 3:
                    err_type = parts[2].strip()
                    stats['by_type'][err_type] = stats['by_type'].get(err_type, 0) + 1
                
                # Parse category
                if len(parts) >= 4:
                    category = parts[3].strip()
                    stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        # Get 10 most recent errors
        stats['recent'] = [l.strip() for l in lines[-10:] if '| ERROR |' in l or '| EXCEPTION |' in l]
    except Exception as e:
        pass
    
    return stats


if __name__ == "__main__":
    # Check for --stats flag
    if '--stats' in sys.argv:
        stats = get_error_stats()
        print("\n=== ERROR STATISTICS ===")
        print(f"Total Errors: {stats['total_errors']}")
        print("\nBy Category:")
        for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        print("\nBy Type:")
        for type_, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
            print(f"  {type_}: {count}")
        print("\n=== RECENT ERRORS ===")
        for err in stats['recent']:
            print(err)
        sys.exit(0)
    
    # Get limit from args
    limit = 100
    if '--limit' in sys.argv:
        try:
            idx = sys.argv.index('--limit')
            limit = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            limit = 100
    
    # Get search term
    search_term = ' '.join(sys.argv[1:])
    if not search_term or search_term in ['--stats', '--limit']:
        print("Usage: python search_errors.py <search_term> [--stats] [--limit N]")
        print("\nExamples:")
        print("  python search_errors.py NotFound")
        print("  python search_errors.py SearchModal")
        print("  python search_errors.py HTTP")
        print("  python search_errors.py --stats")
        print("  python search_errors.py --limit 50")
        sys.exit(1)
    
    # Search
    results = search_errors(search_term, limit)
    
    print(f"\n=== SEARCH RESULTS for '{search_term}' ({len(results)} matches) ===\n")
    for result in results:
        print(result)
    
    if not results:
        print("No matches found.")
