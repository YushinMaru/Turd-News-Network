"""
Discord embed sending logic
"""

import os
import json
import requests
import time
from typing import List, Dict, Optional
from config import DISCORD_DELAY


class DiscordSender:
    """Handles sending embeds to Discord"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def _sanitize_embed(self, embed: Dict) -> Dict:
        """Sanitize embed to prevent Discord 400 errors"""
        # Remove fields with empty values (Discord rejects these)
        if 'fields' in embed:
            embed['fields'] = [
                f for f in embed['fields']
                if f.get('name') and f.get('value') and str(f['value']).strip()
            ]
            # Discord max: 25 fields per embed
            embed['fields'] = embed['fields'][:25]
            # Truncate field values to Discord limits
            for field in embed['fields']:
                field['name'] = str(field['name'])[:256]
                field['value'] = str(field['value'])[:1024]
        # Truncate title (max 256)
        if embed.get('title'):
            embed['title'] = str(embed['title'])[:256]
        # Truncate description (max 4096)
        if embed.get('description'):
            embed['description'] = str(embed['description'])[:4096]
        return embed

    def send_embeds(self, embeds: List[Dict], title: str) -> bool:
        """Send embeds to Discord (handles chunking for 10 embed limit)"""
        try:
            # Sanitize all embeds before sending
            embeds = [self._sanitize_embed(e) for e in embeds if e]

            # Send in chunks of 10 (Discord limit)
            for i in range(0, len(embeds), 10):
                chunk = embeds[i:i+10]

                payload = {
                    "embeds": chunk,
                    "username": "\U0001f48e WSB DD Monitor Enhanced",
                    "avatar_url": "https://styles.redditmedia.com/t5_2th52/styles/communityIcon_vpjqv2x6avy81.png"
                }

                response = self.session.post(self.webhook_url, json=payload)

                if response.status_code == 204:
                    print(f"\u2705 Sent to Discord: {title[:50]}...")
                else:
                    print(f"\u274c Discord error: {response.status_code} - {response.text}")
                    return False

                # Rate limiting between chunks
                if i + 10 < len(embeds):
                    time.sleep(DISCORD_DELAY)

            return True

        except Exception as e:
            print(f"Error sending to Discord: {e}")
            return False

    def send_embeds_with_files(self, embeds: List[Dict], title: str, file_paths: List[str]) -> bool:
        """
        Send embeds with attached files to Discord via multipart/form-data.
        Each file_path in file_paths is attached and can be referenced in embeds
        via "image": {"url": "attachment://<filename>"}.
        Files are deleted after a successful send.
        """
        try:
            embeds = [self._sanitize_embed(e) for e in embeds if e]

            # Build the JSON payload
            payload_json = {
                "embeds": embeds,
                "username": "\U0001f48e WSB DD Monitor Enhanced",
                "avatar_url": "https://styles.redditmedia.com/t5_2th52/styles/communityIcon_vpjqv2x6avy81.png"
            }

            # Build multipart files dict
            # Discord expects files keyed as files[0], files[1], etc.
            files_dict = {}
            open_handles = []
            for idx, fpath in enumerate(file_paths):
                if not os.path.exists(fpath):
                    continue
                fh = open(fpath, 'rb')
                open_handles.append(fh)
                filename = os.path.basename(fpath)
                files_dict[f'files[{idx}]'] = (filename, fh, 'image/png')

            # payload_json goes as a form field
            form_data = {
                'payload_json': (None, json.dumps(payload_json), 'application/json')
            }

            response = self.session.post(
                self.webhook_url,
                files={**form_data, **files_dict}
            )

            # Close all file handles
            for fh in open_handles:
                fh.close()

            if response.status_code in (200, 204):
                print(f"\u2705 Sent to Discord (with chart): {title[:50]}...")
                # Clean up chart files
                for fpath in file_paths:
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass
                return True
            else:
                print(f"\u274c Discord error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"Error sending to Discord with files: {e}")
            return False
