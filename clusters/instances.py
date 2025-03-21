import os
import environ

class InstanceConfig:
    _initialized = False

    def __init__(self):
        if not self._initialized:
            self.env = environ.Env(DEBUG=(bool, False))
            BASE_DIR = os.getcwd()
            environ.Env.read_env(os.environ.get("ENV_FILE", os.path.join(BASE_DIR, ".env")))

            # Store the tokens as instance attributes
            self.openrouter_token = self.env("OPENROUTER_TOKEN", default="openrouter")
            self.gigachat_token = self.env("GIGACHAT_TOKEN", default="gigachat")
            self.youtube_api_key = self.env("YOUTUBE_API_KEY", default="youtube_api_key")

            # Mark as initialized to avoid re-initialization
            InstanceConfig._initialized = True

# Create a single instance
config = InstanceConfig()

# Define variables for direct import access
openrouter_token = config.openrouter_token
gigachat_token = config.gigachat_token
youtube_api_key = config.youtube_api_key
