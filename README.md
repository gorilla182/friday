# Friday — Учебный тест-стенд для автотестов

**Friday** — это специально спроектированный учебный тест-стенд для отработки навыков автоматизации тестирования.

### Для чего создан проект

- Практика **Playwright** (UI-тесты, E2E, компонентные тесты)
- Практика **API-тестирования** (REST, авторизация, негативные сценарии, контракты)
- Изучение работы с реальными системами (аутентификация, владение данными, ошибки, сброс состояния)

Проект имитирует типичное веб-приложение, но при этом остаётся **максимально простым и предсказуемым**, чтобы тесты было удобно писать и поддерживать.

## Архитектура

| Слой          | Технология                          | Особенности |
|---------------|-------------------------------------|-----------|
| **Фронтенд**  | Статический сайт (HTML + Vanilla JS + CSS) | MPA, нет сборки фронтенда |
| **Бэкенд**    | Supabase (PostgreSQL + Auth + RLS) | Публичный ключ в репозитории |
| **API**       | Supabase Edge Functions (Deno)     | Один файл, реалистичные эндпоинты |
| **Деплой**    | Vercel (фронтенд) + Supabase       | Vercel — основной способ |

Фронтенд напрямую работает с Supabase (через клиент) и с кастомным API (через Edge Function). Это позволяет тестировать как прямые вызовы базы, так и классический REST.

## Быстрый старт

### Локальный запуск

```bash
cd site
python -m http.server 8000
# Откройте http://localhost:8000
```

### Тестовые учётные записи

- `alice@example.com` / `password123`
- `bob@example.com` / `password123`

### Сброс данных

Самый удобный способ:

```bash
curl -X POST https://<your-project>.supabase.co/functions/v1/api/admin/reset \
  -H "Content-Type: application/json"
```

Или через RPC (требуется service role key):

```sql
SELECT * FROM public.reset_teststand();
```

### Наполнение каталога товаров

Если каталог пустой, выполните в Supabase SQL Editor:

```sql
-- См. файл supabase/seed-products.sql
```

## Структура проекта

```
friday/
├── site/                          # Статический фронтенд
│   ├── index.html                 # Логин
│   ├── register.html
│   ├── dashboard.html
│   ├── catalog.html
│   ├── cart.html
│   ├── item_detail.html
│   ├── profile.html
│   ├── css/
│   └── js/                        # Включая bootstrap, data layer
├── supabase/
│   ├── schema.sql
│   ├── reset.sql                  # Функция сброса данных
│   ├── functions/api/index.ts     # Основной API (Edge Function)
│   └── seeds/
├── vercel.json
├── .github/workflows/deploy-vercel.yml
└── README.md
```

## UI-функциональность

| Страница          | Основные возможности                              | Data-testid примеры                     |
|-------------------|----------------------------------------------------|-----------------------------------------|
| Логин             | Вход, демо-данные                                  | `login-form`, `login-email-input`       |
| Регистрация       | Создание аккаунта + автологин                      | `register-form`                         |
| Дашборд           | Статистика, рекомендуемые товары                   | `stat-card-*`, `dashboard-product-grid` |
| Каталог           | Поиск, сортировка, фильтр по категории, пагинация | `category-chip-*`, `pagination-*`       |
| Карточка товара   | Детали, добавление в корзину, отзывы               | `item-name`, `reviews-list`             |
| Корзина           | Изменение количества, промокоды, оформление заказа | `cart-item`, `checkout-button`          |
| Профиль           | Редактирование имени, My API Items, история заказов | `tab-orders`, `api-items-table`       |

Все элементы имеют стабильные `data-testid`.

## API Reference

**Base URL:**
```
https://<your-project-ref>.supabase.co/functions/v1/api
```

### Аутентификация

#### Регистрация

```http
POST /auth/register
Content-Type: application/json

{
  "email": "new@example.com",
  "password": "password123",
  "name": "New User"
}
```

**Ответ (201):**
```json
{
  "id": "uuid",
  "email": "new@example.com",
  "name": "New User"
}
```

#### Логин

```http
POST /auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "password123"
}
```

**Ответ:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "Bearer",
  "user": { ... }
}
```

### Items (API Items)

Полноценный CRUD с ownership, пагинацией и фильтрами.

#### Получить список

```http
GET /items?page=1&limit=10&category=testing
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "items": [...],
  "page": 1,
  "limit": 10,
  "total": 42,
  "total_pages": 5
}
```

#### Создать

```http
POST /items
Authorization: Bearer <token>

{
  "title": "Write login tests",
  "description": "Cover happy and negative cases",
  "category": "testing"
}
```

#### Получить по ID / Обновить / Удалить

- `GET /items/{id}`
- `PUT /items/{id}` — только владелец
- `DELETE /items/{id}` — только владелец

### Специальные эндпоинты для тестирования

#### Имитация ошибок

```http
POST /items/trigger-error
Content-Type: application/json

{ "payload": "server_error" }   // 500
{ "payload": "rate_limit" }     // 429
```

#### Полный сброс данных

```http
POST /admin/reset
```

Возвращает результат выполнения `reset_teststand()`.

### Категории

```http
GET /categories
```

Возвращает массив уникальных категорий из `api_items`.

### Товары магазина (для зеркального тестирования)

```http
GET /products
```

Возвращает все товары из публичной таблицы `products`.

### Отзывы

#### Получить отзывы

```http
GET /reviews?product_id=5
```

#### Добавить отзыв

```http
POST /reviews
Authorization: Bearer <token>

{
  "product_id": 5,
  "rating": 5,
  "comment": "Отличный товар!"
}
```

#### Удалить отзыв

```http
DELETE /reviews/{id}
Authorization: Bearer <token>
```

Только владелец может удалить свой отзыв.

### Заказы

```http
GET /orders
Authorization: Bearer <token>
```

Возвращает заказы текущего пользователя с вложенными `order_items`.

### Профиль

#### Получить

```http
GET /profile
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "id": "...",
  "email": "...",
  "name": "...",
  "orders_count": 3
}
```

#### Обновить имя

```http
PUT /profile
Authorization: Bearer <token>

{
  "name": "Новое Имя"
}
```

## База данных

Основные таблицы:
- `products` — публичный каталог
- `api_items` — личные элементы пользователя (для API-тестирования)
- `cart_items`
- `orders` + `order_items`
- `reviews`

Все таблицы защищены Row Level Security (RLS).

## Деплой

### Vercel (рекомендуемый способ)

Vercel обеспечивает быстрые деплои, preview-ссылки для каждого PR, отличный CDN и удобный developer experience.

#### Импорт проекта из GitHub

1. Убедитесь, что код находится в GitHub-репозитории.
2. Перейдите на [https://vercel.com](https://vercel.com) и войдите через GitHub.
3. Нажмите **Add New Project** → выберите ваш репозиторий → **Import**.
4. Vercel автоматически определит настройки из `vercel.json`:
   - **Framework Preset**: `Other`
   - **Build Command**: (пусто)
   - **Output Directory**: `site`
   - **Install Command**: (пусто)

5. Нажмите **Deploy**.

Готово! Сайт будет доступен по адресу вида `https://friday-ваш-аккаунт.vercel.app`.

#### Автоматический деплой через GitHub Actions

После импорта проекта настройте CI/CD:

1. Получите Org ID и Project ID:
   - Установите Vercel CLI: `npm install -g vercel`
   - Выполните: `vercel login` → `vercel link`
   - Откройте `.vercel/project.json`

2. Добавьте секреты в GitHub:
   - **Settings → Secrets and variables → Actions → Secrets**
   - Добавьте:
     - `VERCEL_TOKEN` (создайте на https://vercel.com/account/tokens)
     - `VERCEL_ORG_ID`
     - `VERCEL_PROJECT_ID`

   Рекомендуется хранить все три в **Secrets**, а не в Variables.

3. Workflow `.github/workflows/deploy-vercel.yml` автоматически:
   - Запускает тесты и сборку
   - Делает **Preview** деплои для Pull Request'ов
   - Делает **Production** деплой при пушах в `main`

**Примечание для Hobby-тарифа**: даже на бесплатном плане у вас есть Org ID. Если появляется ошибка про отсутствующий `VERCEL_ORG_ID`, обязательно добавьте его.

### Защита деплоев (Vercel Authentication)

По умолчанию Vercel может включать защиту. Для тестового стенда:

1. Откройте проект в Vercel → **Settings → Deployment Protection**
2. Для **Production** выберите **Disabled**
3. Сохраните

После этого сайт будет публично доступен без авторизации в Vercel.

### Локальная разработка

```bash
cd site
python -m http.server 8000
# Откройте http://localhost:8000
```

## Полезные советы для тестирования

- Всегда используйте `/admin/reset` перед тестом (`autouse` фикстура).
- Проверяйте негативные кейсы: 403 на чужие записи, 404, валидацию.
- Используйте `data-testid` — они стабильны и не зависят от текста.
- Тестируйте как UI, так и прямые вызовы API.
- Обращайте внимание на ownership (только свои items/orders/reviews).

## Взаимодействие фронтенда и бэкенда

- Часть функциональности использует **Supabase JS клиент напрямую** (авторизация, загрузка товаров, отзывы, корзина).
- Часть функциональности идёт через **кастомный API** (`/api/*`) — в основном для практики работы с REST (Items, Orders, Profile и т.д.).
- Это позволяет писать разные типы тестов:
  - Тесты, которые ходят напрямую в Supabase
  - Тесты, которые используют только HTTP API
  - Смешанные сценарии

## Полезные советы для написания тестов

- Всегда сбрасывайте данные через `/admin/reset` перед тестом.
- Используйте `data-testid` — они не зависят от текста и локализации.
- Проверяйте не только happy path, но и:
  - 401/403 при доступе к чужим данным
  - Валидацию входных данных
  - Пагинацию и фильтры
  - Ошибочные сценарии (`/items/trigger-error`)
- Тестируйте как через UI, так и напрямую через API.

Проект специально спроектирован так, чтобы было удобно писать стабильные и понятные автотесты.
