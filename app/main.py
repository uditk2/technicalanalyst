from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.database import init_db
from app.routes.web import read_root, instruments_page, health_check
from app.routes.ingestion import start_ingestion, stop_ingestion, get_ingestion_status
from app.ingestion.models import KotakAuthRequest

app = FastAPI(title="Stock Feed Ingestion Service", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    await init_db()

# Web routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return await read_root(request)

@app.get("/instruments", response_class=HTMLResponse)
async def instruments(request: Request):
    return await instruments_page(request)

@app.get("/health")
async def health():
    return await health_check()

# API routes
@app.post("/ingestion/start")
async def start_feed_ingestion(auth_request: KotakAuthRequest):
    return await start_ingestion(auth_request)

@app.post("/ingestion/stop")
async def stop_feed_ingestion():
    return await stop_ingestion()

@app.get("/ingestion/status")
async def feed_ingestion_status():
    return await get_ingestion_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)