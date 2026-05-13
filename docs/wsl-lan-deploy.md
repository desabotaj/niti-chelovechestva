# Демо по сети из WSL / LAN demo from WSL

## RU

### Что нужно для пары (другой ПК в той же сети Wi‑Fi)

1. На машине с проектом: собрать фронтенд и поднять **preview** (стабильнее, чем `dev`, на 3–4 часа нормально держится).
2. В **WSL2** сервер слушает `0.0.0.0`, но с **другого компьютера** к «внутреннему» IP WSL обычно **не подключиться** — нужен **проброс порта с Windows** на IP WSL (или показывать с того же ноутбука).

### Шаг 1 — запуск во WSL

```bash
cd /mnt/c/Users/toseh/data-art/frontend   # или свой путь к клону
npm ci
npm run demo:lan
```

Откроется превью на порту **4173** (см. `vite.config.ts` и `package.json`).

Проверка с того же ПК в Windows-браузере: `http://localhost:4173` (WSL обычно проксирует порты автоматически).

### Шаг 2 — узнать IP адрес WSL

Во WSL:

```bash
hostname -I | awk '{print $1}'
```

Запомни этот адрес (часто `172.x.x.x`).

### Шаг 3 — проброс порта в Windows (от имени администратора)

Открой **PowerShell от администратора** и подставь свой `WSL_IP` и порт **4173**:

```powershell
$wslIp = "172.???.???.???"   # из шага 2
netsh interface portproxy add v4tov4 listenport=4173 listenaddress=0.0.0.0 connectport=4173 connectaddress=$wslIp
```

Узнать LAN-IP **Windows** (его вводят на другом ПК):

```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notlike '169.254.*' }).IPAddress
```

На **другом ПК** в браузере: `http://<LAN_IP_Windows>:4173`

### Шаг 4 — брандмауэр Windows

Разреши входящий TCP **4173** для частной сети (или временное правило):

```powershell
New-NetFirewallRule -DisplayName "Vite preview 4173" -Direction Inbound -LocalPort 4173 -Protocol TCP -Action Allow
```

### Долгая сессия (3–4 часа)

- Держи открытым терминал WSL или запусти в **tmux** / **screen**, чтобы случайно не закрыть сессию.
- Для демо лучше **preview** (`npm run demo:lan`), а не `dev`: меньше нагрузка и перезапусков.

### Убрать проброс после пары

```powershell
netsh interface portproxy delete v4tov4 listenport=4173 listenaddress=0.0.0.0
```

---

## EN

### Showing from another PC on the same Wi‑Fi

1. On the laptop with the repo: build the frontend and run **Vite preview** (more stable than `dev` for a 3–4 hour session).
2. On **WSL2**, the server listens on `0.0.0.0`, but another machine usually **cannot** reach the WSL internal IP directly — add a **Windows port forward** from your LAN IP to the WSL IP (or demo from the same laptop).

### Step 1 — run in WSL

```bash
cd /path/to/data-art/frontend
npm ci
npm run demo:lan
```

Preview listens on port **4173**.

On the same machine, Windows browser: `http://localhost:4173`.

### Step 2 — WSL IP

In WSL:

```bash
hostname -I | awk '{print $1}'
```

### Step 3 — Windows port proxy (Administrator PowerShell)

```powershell
$wslIp = "172.???.???.???"
netsh interface portproxy add v4tov4 listenport=4173 listenaddress=0.0.0.0 connectport=4173 connectaddress=$wslIp
```

Find the Windows **LAN** IP (use this on the classroom PC):

```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notlike '169.254.*' }).IPAddress
```

On the **other PC**: `http://<Windows_LAN_IP>:4173`

### Step 4 — Windows Firewall

```powershell
New-NetFirewallRule -DisplayName "Vite preview 4173" -Direction Inbound -LocalPort 4173 -Protocol TCP -Action Allow
```

### Long session

Use **tmux** / **screen** so you do not close the terminal by accident. Prefer **preview** over `dev` for demos.

### Remove proxy after class

```powershell
netsh interface portproxy delete v4tov4 listenport=4173 listenaddress=0.0.0.0
```
