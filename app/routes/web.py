from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import app_settings

templates = Jinja2Templates(directory="app/templates")

async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "poll_interval": app_settings.api_poll_interval * 1000
    })

async def instruments_page(request: Request):
    return templates.TemplateResponse("instruments.html", {
        "request": request
    })

async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}