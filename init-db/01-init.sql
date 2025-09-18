-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create stock_feeds table
CREATE TABLE stock_feeds (
    id SERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol VARCHAR(50),
    token VARCHAR(20),
    exchange VARCHAR(20),
    ltp DECIMAL(15,2),
    ltq INTEGER,
    volume BIGINT,
    turnover DECIMAL(20,2),
    change_amount DECIMAL(15,2),
    change_percent DECIMAL(8,4),
    bid_price DECIMAL(15,2),
    ask_price DECIMAL(15,2),
    bid_qty INTEGER,
    ask_qty INTEGER,
    total_buy_qty BIGINT,
    total_sell_qty BIGINT,
    last_trade_time TIMESTAMPTZ,
    feed_time TIMESTAMPTZ,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('stock_feeds', 'timestamp');

-- Create indexes
CREATE INDEX idx_stock_feeds_symbol_time ON stock_feeds (symbol, timestamp DESC);
CREATE INDEX idx_stock_feeds_token_time ON stock_feeds (token, timestamp DESC);
CREATE INDEX idx_stock_feeds_exchange ON stock_feeds (exchange);

-- Create ingestion stats table
CREATE TABLE ingestion_stats (
    id SERIAL PRIMARY KEY,
    records_processed BIGINT DEFAULT 0,
    last_processed_at TIMESTAMPTZ,
    batch_size INTEGER,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert initial stats record
INSERT INTO ingestion_stats (records_processed, last_processed_at) VALUES (0, NOW());