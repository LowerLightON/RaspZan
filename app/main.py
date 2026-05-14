from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.routers import inventory, schedule

app = FastAPI(title=settings.app_name)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(inventory.router)
app.include_router(schedule.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "pages/index.html",
        {"request": request, "app_name": settings.app_name},
    )
