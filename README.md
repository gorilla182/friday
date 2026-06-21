# Teststand

Учебный веб-стенд для практики автотестов на **Python + Playwright + requests**.

Проект намеренно простой: предсказуемое поведение, стабильные локаторы (`data-testid`) и возможность сброса данных между прогонами тестов.

## Почему Flask, а не FastAPI

Выбран **Flask**, потому что:

- **Jinja2** — шаблонизатор «из коробки», без дополнительной настройки
- **Сессии** для UI-авторизации реализуются просто (`flask.session`)
- **Blueprints** позволяют чисто разделить UI- и API-роуты
- Меньше «магии» — удобнее для обучения и отладки тестов

FastAPI лучше подошёл бы, если бы основной фокус был на REST API и OpenAPI/Swagger. Здесь UI и API равнозначны, а Swagger не является обязательным требованием.

## Стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.10+, Flask |
| База данных | SQLite (файл `data/teststand.db`) |
| UI | Jinja2 + минимальный CSS |
| API auth | JWT Bearer token |
| UI auth | Cookie-сессия Flask |

## Установка и запуск

```bash
# After cloning the repository (directory name will match your repo name, e.g. "friday")
cd friday
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Приложение будет доступно по адресу: **http://127.0.0.1:5000**

Опции запуска:

```bash
python app.py --host 0.0.0.0 --port 8080
```

## Структура проекта

```
friday/   # (or your repo name)
├── app.py              # Точка входа, регистрация blueprints, CLI
├── config.py           # Константы (секреты, лимиты, пути к БД)
├── database.py         # SQLite: схема, seed, reset, хелперы
├── ui/
│   ├── __init__.py
│   └── routes.py       # UI-роуты (HTML-страницы, сессии)
├── api/
│   ├── __init__.py
│   └── routes.py       # REST API (/api/v1/...)
├── templates/          # Jinja2-шаблоны
├── static/
│   └── style.css       # Минимальные стили
├── site/               # Static frontend for GitHub Pages (uses Supabase)
├── data/
│   └── teststand.db    # SQLite (создаётся автоматически)
├── requirements.txt
└── README.md
```

## Карта UI-страниц

```
/login ──(успех)──► /dashboard ──► /items/<id> ──(add to cart)──► /cart
   ▲                    │                                              │
   │                    ├──► /profile ──(logout)──► /login            │
   │                    │                                              │
/register              │                                              ▼
                       │                                         /checkout
                       │                                              │
                       └◄──(continue)── /success ◄──(place order)─────┘
```

| Страница | URL | Доступ | Описание |
|----------|-----|--------|----------|
| Login | `/login` | Публичная | Форма входа, ошибка при неверных данных |
| Register | `/register` | Публичная | Регистрация с валидацией email/пароля |
| Dashboard | `/dashboard` | Авторизованные | Каталог товаров |
| Item detail | `/items/<id>` | Авторизованные | Карточка товара, добавление в корзину |
| Cart | `/cart` | Авторизованные | Изменение количества, удаление позиций |
| Checkout | `/checkout` | Авторизованные | Подтверждение заказа |
| Success | `/success?order_number=...` | Авторизованные | Страница успешного заказа |
| Profile | `/profile` | Авторизованные | Данные пользователя, logout |

Неавторизованный доступ к защищённым страницам → редирект на `/login`.

### data-testid

Все интерактивные элементы помечены атрибутом `data-testid`. Ошибки форм выводятся в блоке:

```html
<div data-testid="error-message">...</div>
```

## API-эндпоинты

Базовый URL: `http://127.0.0.1:5000/api/v1`

Формат ошибок (единый для всех эндпоинтов):

```json
{"error": "Human-readable message", "code": "machine_code"}
```

### Таблица эндпоинтов

| Метод | Путь | Auth | Описание |
|-------|------|------|----------|
| POST | `/auth/register` | Нет | Регистрация → 201 / 400 (дубликат) / 422 |
| POST | `/auth/login` | Нет | Логин → Bearer token / 401 |
| GET | `/items` | Нет | Список с пагинацией и фильтром `?category=` |
| POST | `/items` | Bearer | Создание → 201 / 401 / 422 |
| GET | `/items/<id>` | Нет | Получение → 200 / 404 |
| PUT | `/items/<id>` | Bearer | Обновление (только владелец) → 200 / 403 / 404 |
| DELETE | `/items/<id>` | Bearer | Удаление → 204 / 403 / 404 |
| POST | `/items/trigger-error` | Нет | Edge-cases: 429 (rate limit) / 500 (спец. payload) |
| POST | `/admin/reset` | Нет | Сброс БД в исходное состояние |

> **Примечание:** UI (магазин) и API (задачи/items) используют разные сущности в БД. UI работает с `products`, API — с `api_items`.

### Примеры запросов

**Регистрация**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secret123", "name": "Test User"}'
```

Ответ `201`:

```json
{"id": 3, "email": "test@example.com", "name": "Test User"}
```

**Логин**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "password123"}'
```

Ответ `200`:

```json
{"access_token": "eyJ...", "token_type": "Bearer"}
```

**Список items с пагинацией**

```bash
curl "http://127.0.0.1:5000/api/v1/items?page=1&limit=10&category=testing"
```

Ответ `200`:

```json
{
  "items": [{"id": 1, "title": "Write login tests", "description": "...", "category": "testing", "owner_id": 1, "created_at": "..."}],
  "page": 1,
  "limit": 10,
  "total": 3,
  "total_pages": 1
}
```

**Создание item (с токеном)**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/items \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "New task", "description": "Practice POST", "category": "homework"}'
```

**Edge-case: симуляция 500**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/items/trigger-error \
  -H "Content-Type: application/json" \
  -d '{"payload": "server_error"}'
```

**Edge-case: rate limit (429)**

Отправьте более 5 запросов в минуту на `POST /api/v1/items/trigger-error` без спец. payload — получите `429`.

## Тестовые пользователи

Создаются автоматически при первом запуске:

| Email | Password | Name |
|-------|----------|------|
| `alice@example.com` | `password123` | Alice Tester |
| `bob@example.com` | `password123` | Bob Tester |

## Сброс данных

Для изоляции автотестов между прогонами:

**CLI:**

```bash
python app.py --reset-db
```

**HTTP (удобно из фикстур pytest):**

```bash
curl -X POST http://127.0.0.1:5000/api/v1/admin/reset
```

Ответ:

```json
{"status": "ok", "message": "Database has been reset to initial state."}
```

Сброс удаляет файл БД, пересоздаёт схему и заново засеивает тестовых пользователей, товары и API-items.

## Идеи для практики

- **Playwright:** login flow, добавление в корзину, checkout, logout, проверка редиректов
- **requests:** CRUD API items, проверка кодов 401/403/404/422, пагинация, rate limit
- **pytest fixtures:** `POST /admin/reset` в `autouse` fixture перед каждым тестом
