# Friday — Учебный тест-стенд для автотестов

Проект предназначен для практики написания автотестов (Playwright + requests / Playwright + API).

**Архитектура (2026):**
- Фронтенд: полностью статический сайт (HTML + vanilla JS + CSS)
- Бэкенд: Supabase (PostgreSQL + Auth + Row Level Security)
- Деплой фронтенда: Vercel (рекомендуется) или GitHub Pages
- API для тестов: Supabase Edge Functions (реалистичные HTTP эндпоинты)

## Быстрый старт

### Локальный запуск фронтенда

```bash
cd friday
cd site
python -m http.server 8000
# Откройте http://localhost:8000
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

### Наполнение каталога (products)

Если каталог пустой — выполните в Supabase SQL Editor содержимое:

1. `supabase/add-categories.sql` (ALTER + UPDATE категорий)
2. `supabase/seed-products.sql` (INSERT продуктов с категориями)

После этого на `/dashboard.html` появятся товары, поиск, сортировка и чипы категорий будут работать.

## Структура проекта

```
friday/
├── site/                    # Статический фронтенд
│   ├── index.html
│   ├── dashboard.html
│   ├── catalog.html
│   ├── cart.html
│   ├── profile.html
│   ├── item_detail.html
│   ├── register.html
│   ├── css/
│   └── js/
├── supabase/
│   ├── functions/
│   │   └── api/             # Реалистичный API слой (Edge Functions)
│   ├── schema.sql
│   ├── reset.sql            # Функция сброса
│   └── seeds/
├── vercel.json              # Конфигурация для Vercel (рекомендуется)
├── .github/workflows/       # GitHub Actions (отдельные джобы для тестов и деплоя)
└── README.md
```

Старый Flask-код полностью удалён.

## UI Функциональность (для Playwright тестов)

Текущий магазин покрывает:

- Регистрация и логин (с автопереходом)
- Просмотр каталога с **поиском по названию**, **сортировкой** (имя/цена), **фильтром по категории**
- Детальная карточка товара (`item_detail.html`) + добавление в корзину + **отзывы**
- Корзина: обновление количества, удаление, применение промокодов
- Checkout и оформление заказа (создание order + order_items, очистка корзины)
- Профиль: просмотр, **редактирование имени**, **My API Items** (добавление/удаление), безопасность
- **Отзывы к товарам**: просмотр и добавление отзывов с рейтингом 1-5

Все интерактивные элементы имеют `data-testid` для стабильных локаторов (Playwright).

## API Эндпоинты (для тестов на requests / pytest)

Базовый URL:  
`https://fvxhcfisnsganugrgqnm.supabase.co/functions/v1/api`

### Аутентификация

**Регистрация**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "new@example.com",
  "password": "password123",
  "name": "New User"
}
```

**Логин**
```http
POST /auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "password123"
}
```

Ответ:
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "user": { ... }
}
```

### Items (API Items — сервис добавления товаров)

**Список с пагинацией и фильтрами**
```http
GET /items?page=1&limit=10&category=testing
Authorization: Bearer <token>
```

Ответ содержит `items`, `page`, `limit`, `total`, `total_pages`.

**Создание**
```http
POST /items
Authorization: Bearer <token>

{
  "title": "New task",
  "description": "Описание",
  "category": "testing"
}
```

**CRUD по ID**
- `GET /items/123`
- `PUT /items/123` (только владелец)
- `DELETE /items/123` (только владелец)

### Другие эндпоинты

- `GET /categories` — уникальные категории
- `GET /products` — товары магазина (зеркало для тестов)
- `GET /reviews?product_id=1` — отзывы
- `POST /reviews` (auth) — добавить отзыв
- `DELETE /reviews/:id` (auth, только владелец)
- `GET /orders` (auth) — заказы пользователя
- `GET /profile` (auth) — профиль + количество заказов
- `PUT /profile` (auth) — обновить имя

### Edge-кейсы и админ

- `POST /items/trigger-error`
  ```json
  { "payload": "server_error" }   // → 500
  { "payload": "rate_limit" }     // → 429
  ```
- `POST /admin/reset` — полный сброс данных (для изоляции тестов)

## GitHub Actions (деплой на Vercel)

- **deploy-vercel.yml** — `test` → `deploy-preview` (PR) / `deploy-production` (main)

Секреты для Vercel:
- VERCEL_TOKEN
- VERCEL_ORG_ID
- VERCEL_PROJECT_ID

**GitHub Pages больше не поддерживается.** Основной способ деплоя — Vercel + Supabase.

## Как писать тесты

### Playwright (UI)
Используйте `page.goto`, `locator('[data-testid="..."]')`. Все важные элементы помечены `data-testid`.

### requests (API)
```python
import requests

BASE = "https://fvxhcfisnsganugrgqnm.supabase.co/functions/v1/api"

r = requests.post(f"{BASE}/auth/login", json={...})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

r = requests.post(f"{BASE}/items", json={"title": "Test"}, headers=headers)
```

### Сброс перед каждым тестом
```python
requests.post(f"{BASE}/admin/reset")
```

## Полезные советы

- Используйте `/admin/reset` в `autouse` фикстуре.
- Тестируйте негативные сценарии (`/items/trigger-error`, 403 на чужие items).
- Проверяйте пагинацию, фильтры, ownership.
- Тестируйте отзывы и историю заказов через UI + API.

Проект имитирует поведение реальных веб-приложений, но остаётся простым и предсказуемым для написания стабильных автотестов.
