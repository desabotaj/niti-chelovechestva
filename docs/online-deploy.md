# Публикация в интернете / Deploy to the public web

## RU

Чтобы открыть проект **из другого города** по обычной ссылке `https://…`, нужен **статический хостинг**: фронтенд после `npm run build` — это HTML/JS/CSS и папка `data/` внутри `dist/`.

### Важно про данные (`frontend/public/data/`)

Файлы `*.json` в `frontend/public/data/` **в .gitignore** — в репозитории их может не быть. Перед сборкой для продакшена:

1. Сгенерируй и экспортируй тайлы (из каталога `backend`, см. корневой `README.md`).
2. Убедись, что в `frontend/public/data/` лежат `meta.json`, `hex_*.json`, `arcs_*.json`, `lineages.json` и т.д.
3. Выполни `npm run build` в `frontend/` — Vite **скопирует** `public/data` в `dist/data`.

Если деплой идёт из Git без этих файлов, хостинг соберёт пустой сайт без данных — либо закоммить тайлы (`git add -f …`), либо добавь шаг CI, который запускает экспорт на билде.

### Вариант A — самый простой: загрузка готовой `dist`

1. Локально:

   ```bash
   cd frontend
   npm ci
   npm run build
   ```

2. Зарегистрируйся на одном из сервисов и залей **содержимое** папки `frontend/dist` (не исходники):

   - **[Netlify Drop](https://app.netlify.com/drop)** — перетащить папку `dist`, получишь ссылку вида `https://random-name.netlify.app`.
   - **Cloudflare Pages** — проект → «Direct Upload» / загрузка артефакта (аналогично).
   - **Vercel** — через CLI: `npx vercel --prod ./dist` (или подключение репозитория с настройкой root = `frontend`).

Так можно показать пару **без** публикации исходников, только одним архивом `dist`.

### Вариант B — деплой из GitHub (Netlify / Vercel / Cloudflare Pages)

- **Root / base directory**: `frontend`.
- **Build command**: `npm ci && npm run build`.
- **Publish directory**: `dist`.

В репозитории уже есть `frontend/netlify.toml` с `publish = "dist"`.

Снова же: в CI должны появиться JSON-тайлы до или во время `npm run build` (см. раздел про `public/data`).

### GitHub Pages (сайт вида `https://user.github.io/repo/`)

Нужен префикс пути в Vite:

```bash
cd frontend
npm run build -- --base=/ИМЯ_РЕПОЗИТОРИЯ/
```

Залей содержимое `dist` в ветку `gh-pages` или настрой GitHub Actions. Путь к данным подстроится автоматически (в коде используется `import.meta.env.BASE_URL`).

### Вариант C — временная публичная ссылка с домашнего ПК (туннель)

Смысл: на ноутбуке крутится **локальный сервер** (`vite preview`), а **туннель** пробрасывает его в интернет по `https://…`. Файлы никуда не заливаешь. Минусы: ноутбук и интернет должны быть включены; ссылка у **Cloudflare Quick Tunnel** и **ngrok free** обычно **временная**; любой, у кого есть URL, откроет сайт (не для секретов).

#### 0. Подготовка (один раз перед демо)

Убедись, что в `frontend/public/data/` есть JSON после экспорта из backend, затем:

```bash
cd frontend
npm ci
npm run build
```

#### 1. Запуск превью (терминал 1)

Слушать на всех интерфейсах, порт **4173** (уже настроено в `package.json`):

```bash
cd frontend
npm run preview:lan
```

Проверка локально: `http://localhost:4173`.

#### 2A. Cloudflare Quick Tunnel (терминал 2, без регистрации)

Установка **cloudflared** (пример для WSL/Ubuntu x86_64):

```bash
curl -L --fail https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/cloudflared
```

На **Windows** (без WSL): скачай `cloudflared-windows-amd64.exe` с [релизов cloudflared](https://github.com/cloudflare/cloudflared/releases), переименуй в `cloudflared.exe`, положи в PATH или запускай по полному пути; команда та же: `cloudflared tunnel --url http://127.0.0.1:4173`.

Запуск туннеля к превью:

```bash
cloudflared tunnel --url http://127.0.0.1:4173
```

В логе появится строка вида `https://….trycloudflare.com` — это публичный URL. Открой его **с телефона или другого ПК** (другой город тоже ок, если есть интернет).

Остановка: `Ctrl+C` в обоих терминалах.

#### 2B. ngrok (нужен аккаунт на [ngrok.com](https://ngrok.com), бесплатный план)

```bash
# после установки ngrok и привязки authtoken из личного кабинета
ngrok http 4173
```

В выводе будет `Forwarding https://….ngrok-free.app → http://localhost:4173`.

Если в консоли **`Unexpected token '<' … is not valid JSON`**: бесплатный ngrok часто подменяет ответы на **HTML** (заглушка). Запросы к `/data/*.json` идут через `fetch` в `src/data/loader.ts` — там уже добавлен заголовок **`ngrok-skip-browser-warning`**. Пересобери фронт (`npm run build`) и снова запусти `npm run preview:lan`, затем обнови страницу по ссылке ngrok. Если ошибка остаётся, проверь, что в **`dist/data/`** реально лежат JSON после экспорта из backend.

#### Заметки

- Если превью крутится в **WSL**, запускай **cloudflared/ngrok тоже из WSL** и указывай `127.0.0.1:4173`.
- Если превью на **Windows**, а туннель в WSL — иногда нужен `http://host.docker.internal:4173` или IP хоста; проще держать оба процесса в одной среде (оба в WSL или оба в Windows).
- Для пары на 3–4 часа достаточно не закрывать терминалы и не уводить ноутбук в сон.

---

## EN

To open the project **from another city** via a normal `https://…` URL, use **static hosting**: after `npm run build`, the app is plain HTML/JS/CSS plus a `data/` folder inside `dist/`.

### Data files (`frontend/public/data/`)

`*.json` under `frontend/public/data/` are **gitignored** and may not exist in the repo. Before a production build:

1. Generate and export tiles from `backend/` (see root `README.md`).
2. Confirm `meta.json`, `hex_*.json`, `arcs_*.json`, `lineages.json`, etc. are present under `frontend/public/data/`.
3. Run `npm run build` in `frontend/` — Vite **copies** `public/data` into `dist/data`.

If you deploy from Git without these files, the build will ship an empty dataset unless you commit tiles (`git add -f …`) or add a CI step that runs export before `npm run build`.

### Option A — simplest: upload built `dist`

1. Locally:

   ```bash
   cd frontend
   npm ci
   npm run build
   ```

2. Upload the **contents** of `frontend/dist` to:

   - **[Netlify Drop](https://app.netlify.com/drop)** — drag `dist`, get a URL like `https://random-name.netlify.app`.
   - **Cloudflare Pages** — direct upload of the build output.
   - **Vercel** — e.g. `npx vercel --prod ./dist`, or connect the repo with project root `frontend`.

### Option B — deploy from GitHub (Netlify / Vercel / Cloudflare Pages)

- **Base directory**: `frontend`
- **Build**: `npm ci && npm run build`
- **Output**: `dist`

`frontend/netlify.toml` already sets `publish = "dist"`.

Ensure JSON tiles exist before or during the build (see above).

### GitHub Pages (`https://user.github.io/repo/`)

Set Vite base to the repo name:

```bash
cd frontend
npm run build -- --base=/REPO_NAME/
```

Deploy `dist` to `gh-pages` or via Actions. Asset paths resolve via `import.meta.env.BASE_URL`.

### Option C — temporary public URL from your laptop (tunnel)

You run **Vite preview** locally and a **tunnel** exposes it on a public `https://…` URL. Nothing is uploaded to a host. Downsides: laptop and internet must stay on; **Cloudflare Quick Tunnel** and **free ngrok** URLs are usually **temporary**; anyone with the link can open the site (not for private data).

#### 0. Prep (once before demo)

Ensure `frontend/public/data/` contains JSON after backend export, then:

```bash
cd frontend
npm ci
npm run build
```

#### 1. Start preview (terminal 1)

Listen on all interfaces, port **4173** (see `package.json`):

```bash
cd frontend
npm run preview:lan
```

Local check: `http://localhost:4173`.

#### 2A. Cloudflare Quick Tunnel (terminal 2, no signup)

Install **cloudflared** (example: WSL/Ubuntu x86_64):

```bash
curl -L --fail https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/cloudflared
```

On **Windows** (no WSL): download `cloudflared-windows-amd64.exe` from [cloudflared releases](https://github.com/cloudflare/cloudflared/releases), rename to `cloudflared.exe`, add to PATH or run by full path; same command: `cloudflared tunnel --url http://127.0.0.1:4173`.

Start tunnel to preview:

```bash
cloudflared tunnel --url http://127.0.0.1:4173
```

Logs will show a URL like `https://….trycloudflare.com` — open it from another device or city.

Stop: `Ctrl+C` in both terminals.

#### 2B. ngrok ([ngrok.com](https://ngrok.com) account, free tier)

```bash
# after installing ngrok and `ngrok config add-authtoken …` from dashboard
ngrok http 4173
```

Output shows `Forwarding https://….ngrok-free.app → http://localhost:4173`.

If the console shows **`Unexpected token '<' … is not valid JSON`**: free ngrok often returns **HTML** (interstitial) instead of your `/data/*.json` files. `src/data/loader.ts` sends **`ngrok-skip-browser-warning`** on every JSON fetch — rebuild (`npm run build`), restart `npm run preview:lan`, hard-refresh the ngrok URL. If it still fails, confirm **`dist/data/`** actually contains JSON after backend export.

#### Notes

- If preview runs in **WSL**, run **cloudflared/ngrok in WSL** too, targeting `127.0.0.1:4173`.
- If preview is on Windows and tunnel in WSL, you may need the host IP or `host.docker.internal`; simplest is to run both tools in the same environment.
- For a 3–4 hour class, keep terminals open and prevent sleep.
