import time
import threading
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TokenManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TokenManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.token: Optional[str] = None
            self.last_refresh: Optional[datetime] = None
            self.refresh_interval = timedelta(minutes=30)
            self.initialized = True
            self._refresh_lock = threading.Lock()
            self._gigachat_service = None  # Will be set later to avoid circular import

    def set_gigachat_service(self, service):
        """Set the GigaChat service instance to use for token refresh."""
        self._gigachat_service = service

    def get_token(self) -> Optional[str]:
        """Get the current token, refreshing if necessary."""
        with self._refresh_lock:
            current_time = datetime.now()
            
            # If we have no token or it's time to refresh
            if (self.token is None or 
                self.last_refresh is None or 
                current_time - self.last_refresh >= self.refresh_interval):
                self._refresh_token()
            
            return self.token

    def _refresh_token(self) -> None:
        """Refresh the GigaChat token using the GigaChat service."""
        if self._gigachat_service is None:
            raise RuntimeError("GigaChat service not set. Call set_gigachat_service first.")

        try:
            new_token = self._gigachat_service.refresh_token()
            if new_token:
                self.token = new_token
                self.last_refresh = datetime.now()
                logger.info("Successfully refreshed GigaChat token")
            else:
                logger.error("Failed to get new token from GigaChat service")
                if self.token is None:
                    raise ValueError("Unable to obtain valid GigaChat token")
        except Exception as e:
            logger.error(f"Failed to refresh GigaChat token: {str(e)}")
            if self.token is None:
                raise  # Only raise if we don't have any token

# Global instance
token_manager = TokenManager() 