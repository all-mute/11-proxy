"""
FastAPI прокси-сервер для ElevenLabs API
Разработан для деплоя на Vercel
"""
import os
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="ElevenLabs API Proxy",
    description="Прокси-сервер для ElevenLabs API",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Базовый URL ElevenLabs API
ELEVENLABS_API_BASE = os.getenv("ELEVENLABS_API_BASE", "https://api.elevenlabs.io")
# API ключ (можно передавать через заголовок или использовать из переменной окружения)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")


async def forward_request(
    request: Request,
    path: str,
    method: str = "GET",
    include_auth: bool = True
) -> Response:
    """
    Пересылает запрос к ElevenLabs API
    
    Args:
        request: Входящий FastAPI Request
        path: Путь для проксирования (например, /v1/voices)
        method: HTTP метод
        include_auth: Добавлять ли API ключ из заголовка или переменной окружения
    """
    # Формируем полный URL
    target_url = f"{ELEVENLABS_API_BASE}{path}"
    
    # Добавляем query параметры из оригинального запроса
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    logger.info(f"Проксирование {method} {target_url}")
    
    # Получаем заголовки
    headers = {}
    for key, value in request.headers.items():
        # Пропускаем некоторые заголовки, которые должны быть обновлены
        if key.lower() not in ["host", "content-length", "connection"]:
            headers[key] = value
    
    # Добавляем API ключ
    if include_auth:
        # Приоритет: заголовок X-API-Key > переменная окружения
        api_key = request.headers.get("X-API-Key") or request.headers.get("xi-api-key") or ELEVENLABS_API_KEY
        if api_key:
            headers["xi-api-key"] = api_key
    
    # Получаем тело запроса для POST/PUT/PATCH
    json_body = None
    form_data = None
    files = None
    raw_body = None
    content_type = request.headers.get("content-type", "")
    
    if method in ["POST", "PUT", "PATCH"]:
        if "application/json" in content_type:
            try:
                json_body = await request.json()
            except Exception:
                pass
        elif "multipart/form-data" in content_type.lower():
            # Для multipart получаем форму и файлы
            form = await request.form()
            form_dict = {}
            files_dict = {}
            
            for key, value in form.items():
                # Проверяем, является ли значение файлом (UploadFile из FastAPI)
                from fastapi import UploadFile
                if isinstance(value, UploadFile):
                    # Это файл - читаем его содержимое
                    file_content = await value.read()
                    filename = value.filename or 'file'
                    content_type_file = value.content_type or 'application/octet-stream'
                    # Для httpx файлы передаются как кортеж (filename, file_object, content_type)
                    # Используем BytesIO для передачи содержимого
                    from io import BytesIO
                    files_dict[key] = (filename, BytesIO(file_content), content_type_file)
                else:
                    form_dict[key] = value
            
            if files_dict:
                files = files_dict
            if form_dict:
                form_data = form_dict
        else:
            # Для других типов контента читаем как байты
            raw_body = await request.body()
    
    # Создаем HTTP клиент
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Подготавливаем параметры для запроса
            request_kwargs = {
                "method": method,
                "url": target_url,
                "headers": headers,
                "follow_redirects": True,
            }
            
            # Добавляем данные в зависимости от типа
            if json_body:
                request_kwargs["json"] = json_body
            elif files or form_data:
                # Для multipart с файлами и/или данными формы
                # Удаляем Content-Type заголовок для multipart, httpx установит его автоматически
                if "content-type" in headers:
                    headers.pop("content-type")
                
                # httpx автоматически создаст правильный multipart/form-data с boundary
                multipart_dict = {}
                if form_data:
                    multipart_dict.update(form_data)
                if files:
                    multipart_dict.update(files)
                
                # Для httpx нужно использовать files для файлов и data для обычных полей
                if files:
                    request_kwargs["files"] = files
                if form_data:
                    request_kwargs["data"] = form_data
            elif raw_body:
                request_kwargs["content"] = raw_body
            
            # Выполняем запрос
            response = await client.request(**request_kwargs)
            
            # Обрабатываем ответ - передаем все заголовки от ElevenLabs API
            # Исключаем только служебные заголовки проксирования
            response_headers = {}
            
            # Заголовки, которые НЕ нужно передавать клиенту
            headers_to_exclude = {
                "content-encoding",
                "transfer-encoding", 
                "connection",
                "host",
            }
            
            # Копируем все заголовки от ElevenLabs API, кроме исключенных
            for key, value in response.headers.items():
                if key.lower() not in headers_to_exclude:
                    response_headers[key] = value
            
            logger.debug(f"Передаем заголовки: {list(response_headers.keys())[:10]}")
            
            # Определяем тип контента
            content_type = response.headers.get("content-type", "application/json")
            
            # Для аудио используем StreamingResponse
            if "audio" in content_type or content_type.startswith("application/octet-stream"):
                return StreamingResponse(
                    iter([response.content]),
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type=content_type
                )
            
            # Для всех остальных ответов используем Response с оригинальным содержимым
            # Это гарантирует, что ответ будет идентичен ответу от ElevenLabs API
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=content_type
            )
                
        except httpx.TimeoutException:
            logger.error(f"Таймаут при запросе к {target_url}")
            raise HTTPException(status_code=504, detail="Gateway Timeout")
        except httpx.RequestError as e:
            logger.error(f"Ошибка при запросе к {target_url}: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Bad Gateway: {str(e)}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "ElevenLabs API Proxy",
        "version": "1.0.0",
        "base_url": ELEVENLABS_API_BASE,
        "endpoints": {
            "voices": "/v1/voices",
            "text-to-speech": "/v1/text-to-speech/{voice_id}",
            "models": "/v1/models",
            "user": "/v1/user",
            "usage": "/v1/user/subscription",
            "history": "/v1/history",
        },
        "docs": "/docs"
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_all(request: Request, path: str):
    """
    Универсальный прокси для всех запросов к ElevenLabs API
    Примеры:
    - GET /v1/voices - получить список голосов
    - POST /v1/text-to-speech/{voice_id} - генерация речи
    - GET /v1/models - получить список моделей
    """
    method = request.method
    
    # Если путь не начинается с /v1, добавляем его
    if not path.startswith("v1"):
        if path.startswith("/"):
            path = "/v1" + path
        else:
            path = "/v1/" + path
    elif not path.startswith("/"):
        path = "/" + path
    
    return await forward_request(request, path, method)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

