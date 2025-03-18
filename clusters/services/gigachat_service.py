import os
import requests
import logging
from typing import Optional
from django.conf import settings
from .token_manager import token_manager
import uuid
from clusters.instances import gigachat_token

logger = logging.getLogger(__name__)

class GigaChatService:
    def __init__(self):
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.scope = "GIGACHAT_API_PERS"

    def refresh_token(self) -> Optional[str]:
        try:
            payload = {
                'scope': self.scope
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': str(uuid.uuid4()),
                'Authorization': 'Basic ' + gigachat_token
            }
            response = requests.request("POST", self.auth_url, headers=headers, data=payload, verify=False)
            response.raise_for_status()
            data = response.json()
            access_token = data.get("access_token", "Unknown")
            return access_token
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            return None

    def get_token(self) -> str:
        token = token_manager.get_token()
        if token is None:
            raise ValueError("Unable to obtain valid GigaChat token")
        return token

# Global instance
gigachat_service = GigaChatService() 