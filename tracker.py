import os
import re
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

CANARY_URL = "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-07-16"

TARGET_URLS = [
    "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-08-08",
    "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-08-09",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url: str):
    response = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    text = response.text.lower()
    return response.status_code, response.url, text


def summarize_page(label: str, url: str):
    status, final_url, text = fetch(url)

    print(f"\n--- {label} ---")
    print(f"Requested URL: {url}")
    print(f"HTTP status: {status}")
    print(f"Final URL: {final_url}")
    print(f"Text length: {len(text)}")

    checks = {
        "contains_the_odyssey": "the odyssey" in text,
        "contains_imax_70": bool(re.search(r"imax\s*70|70\s*mm", text)),
        "contains_queue": "queue.amctheatres.com" in final_url or "global safety net" in text or "requires javascript" in text,
        "contains_no_showtimes": "no showtimes" in text,
    }

    for key, value in checks.items():
        print(f"{key}: {value}")

    snippet = text[:500].replace("\n", " ")
    print(f"First 500 chars: {snippet}")

    return checks


def send_discord_message(message: str):
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL secret.")

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=15,
    )
    response.raise_for_status()


def main():
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at {checked_at}")

    canary = summarize_page("CANARY July 16 known-live AMC page", CANARY_URL)

    target_results = []
    for url in TARGET_URLS:
        target_results.append(summarize_page("TARGET Aug 8/9 AMC page", url))

    if canary["contains_queue"]:
        print("\nDIAGNOSIS: GitHub is being sent to AMC queue/safety page. Plain AMC scraping is unreliable.")
    elif canary["contains_the_odyssey"] and canary["contains_imax_70"]:
        print("\nCANARY PASS: GitHub can see the known Odyssey IMAX 70mm AMC page.")
    else:
        print("\nCANARY FAIL: GitHub reached AMC but did not see expected Odyssey text.")

    target_found = any(
        result["contains_the_odyssey"] and result["contains_imax_70"]
        for result in target_results
    )

    if target_found:
        send_discord_message(
            "🚨 @everyone POSSIBLE ODYSSEY AUG 8/9 DROP DETECTED 🚨\n"
            "Check AMC Lincoln Square immediately."
        )
        print("TARGET FOUND: Discord alert sent.")
    else:
        print("TARGET NOT FOUND: No Aug 8/9 Odyssey IMAX 70mm detected.")


if __name__ == "__main__":
    main()
