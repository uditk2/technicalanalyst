# Technical Analyst

A FastAPI-based service for ingesting real-time stock feed data into TimescaleDB with TOTP authentication and monitoring ingestion pane.

## Features

- Real-time stock data ingestion via Kotak Neo WebSocket API
- TimescaleDB for efficient time-series data storage
- TOTP authentication for secure access
- Live monitoring ingestion pane
- Docker containerization

## Quick Start

```bash
# Clone and start with Docker
docker-compose up -d

# Access the application
open http://localhost:8000
```

## Installation

```bash
git clone <repository-url>
cd technicalanalyst
docker-compose up -d
```

## Configuration

Set environment variables in `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stockfeed
BUFFER_FLUSH_INTERVAL=3

# Kotak Neo API credentials
KOTAK_CONSUMER_KEY=your-consumer-key
KOTAK_CONSUMER_SECRET=your-consumer-secret
KOTAK_ACCESS_TOKEN=your-access-token
KOTAK_MOBILE_NUMBER=your-mobile-number
KOTAK_UCC=your-ucc
KOTAK_NEO_FIN_KEY=your-neo-fin-key
```

**Note**: The application requires TOTP codes from your Kotak Neo mobile app for authentication, not a separate TOTP secret.

Get your Kotak Neo API credentials from the [Kotak Neo API SDK](https://github.com/Kotak-Neo/Kotak-neo-api-v2).

## License

MIT License