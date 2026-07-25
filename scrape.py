# scrape.py — live Mercari TCG monitor: new listings -> Telegram
# Sharp photo + yen price + collector number + EN translation + copyable Mercari link + PriceCharting search link
# Run:  python scrape.py   (Ctrl+C to stop)

import re
import os
import time
import requests
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright

# brand_id 47084 = Pokémon TCG only; d664efe3 = normal listing (no auction); newest first
SEARCH_URL = (
    "https://jp.mercari.com/search?"
    "brand_id=47084"
    "&d664efe3-ae5a-4824-b729-e789bf93aba9=B38F1DC9286E0B80812D9B19DB14298C1FF1116CA8332D9EE9061026635C9088"
    "&sort=created_time&order=desc"
)

SEEN_FILE = "seen.txt"
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHECK_EVERY_MINUTES = 10

def translate(text):
    # Free Google Translate endpoint (unofficial). Rough but works for gist.
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "ja", "tl": "en", "dt": "t", "q": text},
            timeout=10,
        )
        data = r.json()
        return "".join(chunk[0] for chunk in data[0])
    except Exception:
        return ""

def send_telegram_photo_html(photo_url, caption):
    # Photo + caption with HTML so PRICE CHARTING renders as a clickable link
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML",
        }, timeout=15)
    except Exception as e:
        print(f"Telegram photo send failed: {e}")

def send_telegram(text):
    # Plain text (startup message + fallback)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID, "text": text,
            "disable_web_page_preview": True,
        }, timeout=15)
    except Exception as e:
        print(f"Telegram send failed: {e}")

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen(all_ids):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        for i in all_ids:
            f.write(i + "\n")

def scan_once(page, seen):
    page.goto(SEARCH_URL)
    page.wait_for_selector('li[data-testid="item-cell"]', timeout=30000)
    for _ in range(30):
        page.mouse.wheel(0, 1500)
        page.wait_for_timeout(400)
    page.mouse.wheel(0, -50000)
    page.wait_for_timeout(1000)

    items = page.query_selector_all('li[data-testid="item-cell"]')
    new_cards = []
    all_ids = set(seen)

    for item in items:
        link_el = item.query_selector('a[data-testid="thumbnail-link"]')
        name_el = item.query_selector('span[data-testid="thumbnail-item-name"]')
        thumb_el = item.query_selector('.merItemThumbnail')

        link = link_el.get_attribute("href") if link_el else None
        name = name_el.inner_text() if name_el else "(no name)"
        if name == "(no name)" or not link:
            continue

        # Skip shop/store listings (sealed boxes etc) — remove this block if you want them
        if "/shops/product/" in link:
            item_id = link.split("/product/")[-1]
            all_ids.add(item_id)
            continue

        price = None
        if thumb_el:
            label = thumb_el.get_attribute("aria-label") or ""
            m = re.search(r'([\d,]+)円', label)
            if m:
                price = int(m.group(1).replace(",", ""))

        if not link.startswith("http"):
            link = "https://jp.mercari.com" + link
        item_id = link.split("/item/")[-1]

        all_ids.add(item_id)
        if item_id in seen:
            continue

        num_match = re.search(r'\d{1,3}/\d{1,3}', name)
        collector_no = num_match.group(0) if num_match else "—"

        # Full-res image URL built from item ID (thumbnails are blurry)
        img_url = f"https://static.mercdn.net/item/detail/webp/photos/{item_id}_1.jpg"

        new_cards.append({
            "name": name, "price": price, "link": link,
            "collector_no": collector_no, "img": img_url,
        })

    return new_cards, all_ids

def main():
    seen = load_seen()
    first_run = len(seen) == 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Bot started. Watching Mercari TCG... (Ctrl+C to stop)")
        send_telegram("🟢 Mercari TCG watcher started.")

        while True:
            try:
                new_cards, all_ids = scan_once(page, seen)

                if first_run:
                    print(f"First run — baseline {len(all_ids)} recorded, nothing sent.")
                    first_run = False
                else:
                    print(f"{len(new_cards)} new listings.")
                    for r in new_cards:
                            price = f"{r['price']:,}" if r['price'] else "?"
                            en = translate(r["name"])

                            # Use ENGLISH name + collector number for the search (JP name fails)
                            search_terms = en if en else r["name"]
                            if r["collector_no"] != "—":
                                search_terms += f" {r['collector_no']}"
                            query = quote_plus(f"{search_terms} pricecharting")
                            pc_link = f"https://www.google.com/search?q={query}"

                            caption = f"💴 {price} yen  🎴 {r['collector_no']}\n"
                            if en:
                                caption += f"{en}\n"
                            caption += f"{r['link']}\n"
                            caption += f'━━━━━━━━━\n'
                            caption += f'<a href="{pc_link}">📊 check price charting →</a>'

                            if r["img"]:
                                send_telegram_photo_html(r["img"], caption)
                            else:
                                send_telegram(caption.replace(f'<a href="{pc_link}">📊 check price charting →</a>', pc_link))
                seen = all_ids
                save_seen(all_ids)
            except Exception as e:
                print(f"Scan error (will retry): {e}")

            time.sleep(CHECK_EVERY_MINUTES * 60)

if __name__ == "__main__":
    main()