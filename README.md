# Solana Wallet Checker

![UI](screenshots/main_page.png)

Сервис для асинхронной проверки Solana-кошельков через [Alchemy](https://www.alchemy.com/). Поддерживает одиночную и массовую проверку.

## Стек

- **FastAPI** — REST API
- **SQLAlchemy (async)** — хранение задач и результатов (SQLite в dev, PostgreSQL в prod)
- **Redis** — повторные адреса не проверяются дважды при bulk-обработке
- **httpx** — асинхронные запросы к Alchemy API
- **Pydantic** — валидация и настройки
- **pytest** — тесты

## Структура

```
solana-wallet-checker/
├── frontend/
│   └── index.html
├── backend/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml
```

## API

### `GET /api/v1/wallet/{address}`

Прямая проверка кошелька. Всегда возвращает свежие данные — без кэша.

**Response:**
```json
{
  "address": "...",
  "sol_balance": 1.23,
  "spl_tokens": [{ "mint": "...", "symbol": "USDC", "amount": 100.0 }],
  "nfts": [{ "mint": "...", "name": "...", "collection": "..." }],
  "last_activity_at": "2026-05-12T10:00:00",
  "is_active": true,
  "error": null
}
```

---

### `POST /api/v1/check`

Массовая проверка. Принимает до 1000 адресов, возвращает `task_id` немедленно (HTTP 202), обработка идёт в фоне.

**Request:**
```json
{
  "addresses": ["addr1", "addr2"],
  "options": {
    "include_nfts": true,
    "include_spl": true
  }
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "pending",
  "total": 2,
  "created_at": "2026-05-12T10:00:00"
}
```

---

### `GET /api/v1/task/{task_id}`

Статус задачи и результаты с пагинацией.

**Query params:** `page` (default: 1), `page_size` (default: 100)

**Response:**
```json
{
  "task_id": "uuid",
  "status": "done",
  "total": 2,
  "processed": 2,
  "failed": 0,
  "created_at": "...",
  "completed_at": "...",
  "results": [...]
}
```

Возможные статусы: `pending` → `running` → `done` / `failed`

---

### `GET /`

Веб-интерфейс (single-page, тёмная тема).

## Установка и запуск

### Docker

```bash
docker compose up --build
```

Сервис доступен на [http://localhost:8000](http://localhost:8000)

### Локально

**Требования:** Python 3.11+, Redis

```bash
git clone https://github.com/nikita-seredyagin/solana-wallet-checker
cd solana-wallet-checker/backend

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

Создать файл `backend/.env`:

```env
ALCHEMY_API_KEY=your_key_here
# DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # prod, по умолчанию SQLite
```

```bash
uvicorn app.main:app --reload
```

## Тесты

```bash
cd backend
pytest tests/ -v
```


## Архитектурные решения

- **Нет кэша на `GET /wallet`** — Solana производит блок каждые ~400 мс, кэш сразу устаревает
- **Redis в bulk** (TTL 60 сек) — повторные адреса не проверяются дважды, результат берётся из кэша
- **`asyncio.Semaphore`** ограничивает количество одновременных запросов к Alchemy во избежание рейтлимита
