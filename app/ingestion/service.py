import asyncio
import json
import time
import queue
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import re
import logging

from app.database import SessionLocal, StockFeed, IngestionStats
from .config import ingestion_config
from .kotak_subscriber import kotak_subscriber

logger = logging.getLogger(__name__)

class DataBuffer:
    def __init__(self):
        self.buffer: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()

    async def add(self, data: Dict[str, Any]):
        async with self.lock:
            self.buffer.append(data)

    async def flush(self) -> List[Dict[str, Any]]:
        async with self.lock:
            data = self.buffer.copy()
            self.buffer.clear()
            return data

    async def size(self) -> int:
        async with self.lock:
            return len(self.buffer)

class StockFeedIngestionService:
    """
    Stock feed ingestion service with async processing and thread-safe WebSocket bridge.

    Architecture:
    WebSocket (sync) -> message_queue -> async processing -> buffer -> database
    """
    def __init__(self):
        self.buffer = DataBuffer()
        self.message_queue = queue.Queue()  # Thread-safe bridge for WebSocket messages
        self.is_running = False
        self.total_processed = 0
        self.feed_source = "websocket"

    def parse_feed_data(self, raw_line: str) -> Optional[List[Dict[str, Any]]]:
        try:
            if raw_line.startswith('[Res]:'):
                json_part = raw_line[6:].strip()
                data = json.loads(json_part)

                if data.get('type') == 'stock_feed' and 'data' in data:
                    parsed_items = []

                    # Process all data items, not just the first one
                    for feed_data in data['data']:
                        parsed_data = {
                            'timestamp': datetime.now(timezone.utc),
                            'symbol': feed_data.get('ts'),  # Use 'ts' (trading symbol) as symbol
                            'token': feed_data.get('tk'),
                            'exchange': feed_data.get('e'),
                            'ltp': float(feed_data.get('ltp', 0)) if feed_data.get('ltp') else None,
                            'ltq': int(feed_data.get('ltq', 0)) if feed_data.get('ltq') else None,
                            'volume': int(feed_data.get('v', 0)) if feed_data.get('v') else None,
                            'turnover': float(feed_data.get('to', 0)) if feed_data.get('to') else None,
                            'change_amount': float(feed_data.get('cng', 0)) if feed_data.get('cng') else None,
                            'change_percent': float(feed_data.get('nc', 0)) if feed_data.get('nc') else None,
                            'bid_price': float(feed_data.get('bp', 0)) if feed_data.get('bp') else None,
                            'ask_price': float(feed_data.get('sp', 0)) if feed_data.get('sp') else None,
                            'bid_qty': int(feed_data.get('bq', 0)) if feed_data.get('bq') else None,
                            'ask_qty': int(feed_data.get('bs', 0)) if feed_data.get('bs') else None,
                            'total_buy_qty': int(feed_data.get('tbq', 0)) if feed_data.get('tbq') else None,
                            'total_sell_qty': int(feed_data.get('tsq', 0)) if feed_data.get('tsq') else None,
                            'raw_data': feed_data
                        }

                        if feed_data.get('ltt'):
                            try:
                                parsed_data['last_trade_time'] = datetime.strptime(
                                    feed_data['ltt'], '%d/%m/%Y %H:%M:%S'
                                ).replace(tzinfo=timezone.utc)
                            except:
                                pass

                        if feed_data.get('fdtm'):
                            try:
                                parsed_data['feed_time'] = datetime.strptime(
                                    feed_data['fdtm'], '%d/%m/%Y %H:%M:%S'
                                ).replace(tzinfo=timezone.utc)
                            except:
                                pass

                        parsed_items.append(parsed_data)

                    return parsed_items if parsed_items else None

        except Exception as e:
            logger.error(f"Error parsing feed data: {e}")

        return None

    async def _process_queued_messages(self):
        """Process all queued messages from WebSocket"""
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                await self.process_websocket_message(message)
            except queue.Empty:
                break

    def queue_websocket_message(self, message: str):
        """Thread-safe method to queue messages from WebSocket callback (sync)"""
        try:
            self.message_queue.put_nowait(message)
            print(f"[DEBUG] Queued message: {message[:100]}...")
        except queue.Full:
            logger.warning("Message queue full, dropping message")

    async def process_websocket_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            print(f"[DEBUG] Processing WebSocket message: {message[:200]}...")
            parsed_items = self.parse_feed_data(message)
            if parsed_items:
                # Handle multiple items from the same message
                if isinstance(parsed_items, list):
                    for item in parsed_items:
                        await self.buffer.add(item)
                        print(f"[DEBUG] Added to buffer: {item.get('symbol', 'unknown')} - {item.get('token', 'unknown')}")
                    logger.info(f"Added {len(parsed_items)} items to buffer")
                else:
                    await self.buffer.add(parsed_items)
                    print(f"[DEBUG] Added to buffer: {parsed_items.get('symbol', 'unknown')} - {parsed_items.get('token', 'unknown')}")
                    logger.info(f"Added 1 item to buffer")
            else:
                print(f"[DEBUG] Failed to parse message")
        except Exception as e:
            print(f"[DEBUG] Error processing WebSocket message: {e}")
            logger.error(f"Error processing WebSocket message: {e}")

    async def process_file_data(self, file_path: str):
        """Process data from file (for testing/demo purposes)"""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parsed_data = self.parse_feed_data(line)
                        if parsed_data:
                            await self.buffer.add(parsed_data)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")

    async def flush_buffer_to_db(self):
        start_time = time.time()
        buffer_size = await self.buffer.size()
        data_to_insert = await self.buffer.flush()

        print(f"[DEBUG] Flush attempt: buffer_size={buffer_size}, data_to_insert={len(data_to_insert) if data_to_insert else 0}")

        if not data_to_insert:
            return

        async with SessionLocal() as session:
            try:
                for data in data_to_insert:
                    stock_feed = StockFeed(**data)
                    session.add(stock_feed)

                await session.commit()
                print(f"[DEBUG] Successfully committed {len(data_to_insert)} records to database")

                processing_time = int((time.time() - start_time) * 1000)

                result = await session.execute(
                    select(IngestionStats).order_by(IngestionStats.id.desc()).limit(1)
                )
                stats = result.scalar_one_or_none()

                if stats:
                    old_total = stats.records_processed
                    stats.records_processed += len(data_to_insert)
                    stats.last_processed_at = datetime.now(timezone.utc)
                    stats.batch_size = len(data_to_insert)
                    stats.processing_time_ms = processing_time
                    print(f"[DEBUG] Updated stats: {old_total} -> {stats.records_processed}")
                else:
                    new_stats = IngestionStats(
                        records_processed=len(data_to_insert),
                        last_processed_at=datetime.now(timezone.utc),
                        batch_size=len(data_to_insert),
                        processing_time_ms=processing_time
                    )
                    session.add(new_stats)
                    print(f"[DEBUG] Created new stats record: {len(data_to_insert)} records")

                await session.commit()
                self.total_processed += len(data_to_insert)
                logger.info(f"Inserted {len(data_to_insert)} records in {processing_time}ms")

            except Exception as e:
                await session.rollback()
                print(f"[DEBUG] Database error: {e}")
                logger.error(f"Error inserting data: {e}")

    async def start_websocket_ingestion(self):
        """Start ingestion from WebSocket feed"""
        if self.is_running:
            return

        self.is_running = True
        self.feed_source = "websocket"
        logger.info("Starting WebSocket stock feed ingestion service...")

        try:
            while self.is_running:
                await self._process_queued_messages()
                await self.flush_buffer_to_db()
                await asyncio.sleep(ingestion_config.buffer_flush_interval)

        except Exception as e:
            logger.error(f"Error in WebSocket ingestion service: {e}")
        finally:
            self.is_running = False

    async def start_file_ingestion(self, file_path: str):
        """Start ingestion from file (for testing)"""
        if self.is_running:
            return

        self.is_running = True
        self.feed_source = "file"
        logger.info(f"Starting file-based stock feed ingestion service from {file_path}...")

        try:
            await self.process_file_data(file_path)

            while self.is_running:
                await self.flush_buffer_to_db()
                await asyncio.sleep(ingestion_config.buffer_flush_interval)

        except Exception as e:
            logger.error(f"Error in file ingestion service: {e}")
        finally:
            self.is_running = False

    async def stop_ingestion(self):
        self.is_running = False
        await self.flush_buffer_to_db()

        # Unsubscribe from WebSocket if using WebSocket source
        if self.feed_source == "websocket":
            kotak_subscriber.unsubscribe_from_instruments()

        logger.info("Stock feed ingestion service stopped")

    async def get_stats(self) -> Dict[str, Any]:
        async with SessionLocal() as session:
            result = await session.execute(
                select(IngestionStats).order_by(IngestionStats.id.desc()).limit(1)
            )
            stats = result.scalar_one_or_none()

            if stats:
                return {
                    'total_processed': stats.records_processed,
                    'last_processed_at': stats.last_processed_at.isoformat() if stats.last_processed_at else None,
                    'last_batch_size': stats.batch_size,
                    'last_processing_time_ms': stats.processing_time_ms,
                    'buffer_size': await self.buffer.size(),
                    'is_running': self.is_running,
                    'feed_source': self.feed_source,
                    'websocket_status': kotak_subscriber.get_status()
                }
            else:
                return {
                    'total_processed': 0,
                    'last_processed_at': None,
                    'last_batch_size': 0,
                    'last_processing_time_ms': 0,
                    'buffer_size': await self.buffer.size(),
                    'is_running': self.is_running,
                    'feed_source': self.feed_source,
                    'websocket_status': kotak_subscriber.get_status()
                }

ingestion_service = StockFeedIngestionService()