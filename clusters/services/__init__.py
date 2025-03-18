from .token_manager import token_manager
from .gigachat_service import gigachat_service

# Set up circular dependency
token_manager.set_gigachat_service(gigachat_service)

# Export the instances
__all__ = ['token_manager', 'gigachat_service'] 