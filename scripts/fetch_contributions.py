"""Scrape the public contribution calendar (no token) -> data/contributions.json"""
import json
import re
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "hamarshehmhmd"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def parse_count(text: str) -> int:
    if not text or text.lower().startswith("no contributions"):
        return 0
    m = re.match(r"([\d,]+)\s+contribution", text)
    return int(m.group(1).replace(",", "")) if m else 0


def main() -> None:
    url = f"https://github.com/users/{USERNAME}/contributions"
    r = requests.get(url, headers={"User-Agent": "profile-art-bot"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # counts live in <tool-tip for="contribution-day-component-…"> elements
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "level": int(td.get("data-level", 0)),
            "count": parse_count(tips.get(td.get("id"), "")),
        })
    if not days:
        sys.exit("No contribution cells found - GitHub markup may have changed.")
    days.sort(key=lambda d: d["date"])

    # longest streak
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # current streak (an empty "today" doesn't break it)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["count"] > 0:
            current += 1
        elif i == 0:
            continue
        else:
            break

    best = max(days, key=lambda d: d["count"])
    monthly = OrderedDict()
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    data = {
        "username": USERNAME,
        "generated": date.today().isoformat(),
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"{len(days)} days, {data['total']} contributions -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
