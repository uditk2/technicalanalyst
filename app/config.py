import os
from dotenv import load_dotenv

load_dotenv()

class AppSettings:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/stockfeed")
        self.api_poll_interval = int(os.getenv("API_POLL_INTERVAL", "10"))

app_settings = AppSettings()