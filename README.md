# ElevenLabs API Proxy на FastAPI

Прокси-сервер для ElevenLabs API, разработанный на FastAPI и готовый к развертыванию на Vercel.

## Возможности

- ✅ Универсальный прокси для всех эндпоинтов ElevenLabs API
- ✅ Поддержка всех HTTP методов (GET, POST, PUT, DELETE, PATCH)
- ✅ Автоматическая передача заголовков и параметров
- ✅ Поддержка потоковой передачи аудио
- ✅ Обработка ошибок и таймаутов
- ✅ CORS настроен для всех источников
- ✅ Готово к развертыванию на Vercel

## Структура проекта

```
.
├── app.py              # Основное FastAPI приложение
├── requirements.txt    # Зависимости Python
├── vercel.json        # Конфигурация для Vercel
└── README.md          # Документация
```

## Установка и локальный запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Установите переменные окружения (опционально):
```bash
export ELEVENLABS_API_BASE=https://api.elevenlabs.io
export ELEVENLABS_API_KEY=your_api_key_here
```

3. Запустите сервер:
```bash
uvicorn app:app --reload
```

Сервер будет доступен по адресу: `http://localhost:8000`

## Использование

### Базовый пример

После развертывания, все запросы к вашему прокси будут перенаправляться к ElevenLabs API.

**Пример: Получение списка голосов**

```bash
curl -X GET "https://your-proxy.vercel.app/v1/voices" \
  -H "xi-api-key: YOUR_API_KEY"
```

**Пример: Генерация речи (Text-to-Speech)**

```bash
curl -X POST "https://your-proxy.vercel.app/v1/text-to-speech/YOUR_VOICE_ID" \
  -H "xi-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Привет, это тест",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.75
    }
  }' \
  --output audio.mp3
```

### Доступные эндпоинты

Прокси поддерживает все эндпоинты ElevenLabs API:

- `GET /v1/voices` - Получить список доступных голосов
- `POST /v1/text-to-speech/{voice_id}` - Генерация речи из текста
- `GET /v1/models` - Получить список доступных моделей
- `GET /v1/user` - Информация о пользователе
- `GET /v1/user/subscription` - Информация о подписке
- `GET /v1/history` - История запросов

И любые другие эндпоинты ElevenLabs API.

## Развертывание на Vercel

### Через Vercel CLI

1. Установите Vercel CLI:
```bash
npm i -g vercel
```

2. Разверните проект:
```bash
vercel
```

3. Для продакшена:
```bash
vercel --prod
```

### Через GitHub

1. Загрузите код в GitHub репозиторий
2. Подключите репозиторий к Vercel через веб-интерфейс
3. Vercel автоматически обнаружит FastAPI приложение и развернет его

### Настройка переменных окружения

В настройках проекта на Vercel добавьте переменные окружения:

- `ELEVENLABS_API_BASE` (опционально, по умолчанию: `https://api.elevenlabs.io`)
- `ELEVENLABS_API_KEY` (опционально, если не передаете через заголовок)

**Важно:** API ключ можно передавать через заголовок `X-API-Key` или `xi-api-key` в каждом запросе, что более безопасно.

## Аутентификация

API ключ можно передавать тремя способами:

1. **Через заголовок запроса** (рекомендуется):
   - `X-API-Key: your_api_key`
   - или `xi-api-key: your_api_key`

2. **Через переменную окружения** `ELEVENLABS_API_KEY`

3. **Комбинация**: Если заголовок не передан, будет использована переменная окружения

## Особенности

- **Потоковая передача**: Аудио файлы передаются потоком для экономии памяти
- **Таймауты**: Установлен таймаут 300 секунд для длительных операций (например, генерация речи)
- **CORS**: Настроен для работы из браузера с любого источника
- **Автоматическое определение типа контента**: Поддерживаются JSON, multipart/form-data и бинарные данные

## Документация API

После развертывания документация Swagger доступна по адресу:
- `https://your-proxy.vercel.app/docs` - Swagger UI
- `https://your-proxy.vercel.app/redoc` - ReDoc

## Troubleshooting

### Ошибка 502 Bad Gateway
- Проверьте правильность базового URL ElevenLabs API
- Убедитесь, что API ключ корректный

### Ошибка 504 Gateway Timeout
- Увеличьте таймаут в коде (по умолчанию 300 секунд)

### CORS ошибки
- Проверьте настройки CORS в `app.py`

## Лицензия

MIT

