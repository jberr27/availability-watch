import os
from datetime import datetime, timezone

import requests


def main() -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL secret.")

    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = (
        "✅ **Dune tracker heartbeat**\n"
        "Monitoring is active for new IMAX 70MM showtimes on Dec 18–20.\n"
        f"Heartbeat sent at: {checked_at}"
    )

    response = requests.post(webhook_url, json={"content": message}, timeout=15)
    response.raise_for_status()
    print("Daily Discord heartbeat sent successfully.")


if __name__ == "__main__":
    main()
