from fastapi import FastAPI
from app.core.db import init_db
from app.api.v1.routes import api_router  # asumsi sudah ada

app = FastAPI(title="SKKNI HTTP Scraper")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(api_router)
