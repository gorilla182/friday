# Варианты деплоя

Статический сайт находится в папке `site/`. Его можно задеплоить на Vercel (рекомендуется) или GitHub Pages.

Фронтенд использует публичный ключ Supabase (безопасно хранить в репозитории) и напрямую общается с Supabase (Auth, база данных, Edge Functions).

## 1. Vercel (рекомендуется)

Vercel даёт быстрые деплои, preview-ссылки на каждую ветку/PR, отличный CDN и удобный DX.

### Ручной деплой через Dashboard Vercel

1. Запушьте репозиторий в GitHub.
2. Перейдите на [vercel.com](https://vercel.com) → **Add New Project** → импортируйте репозиторий.
3. Vercel автоматически подхватит настройки из `vercel.json`.

   При необходимости укажите вручную:
   - **Framework Preset**: `Other`
   - **Build Command**: (оставьте пустым)
   - **Output Directory**: `site`
   - **Install Command**: (оставьте пустым)

4. Нажмите **Deploy**.

Сайт будет доступен по адресу `https://ваш-проект.vercel.app`.

### Автоматический деплой через GitHub Actions

В проекте есть workflow `.github/workflows/deploy-vercel.yml` с **отдельными джобами**:

- `test` — проверяет код, собирает TypeScript, запускает тесты
- `deploy-preview` — деплой превью (только для Pull Request)
- `deploy-production` — деплой в продакшн (только на `main`)

**Настройка секретов:**

1. В проекте Vercel → **Settings → General** скопируйте:
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

2. В GitHub → **Settings → Secrets and variables → Actions** добавьте:
   - `VERCEL_TOKEN` (создайте на https://vercel.com/account/tokens)
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

После этого деплой происходит автоматически:
- Пуш в `main` → Production
- Pull Request → Preview (Vercel добавляет комментарий со ссылкой)

### Как это работает

- `vercel.json` указывает, что нужно отдавать только папку `site/` как статический сайт.
- В workflow сначала выполняются тесты и сборка.
- Все ссылки относительные — работают на любом домене.

## 2. GitHub Pages

1. Запушьте код в репозиторий.
2. В репозитории перейдите **Settings → Pages**:
   - Source: **GitHub Actions**

3. Запушьте в `main` (или запустите workflow вручную).

Адрес сайта:
`https://USERNAME.github.io/friday` (или `/REPO-NAME`, если название репозитория отличается).

Workflow находится в `.github/workflows/deploy-pages.yml` и также разделён на отдельные джобы (`test`, `build`, `deploy`).

## Важные замечания

- Ключи Supabase (публичные) безопасно хранить в коде.
- Сайт полностью статический — не требует сервера.
- Навигация использует относительные ссылки на `.html` файлы.
- Можно одновременно использовать Vercel и GitHub Pages.
- Для продакшена подключите свой домен в любой из платформ.

## Сброс данных для тестов

```sql
-- В Supabase SQL Editor
SELECT * FROM public.reset_teststand();
```

Или через Edge Function:

```bash
curl -X POST https://<ваш-проект>.supabase.co/functions/v1/api/admin/reset
```

## Локальный запуск

```bash
cd site
python -m http.server 8000
# откройте http://localhost:8000
```
