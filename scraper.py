"""
Reddit scraping and DD detection
"""

import requests
import re
import time
import hashlib
from typing import List, Dict, Set
from datetime import datetime
from config import *

try:
    from console_formatter import print_scrape_result
    HAS_FORMATTER = True
except:
    HAS_FORMATTER = False


class RedditScraper:
    """Handles Reddit scraping and DD detection"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    def scrape_subreddit(self, subreddit: str, limit: int = 25) -> List[Dict]:
        """Scrape posts from a subreddit with enhanced metadata"""
        posts = []
        try:
            url = f"https://old.reddit.com/r/{subreddit}/new/.json?limit={limit}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                for post in data['data']['children']:
                    try:
                        post_data = post['data']
                        
                        post_id = post_data.get('id', '')
                        if not post_id:
                            continue
                        
                        selftext = post_data.get('selftext', '')
                        title = post_data.get('title', '')
                        
                        if not title:
                            continue
                        
                        # Check if it's DD-related
                        if self.is_dd_post(
                            title,
                            post_data.get('link_flair_text'),
                            selftext
                        ):
                            enhanced_post = {
                                'id': post_id,
                                'title': title,
                                'selftext': selftext,
                                'url': f"https://reddit.com{post_data.get('permalink', '')}",
                                'subreddit': subreddit,
                                'flair': post_data.get('link_flair_text', ''),
                                'score': post_data.get('score', 0),
                                'num_comments': post_data.get('num_comments', 0),
                                'upvote_ratio': post_data.get('upvote_ratio', 0),
                                'author': post_data.get('author', 'Unknown'),
                                'created_utc': datetime.fromtimestamp(
                                    post_data.get('created_utc', 0)
                                ).isoformat(),
                                'post_length': len(selftext)
                            }
                            
                            posts.append(enhanced_post)
                    
                    except Exception as post_error:
                        print(f"   ⚠️  Skipped problematic post in r/{subreddit}: {post_error}")
                        continue
                
                print(f"[OK] Scraped r/{subreddit}: {len(posts)} DD posts found")
            else:
                print(f"❌ Error scraping r/{subreddit}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error scraping r/{subreddit}: {e}")
        
        return posts
    
    def scrape_all_subreddits(self, delay: int = SCRAPE_DELAY) -> List[Dict]:
        """Scrape all configured subreddits"""
        all_posts = []
        
        for subreddit in SUBREDDITS:
            posts = self.scrape_subreddit(subreddit, limit=25)
            all_posts.extend(posts)
            time.sleep(delay)
        
        return all_posts
    
    def is_dd_post(self, title: str, flair: str, selftext: str) -> bool:
        """Check if post is DD-related and not a loss post"""
        title = title or ""
        flair = flair or ""
        selftext = selftext or ""
        
        title_lower = title.lower()
        text_lower = selftext.lower()
        combined = title_lower + ' ' + text_lower
        
        # Exclude loss posts
        for exclude in EXCLUDE_KEYWORDS:
            if exclude in combined:
                return False
        
        # Check flair
        if flair:
            flair_lower = flair.lower()
            for dd_flair in DD_FLAIRS:
                if dd_flair.lower() in flair_lower:
                    return True
        
        # Check title for DD keywords
        for keyword in DD_KEYWORDS:
            if keyword.lower() in title_lower:
                return True
        
        # For longer posts, check analysis keywords
        if len(selftext) > 500:
            analysis_words = ['analysis', 'research', 'fundamentals', 'valuation', 'revenue', 'earnings']
            if any(word in text_lower for word in analysis_words):
                return True
        
        return False
    
    def extract_tickers(self, text: str) -> Set[str]:
        """Extract stock tickers from text"""
        tickers = set()
        
        # Pattern 1: $TICKER format (most reliable)
        dollar_tickers = re.findall(r'\$([A-Z]{2,5})\b', text)
        tickers.update(dollar_tickers)
        
        # Pattern 2: Standalone uppercase words (2-5 letters only, avoid single letters)
        words = re.findall(r'\b([A-Z]{2,5})\b', text)
        for word in words:
            if word not in IGNORE_TICKERS and len(word) >= 2:
                tickers.add(word)
        
        return tickers
    
    def generate_content_hash(self, text: str) -> str:
        """Generate hash for duplicate detection"""
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()
