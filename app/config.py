"""
config.py — App Configuration
==============================
CONCEPT: pydantic-settings

Instead of os.environ.get() scattered everywhere, we define all settings
in one place. Pydantic reads from your .env file automatically.

Why AI engineers need this:
  - Model paths, API keys, batch sizes — all go here
  - Easy to swap between dev/prod environments
  - Type-safe: if MODEL_BATCH_SIZE should be an int, pydantic enforces it
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # pydantic-settings reads these from your .env file
    # The field name (lowercase) maps to the .env key (uppercase)
    app_name: str = "AI Model Serving API"
    api_key: str = "test-key-123"          # In prod, load from secrets manager
    environment: str = "development"
    max_input_length: int = 2000

    # In a real AI app, you'd add things like:
    # model_path: str = "/models/llm-7b"
    # device: str = "cuda"
    # batch_size: int = 32
    # openai_api_key: str = ""

    # Tell pydantic-settings to read from .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Create a single shared instance — import this everywhere
# This is the "singleton settings" pattern used in production FastAPI apps
settings = Settings()
