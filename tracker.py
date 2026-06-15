import os
import re
import html
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

AMC_LINKS = {
    "AMC Aug 8": "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-08-08",
    "AMC Aug 9": "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-08-09",
    "AMC Canary Jul 30": "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes?date=2026-07-30",
}

FANDANGO_LINKS = {
    "Fandango Aug 8": "https://www.fandango.com/the-odyssey-2026-241283/movie-overview?date=2026-08-08&format=IMAX%2070MM",
    "Fandango Aug 9": "https://www.fandango.com/the-odyssey-2026-241283/movie-overview?date=2026-08-09&format=IMAX%2070MM",
    "Fandango Canary Jul 30": "https://www.fandango.com/the-odyssey-2026-241283/movie-overview?date=2026-07-30&format=IMAX%2070MM",
}

IMAX_LINKS = {
    "IMAX Odyssey Page": "https://www.imax.com/movie/the-odyssey",
}

REDDIT_RSS_LINKS = {
    "Reddit search: Odyssey Lincoln Square": "https://www.reddit.com/search.rss?q=%22Odyssey%22%20%22Lincoln%20Square%22&sort=new",
    "Reddit search: Odyssey IMAX 70mm": "https://www.reddit.com/search.rss?q=%22Odyssey%22%20%22IMAX%2070mm%22&sort=new",
    "Reddit search: AMC Lincoln Square tickets": "https://www.reddit.com/search.rss?q=%22AMC%20Lincoln%20Square%22%20tickets&sort=new",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JoseTicketMonitor/1.0; +personal-use)",
    "Accept-Language": "en-US,en;q=0.9",
}

KEYWORDS = [
    "the odyssey",
    "odyssey",
    "lincoln square",
    "amc lincoln",
    "imax 70",
    "imax 70mm",
    "70mm",
    "aug 8",
    "august 8",
    "aug 9",
    "august 9",
    "new dates",
    "tickets live",
    "on sale",
    "showtimes",
    "get tickets",
    "sold out",
]

TARGET_SIGNALS = [
    "aug 8",
    "august 8",
    "aug 9",
    "august 9",
    "new dates",
    "tickets live",
    "on sale",
    "showtimes",
    "get tickets",
]


def normalize(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def fetch_url(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        return {
            "ok": True,
            "status": response.status_code,
            "final_url": response.url,
            "text": normalize(response.text),
            "error": None,
        }
    except Exception as e:
        return {
            "ok": False,
            "status": None,
            "final_url": None,
            "text": "",
            "error": str(e),
        }


def keyword_hits(text: str):
    return [kw for kw in KEYWORDS if kw in text]


def target_hits(text: str):
    return [kw for kw in TARGET_SIGNALS if kw in text]


def contains_queue_signal(final_url: str, text: str):
    final_url = final_url or ""
    return (
        "queue.amctheatres.com" in final_url
        or "global safety net" in text
        or "enqueuetoken" in text
        or "requires javascript" in text
    )


def snippet_around(text: str, terms):
    for term in terms:
        idx = text.find(term)
        if idx != -1:
            start = max(0, idx - 160)
            end = min(len(text), idx + 260)
            return text[start:end]
    return text[:420]


def score_source(text: str):
    """
    Rough signal score:
    - Odyssey/movie relevance
    - Lincoln Square relevance
    - target date / sale language
    """
    score = 0

    if "odyssey" in text:
        score += 2
    if "lincoln square" in text or "amc lincoln" in text:
        score += 3
    if "imax 70" in text or "70mm" in text:
        score += 2
    if any(term in text for term in ["aug 8", "august 8", "aug 9", "august 9"]):
        score += 5
    if any(term in text for term in ["new dates", "tickets live", "on sale", "get tickets", "showtimes"]):
        score += 2

    return score


def print_web_page_diagnostic(label: str, url: str):
    result = fetch_url(url)
    text = result["text"]

    print(f"\n=== {label} ===")
    print(f"Requested: {url}")
    print(f"OK: {result['ok']}")
    print(f"HTTP status: {result['status']}")
    print(f"Final URL: {result['final_url']}")
    print(f"Text length: {len(text)}")

    if result["error"]:
        print(f"ERROR: {result['error']}")
        return

    queue = contains_queue_signal(result["final_url"], text)
    hits = keyword_hits(text)
    targets = target_hits(text)
    score = score_source(text)

    print(f"Queue/safety page detected: {queue}")
    print(f"Keyword hits: {hits}")
    print(f"Target hits: {targets}")
    print(f"Signal score: {score}")

    print("Snippet:")
    print(snippet_around(text, hits or targets))


def print_reddit_rss_diagnostic(label: str, url: str):
    result = fetch_url(url)
    text = result["text"]

    print(f"\n=== {label} ===")
    print(f"Requested: {url}")
    print(f"OK: {result['ok']}")
    print(f"HTTP status: {result['status']}")
    print(f"Final URL: {result['final_url']}")
    print(f"Text length: {len(text)}")

    if result["error"]:
        print(f"ERROR: {result['error']}")
        return

    try:
        root = ET.fromstring(result["text"])
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")

        print(f"RSS entries found: {len(entries)}")

        for i, entry in enumerate(entries[:5], start=1):
            title_el = entry.find("{http://www.w3.org/2005/Atom}title")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            updated_el = entry.find("{http://www.w3.org/2005/Atom}updated")

            title = normalize(title_el.text if title_el is not None else "")
            updated = updated_el.text if updated_el is not None else "unknown"
            link = link_el.attrib.get("href", "unknown") if link_el is not None else "unknown"

            hits = keyword_hits(title)
            targets = target_hits(title)
            score = score_source(title)

            print(f"\nEntry {i}:")
            print(f"Title: {title}")
            print(f"Updated: {updated}")
            print(f"Link: {link}")
            print(f"Keyword hits: {hits}")
            print(f"Target hits: {targets}")
            print(f"Signal score: {score}")

    except Exception as e:
        print(f"RSS parse warning: {e}")
        print("Raw snippet:")
        print(text[:600])


def main():
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at: {checked_at}")
    print("Mode: DIAGNOSTIC ONLY — no Discord alert will be sent.")

    print("\n\n############################")
    print("# AMC DIRECT URL DIAGNOSTIC")
    print("############################")
    for label, url in AMC_LINKS.items():
        print_web_page_diagnostic(label, url)

    print("\n\n############################")
    print("# FANDANGO DIAGNOSTIC")
    print("############################")
    for label, url in FANDANGO_LINKS.items():
        print_web_page_diagnostic(label, url)

    print("\n\n############################")
    print("# IMAX DIAGNOSTIC")
    print("############################")
    for label, url in IMAX_LINKS.items():
        print_web_page_diagnostic(label, url)

    print("\n\n############################")
    print("# REDDIT RSS DIAGNOSTIC")
    print("############################")
    for label, url in REDDIT_RSS_LINKS.items():
        print_reddit_rss_diagnostic(label, url)

    print("\n\nDone.")


if __name__ == "__main__":
    main()
