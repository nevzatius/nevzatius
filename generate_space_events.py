#!/usr/bin/env python3
"""Builds assets/space-events.svg: an animated "Upcoming Sky Events" card.

Reads data/space-events.json, keeps the next few events that have not finished yet,
and writes a self-contained SVG (CSS animations only, no scripts, no external requests)
that renders inside a GitHub README <img>.

Usage:
    python scripts/generate_space_events.py
    python scripts/generate_space_events.py --today 2026-10-29 --count 5
"""
import argparse
import json
import random
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

W = 830
HEADER_H = 80
ROW_H = 58
FOOT_H = 44


def parse_day(value):
    return date.fromisoformat(value) if value else None


def load_events(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    events = []
    for e in raw["events"]:
        start = parse_day(e["start"])
        end = parse_day(e.get("end")) or start
        events.append({
            "start": start,
            "end": end,
            "title": e["title"],
            "detail": e.get("detail", ""),
            "icon": e.get("icon", "planet"),
        })
    events.sort(key=lambda x: x["start"])
    return events


def when_label(ev, today: date) -> str:
    if ev["start"] <= today <= ev["end"]:
        return "Today" if ev["start"] == ev["end"] else "Happening now"
    delta = (ev["start"] - today).days
    if delta == 1:
        return "Tomorrow"
    if delta < 100:
        return f"in {delta} days"
    return f"in {round(delta / 30.4)} months"


def date_chip(ev):
    s, e = ev["start"], ev["end"]
    month = MONTHS[s.month - 1]
    if e != s and e.month == s.month:
        day = f"{s.day}–{e.day}"
    else:
        day = str(s.day)
    return month, day, s.year


def icon_svg(kind: str, x: float, y: float, uid: str) -> str:
    if kind == "meteor":
        return (
            f'<line x1="{x-14}" y1="{y-11}" x2="{x+5}" y2="{y+3}" stroke="url(#mtail)" stroke-width="3" stroke-linecap="round"/>'
            f'<line x1="{x-10}" y1="{y-14}" x2="{x+1}" y2="{y-6}" stroke="url(#mtail)" stroke-width="1.6" stroke-linecap="round" opacity="0.6"/>'
            f'<circle cx="{x+7}" cy="{y+4.5}" r="3.2" fill="#ffffff"/>'
            f'<circle cx="{x+7}" cy="{y+4.5}" r="7" fill="#bcd4ff" opacity="0.3"/>'
        )
    if kind == "moon":
        return (
            f'<circle cx="{x}" cy="{y}" r="15" fill="#dbe7ff" opacity="0.12"/>'
            f'<circle cx="{x}" cy="{y}" r="11" fill="#e8eefc"/>'
            f'<circle cx="{x-3.5}" cy="{y-3}" r="2.6" fill="#c3cdea"/>'
            f'<circle cx="{x+4}" cy="{y+3.5}" r="3.2" fill="#c3cdea"/>'
            f'<circle cx="{x+3}" cy="{y-5}" r="1.5" fill="#c3cdea"/>'
        )
    if kind == "eclipse":
        return (
            f'<circle cx="{x}" cy="{y}" r="16" fill="#ff9a4a" opacity="0.16"/>'
            f'<circle cx="{x}" cy="{y}" r="11" fill="#000"/>'
            f'<circle cx="{x}" cy="{y}" r="11.5" fill="none" stroke="#ffe7c7" stroke-width="2.2"/>'
        )
    # planet with ring
    return (
        f'<ellipse cx="{x}" cy="{y}" rx="16" ry="5" fill="none" stroke="#ffd9a8" stroke-width="1.8" opacity="0.55" transform="rotate(-20 {x} {y})"/>'
        f'<circle cx="{x}" cy="{y}" r="8.5" fill="url(#planet)"/>'
        f'<path d="M{x-16},{y} A16 5 0 0 0 {x+16},{y}" fill="none" stroke="#ffd9a8" stroke-width="1.8" transform="rotate(-20 {x} {y})"/>'
    )


def build_svg(events, today: date) -> str:
    rows = max(len(events), 1)
    H = HEADER_H + rows * ROW_H + FOOT_H

    rng = random.Random(5)
    stars = []
    for _ in range(55):
        sx, sy = rng.uniform(6, W - 6), rng.uniform(6, H - 6)
        r = rng.choice([0.5, 0.6, 0.8, 1.0, 1.3])
        cls = rng.choice(["t1", "t2", "t3"])
        d = round(rng.uniform(0, 7), 2)
        stars.append(
            f'<circle class="{cls}" cx="{sx:.1f}" cy="{sy:.1f}" r="{r}" fill="#fff" '
            f'opacity="{round(rng.uniform(0.3, 0.8), 2)}" style="animation-delay:-{d}s"/>'
        )

    body = []
    if not events:
        body.append(
            f'<text x="{W/2}" y="{HEADER_H + 34}" text-anchor="middle" font-size="15" fill="#8fa3e0">'
            f'No upcoming events listed. Add some to data/space-events.json.</text>'
        )

    for i, ev in enumerate(events):
        y0 = HEADER_H + i * ROW_H
        mid = y0 + ROW_H / 2
        month, day, year = date_chip(ev)
        label = when_label(ev, today)
        soon = i == 0

        if soon:
            body.append(f'<rect x="14" y="{y0+3}" width="{W-28}" height="{ROW_H-6}" rx="14" fill="#ffffff" opacity="0.06"/>')
            body.append(f'<rect x="14" y="{y0+12}" width="3.5" height="{ROW_H-24}" rx="1.75" fill="#ff9a4a" class="pulse"/>')
        elif i > 0:
            body.append(f'<line x1="40" y1="{y0}" x2="{W-40}" y2="{y0}" stroke="#ffffff" opacity="0.06"/>')

        # date chip
        body.append(f'<rect x="30" y="{mid-21}" width="86" height="42" rx="10" fill="#101a45" stroke="#26387f"/>')
        body.append(f'<text x="73" y="{mid-6}" text-anchor="middle" font-size="10.5" font-weight="600" letter-spacing="1.8" fill="#7f95e0">{month} {year}</text>')
        body.append(f'<text x="73" y="{mid+14}" text-anchor="middle" font-size="19" font-weight="700" fill="#ffffff">{escape(day)}</text>')

        # icon
        body.append(icon_svg(ev["icon"], 152, mid, f"i{i}"))
        if soon:
            body.append(f'<circle cx="152" cy="{mid}" r="14" fill="none" stroke="#ff9a4a" stroke-width="1.5" class="ring"/>')

        # text
        body.append(f'<text x="190" y="{mid-3}" font-size="17" font-weight="700" fill="#ffffff">{escape(ev["title"])}</text>')
        body.append(f'<text x="190" y="{mid+16}" font-size="13" fill="#8fa3e0">{escape(ev["detail"])}</text>')

        # countdown pill
        pw = len(label) * 7.4 + 26
        px = W - 30 - pw
        if soon:
            body.append(f'<rect x="{px}" y="{mid-14}" width="{pw}" height="28" rx="14" fill="#ff9a4a" opacity="0.18"/>')
            body.append(f'<rect x="{px}" y="{mid-14}" width="{pw}" height="28" rx="14" fill="none" stroke="#ff9a4a" stroke-width="1.2"/>')
            body.append(f'<text x="{px+pw/2}" y="{mid+5}" text-anchor="middle" font-size="13" font-weight="700" fill="#ffd2a6">{label}</text>')
        else:
            body.append(f'<rect x="{px}" y="{mid-14}" width="{pw}" height="28" rx="14" fill="#101a45" stroke="#26387f"/>')
            body.append(f'<text x="{px+pw/2}" y="{mid+5}" text-anchor="middle" font-size="13" font-weight="600" fill="#9db7ff">{label}</text>')

    foot_y = HEADER_H + rows * ROW_H + 28
    stamp = today.isoformat()

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Upcoming sky events</title>
  <desc id="d">Next astronomy events: {escape(", ".join(e["title"] for e in events))}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#05081a"/>
      <stop offset="0.6" stop-color="#0a1030"/>
      <stop offset="1" stop-color="#13215a"/>
    </linearGradient>
    <radialGradient id="neb" cx="0.85" cy="0.05" r="0.6">
      <stop offset="0" stop-color="#5b3df5" stop-opacity="0.22"/>
      <stop offset="1" stop-color="#5b3df5" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="mtail" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#9ec3ff" stop-opacity="0"/>
      <stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
    <radialGradient id="planet" cx="0.35" cy="0.3" r="0.8">
      <stop offset="0" stop-color="#ffe3bd"/>
      <stop offset="0.6" stop-color="#ff9a4a"/>
      <stop offset="1" stop-color="#8f3df0"/>
    </radialGradient>
    <clipPath id="round"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>

  <style>
    text {{ font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
    .t1 {{ animation: tw 3.2s ease-in-out infinite; }}
    .t2 {{ animation: tw 4.6s ease-in-out infinite; }}
    .t3 {{ animation: tw 6.1s ease-in-out infinite; }}
    @keyframes tw {{ 0%, 100% {{ opacity: .15; }} 50% {{ opacity: .95; }} }}
    .ring {{ transform-box: fill-box; transform-origin: center; animation: ping 2.6s ease-out infinite; }}
    @keyframes ping {{ 0% {{ transform: scale(1); opacity: .9; }} 100% {{ transform: scale(1.9); opacity: 0; }} }}
    .pulse {{ animation: glow 2.6s ease-in-out infinite; }}
    @keyframes glow {{ 0%, 100% {{ opacity: .55; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .t1, .t2, .t3, .ring, .pulse {{ animation: none; }}
    }}
  </style>

  <g clip-path="url(#round)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect width="{W}" height="{H}" fill="url(#neb)"/>
    {chr(10).join("    " + s for s in stars).strip()}

    <!-- header -->
    <ellipse cx="46" cy="40" rx="17" ry="5" fill="none" stroke="#ffd9a8" stroke-width="1.6" opacity="0.5" transform="rotate(-20 46 40)"/>
    <circle cx="46" cy="40" r="9" fill="url(#planet)"/>
    <path d="M29,40 A17 5 0 0 0 63,40" fill="none" stroke="#ffd9a8" stroke-width="1.6" transform="rotate(-20 46 40)"/>
    <text x="76" y="46" font-size="21" font-weight="700" fill="#ffffff">Upcoming Sky Events</text>
    <text x="{W-30}" y="45" text-anchor="end" font-size="12" fill="#6f84cc">Updated {stamp} UTC</text>
    <line x1="30" y1="{HEADER_H-6}" x2="{W-30}" y2="{HEADER_H-6}" stroke="#ffffff" opacity="0.1"/>

    {chr(10).join("    " + s for s in body).strip()}

    <text x="{W/2}" y="{foot_y}" text-anchor="middle" font-size="11.5" fill="#5f73bd" letter-spacing="0.4">Refreshed daily from data/space-events.json</text>
  </g>
</svg>
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(ROOT / "data" / "space-events.json"))
    p.add_argument("--out", default=str(ROOT / "assets" / "space-events.svg"))
    p.add_argument("--today", default=None, help="Override today's date (YYYY-MM-DD)")
    p.add_argument("--count", type=int, default=5)
    a = p.parse_args()

    today = date.fromisoformat(a.today) if a.today else datetime.now(timezone.utc).date()
    upcoming = [e for e in load_events(Path(a.data)) if e["end"] >= today][: a.count]
    svg = build_svg(upcoming, today)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(svg, encoding="utf-8")
    print(f"wrote {a.out} with {len(upcoming)} events (today={today})")


if __name__ == "__main__":
    main()
