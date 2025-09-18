from fastapi import HTTPException
import asyncio

from app.ingestion import ingestion_service, kotak_subscriber
from app.ingestion.models import KotakAuthRequest

async def start_ingestion(auth_request: KotakAuthRequest):
    """Start ingestion with Kotak Neo authentication"""
    if ingestion_service.is_running:
        return {"status": "info", "message": "Ingestion already running"}

    # Step 1: Authenticate with Kotak Neo
    auth_result = kotak_subscriber.authenticate(auth_request.totp_code, auth_request.mpin)
    if not auth_result["success"]:
        raise HTTPException(status_code=401, detail=auth_result["error"])

    # Step 2: Set up message callback BEFORE subscribing
    kotak_subscriber.set_message_callback(ingestion_service.queue_websocket_message)

    # Step 3: Subscribe to instruments
    instruments_to_use = []
    if auth_request.instruments and len(auth_request.instruments) > 0:
        # Convert pydantic models to dicts for the subscriber
        instruments_to_use = [
            {
                "instrument_token": inst.instrument_token,
                "exchange_segment": inst.exchange_segment
            }
            for inst in auth_request.instruments
        ]

    subscribe_result = kotak_subscriber.subscribe_to_instruments(instruments_to_use if instruments_to_use else None)
    if not subscribe_result["success"]:
        raise HTTPException(status_code=400, detail=subscribe_result["error"])

    # Step 4: Start WebSocket ingestion
    asyncio.create_task(ingestion_service.start_websocket_ingestion())

    return {
        "status": "success",
        "message": "Authentication successful, subscribed to feed, and ingestion started!",
        "auth": auth_result,
        "subscription": subscribe_result
    }

async def stop_ingestion():
    await ingestion_service.stop_ingestion()
    return {"status": "success", "message": "Ingestion stopped"}

async def get_ingestion_status():
    stats = await ingestion_service.get_stats()
    return stats