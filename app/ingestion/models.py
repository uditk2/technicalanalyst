from pydantic import BaseModel
from typing import Optional, List

class InstrumentConfig(BaseModel):
    instrument_token: str
    exchange_segment: str
    name: str

class KotakAuthRequest(BaseModel):
    totp_code: str
    mpin: Optional[str] = None
    instruments: Optional[List[InstrumentConfig]] = None

class IngestionStats(BaseModel):
    total_processed: int
    last_processed_at: Optional[str] = None
    last_batch_size: int
    last_processing_time_ms: int
    buffer_size: int
    is_running: bool
    feed_source: str
    websocket_status: dict