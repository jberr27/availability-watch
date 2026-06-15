import os
import requests
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# For now, this is a placeholder-style AMC check.
# We'll first prove GitHub can run Python and send your Discord alert.
AMC_URL = "https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13"

TARGET_DATES = ["2026-08-08", "2026-08-09"]
MOVIE_KEYWORD = "odyssey"


def send_discord_message(message):
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("Missing DISCORD_WEBHOOK_URL secret.")

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=15
    )
    response.raise_for_status()


def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Test mode first: prove the workflow can send an alert.
    # After this works, we’ll replace this with the real AMC checker.
    message = (
        "✅ AMC tracker test worked.\n"
        f"Checked at: {now}\n"
        "Next step: connect this to the real Odyssey/Lincoln Square showtime check."
    )

    send_discord_message(message)
    print("Discord test message sent successfully.")


if __name__ == "__main__":
    main()
