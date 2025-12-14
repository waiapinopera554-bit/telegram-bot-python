import json
from datetime import datetime, timezone

import cloudscraper
from bs4 import BeautifulSoup

URL = "https://fragment.com/gifts?sort=price_asc&filter=sale"
OUT = "gifts_under_price.json"

MAX_PRICE = 8.0   # <-- غيّرها (مثلاً 2.0)
LIMIT = 200

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "desktop": True}
)

def t(el):
    return el.get_text(" ", strip=True) if el else None

def main():
    r = scraper.get(URL, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    items = []
    seen = set()

    # ✅ العناصر الصحيحة حسب HTML اللي عطيتني
    for a in soup.select("a.tm-grid-item[href^='/gift/']"):
        status_el = a.select_one(".tm-grid-item-status")
        status = t(status_el)
        if status != "For sale":
            continue

        price_el = a.select_one(".tm-grid-item-value.tm-value.icon-ton")
        if not price_el:
            continue
        try:
            price = float(price_el.get_text(strip=True))
        except:
            continue

        # بما أن الصفحة مرتبة من الأرخص، نقدر نوقف إذا تعدينا الحد
        if price > MAX_PRICE:
            break

        name = t(a.select_one(".item-name")) or t(a.select_one(".tm-grid-item-name")) or "Unknown"
        num = t(a.select_one(".item-num"))
        # رقم مثل "#119650" داخل item-num غالباً
        gift_no = num.replace("#", "").strip() if num else None

        time_el = a.select_one("time[datetime]")
        time_left = t(time_el)  # مثل: "364 days 2 hours"
        ends_at = time_el.get("datetime") if time_el else None

        href = a.get("href")
        link = "https://fragment.com" + href if href else None

        img_el = a.select_one("img.tm-grid-thumb")
        img = img_el.get("src") if img_el else None

        key = f"{href}-{price}"
        if key in seen:
            continue
        seen.add(key)

        items.append({
            "title": name,
            "gift_no": gift_no,
            "price_ton": price,
            "status": status,
            "time_left": time_left,
            "ends_at_datetime": ends_at,
            "link": link,
            "image": img
        })

        if len(items) >= LIMIT:
            break

    payload = {
        "source": URL,
        "max_price_ton": MAX_PRICE,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] wrote {len(items)} items -> {OUT}")
    if items:
        c = items[0]
        print(f"[CHEAPEST] {c['price_ton']} TON | {c['title']} #{c['gift_no']} | {c['link']}")

if __name__ == "__main__":
    main()
