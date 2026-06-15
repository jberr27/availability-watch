import os
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import requests

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

FANDANGO_TARGETS = {
    "Aug 8": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-08-08",
    "Aug 9": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-08-09",
}

FANDANGO_CANARIES = {
    "Jul 22": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-07-22",
    "Jul 30": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-07-30",
}

AMC_BUY_LINKS = {
    "Aug 8": "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-08-08",
    "Aug 9": "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-08-09",
}

SIGNAL_TERMS = [
    "imax 70mm",
    "imax 70 mm",
    "70mm",
    "70 mm",
]


def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def send_discord_message(message: str):
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL secret.")

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=15,
    )
    response.raise_for_status()


def page_has_70mm_signal(text: str) -> bool:
    return any(term in text for term in SIGNAL_TERMS)


def get_visible_text(page, label: str, url: str) -> str:
    print(f"\n=== Checking {label} ===")
    print(f"URL: {url}")

    response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
    print(f"Initial status: {response.status if response else 'unknown'}")

    # Give Fandango time to render lazy-loaded filters/content.
    page.wait_for_timeout(15000)

    text = normalize(page.locator("body").inner_text(timeout=15000))

    print(f"Final browser URL: {page.url}")
    print(f"Visible text length: {len(text)}")

    for term in SIGNAL_TERMS:
        count = text.count(term)
        if count:
            print(f"Signal term '{term}': {count}")

    return text


def main():
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at: {checked_at}")
    print("Mode: PRODUCTION — alert if Aug 8/9 Fandango shows IMAX 70MM signal.")

    detected_dates = []
    canary_passed = False

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

        print("\n\n################")
        print("# CANARY CHECKS")
        print("################")

        for label, url in FANDANGO_CANARIES.items():
            text = get_visible_text(page, f"Canary {label}", url)
            if page_has_70mm_signal(text):
                canary_passed = True
                print(f"CANARY PASS: {label} shows IMAX 70MM / 70MM signal.")
            else:
                print(f"CANARY WARNING: {label} did not show IMAX 70MM / 70MM signal.")

        print("\n\n################")
        print("# TARGET CHECKS")
        print("################")

        for label, url in FANDANGO_TARGETS.items():
            text = get_visible_text(page, f"Target {label}", url)

            if page_has_70mm_signal(text):
                detected_dates.append(label)
                print(f"TARGET SIGNAL FOUND: {label} shows IMAX 70MM / 70MM.")
            else:
                print(f"TARGET NOT FOUND: {label} does not show IMAX 70MM / 70MM yet.")

        browser.close()

    if detected_dates:
        date_text = ", ".join(detected_dates)

        message = (
            f"🚨 @everyone **POSSIBLE ODYSSEY IMAX 70MM DROP DETECTED: {date_text}** 🚨\n\n"
            "Fandango's AMC Lincoln Square page is showing an IMAX 70MM signal for the target date(s).\n\n"
            "**Open AMC immediately:**\n"
            f"Aug 8: {AMC_BUY_LINKS['Aug 8']}\n"
            f"Aug 9: {AMC_BUY_LINKS['Aug 9']}\n\n"
            "**Backup Fandango pages:**\n"
            f"Aug 8: {FANDANGO_TARGETS['Aug 8']}\n"
            f"Aug 9: {FANDANGO_TARGETS['Aug 9']}\n\n"
            f"Checked at: {checked_at}"
        )

        send_discord_message(message)
        print("DISCORD ALERT SENT.")
    else:
        print("\nNo target dates detected. No Discord alert sent.")

    if not canary_passed:
        print("\nWARNING: Canary did not pass. Detector may be unreliable right now.")


if __name__ == "__main__":
    main()
