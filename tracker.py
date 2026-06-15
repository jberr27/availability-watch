import os
import re
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

ATOM_LINCOLN_SQUARE_URL = "https://www.atomtickets.com/theaters/amc-lincoln-square-13/164"

# Canary = already-known Odyssey date.
# This should be found if the tracker is reading the right page.
CANARY_PATTERNS = [
    r"the odyssey",
    r"sunday jul 26",
    r"thursday aug 6",
]

# Targets = what we actually care about.
TARGET_PATTERNS = [
    r"saturday aug 8",
    r"sunday aug 9",
    r"aug 8",
    r"aug 9",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}


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


def all_patterns_found(page_text: str, patterns: list[str]) -> bool:
    return all(re.search(pattern, page_text) for pattern in patterns)


def any_pattern_found(page_text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, page_text) for pattern in patterns)


def main() -> None:
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at {checked_at}")
    print(f"Checking Atom page: {ATOM_LINCOLN_SQUARE_URL}")

    page_text = fetch_page(ATOM_LINCOLN_SQUARE_URL)

    canary_ok = all_patterns_found(page_text, CANARY_PATTERNS)
    target_found = any_pattern_found(page_text, TARGET_PATTERNS) and "the odyssey" in page_text

    if canary_ok:
        print("CANARY PASS: Found The Odyssey plus known released dates Jul 26 and Aug 6.")
    else:
        print("CANARY WARNING: Could not confirm known Odyssey dates. Page format may have changed.")

    if target_found:
        message = (
            "🚨 @everyone **POSSIBLE ODYSSEY AUG 8/9 DROP DETECTED** 🚨\n\n"
            "Atom’s AMC Lincoln Square page appears to show Aug 8 or Aug 9.\n"
            f"Check immediately: {ATOM_LINCOLN_SQUARE_URL}\n\n"
            f"Checked at: {checked_at}"
        )
        send_discord_message(message)
        print("TARGET FOUND: Discord alert sent.")
    else:
        print("TARGET NOT FOUND: Aug 8/9 do not appear listed yet.")


if __name__ == "__main__":
    main()
