# Варианты деплоя

Статический сайт находится в папке `site/`. Его можно задеплоить на Vercel (рекомендуется) или GitHub Pages.

Фронтенд использует публичный ключ Supabase (безопасно хранить в репозитории) и напрямую общается с Supabase (Auth, база данных, Edge Functions).

## 1. Vercel (рекомендуется)

Vercel даёт быстрые деплои, preview-ссылки на каждую ветку/PR, отличный CDN и удобный DX.

### Как импортировать проект из GitHub (рекомендуемый способ)

1. Убедитесь, что ваш код находится в GitHub-репозитории (например `https://github.com/ваш-юзер/friday`).
2. Перейдите на сайт [https://vercel.com](https://vercel.com) и войдите через GitHub.
3. На главной странице нажмите большую кнопку **Add New Project**.
4. В разделе **Import Git Repository** найдите ваш репозиторий и нажмите **Import**.
5. На странице настройки деплоя:
   - Vercel автоматически определит `vercel.json` и подставит правильные значения:
     - **Framework Preset**: `Other`
     - **Build Command**: (пусто)
     - **Output Directory**: `site`
     - **Install Command**: (пусто)
   - Если что-то не подставилось, укажите вручную как выше.
6. Нажмите **Deploy**.

Готово! Через 30–60 секунд сайт будет доступен по адресу вида:
`https://friday-ваш-юзер.vercel.app`

### Как создать новый проект на Vercel (без импорта из GitHub)

Этот способ используется реже, но полезен для теста:

1. Зайдите на [https://vercel.com](https://vercel.com) → **Add New Project**.
2. Выберите **Upload** (вместо импорта репозитория).
3. Перетащите всю папку `friday` (или только папку `site`, если хотите).
4. После загрузки перейдите в настройки проекта и укажите:
   - **Output Directory**: `site`
   - **Build Command**: (оставьте пустым)
5. Нажмите **Deploy**.

**Важно**: При использовании Upload не будет автоматического деплоя при пушах в Git. Поэтому рекомендуется всегда импортировать проект из GitHub.

### После первого деплоя

1. Откройте полученную ссылку.
2. Проверьте вход (`alice@example.com` / `password123`).
3. Протестируйте добавление товаров в корзину, оформление заказа, добавление API Items и отзывы.

### Автоматический деплой через GitHub Actions (после импорта проекта)

После того как вы импортировали проект на Vercel, вы можете настроить автоматический деплой через GitHub Actions.

1. Получи Org ID и Project ID (даже на бесплатном тарифе Hobby):

   **Самый простой способ (рекомендуется):**
   - Установи Vercel CLI:
     ```bash
     npm install -g vercel
     ```
   - В папке проекта выполни:
     ```bash
     vercel login
     vercel link
     ```
   - Открой файл `.vercel/project.json` — там будут оба ID:
     ```json
     {
       "projectId": "...",
       "orgId": "..."
     }
     ```

   Скопируй `orgId` как `VERCEL_ORG_ID` и `projectId` как `VERCEL_PROJECT_ID`.

   Для этого проекта (уже определено):
   - `VERCEL_ORG_ID` = `team_rv8vy3ZKfmInIb7mkT3Pe0D0`
   - `VERCEL_PROJECT_ID` = `prj_8tPXQ48eT5jQgn7waSM6rFNAw1yi`

2. В GitHub репозитории перейди в:
   **Settings → Secrets and variables → Actions**

   **Важно:**

GitHub имеет два места для хранения значений:

- **Secrets** — для чувствительных данных (токены, пароли, ключи). Они зашифрованы, не показываются в логах и доступны только через `${{ secrets.NAME }}`.
- **Variables** — для обычных настроек (например, имя окружения). Они видны в интерфейсе и логах, доступны через `${{ vars.NAME }}`.

Для Vercel деплоя:

- `VERCEL_TOKEN` — **обязательно** добавляй в **Secrets**.
- `VERCEL_ORG_ID` и `VERCEL_PROJECT_ID` — тоже **лучше добавлять в Secrets** (для единообразия).

В нашем workflow мы используем именно `secrets.` (а не `vars.`).

Где добавлять:
1. Зайди в репозиторий на GitHub
2. **Settings → Secrets and variables → Actions**
3. Переключись на вкладку **Secrets** (не Variables!)
4. Нажми "New repository secret" и добавь три значения:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

Если по какой-то причине хочешь положить Org ID и Project ID в Variables — скажи, я подправлю workflow. Но стандартный и рекомендуемый вариант — все трое в **Secrets**.

   Создать токен можно здесь: https://vercel.com/account/tokens (нужен Full Access)

3. Workflow `.github/workflows/deploy-vercel.yml` запустится автоматически:
   - Pull Request → Preview
   - Пуш в main → Production

**Примечание для бесплатного тарифа (Hobby):**  
На Hobby у тебя **есть** Org ID — это ID твоего личного аккаунта. Vercel требует его, если ты указываешь `VERCEL_PROJECT_ID`.

Если в production job падает ошибка "You specified `VERCEL_PROJECT_ID` but you forgot to specify `VERCEL_ORG_ID`" — значит секрет `VERCEL_ORG_ID` не задан или пустой.

Обязательно получи его через `vercel link` (см. инструкцию выше) и добавь в секреты.

**Важно:** В GitHub Action мы передаём `--token "$VERCEL_TOKEN"` явно — это надёжнее в CI. Локально CLI обычно берёт токен из окружения (`VERCEL_TOKEN`) или из `vercel login`.

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
