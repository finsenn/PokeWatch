# 🎴 PokeWatch

**A real-time Japanese Pokémon TCG sourcing bot.** Watches Mercari Japan for brand-new card listings and pushes them straight to your phone via Telegram — with the card image, price in yen, collector number, an English translation, and a one-tap price-check link.

Built for resellers who source Japanese singles and need to *see new drops the moment they appear* instead of endlessly refreshing the app.

---

## ✨ What it does

- **Watches Mercari Japan** for newly-listed Pokémon TCG cards (fixed-price only, no auctions)
- **Detects only new listings** — remembers what it has already shown you, so you never get spammed with the same cards twice
- **Pushes to Telegram** with:
  - 🖼️ the full-resolution card image
  - 💴 price in Japanese yen
  - 🎴 the collector number (e.g. `195/165`)
  - 🔤 a rough English translation of the listing name
  - 🔗 a copyable Mercari link (hand it straight to your proxy/shipper)
  - 📊 a one-tap "check price charting" search link
- **Runs all day** on a simple loop — set it and forget it

---

## 🛠️ How it works

```
Mercari search page  →  Playwright (headless browser)  →  parse listings
        →  compare against seen.txt (new only)  →  Telegram
```

It drives a real headless browser (Playwright) to load the normal Mercari search page and read the listings that appear — the same thing a person sees when browsing as a guest. New item IDs are tracked in a local `seen.txt` file so each run only surfaces genuinely fresh drops.

---

## 📦 Tech stack

- **Python 3.13**
- **Playwright** — headless browser automation
- **Telegram Bot API** — delivery to your phone
- **python-dotenv** — keeps secrets out of the code

---

## 🚀 Setup

### 1. Clone and enter the project
```bash
git clone https://github.com/YOUR_USERNAME/kaidowatch.git
cd kaidowatch
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Create your Telegram bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram → send `/newbot`
2. Copy the **bot token** it gives you
3. Message [@userinfobot](https://t.me/userinfobot) to get your **chat ID**

### 5. Add your secrets
Copy the example env file and fill in your values:
```bash
cp .env.example .env
```
```
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_telegram_chat_id_here
```

### 6. Run it
```bash
python scrape.py
```
You'll get a `🟢 started` message on Telegram. The first run records a baseline (sends nothing); every run after sends only new listings.

---

## ⚙️ Configuration

Edit the top of `scrape.py`:

| Setting | What it does |
|---|---|
| `CHECK_EVERY_MINUTES` | How often to scan (default `10`) |
| `SEARCH_URL` | The Mercari search to watch — swap the filters for different sets/brands |

---

## 📸 Screenshots

<!-- Add your screenshots here — see the "Screenshots needed" list below -->

| Telegram feed | Terminal running |
|---|---|
| _(card alert screenshot)_ | _(terminal screenshot)_ |

---

## ⚠️ Notes & limitations

- The English translation is a rough gist (via an unofficial translate endpoint) — good for a quick read, not perfect on card-specific terms.
- The "price charting" link opens a Google search you click through yourself — it does **not** scrape or bypass any site's protections.
- Runs while the host machine is on. For 24/7 use, host it on an always-on machine or small server.
- Personal tooling. Be respectful with scan frequency.

---
