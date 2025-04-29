from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.endpoints import router as api_router
from app.api.web_endpoints import router as web_router
from app.config import config

app = FastAPI(
    title="Face Recognition API",
    description="API cho hệ thống chấm công bằng nhận diện khuôn mặt",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include API routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router, prefix="/api/v1")

# Root route to serve the web interface
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )