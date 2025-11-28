"""
Простой прокси для ElevenLabs API
Просто пересылает запросы как есть
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import httpx

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ELEVENLABS_API_BASE = os.getenv("ELEVENLABS_API_BASE", "https://api.elevenlabs.io")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, path: str):
    """Просто проксирует запрос на ElevenLabs API"""
    # Формируем URL
    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith("/v1"):
        path = "/v1" + path
    
    target_url = f"{ELEVENLABS_API_BASE}{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    # Копируем заголовки
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Получаем тело
    body = await request.body()
    
    # Делаем запрос
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body if body else None,
        )
        
        # Возвращаем ответ как есть
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@app.get("/")
async def root():
    return {"service": "ElevenLabs Proxy", "base_url": ELEVENLABS_API_BASE}
