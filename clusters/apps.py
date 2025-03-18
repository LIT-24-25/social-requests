from django.apps import AppConfig
from django.conf import settings


class ClustersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clusters'

    def ready(self):
        from .token_manager import token_manager
        # This will initialize the token manager when Django starts
        token_manager.get_token()