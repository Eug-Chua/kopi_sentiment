#!/usr/bin/env python3
"""
Railway cron job runner for kopi_sentiment.

This script handles:
1. Running daily or weekly analysis
2. Committing results back to GitHub
3. Triggering a Vercel/GitHub Pages rebuild (optional)

Usage:
    python run.py daily [--date YYYY-MM-DD]
    python run.py weekly [--week YYYY-Www]
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed with code {result.returncode}")
    return result


def setup_git():
    """Configure git for committing."""
    run_command(["git", "config", "--global", "user.email", "railway-bot@kopi-sentiment.app"])
    run_command(["git", "config", "--global", "user.name", "Railway Bot"])


def clone_repo():
    """Clone the repository using the GitHub token."""
    github_token = os.environ.get("GITHUB_TOKEN")
    repo_url = os.environ.get("GITHUB_REPO", "github.com/eugenechua/kopi_sentiment")

    if not github_token:
        raise RuntimeError("GITHUB_TOKEN environment variable is required")

    # Clone with token auth
    auth_url = f"https://x-access-token:{github_token}@{repo_url}.git"
    run_command(["git", "clone", "--depth", "1", auth_url, "/app/repo"])
    os.chdir("/app/repo")


def run_daily_analysis(date: str | None = None):
    """Run daily sentiment analysis."""
    cmd = ["python", "-m", "kopi_sentiment.cli", "daily"]
    if date:
        cmd.extend(["--date", date])
    run_command(cmd)


def run_weekly_analysis(week: str | None = None):
    """Run weekly sentiment analysis."""
    cmd = ["python", "-m", "kopi_sentiment.cli", "weekly"]
    if week:
        cmd.extend(["--week", week])
    run_command(cmd)


def copy_to_web():
    """Copy reports to web public folder."""
    Path("web/public/data/daily").mkdir(parents=True, exist_ok=True)
    Path("web/public/data/weekly").mkdir(parents=True, exist_ok=True)

    # Copy daily reports
    for f in Path("data/daily").glob("*.json"):
        dest = Path("web/public/data/daily") / f.name
        dest.write_text(f.read_text())
        print(f"Copied {f} -> {dest}")

    # Copy weekly reports
    for f in Path("data/weekly").glob("*.json"):
        dest = Path("web/public/data/weekly") / f.name
        dest.write_text(f.read_text())
        print(f"Copied {f} -> {dest}")


def commit_and_push(analysis_type: str):
    """Commit changes and push to GitHub."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Stage all data files
    run_command(["git", "add", "data/", "web/public/data/"], check=False)

    # Check if there are changes to commit
    result = run_command(["git", "diff", "--staged", "--quiet"], check=False)
    if result.returncode == 0:
        print("No changes to commit")
        return

    # Commit and push
    commit_msg = f"{analysis_type.capitalize()} sentiment analysis - {timestamp} (Railway)"
    run_command(["git", "commit", "-m", commit_msg])
    run_command(["git", "push"])
    print(f"Pushed changes: {commit_msg}")


def trigger_deploy():
    """Trigger a deployment webhook if configured."""
    deploy_hook = os.environ.get("DEPLOY_HOOK_URL")
    if deploy_hook:
        import urllib.request
        print(f"Triggering deploy hook...")
        req = urllib.request.Request(deploy_hook, method="POST")
        with urllib.request.urlopen(req) as response:
            print(f"Deploy hook response: {response.status}")


def main():
    parser = argparse.ArgumentParser(description="Railway cron runner for kopi_sentiment")
    parser.add_argument("command", choices=["daily", "weekly"], help="Analysis type to run")
    parser.add_argument("--date", help="Date for daily analysis (YYYY-MM-DD)")
    parser.add_argument("--week", help="Week for weekly analysis (YYYY-Www)")
    parser.add_argument("--skip-push", action="store_true", help="Skip git commit/push")
    parser.add_argument("--skip-deploy", action="store_true", help="Skip deploy hook trigger")

    args = parser.parse_args()

    print(f"=== Railway Cron Job: {args.command} ===")
    print(f"Time: {datetime.now().isoformat()}")

    # Setup
    setup_git()
    clone_repo()

    # Run analysis
    if args.command == "daily":
        run_daily_analysis(args.date)
    else:
        run_weekly_analysis(args.week)

    # Copy to web folder
    copy_to_web()

    # Commit and push
    if not args.skip_push:
        commit_and_push(args.command)

    # Trigger deployment
    if not args.skip_deploy:
        trigger_deploy()

    print(f"=== Completed: {args.command} ===")


if __name__ == "__main__":
    main()
