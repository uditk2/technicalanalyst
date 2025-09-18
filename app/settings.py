import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Database settings
        self.database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/stockfeed")

        # App settings
        self.api_poll_interval = int(os.getenv("API_POLL_INTERVAL", "10"))

settings = Settings()