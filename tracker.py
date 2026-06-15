import re
import html
import requests
from datetime import datetime, timezone

FANDANGO_LINKS = {
    "Fandango Aug 8": "https://www.fandango.com/the-odyssey-2026-241283/movie-overview?date=2026-08-08&format=IMAX%2070MM",
    "Fandango Aug 9": "https://www.fandango.com/the-odyssey-2026-241283/movie-overview?date=2026-08-09&format=IMAX%2070MM",
    "Fandango Canary Jul 30": "https://www.fandango.com/the-odyssey-2026-241283/movie-overview?date=2026-07-30&format=IMAX%2070MM",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JoseTicketMonitor/1.0; personal-use)",
    "Accept-Language": "en-US,en;q=0.9",
}

STRONG_SIGNALS = [
    "amc lincoln square",
    "lincoln square 13",
    "amc lincoln",
    "new york city",
    "2026-08-08",
    "2026-08-09",
    "2026-07-30",
    "aug 8",
    "aug 9",
    "jul 30",
    "imax 70mm",
    "imax 70 mm",
    "showtime",
    "showtimes",
    "theater",
    "theatre",
    "ticketing",
    "performance",
    "seat",
    "sold out",
    "near you",
]

JSONISH_PATTERNS = [
    "__NEXT_DATA__",
    "window.__",
    "apollo",
    "redux",
    "showtimes",
    "theaters",
    "theatres",
    "performances",
    "movieId",
    "theaterId",
    "date",
]


def normalize(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def fetch(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    print(f"HTTP status: {response.status_code}")
    print(f"Final URL: {response.url}")
    response.raise_for_status()
    return normalize(response.text)


def count_occurrences(text: str, term: str) -> int:
    return text.count(term.lower())


def snippet_around(text: str, term: str, radius: int = 250) -> str:
    idx = text.find(term.lower())
    if idx == -1:
        return ""
    start = max(0, idx - radius)
    end = min(len(text), idx + radius)
    return text[start:end]


def analyze_page(label: str, url: str):
    print(f"\n\n=== {label} ===")
    print(f"URL: {url}")

    try:
        text = fetch(url)
    except Exception as e:
        print(f"ERROR fetching page: {e}")
        return

    print(f"Text length: {len(text)}")

    print("\nStrong signal counts:")
    for signal in STRONG_SIGNALS:
        count = count_occurrences(text, signal)
        if count:
            print(f"- {signal}: {count}")

    print("\nJSON/data pattern counts:")
    for pattern in JSONISH_PATTERNS:
        count = count_occurrences(text, pattern)
        if count:
            print(f"- {pattern}: {count}")

    print("\nMost useful snippets:")

    for term in [
        "amc lincoln square",
        "lincoln square",
        "2026-08-08",
        "2026-08-09",
        "2026-07-30",
        "imax 70mm",
        "showtimes",
        "theater",
        "ticketing",
        "__next_data__",
    ]:
        snippet = snippet_around(text, term)
        if snippet:
            print(f"\n--- around '{term}' ---")
            print(snippet[:800])


def main():
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at: {checked_at}")
    print("Mode: FANDANGO DEEP DIAGNOSTIC ONLY — no Discord alert will be sent.")

    for label, url in FANDANGO_LINKS.items():
        analyze_page(label, url)

    print("\n\nDone.")


if __name__ == "__main__":
    main()
