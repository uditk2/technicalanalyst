import os
from dotenv import load_dotenv

load_dotenv()

class IngestionConfig:
    def __init__(self):
        self.kotak_environment = os.getenv("KOTAK_ENVIRONMENT", "prod")
        self.kotak_ucc = os.getenv("KOTAK_UCC")
        self.kotak_consumer_key = os.getenv("KOTAK_CONSUMER_KEY")
        self.kotak_consumer_secret = os.getenv("KOTAK_CONSUMER_SECRET")
        self.kotak_neo_fin_key = os.getenv("KOTAK_NEO_FIN_KEY")
        self.kotak_mobile_number = os.getenv("KOTAK_MOBILE_NUMBER")
        self.buffer_flush_interval = int(os.getenv("BUFFER_FLUSH_INTERVAL", "3"))

ingestion_config = IngestionConfig()