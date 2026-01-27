from __future__ import annotations

import calendar
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from zoneinfo import ZoneInfo

import requests
from flask import Flask, render_template, url_for, request, redirect

# ----------------------------
# Config
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
PLAN_PATH = BASE_DIR / "reading_plan.json"

# Guardrails (keep while developing; remove later if you want)
MIN_DAY = date(2026, 1, 1)
MAX_DAY = date(2026, 12, 31)

# ESV API
ESV_API_URL = "https://api.esv.org/v3/passage/text/"
ESV_API_KEY_ENV = "ESV_API_KEY"

# Simple in-memory cache (per-process) so refreshing doesn’t re-hit the API a ton
_ESV_CACHE: Dict[str, str] = {}


# ----------------------------
# Models
# ----------------------------
@dataclass
class Passage:
    reference: str
    text: str


# ----------------------------
# Reading plan (local JSON)
# ----------------------------
def load_plan() -> Dict[int, List[str]]:
    if not PLAN_PATH.exists():
        raise FileNotFoundError(
            f"Missing reading plan file at {PLAN_PATH}. Put reading_plan.json next to app.py."
        )
    data = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    plan: Dict[int, List[str]] = {}
    for k, v in data.items():
        try:
            day_num = int(k)
        except ValueError:
            continue
        if isinstance(v, list):
            plan[day_num] = [str(x) for x in v]
        else:
            plan[day_num] = [str(v)]
    return plan


PLAN = load_plan()


def day_of_year(d: date) -> int:
    return int(d.strftime("%j"))  # Jan 1 => 1


def get_plan_references_for_date(d: date) -> List[str]:
    day_num = day_of_year(d)
    if day_num == 366:  # simple leap-day behavior
        day_num = 365
    return PLAN.get(day_num, ["(No readings found for this day)"])


# ----------------------------
# ESV API fetch
# ----------------------------
def fetch_esv_passage_text(reference: str) -> str:
    """Fetch a passage from the ESV API as plain text.

    We turn off verse numbers, headings, and footnotes.
    We keep the default short copyright marker "(ESV)".
    """
    if reference in _ESV_CACHE:
        return _ESV_CACHE[reference]

    api_key = os.environ.get(ESV_API_KEY_ENV)
    if not api_key:
        text = (
            f"[PLACEHOLDER for {reference}]\n\n"
            f"Set environment variable {ESV_API_KEY_ENV} to enable ESV text."
        )
        _ESV_CACHE[reference] = text
        return text

    headers = {
        "Authorization": f"Token {api_key}",
        "User-Agent": "DailyBibleReadingApp/1.0",
    }

    params = {
        "q": reference,
        "include-passage-references": "false",
        "include-verse-numbers": "false",
        "include-first-verse-numbers": "false",
        "include-footnotes": "false",
        "include-footnote-body": "false",
        "include-headings": "false",
        "include-short-copyright": "true",  # keeps "(ESV)" marker
        "line-length": "0",                # no hard wrapping; let CSS handle it
    }

    resp = requests.get(ESV_API_URL, headers=headers, params=params, timeout=20)
    if resp.status_code == 401:
        text = (
            f"[PLACEHOLDER for {reference}]\n\n"
            f"ESV API returned 401 Unauthorized. Double-check {ESV_API_KEY_ENV}."
        )
        _ESV_CACHE[reference] = text
        return text

    resp.raise_for_status()
    data = resp.json()

    passages = data.get("passages") or []
    text = "\n\n".join(p.strip() for p in passages if isinstance(p, str)).strip()

    # Defensive fallback
    if not text:
        text = f"[No text returned for {reference}]"

    _ESV_CACHE[reference] = text
    return text


def get_passages_for_day(d: date) -> Tuple[int, List[Passage]]:
    plan_day = day_of_year(d)
    refs = get_plan_references_for_date(d)
    passages = [Passage(reference=r, text=fetch_esv_passage_text(r)) for r in refs]
    return plan_day, passages


# ----------------------------
# Calendar helpers
# ----------------------------
def clamp_day(d: date) -> date:
    if d < MIN_DAY:
        return MIN_DAY
    if d > MAX_DAY:
        return MAX_DAY
    return d


def parse_ym(s: str) -> Tuple[int, int]:
    y, m = s.split("-")
    return int(y), int(m)


def add_months(d: date, delta_months: int) -> date:
    y = d.year + (d.month - 1 + delta_months) // 12
    m = (d.month - 1 + delta_months) % 12 + 1
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


# ----------------------------
# Flask app
# ----------------------------
app = Flask(__name__)

# Hardcode "today" to US Central Time (America/Chicago).
# This avoids off-by-one-day issues when the server runs in UTC.
try:
    CENTRAL_TZ = ZoneInfo("America/Chicago")
except Exception:
    CENTRAL_TZ = None


def central_today() -> date:
    """Return today's date in US Central time.

    Falls back to the server's local date if timezone data is unavailable.
    (Installing the `tzdata` package in requirements is recommended.)
    """
    if CENTRAL_TZ is not None:
        return datetime.now(CENTRAL_TZ).date()
    return datetime.now().date()


@app.get("/")
def root():
    # Always land on Central Time "today".
    return redirect(url_for("day_view", day=central_today().isoformat()))


@app.get("/today")
def today_redirect():
    return redirect(url_for("day_view", day=central_today().isoformat()))


@app.get("/day/<day>")
def day_view(day: str):
    try:
        d = datetime.strptime(day, "%Y-%m-%d").date()
    except Exception:
        d = central_today()

    d = clamp_day(d)

    _, passages = get_passages_for_day(d)

    return render_template(
        "day.html",
        day=d,
        passages=passages,
        esv_enabled=bool(os.environ.get(ESV_API_KEY_ENV)),
    )


@app.get("/calendar")
def calendar_view():
    ym = request.args.get("ym")
    today = central_today()

    if ym:
        try:
            y, m = parse_ym(ym)
            current = date(y, m, 1)
        except Exception:
            current = date(today.year, today.month, 1)
    else:
        current = date(today.year, today.month, 1)

    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    weeks = cal.monthdatescalendar(current.year, current.month)

    prev_month = add_months(current, -1)
    next_month = add_months(current, 1)

    return render_template(
        "calendar.html",
        current=current,
        weeks=weeks,
        today=today,
        prev_month=prev_month,
        next_month=next_month,
        min_day=MIN_DAY,
        max_day=MAX_DAY,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
