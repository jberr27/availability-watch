import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


def load_config() -> dict:
    raw = os.environ.get("WATCH_CONFIG")
    if not raw:
        raise RuntimeError("Missing WATCH_CONFIG secret.")

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"WATCH_CONFIG is not valid JSON: {error}") from error

    required = ["alert_title", "default_signal_terms", "canaries", "targets"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise RuntimeError(f"WATCH_CONFIG is missing: {', '.join(missing)}")

    for group in ("canaries", "targets"):
        for item in config[group]:
            if not item.get("label") or not item.get("url"):
                raise RuntimeError(f"Each {group} entry needs label and url.")

    return config


def normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def signal_terms(item: dict, config: dict) -> list[str]:
    return [
        normalize(term)
        for term in item.get("signal_terms", config["default_signal_terms"])
        if normalize(term)
    ]


def matching_terms(text: str, item: dict, config: dict) -> list[str]:
    terms = signal_terms(item, config)
    hits = [term for term in terms if term in text]
    mode = item.get("match", config.get("default_match", "any"))

    if mode == "all":
        return hits if len(hits) == len(terms) else []
    if mode != "any":
        raise RuntimeError(f"Unsupported match mode: {mode}")
    return hits


SHOWTIME_PATTERN = re.compile(r"\b(?:1[0-2]|[1-9]):[0-5]\d\s*[ap](?:m)?\b")


def section_text(text: str, item: dict) -> str:
    start_marker = normalize(item.get("section_start", ""))
    end_marker = normalize(item.get("section_end", ""))
    if not start_marker:
        return text

    start = text.find(start_marker)
    if start == -1:
        return ""

    section = text[start:]
    if end_marker:
        end = section.find(end_marker, len(start_marker))
        if end != -1:
            section = section[:end]
    return section


def normalized_showtime(value: str) -> str:
    return normalize(value).replace(" ", "").removesuffix("m")


def new_showtimes(text: str, item: dict) -> list[str]:
    scoped_text = section_text(text, item)
    if not scoped_text:
        return []

    baseline = {
        normalized_showtime(value) for value in item.get("baseline_times", [])
    }
    discovered = {
        normalized_showtime(value) for value in SHOWTIME_PATTERN.findall(scoped_text)
    }
    return sorted(discovered - baseline)


def detection_hits(text: str, item: dict, config: dict) -> list[str]:
    detection = item.get("detection", "terms")
    if detection == "terms":
        return matching_terms(text, item, config)
    if detection == "new_showtimes":
        return new_showtimes(text, item)
    raise RuntimeError(f"Unsupported detection mode: {detection}")


def send_discord_message(webhook_url: str, message: str) -> None:
    response = requests.post(webhook_url, json={"content": message}, timeout=15)
    response.raise_for_status()


def rendered_text(page, item: dict, config: dict) -> tuple[str, list[str]]:
    label = item["label"]
    url = item["url"]
    timeout_seconds = int(config.get("render_timeout_seconds", 15))

    print(f"\n=== Checking {label} ===")
    print(f"URL: {url}")

    response = page.goto(url, wait_until="domcontentloaded", timeout=45_000)
    print(f"Initial status: {response.status if response else 'unknown'}")

    last_text = ""
    for _ in range(timeout_seconds):
        try:
            last_text = normalize(page.locator("body").inner_text(timeout=3_000))
        except PlaywrightTimeoutError:
            last_text = ""

        hits = detection_hits(last_text, item, config)
        if hits:
            print(f"Signal detected after rendering: {', '.join(hits)}")
            return last_text, hits
        page.wait_for_timeout(1_000)

    print(f"No signal after {timeout_seconds} seconds of rendering.")
    return last_text, []


def main() -> int:
    config = load_config()
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL secret.")

    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"Checked at: {checked_at}")
    print("Mode: repeat alerts while configured target signals are visible.")

    canary_results: list[bool] = []
    detected_targets: list[tuple[dict, list[str]]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1365, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        try:
            print("\n# HEALTH CHECKS")
            for item in config["canaries"]:
                _, hits = rendered_text(page, item, config)
                passed = bool(hits)
                canary_results.append(passed)
                print(f"HEALTH {'PASS' if passed else 'FAIL'}: {item['label']}")

            if not all(canary_results):
                print("Health checks failed. Targets were not evaluated.")
                return 2

            print("\n# TARGET CHECKS")
            for item in config["targets"]:
                _, hits = rendered_text(page, item, config)
                if hits:
                    detected_targets.append((item, hits))
                    print(f"TARGET FOUND: {item['label']} ({', '.join(hits)})")
                else:
                    print(f"TARGET NOT FOUND: {item['label']}")
        finally:
            browser.close()

    if not detected_targets:
        print("\nNo target signals detected. No Discord alert sent.")
        return 0

    labels = ", ".join(
        f"{item['label']} ({', '.join(hits)})"
        for item, hits in detected_targets
    )
    links = []
    for item, _ in detected_targets:
        link = item.get("action_url") or config.get("default_action_url") or item["url"]
        links.append(f"{item['label']}: {link}")

    mention = config.get("mention", "@everyone")
    message = (
        f"🚨 {mention} **{config['alert_title']}: {labels}** 🚨\n\n"
        + "\n".join(links)
        + f"\n\nChecked at: {checked_at}"
    )
    send_discord_message(webhook_url, message)
    print("DISCORD ALERT SENT.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"TRACKER ERROR: {error}", file=sys.stderr)
        raise
