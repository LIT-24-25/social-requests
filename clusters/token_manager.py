import time
import threading
import logging
from typing import Optional
from datetime import datetime, timedelta
import os
import uuid
import requests
from clusters.instances import gigachat_token

logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.token_path = os.path.join(os.path.dirname(__file__), 'token.txt')
            self.token = None
            self.last_refresh = None
            
            if os.path.exists(self.token_path):
                with open(self.token_path, 'r') as f:
                    lines = f.readlines()
                    if len(lines) >= 2 and lines[0].strip() and lines[1].strip():
                        self.token = lines[0].strip()
                        try:
                            self.last_refresh = datetime.strptime(lines[1].strip(), '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            self.last_refresh = None
            else:
                with open(self.token_path, 'w') as f:
                    f.write('')
            self.refresh_interval = timedelta(minutes=30)
            self.initialized = True

    def get_token(self) -> Optional[str]:
        """Get the current token, refreshing if necessary."""
        current_time = datetime.now()
        
        if (self.token is None or (self.last_refresh is None) or (current_time - self.last_refresh >= self.refresh_interval)):
            self.refresh_token()
        
        return self.token

    def refresh_token(self) -> None:
        try:
            payload = {
                'scope': 'GIGACHAT_API_PERS'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': str(uuid.uuid4()),
                'Authorization': 'Basic ' + gigachat_token
            }
            response = requests.request("POST", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth", headers=headers, data=payload, verify=False)
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token", "Unknown")
            self.last_refresh = datetime.now()
        except:
            self.token = "Unknown"
            self.last_refresh = datetime.now()
        with open(self.token_path, 'w') as f:
            f.write(self.token + '\n')
            f.write(self.last_refresh.strftime('%Y-%m-%d %H:%M:%S'))
        logger.info("Successfully refreshed GigaChat token")

# Global instance
token_manager = TokenManager() 