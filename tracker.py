import re
import html
import requests
from datetime import datetime, timezone

FANDANGO_THEATER_LINKS = {
    "Fandango Theater Canary Jul 22": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-07-22",
    "Fandango Theater Canary Jul 30": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-07-30",
    "Fandango Theater Target Aug 8": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-08-08",
    "Fandango Theater Target Aug 9": "https://www.fandango.com/amc-lincoln-square-13-aabqi/theater-page?format=IMAX%2070MM&date=2026-08-09",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JoseTicketMonitor/1.0; personal-use)",
    "Accept-Language": "en-US,en;q=0.9",
}

SIGNALS = [
    "amc lincoln square 13",
    "1998 broadway",
    "the odyssey",
    "odyssey",
    "imax 70mm",
    "imax 70 mm",
    "70mm",
    "jul 22",
    "jul 30",
    "aug 8",
    "aug 9",
    "2026-07-22",
    "2026-07-30",
    "2026-08-08",
    "2026-08-09",
    "get tickets",
    "buy tickets",
    "sold out",
    "no showtimes",
    "loading calendar",
    "loading format filters",
    "movie-times",
    "showtime",
    "showtimes",
    "ticketing",
    "performance",
    "seat",
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

def snippet_around(text: str, term: str, radius: int = 300) -> str:
    idx = text.find(term.lower())
    if idx == -1:
        return ""
    start = max(0, idx - radius)
    end = min(len(text), idx + radius)
    return text[start:end]

def analyze(label: str, url: str):
    print(f"\n\n=== {label} ===")
    print(f"URL: {url}")

    try:
        text = fetch(url)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    print(f"Text length: {len(text)}")

    print("\nSignal counts:")
    for signal in SIGNALS:
        count = text.count(signal.lower())
        if count:
            print(f"- {signal}: {count}")

    print("\nKey snippets:")
    for term in [
        "the odyssey",
        "amc lincoln square 13",
        "1998 broadway",
        "imax 70mm",
        "get tickets",
        "sold out",
        "no showtimes",
        "loading calendar",
        "showtimes",
    ]:
        snippet = snippet_around(text, term)
        if snippet:
            print(f"\n--- around '{term}' ---")
            print(snippet[:900])

def main():
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at: {checked_at}")
    print("Mode: FANDANGO THEATER-PAGE DIAGNOSTIC ONLY — no Discord alert.")

    for label, url in FANDANGO_THEATER_LINKS.items():
        analyze(label, url)

    print("\n\nDone.")

if __name__ == "__main__":
    main()
