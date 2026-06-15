import os
import re
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

TARGET_DATES = ["2026-08-08", "2026-08-09"]

SHOWTIME_URLS = [
    f"https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date={date}"
    for date in TARGET_DATES
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

# Words we expect to see once the right ticket block appears.
MOVIE_PATTERNS = [
    r"the\s+odyssey",
    r"odyssey",
]

FORMAT_PATTERNS = [
    r"imax\s*70\s*mm",
    r"imax\s*70mm",
    r"70\s*mm",
]


def send_discord_message(message: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL GitHub secret.")

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=15,
    )
    response.raise_for_status()


def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text.lower()


def has_match(page_text: str) -> bool:
    movie_found = any(re.search(pattern, page_text) for pattern in MOVIE_PATTERNS)
    format_found = any(re.search(pattern, page_text) for pattern in FORMAT_PATTERNS)

    # We want Odyssey + some indication of IMAX 70mm/70mm.
    return movie_found and format_found


def main() -> None:
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"Checked at {checked_at}")

    matches = []

    for url in SHOWTIME_URLS:
        print(f"Checking {url}")

        try:
            page_text = fetch_page(url)

            if has_match(page_text):
                matches.append(url)

        except Exception as error:
            print(f"Error checking {url}: {error}")

    if matches:
        message = (
            "🚨 @everyone **THE ODYSSEY IMAX 70MM MAY BE LIVE AT AMC LINCOLN SQUARE** 🚨\n\n"
            "Check these links immediately:\n"
            + "\n".join(matches)
            + f"\n\nChecked at: {checked_at}"
        )

        send_discord_message(message)
        print("Match found. Discord alert sent.")
    else:
        print("No matching Odyssey IMAX 70mm showtimes found yet.")


if __name__ == "__main__":
    main()
