# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based stock feed ingestion service that collects real-time stock data from Kotak Neo WebSocket API and stores it in TimescaleDB. The application provides both web UI and REST API endpoints for monitoring and managing stock data ingestion with TOTP authentication.

## Development Commands

### Docker Development (Recommended)
```bash
# Start all services (TimescaleDB, Redis, FastAPI app)
docker-compose up -d

# Access the application
open http://localhost:8000

# View application logs
docker-compose logs -f app

# View database logs
docker-compose logs -f timescaledb

# Stop all services
docker-compose down

# Rebuild and restart after code changes
docker-compose build app && docker-compose up -d app

# Connect to database directly
docker exec -it timescaledb psql -U postgres -d stockfeed
```

### Manual Python Development
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (note: neo-api-client requires specific versions)
pip install -r requirements.txt

# Run database (TimescaleDB) separately via Docker
docker-compose up -d timescaledb redis

# Run the application with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Check dependency compatibility (if issues arise)
python check_deps.py
```

### Database Management
```bash
# Initialize database schema
docker-compose exec timescaledb psql -U postgres -d stockfeed -f /docker-entrypoint-initdb.d/01-init.sql

# View hypertables
docker-compose exec timescaledb psql -U postgres -d stockfeed -c "SELECT * FROM timescaledb_information.hypertables;"

# Query recent stock data
docker-compose exec timescaledb psql -U postgres -d stockfeed -c "SELECT symbol, ltp, timestamp FROM stock_feeds ORDER BY timestamp DESC LIMIT 10;"
```

## Architecture

### Application Structure
```
app/
├── main.py                    # FastAPI app initialization, route inclusion
├── settings.py               # Global application settings and environment config
├── database/
│   ├── __init__.py           # Database exports and initialization
│   ├── config.py             # Database configuration (aliases settings)
│   └── models.py             # SQLAlchemy models (StockFeed, IngestionStats)
├── ingestion/
│   ├── __init__.py           # Ingestion service exports
│   ├── config.py             # Kotak API credentials and ingestion settings
│   ├── models.py             # Pydantic models for API requests
│   ├── service.py            # Core ingestion service with buffering
│   └── kotak_subscriber.py   # WebSocket client for Kotak Neo API
├── routes/
│   ├── __init__.py           # Routes exports
│   ├── web.py                # HTML page routes (root, instruments page)
│   ├── ingestion.py          # Ingestion control API (start/stop/status)
│   └── instruments.py        # Instrument management API (search/validate)
├── config/
│   ├── __init__.py           # Config exports
│   └── instruments.py        # Instrument registry and search functionality
├── static/
│   ├── css/theme.css         # Application styling with CSS variables
│   └── js/
│       ├── theme.js          # Theme utilities and API client
│       ├── autocomplete.js   # Instrument autocomplete functionality
│       └── instruments.js    # Instrument selection logic
├── templates/
│   ├── base.html             # Base template with navigation and theming
│   ├── index.html            # Main ingestion dashboard
│   └── instruments.html      # Instrument selection interface
└── data/
    └── instruments.json      # Static instrument database
```

### Core Components

1. **FastAPI Application** (`app/main.py`)
   - Main entry point with startup events (database initialization)
   - Route inclusion for web and API endpoints
   - Static file serving for CSS/JS assets
   - Unified error handling

2. **Database Layer** (`app/database/`)
   - **models.py**: SQLAlchemy 2.0 async models with TimescaleDB optimization
     - `StockFeed`: Main time-series table with market data + JSONB raw_data
     - `IngestionStats`: Processing metrics and performance tracking
   - **config.py**: Database connection settings
   - Async session factory with connection pooling
   - Database initialization with hypertable creation

3. **Ingestion Service** (`app/ingestion/`)
   - **service.py**: `StockFeedIngestionService` - Core processing engine
     - Thread-safe message queue bridging sync WebSocket to async processing
     - Buffered batch processing with configurable flush intervals
     - Feed parsing from Kotak Neo format to database schema
     - Statistics tracking and error handling
   - **kotak_subscriber.py**: `KotakNeoSubscriber` - WebSocket client
     - TOTP authentication with Kotak Neo API
     - Instrument subscription/unsubscription management
     - Real-time message callback handling
   - **config.py**: Environment-based configuration for API credentials
   - **models.py**: Pydantic models for authentication requests

4. **API Routes** (`app/routes/`)
   - **web.py**: Server-side rendered pages using Jinja2 templates
   - **instruments.py**: RESTful API for instrument management
     - Search, autocomplete, validation endpoints
     - Sector and exchange filtering
     - Preset subscription sets (Nifty 50, top 10, indices)
   - **ingestion.py**: Ingestion control endpoints
     - Start/stop ingestion with authentication
     - Real-time status and statistics

5. **Configuration** (`app/config/`)
   - **instruments.py**: `InstrumentRegistry` - Instrument database management
     - JSON-based instrument database (`app/data/instruments.json`)
     - Search by symbol, company name, sector
     - Kotak API format conversion
     - Exchange segment and sector management

### Data Flow Architecture

```
TOTP Auth → WebSocket Subscribe → Real-time Feed → Buffer → TimescaleDB
     ↓              ↓                    ↓           ↓         ↓
  Kotak Neo  →  Subscription     →   Message   →  Batch  →  Hypertable
   Mobile        Management         Processing     Insert     Storage
```

1. **Authentication**: TOTP from Kotak Neo mobile app + optional MPIN
2. **Subscription**: Instrument selection via web UI or API
3. **Real-time Data**: WebSocket receives JSON feed data
4. **Processing**: Parse, validate, and buffer feed messages
5. **Storage**: Batch insert to TimescaleDB hypertable
6. **Monitoring**: Live dashboard with real-time statistics

### Key Dependencies & Compatibility

```txt
# Core Framework
fastapi==0.103.2              # Web framework (pinned for neo-api-client compatibility)
uvicorn==0.14.0               # ASGI server (compatible with websockets 8.1)
pydantic==1.10.12             # Data validation (v1 for compatibility)

# Database & Async
sqlalchemy==2.0.23            # Modern async ORM
asyncpg==0.29.0               # PostgreSQL async driver

# Kotak API Integration
websockets==8.1               # Required by neo-api-client (CRITICAL VERSION)
neo-api-client                # Kotak Neo WebSocket API (from GitHub)

# Additional Features
python-multipart==0.0.6       # Form handling
pyotp==2.9.0                  # TOTP authentication
qrcode[pil]==7.4.2            # QR code generation
jinja2==3.1.2                 # Template engine
aiofiles==23.2.1              # Async file operations
```

## Environment Configuration

### Required Environment Variables

Create `.env` file (see `.env.example`):

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@timescaledb:5432/stockfeed
REDIS_URL=redis://redis:6379/0

# Kotak Neo API Credentials (REQUIRED)
KOTAK_ENVIRONMENT=prod
KOTAK_UCC=your_ucc
KOTAK_CONSUMER_KEY=your_consumer_key
KOTAK_CONSUMER_SECRET=your_consumer_secret
KOTAK_NEO_FIN_KEY=your_neo_fin_key
KOTAK_MOBILE_NUMBER=your_mobile_number

# Application Configuration
BUFFER_FLUSH_INTERVAL=3       # Seconds between database flushes
API_POLL_INTERVAL=10          # Frontend polling interval (seconds)
```

### Getting Kotak Neo Credentials

1. Register at [Kotak Neo API](https://github.com/Kotak-Neo/Kotak-neo-api-v2)
2. Generate API credentials in developer portal
3. Install Kotak Neo mobile app for TOTP codes
4. Use mobile app's 6-digit TOTP codes for authentication

## Database Schema

### TimescaleDB Tables

**stock_feeds** (Hypertable partitioned by timestamp):
```sql
- id: SERIAL PRIMARY KEY
- timestamp: TIMESTAMPTZ (partition key)
- symbol: VARCHAR(50) (trading symbol)
- token: VARCHAR(20) (instrument token)
- exchange: VARCHAR(20) (exchange segment)
- ltp: DECIMAL(15,2) (last traded price)
- ltq: INTEGER (last traded quantity)
- volume: BIGINT (total volume)
- turnover: DECIMAL(20,2) (total turnover)
- change_amount: DECIMAL(15,2) (price change)
- change_percent: DECIMAL(8,4) (percentage change)
- bid_price/ask_price: DECIMAL(15,2) (order book)
- bid_qty/ask_qty: INTEGER (order quantities)
- total_buy_qty/total_sell_qty: BIGINT (market depth)
- last_trade_time: TIMESTAMPTZ (last trade timestamp)
- feed_time: TIMESTAMPTZ (feed generation timestamp)
- raw_data: JSONB (complete feed data)
- created_at: TIMESTAMPTZ (record insertion time)
```

**ingestion_stats** (Processing metrics):
```sql
- id: SERIAL PRIMARY KEY
- records_processed: BIGINT (cumulative count)
- last_processed_at: TIMESTAMPTZ (last successful batch)
- batch_size: INTEGER (last batch size)
- processing_time_ms: INTEGER (last batch processing time)
- created_at: TIMESTAMPTZ (stats record creation)
```

### Indexes & Optimization
```sql
- Primary index: timestamp (hypertable partitioning)
- Symbol-time index: (symbol, timestamp DESC) for symbol queries
- Token-time index: (token, timestamp DESC) for token queries
- Exchange index: (exchange) for filtering by exchange
```

## Instrument Management

### Instrument Registry (`app/config/instruments.py`)

The `InstrumentRegistry` class provides comprehensive instrument management:

**Core Features:**
- JSON-based instrument database (`app/data/instruments.json`)
- Search by symbol, company name, or sector
- Exchange segment filtering (NSE_CM, BSE_CM, NSE_FO, etc.)
- Sector-based categorization
- Kotak API format conversion

**API Endpoints:**
```
GET /api/instruments/search?query=RELIANCE&limit=10
GET /api/instruments/autocomplete?query=TCS
GET /api/instruments/all
GET /api/instruments/sectors
GET /api/instruments/exchanges
GET /api/instruments/sector/banking
GET /api/instruments/token/11536
POST /api/instruments/validate
POST /api/instruments/format-for-subscription
GET /api/instruments/nifty50-subscription
GET /api/instruments/quick-subscription/nifty50
```

**Predefined Sets:**
- **Nifty 50**: All constituent stocks for broad market coverage
- **Indices**: Major indices (Nifty 50, Bank Nifty)
- **Top 10**: Highest market cap stocks
- **Custom**: User-selected instrument combinations

## Ingestion Process

### Authentication Flow
1. User enters 6-digit TOTP from Kotak Neo mobile app
2. Optional MPIN for 2FA (if required by account)
3. Initialize Kotak Neo API client with credentials
4. Authenticate and obtain session token

### WebSocket Subscription
1. Select instruments via web UI or API
2. Format instruments for Kotak API (token + exchange)
3. Subscribe to real-time feed via WebSocket
4. Set up message callback for data processing

### Data Processing Pipeline
```
WebSocket Message → Parse JSON → Validate → Buffer → Batch Insert → Update Stats
```

**Message Processing (`service.py`):**
- Parse `[Res]:` prefixed JSON messages
- Extract market data fields (ltp, volume, timestamps, etc.)
- Handle multiple instruments per message
- Thread-safe queuing from sync WebSocket to async processing

**Buffering Strategy:**
- In-memory buffer with configurable flush interval (default: 3 seconds)
- Batch processing for database efficiency
- Error handling with transaction rollback
- Statistics tracking for performance monitoring

### Performance Monitoring
- Real-time statistics dashboard
- Processing metrics (batch size, timing, throughput)
- Buffer status and WebSocket connection health
- Database performance tracking

## UI Components & Frontend

### Template Structure
- **base.html**: Common layout with navigation, Material Icons, responsive design
- **index.html**: Main ingestion dashboard with real-time statistics
- **instruments.html**: Instrument selection and management interface

### Styling & Theming (`app/static/css/theme.css`)
- CSS custom properties for consistent theming
- Material Design inspired components
- Responsive layout with mobile support
- Glass morphism effects and smooth animations

### JavaScript Functionality
- **theme.js**: Utilities, API client, storage management
- **autocomplete.js**: Real-time instrument search
- **instruments.js**: Instrument selection and validation
- Live polling for statistics updates
- Real-time status indicators

### Key UI Features
- Real-time ingestion statistics display
- Instrument search and autocomplete
- TOTP/MPIN authentication forms
- Live connection status indicators
- Responsive mobile-friendly design

## Development & Testing

### Local Development Workflow
1. Start services: `docker-compose up -d`
2. Make code changes in `app/` directory
3. Application auto-reloads with `--reload` flag
4. Test via web UI at `http://localhost:8000`
5. API testing via `/docs` (FastAPI auto-generated documentation)

### Testing with Demo Data
- Use `notebooks/kotak_neo_websocket_demo.ipynb` for API exploration
- Sample feed data in `feed_data.txt` for offline testing
- `check_deps.py` script for dependency compatibility verification

### Database Operations
```bash
# View live data
docker-compose exec timescaledb psql -U postgres -d stockfeed -c "
SELECT symbol, ltp, volume, timestamp
FROM stock_feeds
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC LIMIT 20;"

# Check ingestion stats
docker-compose exec timescaledb psql -U postgres -d stockfeed -c "
SELECT records_processed, last_processed_at, batch_size, processing_time_ms
FROM ingestion_stats
ORDER BY id DESC LIMIT 5;"
```

### Debugging Tips
- Monitor logs: `docker-compose logs -f app`
- Check WebSocket connection status in UI
- Verify TOTP codes are current (6-digit, time-sensitive)
- Ensure Kotak API credentials are valid
- Test instrument selection before starting ingestion

## Important Development Notes

### Dependency Management
- **Critical**: `websockets==8.1` required by neo-api-client
- Use `check_deps.py` to verify compatibility before major updates
- Pin FastAPI/uvicorn versions for WebSocket compatibility

### Authentication Requirements
- TOTP codes expire quickly (30-60 seconds)
- Mobile app must be available for real-time authentication
- Some accounts require additional MPIN for 2FA

### WebSocket Connection Management
- Handle connection drops gracefully
- Implement reconnection logic for production use
- Monitor connection status in UI

### TimescaleDB Optimization
- Hypertables automatically partition by timestamp
- Use time-based queries for optimal performance
- Consider data retention policies for large datasets