# Friday — Учебный тест-стенд для автотестов

Проект предназначен для практики написания автотестов (Playwright + requests / Playwright + API).

**Архитектура (2026):**
- Фронтенд: полностью статический сайт (HTML + vanilla JS + CSS)
- Бэкенд: Supabase (PostgreSQL + Auth + Row Level Security)
- Деплой фронтенда: GitHub Pages + GitHub Actions
- API для тестов: Supabase Edge Functions (реалистичные HTTP эндпоинты)

## Быстрый старт

### Локальный запуск фронтенда

```bash
cd friday
cd site
python -m http.server 8000
# Открой http://localhost:8000
```

Тестовые пользователи (созданы в Supabase):
- `alice@example.com` / `password123`
- `bob@example.com` / `password123`

### Сброс данных (для изоляции тестов)

Самый удобный способ — вызвать Edge Function:

```bash
curl -X POST https://fvxhcfisnsganugrgqnm.supabase.co/functions/v1/api/admin/reset \
  -H "Content-Type: application/json"
```

Или используйте RPC напрямую через Supabase клиент с service role key (только для CI).

## Структура проекта

```
friday/
├── site/                    # Статический фронтенд (деплоится на GitHub Pages)
│   ├── index.html
│   ├── dashboard.html
│   ├── cart.html
│   ├── ...
│   ├── js/supabase-client.js
│   └── style.css
├── supabase/
│   ├── functions/
│   │   └── api/             # Реалистичный API слой (Edge Functions)
│   │       └── index.ts
│   ├── schema.sql
│   └── reset.sql            # Функция сброса
├── .github/workflows/       # Деплой на GitHub Pages
└── README.md
```

Старый Flask-код полностью удалён.

## UI Функциональность (для Playwright тестов)

Текущий магазин покрывает:

- Регистрация и логин (с автопереходом)
- Просмотр каталога с **поиском по названию**, **сортировкой** (имя/цена), **фильтром по категории** (новое)
- Детальная карточка товара + добавление в корзину
- Корзина: обновление количества, удаление
- Checkout и оформление заказа
- Профиль: просмотр, **редактирование имени** (новое), **история заказов** (новое)
- **Отзывы к товарам** (новое): просмотр и добавление отзывов с рейтингом 1-5

Все интерактивные элементы имеют `data-testid` для стабильных локаторов.

Новые UI "эндпоинты"/потоки:
- Поиск и фильтрация товаров
- История заказов
- Редактирование профиля
- Добавление и просмотр отзывов на странице товара

Это позволяет покрывать больше сценариев в Playwright тестах.

## API Эндпоинты (для тестов на requests)

Базовый URL:  
`https://fvxhcfisnsganugrgqnm.supabase.co/functions/v1/api`

### Аутентификация

```http
POST /auth/register
Content-Type: application/json

{
  "email": "new@example.com",
  "password": "password123",
  "name": "New User"
}
```

```http
POST /auth/login
{
  "email": "alice@example.com",
  "password": "password123"
}

# Ответ
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "user": { ... }
}
```

### Основные эндпоинты

**Items (CRUD + пагинация + фильтры)**

```http
GET /items?page=1&limit=10&category=testing
Authorization: Bearer <token>

POST /items
Authorization: Bearer <token>
{
  "title": "New task",
  "description": "...",
  "category": "testing"
}

GET /items/123
PUT /items/123
DELETE /items/123
```

**Дополнительные (новые для покрытия UI)**

```http
GET /categories
GET /products
GET /reviews?product_id=1
POST /reviews   (auth required)
{
  "product_id": 1,
  "rating": 5,
  "comment": "Great product!"
}
```

**Особенности (как в реальных проектах):**
- Пагинация с `page`, `limit`, `total`, `total_pages`
- Фильтрация по `category`
- Только владелец может обновлять/удалять свои items (403)
- Валидация (422)
- Правильные статус-коды (200, 201, 204, 401, 403, 404, 422, 429, 500)
- Reviews поддержка для UI тестов

### Edge-кейсы для практики

```http
POST /items/trigger-error
{
  "payload": "server_error"   # → 500
}

# Без payload или с другим значением может вернуть 429 (rate limit simulation)
```

### Сброс данных

```http
POST /admin/reset
# Возвращает { "status": "ok", "message": "..." }
```

## Как писать тесты

### Playwright (UI)

Используйте обычные `page.goto`, `locator('[data-testid="..."]')`.

Все важные элементы помечены `data-testid`.

### requests (API)

```python
import requests

BASE = "https://fvxhcfisnsganugrgqnm.supabase.co/functions/v1/api"

# Логин
r = requests.post(f"{BASE}/auth/login", json={
    "email": "alice@example.com",
    "password": "password123"
})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Создать item
r = requests.post(f"{BASE}/items", json={"title": "Test"}, headers=headers)
```

### Сброс перед каждым тестом (рекомендуется)

```python
requests.post(f"{BASE}/admin/reset")
```

## Деплой на GitHub Pages

Смотрите файл `DEPLOY.md`.

Workflow деплоит только папку `site/`.

## Полезные советы для практики

- Используйте `/admin/reset` в `autouse` фикстуре pytest.
- Тестируйте негативные сценарии через `/items/trigger-error`.
- Проверяйте ownership (403 при попытке изменить чужой item).
- Тестируйте пагинацию и фильтры.

---

Проект специально сделан так, чтобы имитировать поведение реальных веб-приложений, но при этом оставался максимально простым и предсказуемым для написания тестов.