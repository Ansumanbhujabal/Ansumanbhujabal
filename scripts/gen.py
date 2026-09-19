#!/usr/bin/env python3
"""Generate the profile README's SVG assets from live GitHub data.

One design system, lifted from ansumanbhujabal.github.io:

  header.svg        masthead — kicker, name, positioning line
  links/*.svg       clickable chips (portfolio, linkedin, writing, resume)
  ticker.svg        the live layer — last shipped, current focus, refreshed at
  timeline.svg      work history, the portfolio's timeline rendered for GitHub
  oss/*.svg         one chip per upstream project, real logo embedded
  activity.svg      daily contribution graph over 12 months
  stats.svg         last-52-weeks totals and language mix
  lifetime.svg      all-time totals since 2022, with a per-year breakdown
  stack/*.svg       tech badges, glyphs from simple-icons

Everything is self-contained: fonts and logos are base64-embedded, colours flip
with prefers-color-scheme, no external requests at render time. GitHub proxies
images through camo, which blocks network fetches from inside an SVG but allows
inline data: URIs and CSS animation.

Links can't live *inside* an SVG used as an <img> — camo strips the interaction
— so anything clickable is its own small SVG the README wraps in an anchor.

Usage:  python3 scripts/gen.py
"""

import base64
import json
import pathlib
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone

USER = "Ansumanbhujabal"
FIRST_YEAR = 2022
ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = ROOT / ".cache"

# ---------------------------------------------------------------- design tokens
# Dark values are GitHub's own dark palette, so the SVGs sit flush on the page
# instead of floating on a mismatched rectangle.
LIGHT = dict(tx="#1a1a1a", mu="#666660", ac="#b84700", bd="#dddddd", sf="#faf9f2",
             grid="#e8e8e0", on="#ffffff")
DARK = dict(tx="#e6edf3", mu="#8b949e", ac="#70d100", bd="#30363d", sf="#161b22",
            grid="#21262d", on="#0b1000")

# Unica One is a display face — it only behaves above ~40px, which is why the
# timeline looked off. Supreme carries every mid-size heading instead, exactly
# as the portfolio pairs them.
FONTS = {"Unica One": ("unica-one-400.woff2", 400), "Supreme": ("supreme-500.woff2", 500)}
FD = "'Unica One', Impact, 'Haettenschweiler', 'Arial Narrow', sans-serif"
FB = "'Supreme', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"
FM = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

NOW = "BlueDot Impact · AI Safety cohort"
ROLES = "AI ARCHITECT · APPLIED AI SAFETY · AIOPS · FORWARD-DEPLOYED"
AVAILABILITY = "OPEN TO REMOTE · RELOCATION"

LINKS = [
    ("PORTFOLIO", "https://ansumanbhujabal.github.io/", True),
    ("LINKEDIN", "https://linkedin.com/in/ansuman-simanta-sekhar-bhujabala", False),
    ("WRITING", "https://ansumanbhujabal.medium.com/", False),
    ("RÉSUMÉ", "https://drive.google.com/file/d/1S340XHOjErqi-SqDuO8oZVCntGLtgQ_v/view?usp=sharing", False),
]

OSS = [
    ("langchain-ai", "LangGraph", "agent orchestration"),
    ("crewAIInc", "CrewAI", "multi-agent platform"),
    ("ollama", "Ollama", "local LLM runtime"),
    ("langflow-ai", "Langflow", "visual agent builder"),
    ("agno-agi", "Agno", "agent framework"),
    ("h2oai", "h2oGPT", "LLM deployment"),
    ("browser-use", "Browser Use", "browser automation"),
]

# (icon slug or None, label). AWS, Azure and OpenAI are trademark-removed from
# simple-icons, so they ride as text-only chips in the same frame.
STACK = [
    ("python", "Python"), ("pytorch", "PyTorch"), ("huggingface", "Transformers"),
    ("langchain", "LangChain"), ("langgraph", "LangGraph"), ("anthropic", "Claude"),
    (None, "OpenAI"), ("fastapi", "FastAPI"), ("docker", "Docker"),
    ("qdrant", "Qdrant"), ("mongodb", "MongoDB"), ("mlflow", "MLflow"),
    ("ollama", "Ollama"), (None, "AWS"), (None, "Azure"),
    ("githubactions", "Actions"),
]

TIMELINE = [
    ("2026", "BlueDot Impact", "TECHNICAL AI SAFETY COHORT",
     "Formalising evals, governance, and adversarial thinking."),
    ("FEB 2025 — PRESENT", "Anyfeast", "AI ENGINEER (CTO)",
     "Stealth AI startup, London. 130,000+ recipes, 50+ dietary verticals, 8-person team."),
    ("JAN — FEB 2025", "Stealth Browser AI Startup", "AI DEVELOPER, CONTRACT",
     "Headless agentic QA automation on BrowserUse and AWS Lambda."),
    ("DEC 2024 — JAN 2025", "Stealth AI Healthtech", "RESEARCH INTERN",
     "Chicago, remote. Patient mental-health tracking from clinical conversations."),
    ("MAY 2024 — JAN 2025", "Invest4Edu", "AI ENGINEER INTERN",
     "ETL over 10M+ records; RAG Q&A at 78% accuracy with refusal handling."),
]


def fetch(url, raw=False):
    """GET with a small on-disk cache so reruns stay cheap and rate limits hold."""
    CACHE.mkdir(exist_ok=True)
    key = CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", url)[-90:] + (".bin" if raw else ".json"))
    if key.exists():
        return key.read_bytes() if raw else json.loads(key.read_text())
    req = urllib.request.Request(
        url, headers={"User-Agent": "profile-gen", "Accept": "application/vnd.github+json"}
    )
    body = urllib.request.urlopen(req, timeout=30).read()
    key.write_bytes(body)
    return body if raw else json.loads(body)


def calendar(frm=None, to=None):
    """Daily contribution counts. Public HTML, no token — which is what keeps
    the nightly workflow runnable without extra secrets."""
    url = f"https://github.com/users/{USER}/contributions"
    if frm:
        url += f"?from={frm}&to={to}"
    html = fetch(url, raw=True).decode()
    cells = re.findall(r'data-date="([0-9-]+)"[^>]*id="([^"]+)"[^>]*data-level="\d"', html)
    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html))
    out = []
    for date, cid in cells:
        m = re.match(r"(\d+|No)", tips.get(cid, "").strip())
        out.append((date, 0 if not m or m.group(1) == "No" else int(m.group(1))))
    return sorted(out)


def longest_streak(days):
    best = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        best = max(best, run)
    return best


def search_count(q):
    try:
        return fetch(f"https://api.github.com/search/issues?q={q}&per_page=1")["total_count"]
    except Exception:
        return 0


def collect():
    days = calendar()

    # Per-year calendars give both the lifetime total and a streak computed over
    # the full history rather than just the rolling window.
    per_year, all_days = {}, []
    for y in range(FIRST_YEAR, datetime.now(timezone.utc).year + 1):
        yd = calendar(f"{y}-01-01", f"{y}-12-31")
        per_year[y] = sum(n for _, n in yd)
        all_days += yd

    repos, page = [], 1
    while page < 4:
        batch = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos += batch
        page += 1
    own = [r for r in repos if not r["fork"]]

    events = fetch(f"https://api.github.com/users/{USER}/events/public?per_page=30")
    shipped = next(
        (e for e in events if e["type"] == "PushEvent" and not e["repo"]["name"].endswith(USER)),
        None,
    )

    try:
        commits = fetch(f"https://api.github.com/search/commits?q=author:{USER}&per_page=1")["total_count"]
    except Exception:
        commits = 0

    weeks = [sum(n for _, n in days[i:i + 7]) for i in range(0, len(days), 7)]
    return dict(
        days=days,
        total=sum(n for _, n in days),
        peak_week=max(weeks) if weeks else 0,
        repos=len(own),
        stars=sum(r["stargazers_count"] for r in own),
        langs=Counter(r["language"] for r in own if r["language"]).most_common(4),
        shipped=shipped["repo"]["name"].split("/")[-1] if shipped else "—",
        per_year=per_year,
        all_time=sum(per_year.values()),
        streak=longest_streak(sorted(set(all_days))),
        commits=commits,
        prs=search_count(f"author:{USER}+type:pr"),
        merged=search_count(f"author:{USER}+type:pr+is:merged"),
    )


def b64(path, mime):
    return f"data:{mime};base64," + base64.b64encode(pathlib.Path(path).read_bytes()).decode()


def font_face(*families):
    out = []
    for fam in families:
        file, weight = FONTS[fam]
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{weight};"
            f"src:url({b64(ASSETS / file, 'font/woff2')}) format('woff2');}}"
        )
    return "".join(out)


def theme_vars():
    """Light by default, dark under prefers-color-scheme. Presentation attributes
    can't take var(), so every fill lands through a CSS class instead."""
    light = ";".join(f"--{k}:{v}" for k, v in LIGHT.items())
    dark = ";".join(f"--{k}:{v}" for k, v in DARK.items())
    return f"svg{{{light}}}@media(prefers-color-scheme:dark){{svg{{{dark}}}}}"


BASE_CSS = """
.d{font-family:%s} .b{font-family:%s} .m{font-family:%s}
.tx{fill:var(--tx)} .mu{fill:var(--mu)} .ac{fill:var(--ac)}
.kick{font-size:10.5px;letter-spacing:2.4px;font-weight:500}
.lab{font-size:9px;letter-spacing:1.6px}
.card{fill:var(--sf);stroke:var(--bd);stroke-width:1}
.in{animation:rise .6s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes rise{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
""" % (FD, FB, FM)

# Every animation runs forwards from a *visible* base state, and nothing uses
# animation-delay. If the clock never advances — headless renderers, feed
# readers, reduced motion — the asset still draws complete. Staggering comes
# from varied durations instead: they start together and land apart.


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, css, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
        f"<style>{css}</style>{body}</svg>"
    )


# ---------------------------------------------------------------------- header
def header():
    css = f"""{font_face('Unica One')}{theme_vars()}{BASE_CSS}
    .name{{font-size:76px;letter-spacing:.5px}}
    .rule{{stroke:var(--bd);stroke-width:1;transform-origin:left center;
      animation:draw .9s cubic-bezier(.2,.7,.2,1) forwards}}
    .d2{{animation-duration:.72s}} .d3{{animation-duration:.9s}} .d4{{animation-duration:1.08s}}
    .cur{{fill:var(--ac);animation:blink 1.1s steps(1) infinite}}
    @keyframes draw{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
    @keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
    """
    body = f"""<g class="in"><rect x="0" y="26" width="3" height="11" class="ac"/>
<text x="12" y="36" class="m kick ac">AI ENGINEER · AGENTIC SYSTEMS · EVALS · AI SECURITY</text></g>
<text x="0" y="112" class="d name tx in d2">ANSUMAN BHUJABALA</text>
<line x1="0" y1="132" x2="900" y2="132" class="rule"/>
<g class="in d3"><text x="0" y="158" class="m mu" font-size="12.5">I build agents that hold up in production — and the harnesses that prove it.<tspan class="cur" dx="6">&#9608;</tspan></text></g>
<g class="in d4"><text x="0" y="186" class="m mu lab">{esc(AVAILABILITY)}</text>
<text x="900" y="186" text-anchor="end" class="m lab ac">{esc(ROLES)}</text></g>"""
    return svg(900, 196, css, body, "Ansuman Bhujabala — AI Engineer")


# ----------------------------------------------------------------- link chips
def link_chip(label, filled):
    w = int(len(label) * 7.6 + 34)
    css = f"""{theme_vars()}{BASE_CSS}
    .fillbtn{{fill:var(--ac)}} .ghost{{fill:none;stroke:var(--bd);stroke-width:1}}
    .onac{{fill:var(--on)}}
    """
    shape = (
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="31" rx="3" class="fillbtn"/>'
        if filled else
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="31" rx="3" class="ghost"/>'
    )
    cls = "onac" if filled else "tx"
    body = shape + f'<text x="{w / 2:.0f}" y="20" text-anchor="middle" class="m lab {cls}">{esc(label)}</text>'
    return svg(w, 32, css, body, label)


# --------------------------------------------------------------- stack badges
def stack_badge(slug, label):
    icon_w = 24 if slug else 0
    w = int(len(label) * 6.9 + icon_w + 26)
    css = f"""{theme_vars()}{BASE_CSS}
    .chip{{fill:var(--sf);stroke:var(--bd);stroke-width:1}}
    .glyph{{fill:var(--ac)}}
    """
    mark = ""
    if slug:
        raw = (ASSETS / "icons" / f"{slug}.svg").read_text()
        d = re.search(r'<path d="([^"]+)"', raw).group(1)
        # simple-icons ship on a 24px grid; 0.58 puts them at ~14px inside a
        # 28px chip, and the glyph takes the theme colour, not the brand's.
        mark = f'<g transform="translate(13,7) scale(0.58)"><path d="{d}" class="glyph"/></g>'
    body = (
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="27" rx="4" class="chip"/>'
        f'{mark}<text x="{13 + icon_w}" y="18.5" class="b tx" font-size="11.5">{esc(label)}</text>'
    )
    return svg(w, 28, css, body, label)


# ---------------------------------------------------------------------- ticker
def ticker(d):
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y").upper()
    css = f"""{theme_vars()}{BASE_CSS}
    .bar{{fill:var(--sf)}} .edge{{stroke:var(--bd);stroke-width:1}}
    .dot{{fill:var(--ac);animation:pulse 2s ease-in-out infinite}}
    .halo{{fill:var(--ac);opacity:.3;animation:halo 2s ease-in-out infinite}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.45}}}}
    @keyframes halo{{0%{{opacity:.3;r:4}}70%,100%{{opacity:0;r:11}}}}
    """
    # Monospace advance at 9px plus 1.6px tracking ≈ 7.0px per character; the
    # label's own width sets where its value can start.
    seg = lambda x, label, value: (
        f'<text x="{x}" y="22" class="m lab mu">{label}</text>'
        f'<text x="{x + len(label) * 7.0 + 14:.0f}" y="22" class="m tx" font-size="11">{esc(value)}</text>'
    )
    body = f"""<rect x="0" y="0" width="900" height="34" class="bar"/>
<line x1="0" y1="0.5" x2="900" y2="0.5" class="edge"/><line x1="0" y1="33.5" x2="900" y2="33.5" class="edge"/>
<circle cx="20" cy="17" r="4" class="halo"/><circle cx="20" cy="17" r="3" class="dot"/>
{seg(38, "LAST SHIPPED", d["shipped"])}
{seg(400, "NOW", NOW)}
<text x="880" y="22" text-anchor="end" class="m lab mu">REFRESHED {stamp}</text>"""
    return svg(900, 34, css, body, "live status")


# -------------------------------------------------------------------- timeline
def timeline():
    row, top, axis = 68, 60, 214
    H = top + row * len(TIMELINE) + 8
    css = f"""{font_face('Supreme')}{theme_vars()}{BASE_CSS}
    .role{{font-size:17px;font-weight:500}}
    .axis{{stroke:var(--bd);stroke-width:1}}
    .node{{fill:var(--sf);stroke:var(--bd);stroke-width:1.5}}
    .live{{fill:var(--ac);stroke:none}}
    """
    rows = []
    for i, (when, org, title, note) in enumerate(TIMELINE):
        y = top + i * row
        node = "node live" if i <= 1 else "node"
        rows.append(
            f'<g class="in" style="animation-duration:{.5 + i * .1:.2f}s">'
            f'<text x="34" y="{y + 4}" class="m mu" font-size="10.5" letter-spacing="1.4">{esc(when)}</text>'
            f'<circle cx="{axis}" cy="{y}" r="4.5" class="{node}"/>'
            f'<text x="{axis + 24}" y="{y + 5}" class="b role tx">{esc(org)}</text>'
            f'<text x="{axis + 24}" y="{y + 25}" class="m ac" font-size="10.5" letter-spacing="1.4">{esc(title)}</text>'
            f'<text x="{axis + 24}" y="{y + 43}" class="m mu" font-size="12">{esc(note)}</text></g>'
        )
    body = (
        f'<line x1="{axis}" y1="{top}" x2="{axis}" y2="{top + row * (len(TIMELINE) - 1)}" class="axis"/>'
        + "".join(rows)
    )
    return svg(900, H, css, body, "work timeline")


# ------------------------------------------------------------------- oss chips
def oss_chip(org, name, what):
    W, H = 196, 58
    css = f"""{theme_vars()}{BASE_CSS}"""
    body = f"""<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="5" class="card"/>
<clipPath id="c"><rect x="14" y="15" width="28" height="28" rx="6"/></clipPath>
<rect x="14" y="15" width="28" height="28" rx="6" fill="#ffffff"/>
<image href="{b64(ASSETS / 'logos' / f'{org}.png', 'image/png')}" x="14" y="15" width="28" height="28" clip-path="url(#c)" preserveAspectRatio="xMidYMid slice"/>
<text x="54" y="29" class="b tx" font-size="12.5">{esc(name)}</text>
<text x="54" y="42" class="m lab mu">{esc(what.upper())}</text>"""
    return svg(W, H, css, body, f"{name} — {what}")


# -------------------------------------------------------------------- activity
def activity(d):
    W, H = 900, 250
    days, vals = [x[0] for x in d["days"]], [x[1] for x in d["days"]]
    peak = max(vals) or 1
    x0, x1, base, top = 34, W - 34, 200, 76
    step = (x1 - x0) / max(len(vals) - 1, 1)
    pts = [(x0 + i * step, base - (v / peak) * (base - top)) for i, v in enumerate(vals)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = f"{line} L{pts[-1][0]:.1f} {base} L{pts[0][0]:.1f} {base} Z"

    grid = []
    for frac in (0.25, 0.5, 0.75, 1.0):
        y = base - frac * (base - top)
        grid.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>')
        grid.append(f'<text x="{x0 - 8}" y="{y + 3:.1f}" text-anchor="end" class="m lab mu">{int(peak * frac)}</text>')

    ticks, seen = [], None
    for i, iso in enumerate(days):
        if iso[:7] != seen:
            seen = iso[:7]
            x = x0 + i * step
            if x < x1 - 20:
                ticks.append(f'<line x1="{x:.1f}" y1="{base}" x2="{x:.1f}" y2="{base + 4}" class="grid"/>')
                ticks.append(
                    f'<text x="{x:.1f}" y="{base + 18}" text-anchor="middle" class="m lab mu">'
                    f'{datetime.strptime(iso, "%Y-%m-%d").strftime("%b").upper()}</text>'
                )

    css = f"""{font_face('Unica One')}{theme_vars()}{BASE_CSS}
    .grid{{stroke:var(--grid);stroke-width:1}}
    .spark{{fill:none;stroke:var(--ac);stroke-width:1.6;stroke-linejoin:round;
      stroke-dasharray:4200;animation:trace 2.4s cubic-bezier(.3,.6,.2,1) forwards}}
    .fill{{fill:var(--ac);opacity:.12;animation:fade 1.8s forwards}}
    @keyframes trace{{from{{stroke-dashoffset:4200}}to{{stroke-dashoffset:0}}}}
    @keyframes fade{{from{{opacity:0}}to{{opacity:.12}}}}
    """
    body = f"""<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" class="card"/>
<rect x="34" y="34" width="3" height="10" class="ac"/>
<text x="46" y="43" class="m kick ac">LAST 12 MONTHS</text>
<text x="{W - 34}" y="43" text-anchor="end" class="m lab mu">{len(days)} DAYS · PEAK {peak}/DAY</text>
{''.join(grid)}
<path d="{area}" class="fill"/><path d="{line}" class="spark"/>
<line x1="{x0}" y1="{base}.5" x2="{x1}" y2="{base}.5" class="grid"/>
{''.join(ticks)}"""
    return svg(W, H, css, body, "daily contribution activity")


def number_row(cols, width, y_num=104, pad=34):
    """Five big numbers with two label lines, evenly spread."""
    step = (width - pad * 2) / len(cols)
    out = []
    for i, (n, l1, l2) in enumerate(cols):
        x = pad + i * step
        out.append(
            f'<g class="in" style="animation-duration:{.5 + i * .12:.2f}s">'
            f'<text x="{x:.0f}" y="{y_num}" class="d tx" font-size="40">{n}</text>'
            f'<text x="{x:.0f}" y="{y_num + 18}" class="m lab ac">{l1}</text>'
            f'<text x="{x:.0f}" y="{y_num + 32}" class="m lab mu">{l2}</text></g>'
        )
    return "".join(out)


# ----------------------------------------------------------------------- stats
def stats(d):
    W, H = 900, 196
    # Streaks are the wrong lens on a bursty build pattern — a 1-day current
    # streak reads as inactive next to a 196-contribution week.
    cols = [
        (f'{d["total"]:,}', "CONTRIBUTIONS", "LAST 52 WEEKS"),
        (f'{d["peak_week"]}', "BUSIEST WEEK", "CONTRIBUTIONS"),
        (f'{d["repos"]}', "PUBLIC REPOS", "AUTHORED"),
        (f'{d["stars"]}', "STARS", "EARNED"),
        (f"{len(OSS)}", "UPSTREAM", "PROJECTS FILED"),
    ]
    total = sum(c for _, c in d["langs"]) or 1
    bar, lx, legend, last = [], 34, [], -999
    for i, (name, count) in enumerate(d["langs"]):
        w = (W - 68) * count / total
        pct = count * 100 // total
        bar.append(
            f'<rect x="{lx:.1f}" y="160" width="{max(w - 2, 1):.1f}" height="6" rx="1" class="ac" '
            f'style="opacity:{1 - i * .22:.2f};transform-origin:left;'
            f'animation:grow {.6 + i * .12:.2f}s cubic-bezier(.2,.7,.2,1) forwards"/>'
        )
        # A 1% slice has no room for a caption — label only what fits.
        if pct >= 5 and lx - last > 120:
            legend.append((lx, f"{name.upper()} {pct}%"))
            last = lx
        lx += w
    for x, t in legend:
        bar.append(f'<text x="{x:.1f}" y="182" class="m lab mu">{t}</text>')

    css = f"""{font_face('Unica One')}{theme_vars()}{BASE_CSS}
    @keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
    """
    body = f"""<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" class="card"/>
<rect x="34" y="34" width="3" height="10" class="ac"/>
<text x="46" y="43" class="m kick ac">RECENT</text>
<text x="{W - 34}" y="43" text-anchor="end" class="m lab mu">AUTO-GENERATED NIGHTLY · NOT A BADGE</text>
{number_row(cols, W)}{''.join(bar)}"""
    return svg(W, H, css, body, "last 52 weeks totals and language mix")


# -------------------------------------------------------------------- lifetime
def lifetime(d):
    W, H = 900, 254
    cols = [
        (f'{d["all_time"]:,}', "CONTRIBUTIONS", "ALL TIME"),
        (f'{d["commits"]:,}', "COMMITS", "AUTHORED"),
        (f'{d["prs"]}', "PULL REQUESTS", f'{d["merged"]} MERGED'),
        (f'{d["streak"]}', "LONGEST STREAK", "DAYS"),
        (f'{len(d["per_year"])}', "YEARS", f"ON GITHUB"),
    ]

    years = sorted(d["per_year"])
    peak = max(d["per_year"].values()) or 1
    span, bw, ybase, ytop = (W - 68) / len(years), 76, 218, 166
    bars = []
    for i, y in enumerate(years):
        v = d["per_year"][y]
        # A 2px floor keeps a thin year visible instead of vanishing into the axis.
        h = max((v / peak) * (ybase - ytop), 2)
        x = 34 + i * span + (span - bw) / 2
        bars.append(
            f'<rect x="{x:.1f}" y="{ybase - h:.1f}" width="{bw}" height="{h:.1f}" rx="2" class="ac" '
            f'style="opacity:.85;transform-origin:center bottom;'
            f'animation:sprout {.6 + i * .1:.2f}s cubic-bezier(.2,.7,.2,1) forwards"/>'
            f'<text x="{x + bw / 2:.1f}" y="{ybase - h - 7:.1f}" text-anchor="middle" class="m tx" font-size="11">{v}</text>'
            f'<text x="{x + bw / 2:.1f}" y="{ybase + 17}" text-anchor="middle" class="m lab mu">{y}</text>'
        )

    css = f"""{font_face('Unica One')}{theme_vars()}{BASE_CSS}
    .grid{{stroke:var(--grid);stroke-width:1}}
    @keyframes sprout{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
    """
    body = f"""<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="6" class="card"/>
<rect x="34" y="34" width="3" height="10" class="ac"/>
<text x="46" y="43" class="m kick ac">ALL TIME</text>
<text x="{W - 34}" y="43" text-anchor="end" class="m lab mu">CONTRIBUTIONS PER YEAR</text>
{number_row(cols, W)}
<line x1="34" y1="{ybase}.5" x2="{W - 34}" y2="{ybase}.5" class="grid"/>
{''.join(bars)}"""
    return svg(W, H, css, body, "all-time GitHub totals by year")


def main():
    d = collect()
    for sub in ("links", "oss", "stack"):
        (ASSETS / sub).mkdir(parents=True, exist_ok=True)

    written = []

    def put(rel, markup):
        (ASSETS / rel).write_text(markup)
        written.append((rel, len(markup)))

    put("header.svg", header())
    put("ticker.svg", ticker(d))
    put("timeline.svg", timeline())
    put("activity.svg", activity(d))
    put("stats.svg", stats(d))
    put("lifetime.svg", lifetime(d))

    for label, _url, filled in LINKS:
        put(f"links/{label.lower().replace('é', 'e')}.svg", link_chip(label, filled))
    for org, name, what in OSS:
        put(f"oss/{org}.svg", oss_chip(org, name, what))
    for slug, label in STACK:
        put(f"stack/{(slug or label).lower()}.svg", stack_badge(slug, label))

    for name, size in written:
        print(f"  {name:<30} {size / 1024:6.1f} KB")
    print(
        f"\n52wk={d['total']} peak_week={d['peak_week']} | all_time={d['all_time']} "
        f"commits={d['commits']} prs={d['prs']}/{d['merged']} streak={d['streak']}\n"
        f"per_year={dict(sorted(d['per_year'].items()))}"
    )


if __name__ == "__main__":
    main()
