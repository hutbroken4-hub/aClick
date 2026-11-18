from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import router

app = FastAPI(title="aClick API", version="0.1.0")
app.include_router(router, prefix="/api")

@app.on_event("startup")
def startup() -> None:
    init_db()

app.mount("/", StaticFiles(directory="app/static", html=True), name="app")
