
# Enable ANSI colors on Windows
import os
import sys
if sys.platform == 'win32':
    os.system('color')  # Enable ANSI support in Windows Command Prompt
"""
Console output formatter with colors - NO EMOJIS for Windows compatibility
"""

import sys
import platform

IS_WINDOWS = platform.system() == 'Windows'

# Enable ANSI colors on Windows
if IS_WINDOWS:
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass


class Colors:
    """ANSI color codes for console output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    MAGENTA = '\033[35m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    @staticmethod
    def success(text):
        return f"{Colors.GREEN}{text}{Colors.END}"
    
    @staticmethod
    def error(text):
        return f"{Colors.RED}{text}{Colors.END}"
    
    @staticmethod
    def warning(text):
        return f"{Colors.YELLOW}{text}{Colors.END}"
    
    @staticmethod
    def info(text):
        return f"{Colors.CYAN}{text}{Colors.END}"
    
    @staticmethod
    def bold(text):
        return f"{Colors.BOLD}{text}{Colors.END}"
    
    @staticmethod
    def header(text):
        return f"{Colors.BOLD}{Colors.MAGENTA}{text}{Colors.END}"


# Simple ASCII symbols - NO EMOJIS
SYMBOLS = {
    'check': '[OK]',
    'cross': '[X]',
    'warning': '[!]',
    'info': '[i]',
    'arrow': '->',
    'bullet': '*',
    'rocket': '[^]',
    'chart': '[#]',
    'money': '[$]',
    'fire': '[*]',
    'target': '[O]',
}


def print_banner():
    """Print startup banner"""
    banner = f"""
{Colors.BOLD}{Colors.CYAN}{'='*70}
  WSB MONITOR ENHANCED v4.0 - Reddit DD Tracker with AI
  {SYMBOLS['rocket']} Momentum Scoring | {SYMBOLS['chart']} Compact Embeds | {SYMBOLS['money']} AI Recommendations
{'='*70}{Colors.END}
"""
    print(banner)


def print_separator(char="=", length=70):
    """Print a separator line"""
    print(f"{Colors.GRAY}{char * length}{Colors.END}")


def print_section_header(title):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'-' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'-' * 70}{Colors.END}")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}{SYMBOLS['check']} {message}{Colors.END}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}{SYMBOLS['cross']} {message}{Colors.END}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}{SYMBOLS['warning']} {message}{Colors.END}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.CYAN}{SYMBOLS['info']} {message}{Colors.END}")


def print_stat(label, value, color=None):
    """Print a statistic"""
    if color:
        print(f"{Colors.GRAY}   {label}:{Colors.END} {color}{value}{Colors.END}")
    else:
        print(f"{Colors.GRAY}   {label}:{Colors.END} {Colors.WHITE}{value}{Colors.END}")


def print_processing(ticker, title):
    """Print processing header for a stock"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{SYMBOLS['chart']} Processing:{Colors.END} {Colors.WHITE}{title[:60]}{Colors.END}")
    print(f"{Colors.GRAY}   Ticker: {Colors.END}{Colors.BOLD}{Colors.GREEN}${ticker}{Colors.END}")


def print_scrape_result(subreddit, count):
    """Print scraping result"""
    if count > 0:
        print(f"{Colors.GREEN}   {SYMBOLS['check']} r/{subreddit}: {count} posts{Colors.END}")
    else:
        print(f"{Colors.GRAY}   - r/{subreddit}: 0 posts{Colors.END}")
