from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import text, DECIMAL, Integer, String, BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional
import json

from .config import db_settings

engine = create_async_engine(db_settings.database_url, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class StockFeed(Base):
    __tablename__ = "stock_feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    symbol: Mapped[Optional[str]] = mapped_column(String(50))
    token: Mapped[Optional[str]] = mapped_column(String(20))
    exchange: Mapped[Optional[str]] = mapped_column(String(20))
    ltp: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2))
    ltq: Mapped[Optional[int]] = mapped_column(Integer)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    turnover: Mapped[Optional[float]] = mapped_column(DECIMAL(20, 2))
    change_amount: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2))
    change_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(8, 4))
    bid_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2))
    ask_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 2))
    bid_qty: Mapped[Optional[int]] = mapped_column(Integer)
    ask_qty: Mapped[Optional[int]] = mapped_column(Integer)
    total_buy_qty: Mapped[Optional[int]] = mapped_column(BigInteger)
    total_sell_qty: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_trade_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    feed_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class IngestionStats(Base):
    __tablename__ = "ingestion_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    records_processed: Mapped[int] = mapped_column(BigInteger, default=0)
    last_processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    batch_size: Mapped[Optional[int]] = mapped_column(Integer)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

async def get_session():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)