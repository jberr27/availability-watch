import os
import sys

import requests


FAILURE_CONCLUSIONS = {
    "action_required",
    "cancelled",
    "failure",
    "startup_failure",
    "stale",
    "timed_out",
}


def is_failure(run: dict) -> bool:
    return run.get("conclusion") in FAILURE_CONCLUSIONS


def crossed_failure_threshold(previous_runs: list[dict], threshold: int = 3) -> bool:
    """The current run failed; alert only when this run first reaches threshold."""
    needed_previous_failures = threshold - 1
    if len(previous_runs) < needed_previous_failures:
        return False

    preceding = previous_runs[:needed_previous_failures]
    if not all(is_failure(run) for run in preceding):
        return False

    # Suppress repeated alerts on the fourth and later failures in one streak.
    older_run = previous_runs[needed_previous_failures:threshold]
    return not older_run or not is_failure(older_run[0])


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    current_run_id = os.environ.get("GITHUB_RUN_ID")
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not all((token, repository, current_run_id, webhook_url)):
        raise RuntimeError("Missing failure-monitor environment configuration.")

    api_url = (
        f"https://api.github.com/repos/{repository}/actions/workflows/"
        "run_tracker.yml/runs"
    )
    response = requests.get(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        params={"branch": "main", "event": "workflow_dispatch", "per_page": 10},
        timeout=15,
    )
    response.raise_for_status()

    previous_completed_runs = [
        run
        for run in response.json().get("workflow_runs", [])
        if str(run.get("id")) != current_run_id and run.get("status") == "completed"
    ]

    if not crossed_failure_threshold(previous_completed_runs):
        print("Failure threshold not newly reached. No Discord warning sent.")
        return 0

    run_url = f"https://github.com/{repository}/actions/runs/{current_run_id}"
    message = (
        "⚠️ @everyone **Dune tracker failed 3 checks in a row**\n"
        "Monitoring may be temporarily unavailable. Inspect the latest run:\n"
        f"{run_url}"
    )
    discord_response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=15,
    )
    discord_response.raise_for_status()
    print("Three-strike Discord warning sent.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FAILURE MONITOR ERROR: {error}", file=sys.stderr)
        raise
