from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from my_site.config import ALLOWED_ORIGINS

# ✅ твои роутеры
from my_site.api.resumes import resumes_router
from my_site.api.auth import auth_router
from my_site.api.jobs import jobs_router

app = FastAPI(title="AI Resume Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаём папку для медиа если нет
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

# ✅ подключаем роутеры
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "AI Resume Analyzer API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "sqlalchemy": "2.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)