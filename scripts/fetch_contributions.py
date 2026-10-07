"""Scrape the public contribution calendar (no token) into data/contributions.json.

Usage: python scripts/fetch_contributions.py [username]
"""
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
USERNAME = os.environ.get("GH_USERNAME", "Krist-Kul")


def parse_count(tip: str) -> int:
    m = re.match(r"\s*([\d,]+) contributions?", tip)
    return int(m.group(1).replace(",", "")) if m else 0


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # Current streak: a zero today doesn't break it (the day isn't over yet).
    current = 0
    tail = days[:-1] if days and days[-1]["count"] == 0 else days
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    return current, longest


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    resp = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-readme-heatmap"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append(
            {
                "date": td["data-date"],
                "level": int(td.get("data-level", 0)),
                "count": parse_count(tips.get(td.get("id"), "")),
            }
        )
    if not days:
        sys.exit("no contribution cells found; GitHub markup may have changed")
    days.sort(key=lambda d: d["date"])

    heading = soup.find("h2", id="js-contribution-activity-description")
    m = re.search(r"([\d,]+)\s+contributions?", heading.get_text(" ", strip=True)) if heading else None
    total = int(m.group(1).replace(",", "")) if m else sum(d["count"] for d in days)

    monthly: dict[str, int] = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)

    data = {
        "username": user,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": dict(monthly),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(days)} days, {total} contributions, streak {current}/{longest}")


if __name__ == "__main__":
    main()
