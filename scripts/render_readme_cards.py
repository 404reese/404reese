#!/usr/bin/env python3
"""Render every card on the profile README as an animated SVG, plus README.md.

    python scripts/render_readme_cards.py            # animated cards
    STATIC=1 python scripts/render_readme_cards.py   # final frames only (for previews)

Reads data/github.json (written by scripts/fetch_data.py). Standard library only.
A README can't run CSS or JS, so each card is a self-contained SVG: fonts are
embedded as base64 WOFF, motion is CSS keyframes + SMIL, which both play in <img>.
"""
import base64
import datetime
import json
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = Path(__file__).resolve().parent / "fonts"
STATIC = os.environ.get("STATIC") == "1"

# ───────────────────────── content: edit freely ─────────────────────────
LOGIN = "404reese"
ROLE = "FULL STACK AI DEVELOPER"
FIRST_NAME, LAST_NAME = "Riddhesh", "Chaudhary"
TAGLINE = ["I build AI systems that run in production:", "multi-agent LLM pipelines, RAG, data infra."]
SITE_LABEL, SITE_URL = "riddhesh.me", "https://riddhesh.me/"
PROJECTS_URL = "https://riddhesh.me/projects"  # where the What I Build panel links to
TILES = [  # (file slug, small label, big title, sub line, url)
    ("portfolio", "PORTFOLIO", "riddhesh.me", "Projects, resume, writing", "https://riddhesh.me/"),
    ("linkedin", "LINKEDIN", "Let's connect", "in/riddheshchaudhary", "https://www.linkedin.com/in/riddheshchaudhary"),
    ("youtube", "YOUTUBE", "Watch me build", "@404reese", "https://youtube.com/@404reese"),
]
SKILLS = [  # (title, items, icon file in scripts/icons/, tile tint) - same images and tints as riddhesh.me
    ("AI & LLM Engineering", "Multi-agent systems, Eval, Harness, LangGraph, LangChain, MCP", "openai.svg", "#EFEFED"),
    ("RAG & Vector Search", "Pinecone, ChromaDB, embeddings, hybrid retrieval, GraphRAG", "pinecone.png", "#EFEFED"),
    ("Machine Learning", "PyTorch, TensorFlow, OpenCV, Scikit-learn, LightGBM, SHAP", "tensorflow.svg", "#FCEBD9"),
    ("Data Engineering", "PySpark, DuckDB, Parquet, BigQuery, ETL pipelines", "spark.png", "#FBE6DC"),
    ("Python Development", "FastAPI, Flask, Django, async orchestration, scripting", "python.svg", "#FBFBE0"),
    ("JavaScript Ecosystem", "React, Next.js, Node.js, Express, TypeScript, Tailwind, Vite", "javascript.svg", "#FBFBE0"),
    ("Databases & ORMs", "PostgreSQL, MySQL, MongoDB, Supabase, Neo4j, Redis, SQL, Prisma", "postgresql.svg", "#DBEAFE"),
    ("Cloud & DevOps", "GCP, AWS, Firebase, Cloudflare, Docker, Vercel, Nginx, Linux VPS, Git, CI/CD", "docker.svg", "#DBEAFE"),
]
PROJECTS = [  # (preview file slug in scripts/previews/, name, tags, description, link) - same as riddhesh.me
    ("axiomstation", "AxiomStation", ["Next.js", "FastAPI", "LiteLLM", "MCP"],
     "Autonomous no-code AI agent orchestrator. Describe a multi-agent workflow in plain English and watch it get built, deployed and traced.",
     "https://riddhesh.me/projects/axiomstation"),
    ("override", "Override", ["FastAPI", "Multi-LLM", "Pinecone", "RAG"],
     "An adversarial LLM council reviews your employment contract and a judge outside the council decides the verdict.",
     "https://riddhesh.me/projects/override"),
    ("clasicraft", "ClasiCraft", ["WordPress", "SEO", "E-commerce"],
     "A sleek, minimal e-commerce platform with advanced SEO and role-based employee access control.",
     "https://clasicraft.in"),
    ("trash-tracker", "Smart Trash Tracker", ["IoT", "Flutter", "AWS", "MongoDB"],
     "Track submitted trash in real time and monitor waste collection with an intelligent tracking system.",
     "https://github.com/404reese"),
]

# ───────────────────────── look (from riddhesh.me) ─────────────────────────
PAPER, CARD, INK, SUB, BLUE, LINE = "#FFFFFF", "#FFFFFF", "#111111", "#555555", "#0055FF", "#E8E8E8"
SOFT = "#F4F4F3"
GRAPH = ["#EEF0F3", "#CCDDFF", "#8FB4FF", "#4583FF", BLUE]
W = 840  # every full-width card shares this viewBox width

FONT_FILES = {
    "pf": ("PF", "normal", 500, "pf-500.woff"),
    "pfi": ("PF", "italic", 400, "pfi-400.woff"),
    "pfib": ("PF", "italic", 700, "pfi-700.woff"),
    "in": ("Inter", "normal", 400, "inter-400.woff"),
    "inb": ("Inter", "normal", 600, "inter-600.woff"),
    "mono": ("Mono", "normal", 400, "mono-400.woff"),
}
_font_cache = {}


def font_css(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        if fn not in _font_cache:
            _font_cache[fn] = base64.b64encode((FONTS / fn).read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{_font_cache[fn]}) format('woff')}}"
        )
    return "".join(out)


BASE_CSS = f"""
text{{font-family:'Inter',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:{INK}}}
.serif{{font-family:'PF','Playfair Display',Georgia,'Times New Roman',serif;font-weight:500;font-feature-settings:'lnum';font-variant-numeric:lining-nums}}
.ital{{font-family:'PF','Playfair Display',Georgia,serif;font-style:italic;font-weight:700;font-feature-settings:'lnum';font-variant-numeric:lining-nums}}
.ital-l{{font-family:'PF','Playfair Display',Georgia,serif;font-style:italic;font-weight:400}}
.mono{{font-family:'Mono',ui-monospace,SFMono-Regular,Consolas,'Courier New',monospace}}
.b{{font-weight:600}}.sub{{fill:{SUB}}}.blue{{fill:{BLUE}}}
.cap{{font-weight:600;font-size:11px;letter-spacing:1.6px}}
"""
MOTION_CSS = """
.rise{animation:rise .8s cubic-bezier(.2,.7,.2,1) both}
.pop{animation:pop .7s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:center}
.fade{animation:fade .6s ease-out both}
.grow{animation:grow .9s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:bottom}
.draw{animation:draw .8s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:left}
.float{animation:float 5s ease-in-out infinite}
.nudge{animation:nudge 2.4s ease-in-out infinite}
.wave{animation:wave 2.6s ease-in-out infinite;transform-box:fill-box;transform-origin:70% 85%}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.94) translateY(10px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:none}}
@keyframes draw{from{transform:scaleX(0)}to{transform:none}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
@keyframes nudge{0%,100%{transform:translate(0,0)}50%{transform:translate(3px,-3px)}}
@keyframes wave{0%,55%,100%{transform:rotate(0)}10%,30%{transform:rotate(16deg)}20%,40%{transform:rotate(-10deg)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.frame{display:none}.final{visibility:visible!important}}
"""


def d(seconds):
    """Inline animation delay (dropped in STATIC mode)."""
    return "" if STATIC else f' style="animation-delay:{seconds:.2f}s"'


def svg(w, h, body, fonts, label, defs="", frame=True, fill=None, pad=0):
    """Wrap a card. `pad` shrinks the content inside the white panel so it never touches the edge
    (every card needs its own opaque panel: a transparent one is unreadable on GitHub's dark theme)."""
    css = font_css(fonts) + BASE_CSS + ("" if STATIC else MOTION_CSS)
    if pad:
        k = (w - 2 * pad) / w
        body = f'<g transform="translate({pad} {pad + 4}) scale({k:.4f})">{body}</g>'
        h = round(h * k + 2 * pad + 8)
    bg = (f'<rect x="4.5" y="6.5" width="{w - 9}" height="{h - 13}" rx="22" fill="{fill or PAPER}" stroke="{fill or LINE}"/>'
          if frame else "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<defs><style>{css}</style>{defs}</defs>{bg}{body}</svg>\n"
    )


def write(name, content):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(content, encoding="utf-8")


def wrap(text, width, max_lines=2):
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + 1 > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: width - 1].rstrip(" ,.") + "…"
    return lines


def rich(line):
    """'a **b** c' -> tspans with bold dark spans."""
    out = []
    for i, part in enumerate(line.split("**")):
        if part:
            out.append(f'<tspan class="b" fill="{INK}">{escape(part)}</tspan>' if i % 2 else escape(part))
    return "".join(out)


def counter(x, y, value, cls, size, begin, anchor="start"):
    """Count up to `value` with SMIL <set> frames (CSS can't change text)."""
    attrs = f'class="{cls}" x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}"'
    if STATIC or value < 2:
        return f"<text {attrs}>{value:,}</text>"
    frames, total = 18, 1.2
    step = total / frames
    out = [
        f'<text {attrs} class="{cls} final">{value:,}'
        f'<set attributeName="visibility" to="hidden" begin="0s" dur="{begin + total:.2f}s"/></text>'
    ]
    for i in range(frames):
        t = (i + 1) / (frames + 1)
        v = round(value * (1 - (1 - t) ** 3))  # ease-out
        out.append(
            f'<text {attrs} class="{cls} frame" visibility="hidden">{v:,}'
            f'<set attributeName="visibility" to="visible" begin="{begin + i * step:.2f}s" dur="{step:.3f}s"/></text>'
        )
    return "".join(out).replace(f'class="{cls}" x=', "x=")


def heading(x, y, plain, accent, size, delay, anchor="start"):
    """'What I Know' style heading: bold italic serif, last word blue + underlined."""
    return (
        f'<g class="rise"{d(delay)}><text class="ital" x="{x}" y="{y}" font-size="{size}" '
        f'letter-spacing="-1" text-anchor="{anchor}">{escape(plain)} '
        f'<tspan class="blue" text-decoration="underline">{escape(accent)}</tspan></text></g>'
    )


ICON_DIR = Path(__file__).resolve().parent / "icons"
MIME = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg"}


def icon(name, x, y, tint, size=60, pad=11):
    """Tinted rounded box with an image file embedded as a data URI (an SVG shown via <img> can't load URLs)."""
    f = ICON_DIR / name
    uri = f"data:{MIME[f.suffix.lower()]};base64,{base64.b64encode(f.read_bytes()).decode()}"
    inner = size - 2 * pad
    return (
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="14" fill="{tint}"/>'
        f'<image x="{x + pad}" y="{y + pad}" width="{inner}" height="{inner}" preserveAspectRatio="xMidYMid meet" href="{uri}"/>'
    )


# ───────────────────────── cards ─────────────────────────
def hero():
    """Name card: role label, big serif name with a blue sheen, tagline, site link, ASCII portrait."""
    h = 420
    rows = (Path(__file__).resolve().parent / "portrait.txt").read_text().rstrip("\n").split("\n")
    cols = max(len(r) for r in rows)
    px1, pw = 812, 316                      # portrait right edge and width
    fs = pw / (cols * 0.6)                  # mono glyphs are 0.6em wide
    px0 = px1 - pw
    py0 = (h - len(rows) * fs) / 2 + fs
    art = []
    for i, r in enumerate(rows):
        if not r.strip():
            continue
        lead = len(r) - len(r.lstrip())
        txt = r.strip()
        art.append(
            f'<text class="mono fade"{d(0.5 + i * 0.018)} x="{px0 + lead * 0.6 * fs:.2f}" y="{py0 + i * fs:.2f}" '
            f'font-size="{fs:.3f}" textLength="{len(txt) * 0.6 * fs:.2f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{escape(txt)}</text>'
        )
    sheen = "" if STATIC else (
        '<animateTransform attributeName="gradientTransform" type="translate" from="-220 0" to="640 0" '
        'begin="1.2s" dur="5s" repeatCount="indefinite"/>'
    )
    defs = (
        f'<linearGradient id="sheen" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="170" y2="0" '
        f'gradientTransform="translate(215 0)">'
        f'<stop offset="0" stop-color="{INK}"/><stop offset=".5" stop-color="{BLUE}"/><stop offset="1" stop-color="{INK}"/>'
        f"{sheen}</linearGradient>"
    )
    tag = "".join(
        f'<text x="46" y="{318 + i * 27}" font-size="19" style="fill:#2B2B2B">{escape(t)}</text>' for i, t in enumerate(TAGLINE)
    )
    lx = 46 + len(SITE_LABEL) * 13 * 0.6 + 20
    body = f"""
<g class="rise"{d(0.0)}><rect x="46" y="48" width="8" height="8" rx="2" fill="{BLUE}"/>
<text class="mono sub" x="64" y="56.500" font-size="12" letter-spacing="1.800">{escape(ROLE)}</text></g>
<g class="rise"{d(0.15)}><text class="serif" x="42" y="162" font-size="98" letter-spacing="-3">{escape(FIRST_NAME)}</text></g>
<g class="rise"{d(0.3)}><text class="ital-l" x="42" y="256" font-size="98" letter-spacing="-3" style="fill:url(#sheen)">{escape(LAST_NAME)}</text></g>
<g class="rise"{d(0.45)}>{tag}</g>
<g class="rise"{d(0.6)}><text class="mono" x="46" y="386" font-size="13" letter-spacing=".800">{escape(SITE_LABEL)}</text>
<g class="nudge"><path d="M{lx:.1f} 386l8-8m-6 0h6v6" fill="none" stroke="{BLUE}" stroke-width="1.600" stroke-linecap="round" stroke-linejoin="round"/></g></g>
{"".join(art)}
"""
    write("hero.svg", svg(W, h, body, ["pf", "pfi", "in", "mono"],
                          f"{FIRST_NAME} {LAST_NAME}, {ROLE}. {' '.join(TAGLINE)} {SITE_LABEL}", defs, fill=SOFT))


def tiles():
    w, h = 400, 150
    for i, (slug, label, title, sub, _url) in enumerate(TILES):
        t = 0.2 + i * 0.12
        body = f"""
<g class="pop"{d(t)}>
<text class="cap sub" x="28" y="42">{escape(label)}</text>
<text class="ital" x="28" y="92" font-size="38" letter-spacing="-.500">{escape(title)}</text>
<text class="sub" x="28" y="120" font-size="14">{escape(sub)}</text>
<circle cx="{w - 46}" cy="44" r="20" fill="{BLUE}"/>
<g class="nudge"><path d="M{w - 52} 50l12-12m-9 0h9v9" fill="none" stroke="#fff" stroke-width="2.200" stroke-linecap="round" stroke-linejoin="round"/></g>
</g>"""
        write(f"tile-{slug}.svg", svg(w, h, body, ["pfib", "in", "inb"], f"{label.title()}: {title} ({sub})"))


def know():
    col_w, gap, top, card_h, row_gap = 402, 16, 128, 104, 14
    rows = (len(SKILLS) + 1) // 2
    h = top + rows * card_h + (rows - 1) * row_gap + 16
    parts = [heading(14, 82, "What I", "Know", 66, 0.0)]
    for i, (title, items, ic, tint) in enumerate(SKILLS):
        x = 10 + (i % 2) * (col_w + gap)
        y = top + (i // 2) * (card_h + row_gap)
        lines = "".join(
            f'<text class="sub" x="{x + 106}" y="{y + 66 + j * 19}" font-size="13.5">{escape(l)}</text>'
            for j, l in enumerate(wrap(items, 40))
        )
        parts.append(
            f'<g class="pop"{d(0.25 + i * 0.08)}>'
            f'<rect x="{x}.5" y="{y}.5" width="{col_w - 1}" height="{card_h - 1}" rx="18" fill="{CARD}" stroke="{LINE}"/>'
            f"{icon(ic, x + 24, y + 22, tint)}"
            f'<text class="b" x="{x + 106}" y="{y + 43}" font-size="16.5">{escape(title)}</text>{lines}</g>'
        )
    write("know.svg", svg(W, h, "".join(parts), ["pfib", "in", "inb"],
                          "What I know: " + "; ".join(f"{t} ({i})" for t, i, *_ in SKILLS), pad=24))


def streaks(days):
    today = datetime.date.today().isoformat()
    past = [x for x in days if x["date"] <= today]
    best = run = 0
    for x in past:
        run = run + 1 if x["count"] else 0
        best = max(best, run)
    cur = 0
    tail = past[:-1] if past and past[-1]["count"] == 0 else past  # today may still be empty
    for x in reversed(tail):
        if not x["count"]:
            break
        cur += 1
    return cur, best


def activity(data):
    h = 340
    days = data["days"]
    cur, best = streaks(days)
    months = {}
    for x in days:
        months[x["date"][:7]] = months.get(x["date"][:7], 0) + x["count"]
    keys = sorted(months)[-12:]
    peak = max([months[k] for k in keys] + [1])

    parts = [heading(30, 78, "What I", "Ship", 54, 0.0)]
    stats = [(data["total"], "CONTRIBUTIONS · PAST YEAR"), (cur, "DAY STREAK · CURRENT"), (best, "DAY STREAK · BEST THIS YEAR")]
    for i, (val, label) in enumerate(stats):
        y = 150 + i * 68
        parts.append(counter(30, y, val, "serif", 44, 0.5 + i * 0.2))
        parts.append(f'<g class="fade"{d(0.4 + i * 0.2)}><text class="cap sub" x="30" y="{y + 20}" font-size="10.5">{label}</text></g>')

    x0, x1, base, max_h = 330, 810, 284, 150
    slot = (x1 - x0) / len(keys)
    bw = min(26, slot - 10)
    parts.append(f'<line x1="{x0}" y1="{base + .5}" x2="{x1}" y2="{base + .5}" stroke="{LINE}"/>')
    for i, k in enumerate(keys):
        v = months[k]
        bh = max(3, v / peak * max_h)
        bx = x0 + i * slot + (slot - bw) / 2
        mon = datetime.date(int(k[:4]), int(k[5:]), 1).strftime("%b")
        fill = BLUE if v == peak else "#B8CFFF" if v else GRAPH[0]
        t = 0.5 + i * 0.06
        parts.append(
            f'<rect class="grow"{d(t)} x="{bx:.1f}" y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" fill="{fill}"/>'
            f'<g class="fade"{d(t + 0.5)}><text class="b{" blue" if v == peak else ""}" x="{bx + bw / 2:.1f}" y="{base - bh - 8:.1f}" font-size="10.5" '
            f'text-anchor="middle">{v}</text></g>'
            f'<text class="sub" x="{bx + bw / 2:.1f}" y="{base + 20}" font-size="11" text-anchor="middle">{mon}</text>'
        )
    write("activity.svg", svg(W, h, "".join(parts), ["pf", "pfib", "in", "inb"],
                              f"{data['total']} contributions in the past year, current streak {cur} days, "
                              f"best streak {best} days, with a monthly bar chart."))


def graph(data):
    days = data["days"]
    counts = sorted(x["count"] for x in days if x["count"])
    q = [counts[int(len(counts) * p)] for p in (0.25, 0.5, 0.75)] if counts else [1, 2, 3]

    def level(c):
        return 0 if not c else 1 + sum(c > t for t in q)

    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    cell, pitch, top = 11, 14, 54
    weeks = (lead + len(days) + 6) // 7
    x0 = (W - (weeks * pitch - (pitch - cell))) / 2
    h = top + 7 * pitch + 44
    parts = [f'<g class="fade"{d(0)}><text class="cap sub" x="{x0:.1f}" y="34">CONTRIBUTION GRAPH · PAST YEAR</text></g>']
    seen_month = None
    for i, x in enumerate(days):
        col, row = divmod(i + lead, 7)
        cx = x0 + col * pitch
        mon = x["date"][:7]
        if row == 0 and mon != seen_month and col < weeks - 2:
            if seen_month is not None:
                name = datetime.date.fromisoformat(x["date"]).strftime("%b")
                parts.append(f'<text class="sub" x="{cx:.1f}" y="{top + 7 * pitch + 12}" font-size="10">{name}</text>')
            seen_month = mon
        parts.append(
            f'<rect class="fade"{d(0.2 + col * 0.022 + row * 0.015)} x="{cx:.1f}" y="{top + row * pitch}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{GRAPH[level(x["count"])]}"/>'
        )
    lx = x0 + weeks * pitch - (pitch - cell) - 5 * pitch - 34
    ly = 25
    parts.append(f'<text class="sub" x="{lx - 6:.1f}" y="{ly + 9}" font-size="10" text-anchor="end">Less</text>')
    for i, c in enumerate(GRAPH):
        parts.append(f'<rect x="{lx + i * pitch:.1f}" y="{ly}" width="{cell}" height="{cell}" rx="3" fill="{c}"/>')
    parts.append(f'<text class="sub" x="{lx + 5 * pitch + 3:.1f}" y="{ly + 9}" font-size="10">More</text>')
    write("graph.svg", svg(W, h, "".join(parts), ["in", "inb"],
                           f"Contribution graph: {data['total']} contributions in the past year."))


PREVIEWS = Path(__file__).resolve().parent / "previews"


def build():
    """'What I Build' as one panel: heading plus a 2-column grid of projects.

    Each looping preview (.webp in scripts/previews/) is embedded as a data URI so the whole
    section is a single image with a single white background.
    """
    col_w, gap, top = 402, 16, 128
    pv_h = round(col_w * 400 / 640)
    card_h, row_gap = pv_h + 126, 22
    rows_n = (len(PROJECTS) + 1) // 2
    h = top + rows_n * card_h + (rows_n - 1) * row_gap + 6
    parts = [heading(14, 82, "What I", "Build", 66, 0.0)]
    for i, (slug, name, tags, desc, _url) in enumerate(PROJECTS):
        x = 10 + (i % 2) * (col_w + gap)
        y = top + (i // 2) * (card_h + row_gap)
        uri = "data:image/webp;base64," + base64.b64encode((PREVIEWS / f"{slug}.webp").read_bytes()).decode()
        lines = "".join(
            f'<text class="sub" x="{x + 4}" y="{y + pv_h + 58 + j * 19}" font-size="13.5">{escape(l)}</text>'
            for j, l in enumerate(wrap(desc, 56))
        )
        pills, px = [], x + 4
        for t in tags:
            pw = len(t) * 6.500 + 20
            pills.append(
                f'<rect x="{px:.1f}" y="{y + pv_h + 94}" width="{pw:.1f}" height="24" rx="12" fill="{SOFT}" stroke="{LINE}"/>'
                f'<text class="b" x="{px + pw / 2:.1f}" y="{y + pv_h + 110}" font-size="11" text-anchor="middle">{escape(t)}</text>'
            )
            px += pw + 6
        parts.append(
            f'<g class="pop"{d(0.25 + i * 0.12)}>'
            f'<rect x="{x}" y="{y}" width="{col_w}" height="{pv_h}" rx="19" fill="{SOFT}"/>'
            f'<image x="{x}" y="{y}" width="{col_w}" height="{pv_h}" preserveAspectRatio="xMidYMid slice" href="{uri}"/>'
            f'<rect x="{x}.5" y="{y}.5" width="{col_w - 1}" height="{pv_h - 1}" rx="19" fill="none" stroke="{LINE}"/>'
            f'<text class="ital" x="{x + 4}" y="{y + pv_h + 34}" font-size="26" letter-spacing="-.300">{escape(name)}</text>'
            f'<g class="nudge"><path d="M{x + col_w - 22} {y + pv_h + 30}l12-12m-9 0h9v9" fill="none" stroke="{BLUE}" '
            f'stroke-width="2.200" stroke-linecap="round" stroke-linejoin="round"/></g>'
            f'{lines}{"".join(pills)}</g>'
        )
    write("build.svg", svg(W, h, "".join(parts), ["pfib", "in", "inb"],
                           "What I build: " + "; ".join(f"{n} ({ds})" for _s, n, _t, ds, _u in PROJECTS), pad=24))
    for stale in list(ASSETS.glob("repo-*.svg")) + list(ASSETS.glob("project-*.svg")) + [ASSETS / "title-build.svg"]:
        try:  # left over from earlier layouts
            stale.unlink()
        except OSError:
            pass


# Rank ladders for the trophy card: (rank, minimum value), best first.
LADDERS = {
    "commits":   [("SSS", 4000), ("SS", 2000), ("S", 1000), ("AAA", 400), ("AA", 200), ("A", 100), ("B", 10), ("C", 1)],
    "stars":     [("SSS", 2000), ("SS", 700), ("S", 200), ("AAA", 100), ("AA", 50), ("A", 30), ("B", 10), ("C", 1)],
    "followers": [("SSS", 1000), ("SS", 400), ("S", 200), ("AAA", 100), ("AA", 50), ("A", 20), ("B", 10), ("C", 1)],
    "prs":       [("SSS", 1000), ("SS", 500), ("S", 200), ("AAA", 100), ("AA", 50), ("A", 20), ("B", 10), ("C", 1)],
    "issues":    [("SSS", 1000), ("SS", 500), ("S", 200), ("AAA", 100), ("AA", 50), ("A", 20), ("B", 10), ("C", 1)],
    "repos":     [("SSS", 100), ("SS", 75), ("S", 50), ("AAA", 40), ("AA", 30), ("A", 20), ("B", 10), ("C", 1)],
}
TROPHIES = [("commits", "COMMITS"), ("prs", "PULL REQUESTS"), ("issues", "ISSUES"),
            ("repos", "REPOSITORIES"), ("followers", "FOLLOWERS"), ("stars", "STARS")]
CUP_TIERS = {  # tier -> (cup fill, cup shade, letter colour, halo)
    "S": ("#F6C945", "#D9A514", "#5A4300", "#FFF6D0"),   # gold
    "A": ("#C7D2E2", "#9AA9BF", "#1F2A3A", "#EEF2F8"),   # silver
    "B": ("#E0A977", "#BE8249", "#4A2A0C", "#FBEFE4"),   # bronze
}
CUP_DEFAULT = ("#D9D9D9", "#B5B5B5", "#333333", "#F3F3F3")


def cup(cx, cy, rank):
    """Filled trophy cup with the rank letter on the bowl."""
    fill, shade, ink, halo = CUP_TIERS.get(rank[0], CUP_DEFAULT)
    size = {1: 25, 2: 19}.get(len(rank), 14.500)
    return (
        f'<g transform="translate({cx:.1f} {cy:.1f})">'
        f'<circle r="43" fill="{halo}"/>'
        f'<path d="M-23 -22h-9a4 4 0 0 0-4 4c0 10 6 17 16 18M23 -22h9a4 4 0 0 1 4 4c0 10-6 17-16 18" '
        f'fill="none" stroke="{shade}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M-25 -30h50v20a25 25 0 0 1-50 0z" fill="{fill}"/>'
        f'<path d="M-25 -30h50v5h-50z" fill="{shade}" opacity=".550"/>'
        f'<path d="M-5 14h10l2 9h-14z" fill="{shade}"/>'
        f'<rect x="-17" y="22" width="34" height="8" rx="3" fill="{fill}"/>'
        f'<path d="M-17 -21v10a17 17 0 0 0 5 12" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".600"/>'
        f'<text class="b" x="0" y="{-7 + size * 0.36:.1f}" font-size="{size}" text-anchor="middle" style="fill:{ink}">{rank}</text>'
        f"</g>"
    )


def rank_of(key, value):
    """-> (rank, progress 0..1 towards the next rank, next rank or None)."""
    ladder = LADDERS[key]
    for i, (rank, need) in enumerate(ladder):
        if value >= need:
            if i == 0:
                return rank, 1.0, None
            nxt_rank, nxt_need = ladder[i - 1]
            return rank, (value - need) / (nxt_need - need), nxt_rank
    return "–", value / ladder[-1][1] if ladder[-1][1] else 0, ladder[-1][0]


def trophies(data):
    stats = data.get("stats")
    if not stats:
        return False
    n, gap, top, th = len(TROPHIES), 12, 128, 232
    tw = (W - 20 - (n - 1) * gap) / n
    parts = [heading(14, 82, "What I've", "Earned", 66, 0.0)]
    said = []
    for i, (key, label) in enumerate(TROPHIES):
        value = stats.get(key, 0)
        rank, prog, nxt = rank_of(key, value)
        need = dict(LADDERS[key]).get(nxt, 0) - value if nxt else 0
        hint = f"{need:,} more to {nxt}" if nxt else "Top rank"
        x = 10 + i * (tw + gap)
        cx = x + tw / 2
        t = 0.25 + i * 0.1
        bx, bw_full = x + 18, tw - 36
        parts.append(
            f'<g class="pop"{d(t)}>'
            f'<rect x="{x:.1f}" y="{top}.5" width="{tw:.1f}" height="{th - 1}" rx="18" fill="{CARD}" stroke="{LINE}"/>'
            f'<text class="cap" x="{cx:.1f}" y="{top + 30}" font-size="9.500" letter-spacing="1.200" text-anchor="middle">{label}</text>'
            f"{cup(cx, top + 92, rank)}"
            f'<text class="sub" x="{cx:.1f}" y="{top + 192}" font-size="10.500" text-anchor="middle">{hint}</text>'
            f'<rect x="{bx:.1f}" y="{top + th - 24}" width="{bw_full:.1f}" height="4" rx="2" fill="{GRAPH[0]}"/>'
            f'<rect class="draw"{d(t + 0.5)} x="{bx:.1f}" y="{top + th - 24}" width="{max(4, bw_full * prog):.1f}" height="4" rx="2" fill="{BLUE}"/>'
            f"</g>"
        )
        parts.append(counter(f"{cx:.1f}", top + 172, value, "b", 17, t + 0.3, "middle"))
        said.append(f"{label.title()} {value} (rank {rank})")
    write("trophies.svg", svg(W, top + th + 16, "".join(parts), ["pfib", "in", "inb"],
                              "Trophies: " + ", ".join(said), pad=24))
    return True


def title_card(name, plain, accent, label):
    write(name, svg(W, 104, heading(14, 76, plain, accent, 62, 0.0), ["pfib"], label, pad=24))


def readme(has_trophies):
    def row(items, width):
        return "\n".join(
            f'  <a href="{url}"><img src="assets/{src}" width="{width}" alt="{escape(alt)}"></a>' for url, src, alt in items
        )

    tile_w = {1: "60%", 2: "49%", 3: "32.5%"}.get(len(TILES), "32.5%")
    tile_row = row([(u, f"tile-{s}.svg", f"{l.title()}: {t}") for s, l, t, _sub, u in TILES], tile_w)
    repo_block = (
        f'\n  <a href="{PROJECTS_URL}"><img src="assets/build.svg" width="100%" alt="What I Build: '
        + ", ".join(n for _s, n, *_ in PROJECTS) + '"></a>\n'
    )
    trophy_block = (
        '\n  <img src="assets/trophies.svg" width="100%" alt="What I\'ve Earned: trophy ranks for commits, pull requests, '
        'issues, repositories, followers and stars">' if has_trophies else ""
    )
    (ROOT / "README.md").write_text(f"""<!-- Generated by scripts/render_readme_cards.py. Edit the script, not this file. -->
<div align="center">
  <a href="{SITE_URL}"><img src="assets/hero.svg" width="100%" alt="{FIRST_NAME} {LAST_NAME}, {ROLE}. {' '.join(TAGLINE)}"></a>
{tile_row}
  <img src="assets/know.svg" width="100%" alt="What I Know: AI and LLM engineering, RAG, machine learning, data engineering, Python, JavaScript, databases, cloud and DevOps">
  <img src="assets/activity.svg" width="100%" alt="What I Ship: contribution totals, streaks and monthly activity">
  <img src="assets/graph.svg" width="100%" alt="Contribution graph for the past year">{trophy_block}{repo_block}</div>
""", encoding="utf-8")


def main():
    data = json.loads((ROOT / "data" / "github.json").read_text())
    hero()
    tiles()
    know()
    activity(data)
    graph(data)
    has_trophies = trophies(data)
    build()
    readme(has_trophies)
    print(f"rendered {len(list(ASSETS.glob('*.svg')))} cards{' (static)' if STATIC else ''}")


if __name__ == "__main__":
    main()
