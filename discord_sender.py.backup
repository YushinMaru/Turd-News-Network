"""
Discord embed sending logic
"""

import requests
import time
from typing import List, Dict
from config import DISCORD_DELAY


class DiscordSender:
    """Handles sending embeds to Discord"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()
    
    def send_embeds(self, embeds: List[Dict], title: str) -> bool:
        """Send embeds to Discord (handles chunking for 10 embed limit)"""
        try:
            # Send in chunks of 10 (Discord limit)
            for i in range(0, len(embeds), 10):
                chunk = embeds[i:i+10]
                
                payload = {
                    "embeds": chunk,
                    "username": "Ã°Å¸â€™Å½ WSB DD Monitor Enhanced",
                    "avatar_url": "https://styles.redditmedia.com/t5_2th52/styles/communityIcon_vpjqv2x6avy81.png"
                }
                
                response = self.session.post(self.webhook_url, json=payload)
                
                if response.status_code == 204:
                    print(f"Ã¢Å“â€¦ Sent to Discord: {title[:50]}...")
                else:
                    print(f"Ã¢ÂÅ’ Discord error: {response.status_code} - {response.text}")
                    return False
                
                # Rate limiting between chunks
                if i + 10 < len(embeds):
                    time.sleep(DISCORD_DELAY)
            
            return True
            
        except Exception as e:
            print(f"Error sending to Discord: {e}")
            return False
