from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI()

# Целевой URL для туннелирования
TARGET_URL = "https://api.elevenlabs.io"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    """
    Туннелирует все запросы на api.elevenlabs.io
    """
    # Формируем целевой URL
    target_path = f"{TARGET_URL}/{path}" if path else TARGET_URL
    
    # Добавляем query параметры если есть
    if request.url.query:
        target_path += f"?{request.url.query}"
    
    # Получаем заголовки запроса (исключаем некоторые системные)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Получаем тело запроса
    body = await request.body()
    
    # Создаем клиент для выполнения запроса
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Выполняем запрос на целевой сервер
            response = await client.request(
                method=request.method,
                url=target_path,
                headers=headers,
                content=body if body else None,
                follow_redirects=True
            )
            
            # Формируем ответ
            response_headers = dict(response.headers)
            # Удаляем заголовки, которые могут вызвать проблемы
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            response_headers.pop("content-length", None)
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type")
            )
            
        except httpx.TimeoutException:
            return Response(
                content="Gateway Timeout",
                status_code=504
            )
        except httpx.RequestError as e:
            return Response(
                content=f"Proxy Error: {str(e)}",
                status_code=502
            )

@app.get("/")
async def root():
    """
    Корневой endpoint
    """
    return {
        "service": "Proxy Tunnel",
        "target": TARGET_URL,
        "status": "active"
    }

@app.get("/health")
async def health():
    """
    Health check endpoint
    """
    return {"status": "ok"}

