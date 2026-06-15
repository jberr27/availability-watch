from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

URLS = {
    "Fandango Theater Canary Jul 22": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-07-22",
    "Fandango Theater Canary Jul 30": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-07-30",
    "Fandango Theater Target Aug 8": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-08-08",
    "Fandango Theater Target Aug 9": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-08-09",
}

KEY_TERMS = [
    "the odyssey",
    "imax 70mm",
    "70mm",
    "amc lincoln square",
    "sold out",
    "get tickets",
    "buy tickets",
    "no showtimes",
    "showtimes",
    "loading calendar",
    "loading format filters",
]


def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def analyze_page(page, label: str, url: str):
    print(f"\n\n=== {label} ===")
    print(f"URL: {url}")

    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        print(f"Initial status: {response.status if response else 'unknown'}")

        page.wait_for_timeout(15000)

        text = normalize(page.locator("body").inner_text(timeout=15000))
        current_url = page.url

        print(f"Final browser URL: {current_url}")
        print(f"Visible text length: {len(text)}")

        print("\nVisible term counts:")
        for term in KEY_TERMS:
            count = text.count(term)
            if count:
                print(f"- {term}: {count}")

        for term in ["the odyssey", "sold out", "no showtimes", "get tickets", "buy tickets"]:
            idx = text.find(term)
            if idx != -1:
                start = max(0, idx - 250)
                end = min(len(text), idx + 500)
                print(f"\n--- visible snippet around '{term}' ---")
                print(text[start:end])

    except Exception as e:
        print(f"ERROR: {e}")


def main():
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at: {checked_at}")
    print("Mode: PLAYWRIGHT FANDANGO RENDER TEST — no Discord alert.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1365, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        for label, url in URLS.items():
            analyze_page(page, label, url)

        browser.close()

    print("\n\nDone.")


if __name__ == "__main__":
    main()
