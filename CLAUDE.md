# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based technical analyst service that collects real-time stock data from Kotak Neo WebSocket API and stores it in TimescaleDB. The application provides both web UI and REST API endpoints for monitoring and managing stock data ingestion.

## Development Commands

### Local Development
```bash
# Start the application with Docker
docker-compose up -d

# Access the application
open http://localhost:8000

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Manual Python Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

### Core Components

1. **FastAPI Application** (`app/main.py`)
   - Main entry point with route definitions
   - Includes both web routes and API endpoints
   - Static file serving for UI assets

2. **Database Layer** (`app/database/`)
   - SQLAlchemy async models with TimescaleDB
   - Two main tables: `stock_feeds` and `ingestion_stats`
   - Connection pooling via async session factory

3. **Ingestion Service** (`app/ingestion/`)
   - `KotakNeoSubscriber`: WebSocket client for real-time data
   - `config.py`: Environment-based configuration
   - `service.py`: Background ingestion orchestration

4. **API Routes** (`app/routes/`)
   - `web.py`: HTML template rendering
   - `instruments.py`: REST API for instrument search/management
   - `ingestion.py`: Ingestion control endpoints

5. **Configuration** (`app/config/`)
   - `instruments.py`: Instrument registry and search functionality
   - Environment variables managed via `app/settings.py`

### Data Flow

1. **Authentication**: TOTP-based auth with Kotak Neo API
2. **Subscription**: Select instruments via web UI or API
3. **Real-time Data**: WebSocket connection streams market data
4. **Storage**: Data buffered and bulk-inserted into TimescaleDB
5. **Monitoring**: Live dashboard shows ingestion status and stats

### Key Dependencies

- **FastAPI**: Web framework with async support
- **SQLAlchemy 2.0**: Database ORM with async support
- **TimescaleDB**: Time-series optimized PostgreSQL
- **neo-api-client**: Kotak Neo WebSocket API client
- **Jinja2**: Template rendering for web UI
- **asyncpg**: Async PostgreSQL driver

## Environment Configuration

The application requires these environment variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@timescaledb:5432/stockfeed
REDIS_URL=redis://redis:6379/0
API_POLL_INTERVAL=10

# Kotak Neo API credentials (required)
KOTAK_CONSUMER_KEY=your-consumer-key
KOTAK_CONSUMER_SECRET=your-consumer-secret
KOTAK_UCC=your-ucc
KOTAK_NEO_FIN_KEY=your-neo-fin-key
KOTAK_MOBILE_NUMBER=your-mobile-number
```

## Working with Instruments

The instrument registry (`app/config/instruments.py`) provides search and management capabilities:

- Search by symbol, company name, or sector
- Autocomplete for UI components
- Validation for Kotak API format
- Predefined sets (Nifty 50, indices, top 10)

## Database Schema

- **stock_feeds**: Real-time market data with JSONB for raw feed data
- **ingestion_stats**: Processing metrics and performance tracking
- TimescaleDB hypertables optimize time-series queries

## Ingestion Process

1. Initialize Kotak Neo client with credentials
2. Authenticate using TOTP code from mobile app
3. Subscribe to instrument list (WebSocket)
4. Process incoming data and batch insert to database
5. Track statistics and handle reconnection logic

## UI Components

- **Templates**: Located in `app/templates/`
- **Static Assets**: Served from `app/static/`
- **Jinja2 Templating**: Server-side rendering with context variables
- **Real-time Updates**: JavaScript polling for live data refresh