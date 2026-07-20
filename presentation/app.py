"""Streamlit slide-deck viewer for the final defense presentation.

Mirrors the content of output/Airline-Data-Platform-Final-Defense.pptx.
Run: streamlit run app.py
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_SCREENSHOT = ROOT / "docs" / "images" / "dashboard-screenshot.jpg"

st.set_page_config(
    page_title="Airline Data Platform — Final Defense",
    page_icon="✈️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Palette (matches build_deck.js) + global styling
# ---------------------------------------------------------------------------
NAVY = "#0B1F3A"
NAVY_DEEP = "#071527"
STEEL = "#1C3D5A"
CYAN = "#4CC9F0"
CYAN_DIM = "#2E8FB0"
AMBER = "#F2A93B"
OFFWHITE = "#F7F9FB"
TEXT_DARK = "#0B1F3A"
TEXT_MUTED = "#5A6B7D"
BORDER = "#E1E7ED"

st.markdown(
    f"""
    <style>
    .stApp {{ background: #E9EDF2; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding-top: 1.5rem; max-width: 1200px; }}

    .slide {{
        aspect-ratio: 16 / 9;
        border-radius: 14px;
        padding: 3.2% 4.2%;
        box-shadow: 0 8px 28px rgba(11,31,58,0.18);
        font-family: 'Segoe UI', Calibri, sans-serif;
        overflow: hidden;
        position: relative;
    }}
    .slide-dark {{ background: linear-gradient(160deg, {NAVY} 60%, {NAVY_DEEP} 100%); color: white; }}
    .slide-light {{ background: {OFFWHITE}; color: {TEXT_DARK}; }}

    .kicker {{ color: {CYAN_DIM}; font-weight: 700; font-size: 0.8rem; letter-spacing: 2px;
               text-transform: uppercase; margin-bottom: 4px; }}
    .title {{ font-family: Cambria, Georgia, serif; font-weight: 700; font-size: 1.9rem;
              margin: 0 0 0.6rem 0; }}
    .subtitle {{ color: {CYAN}; font-size: 1.1rem; margin-bottom: 0.3rem; }}

    .card {{ background: white; border: 1px solid {BORDER}; border-radius: 10px; padding: 14px 16px;
             box-shadow: 0 3px 10px rgba(11,31,58,0.08); }}
    .card-dark {{ background: {NAVY}; color: white; border-radius: 10px; padding: 14px 16px; }}
    .icon-circle {{ width: 46px; height: 46px; border-radius: 50%; background: {STEEL};
                    display: flex; align-items: center; justify-content: center; font-size: 1.4rem;
                    box-shadow: 0 3px 8px rgba(11,31,58,0.25); flex-shrink: 0; }}
    .icon-circle-light {{ background: #E9F3F8; }}
    .stat {{ font-family: Cambria, Georgia, serif; font-weight: 700; font-size: 2.1rem; color: {CYAN}; }}
    .stat-dark {{ color: {NAVY}; }}
    .label {{ color: {TEXT_MUTED}; font-size: 0.8rem; }}
    .label-on-dark {{ color: #9FB2C6; font-size: 0.8rem; }}

    .grid {{ display: grid; gap: 14px; }}
    .cols-2 {{ grid-template-columns: 1fr 1fr; }}
    .cols-3 {{ grid-template-columns: 1fr 1fr 1fr; }}

    ul.bullets {{ margin: 0; padding-left: 1.1rem; }}
    ul.bullets li {{ margin-bottom: 8px; line-height: 1.35; font-size: 0.92rem; }}
    ul.bullets li::marker {{ color: {CYAN_DIM}; }}

    table.owner {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    table.owner th {{ background: {NAVY}; color: white; text-align: left; padding: 8px 10px; }}
    table.owner td {{ padding: 8px 10px; border-bottom: 1px solid {BORDER}; }}
    table.owner tr:nth-child(even) td {{ background: white; }}
    table.owner tr:nth-child(odd) td {{ background: {OFFWHITE}; }}

    .flow {{ display: flex; align-items: stretch; gap: 6px; }}
    .flow-box {{ border-radius: 8px; padding: 10px; font-size: 0.72rem; flex: 1;
                 display: flex; flex-direction: column; justify-content: center; }}
    .flow-arrow {{ align-self: center; color: {BORDER}; font-size: 1.3rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def img_b64(path: Path) -> str | None:
    if not path.exists():
        logger.warning("Missing image: %s", path)
        return None
    return base64.b64encode(path.read_bytes()).decode("ascii")


# ---------------------------------------------------------------------------
# Slide content — each function returns an HTML string for one slide
# ---------------------------------------------------------------------------

def slide_title() -> str:
    return f"""
    <div class="slide slide-dark">
        <div style="position:absolute; top:14%; right:10%; width:120px; height:120px;
                    border:1px solid {CYAN}55; border-radius:50%;"></div>
        <div style="position:absolute; top:17%; right:13%; width:75px; height:75px;
                    border:1px solid {CYAN}77; border-radius:50%;"></div>
        <div style="margin-top:14%;">
            <div class="title" style="font-size:2.1rem; max-width:88%; line-height:1.25;">AIRLINE DATA ENGINEERING PLATFORM</div>
            <div class="subtitle" style="margin-top:10px;">A live medallion pipeline for airline &amp; flight data</div>
            <div class="label-on-dark">DataScientest Data Engineer Bootcamp — Capstone Project · Final Defense</div>
        </div>
        <div style="position:absolute; bottom:8%; left:4.2%; right:4.2%; border-top:1px solid #2E5A7A80;
                    padding-top:14px; display:flex; justify-content:space-between; align-items:center;">
            <b>Matthias Köhler &nbsp;·&nbsp; Pavel &nbsp;·&nbsp; Chaithra</b>
            <span style="color:{CYAN};">20 July 2026</span>
        </div>
    </div>
    """


def slide_challenge() -> str:
    return f"""
    <div class="slide slide-light">
        <div class="kicker">Introduction</div>
        <div class="title">The Challenge</div>
        <div class="grid cols-2" style="margin-top:10px; align-items:start;">
            <div>
                <p style="font-size:0.95rem; line-height:1.4;">Build a complete, production-style Data
                Engineering architecture around live airline / flight data — collection, storage,
                transformation, an API, automation, containerization, and a live dashboard.</p>
                <div style="display:flex; gap:10px; margin-top:14px;">
                    <div class="icon-circle icon-circle-light">🔒</div>
                    <div><b>No premium API access</b><br><span class="label">Lufthansa's public API stayed
                    closed — no token was ever issued to the project.</span></div>
                </div>
                <div style="display:flex; gap:10px; margin-top:14px;">
                    <div class="icon-circle icon-circle-light">📡</div>
                    <div><b>A partially network-restricted VM</b><br><span class="label">OpenSky blocks the
                    production VM's egress outright — the pipeline had to design around it.</span></div>
                </div>
                <div style="display:flex; gap:10px; margin-top:14px;">
                    <div class="icon-circle icon-circle-light">🔄</div>
                    <div><b>An evolving team and feature set</b><br><span class="label">The team started at
                    four, dropped to three mid-project, and scope shifted with it.</span></div>
                </div>
            </div>
            <div class="card-dark" style="height:88%;">
                <div style="font-size:1.6rem;">&ldquo;</div>
                <p style="font-family:Cambria, Georgia, serif; font-style:italic; font-size:1.15rem; line-height:1.5;">
                Machine Learning performance is NOT the main objective. The main evaluation criterion is
                Data Engineering mastery.</p>
                <p style="color:{CYAN};">— Nicolas, Mentor (DataScientest)</p>
                <hr style="border-color:#2E5A7A80;">
                <p class="label-on-dark">Recommended ML effort: 1–2 days max, Kaggle-inspired, ship and move on.</p>
            </div>
        </div>
    </div>
    """


def slide_team() -> str:
    members = [
        ("Matthias Köhler", "Infrastructure, Deployment, GitOps",
         "Owns cloud infra, CI/CD, GitOps, ingress, and the Q staging environment."),
        ("Pavel", "Data Engineering, API Integration",
         "API integration across the pipeline; designed and shipped the ML flight-delay service."),
        ("Chaithra", "Data Engineering",
         "Warehouse exploration (Redshift silver-history) and ETL scheduling proposals."),
    ]
    cards = "".join(
        f"""<div class="card" style="text-align:center; padding:22px 14px;">
            <div class="icon-circle" style="margin:0 auto 12px auto;">🧑‍🚀</div>
            <div style="font-weight:700; font-family:Cambria, Georgia, serif; font-size:1.05rem;">{n}</div>
            <div style="color:{CYAN_DIM}; font-weight:700; font-size:0.8rem; margin:6px 0;">{r}</div>
            <div class="label">{note}</div>
        </div>"""
        for n, r, note in members
    )
    return f"""
    <div class="slide slide-light">
        <div class="kicker">Introduction</div>
        <div class="title">The Team</div>
        <div class="grid cols-3" style="margin-top:14px;">{cards}</div>
        <p class="label" style="margin-top:16px; font-style:italic;">Supervised by mentor Nicolas
        (DataScientest). The team started at four; one member left early to focus on remaining
        bootcamp coursework.</p>
    </div>
    """


def slide_workflow() -> str:
    steps = [("0", "Scoping", "07 May"), ("1", "Data Discovery", "20 May"),
             ("2", "API &amp; Consumption", "10 Jun"), ("3", "Automation", "16 Jun"),
             ("4", "Deployment", "02 Jul"), ("🎓", "Final Defense", "20 Jul")]
    step_html = "".join(
        f"""<div style="text-align:center; flex:1;">
            <div style="width:34px; height:34px; border-radius:50%; background:{CYAN_DIM if i==5 else NAVY};
                        color:white; display:flex; align-items:center; justify-content:center;
                        margin:0 auto 6px auto; font-weight:700; font-size:0.85rem;">{n}</div>
            <div style="font-weight:700; font-size:0.72rem;">{label}</div>
            <div style="color:{CYAN_DIM}; font-size:0.68rem;">{date}</div>
        </div>"""
        for i, (n, label, date) in enumerate(steps)
    )
    return f"""
    <div class="slide slide-light">
        <div class="kicker">Project Management</div>
        <div class="title">Milestones &amp; Workflow</div>
        <div style="display:flex; align-items:flex-start; border-top:2px solid {BORDER}; margin-top:26px; padding-top:-17px; position:relative;">
            <div style="position:absolute; top:-2px; left:2%; right:2%; height:2px; background:{BORDER};"></div>
            {step_html}
        </div>
        <div class="grid cols-2" style="margin-top:22px;">
            <div class="card">
                <div style="display:flex; gap:10px; align-items:center; margin-bottom:8px;">
                    <div class="icon-circle">🔀</div><b style="font-family:Cambria, Georgia, serif; font-size:1.05rem;">GitHub Flow</b>
                </div>
                <ul class="bullets">
                    <li>Feature branches (feature/ · fix/ · chore/), never pushed to main</li>
                    <li>Every change reviewed and merged through a PR</li>
                    <li>Squash-and-merge — one commit per PR, linear history</li>
                </ul>
            </div>
            <div class="card-dark">
                <div style="display:flex; gap:10px; align-items:center; margin-bottom:8px;">
                    <div class="icon-circle" style="background:{CYAN_DIM};">📋</div>
                    <b style="font-family:Cambria, Georgia, serif; font-size:1.0rem;">Lesson learned — PR #24 → #25</b>
                </div>
                <p class="label-on-dark">A clean, "obviously safe" hotfix was merged on sight — it turned
                out to belong inside a larger effort instead, and had to be reverted.</p>
                <p style="color:{CYAN}; font-weight:700; font-style:italic; font-size:0.85rem;">Now codified as
                policy: never merge without asking — even a clean hotfix.</p>
            </div>
        </div>
    </div>
    """


def slide_ownership() -> str:
    rows = [
        ("Cloud infrastructure, deployment, GitOps, CI/CD, ingress", "Matthias", "Live in production", "#1B8A5A"),
        ("API integration; ML flight-delay prediction service", "Pavel", "Live in production", "#1B8A5A"),
        ("Warehouse exploration (Redshift silver-history), ETL scheduling proposal", "Chaithra", "Exploratory / draft", AMBER),
        ("Architecture decisions — 16 ADRs documenting the why", "Shared", "Ongoing", CYAN_DIM),
    ]
    rows_html = "".join(
        f"<tr><td>{a}</td><td>{o}</td><td style='color:{c}; font-weight:700;'>{s}</td></tr>"
        for a, o, s, c in rows
    )
    return f"""
    <div class="slide slide-light">
        <div class="kicker">Project Management</div>
        <div class="title">Task Ownership</div>
        <table class="owner" style="margin-top:18px;">
            <tr><th>Area</th><th>Owner</th><th>Status</th></tr>
            {rows_html}
        </table>
        <p class="label" style="margin-top:16px; font-style:italic;">Ownership is grouped by delivered
        area rather than raw commit counts — commit history skews toward whoever's account carries
        shared/AI-assisted commits, which doesn't reflect who actually drove each part of the system.</p>
    </div>
    """


def slide_architecture() -> str:
    boxes = [
        ("OpenSky + adsb.lol", "Live states, ~50s cycle", STEEL),
        ("MongoDB Atlas", "Bronze — raw landing zone", "#FF6B35"),
        ("Python ETL", "silver.py, freshest-wins", NAVY),
        ("Supabase Postgres", "Silver — map1", "#FF6B35"),
        ("Streamlit + FastAPI/Dash", "Gold — two live stacks", CYAN_DIM),
    ]
    flow_html = ""
    for i, (label, sub, color) in enumerate(boxes):
        flow_html += f"""<div class="flow-box" style="background:{color}; color:white;">
            <b>{label}</b><span style="opacity:0.85; margin-top:4px;">{sub}</span></div>"""
        if i < len(boxes) - 1:
            flow_html += '<div class="flow-arrow">&#8594;</div>'
    return f"""
    <div class="slide slide-light">
        <div class="kicker">Architecture</div>
        <div class="title">The Medallion Pipeline</div>
        <div class="flow" style="margin-top:26px;">{flow_html}</div>
        <p style="text-align:center; color:{TEXT_MUTED}; font-style:italic; font-size:0.82rem; margin-top:14px;">
        Bronze — raw &nbsp;·&nbsp; Silver — normalized &nbsp;·&nbsp; Gold — consumption</p>
        <div class="card-dark" style="margin-top:18px; display:flex; gap:14px; align-items:center;">
            <div class="icon-circle" style="background:{CYAN_DIM};">🛡️</div>
            <div>
                <b>Cloudflare Tunnel — the only ingress</b><br>
                <span class="label-on-dark">Outbound-only connection to the edge — zero inbound web ports on either VM.</span>
            </div>
        </div>
        <p style="text-align:center; color:{TEXT_MUTED}; font-size:0.78rem; margin-top:14px;">Data stores are
        managed cloud services; every application service is one Docker container, deployed as its own
        Portainer GitOps stack auto-pulling main.</p>
    </div>
    """


def pillar_slide(kicker: str, title: str, icon: str, bullets_list: list[str],
                  stat_value: str, stat_label: str, extra_title: str, extra_body: str) -> str:
    bullets_html = "".join(f"<li>{b}</li>" for b in bullets_list)
    return f"""
    <div class="slide slide-light">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div><div class="kicker">{kicker}</div><div class="title">{title}</div></div>
            <div class="icon-circle" style="width:58px; height:58px; font-size:1.8rem;">{icon}</div>
        </div>
        <div class="grid cols-2" style="margin-top:16px; align-items:start;">
            <ul class="bullets" style="font-size:0.95rem;">{bullets_html}</ul>
            <div>
                <div class="card-dark" style="text-align:center; margin-bottom:14px;">
                    <div class="stat">{stat_value}</div>
                    <div class="label-on-dark">{stat_label}</div>
                </div>
                <div class="card">
                    <b style="color:{CYAN_DIM}; font-size:0.78rem; letter-spacing:1px;">{extra_title}</b>
                    <p class="label" style="margin-top:6px;">{extra_body}</p>
                </div>
            </div>
        </div>
    </div>
    """


def slide_gold() -> str:
    img_data = img_b64(DASHBOARD_SCREENSHOT)
    img_html = (
        f'<img src="data:image/jpeg;base64,{img_data}" style="width:100%; border-radius:8px; margin-top:12px; max-height:150px; object-fit:cover;">'
        if img_data else ""
    )
    return f"""
    <div class="slide slide-light">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div><div class="kicker">Deep Dive — Pillar 3 of 4</div><div class="title">Gold — Consumption</div></div>
            <div class="icon-circle" style="width:58px; height:58px; font-size:1.8rem;">📊</div>
        </div>
        <div class="grid cols-3" style="margin-top:14px;">
            <div class="card">
                <b>Streamlit Dashboard</b>
                <ul class="bullets" style="font-size:0.78rem; margin-top:8px;">
                    <li>Reads map1 directly via psycopg2</li>
                    <li>Cached queries, live map + metrics</li>
                    <li>airline-dashboard.matthiaskoehler.com</li>
                </ul>
            </div>
            <div class="card">
                <b>FastAPI + Dash</b>
                <ul class="bullets" style="font-size:0.78rem; margin-top:8px;">
                    <li>Read-only API over Supavisor pooler</li>
                    <li>Dash frontend polls every 45s</li>
                    <li>airlive.matthiaskoehler.com</li>
                </ul>
            </div>
            <div class="card-dark">
                <b>Two stacks, one source of truth</b>
                <p class="label-on-dark" style="margin-top:8px; font-size:0.78rem;">Both read the same
                map1 table, built independently. Scope is positions, aircraft, and airline only — no
                route or delay analytics, since the live feed carries no origin/destination or times.</p>
            </div>
        </div>
        {img_html}
    </div>
    """


def slide_bonus_ml() -> str:
    stats = [("539,382", "training flights"), ("0.721", "test ROC-AUC"), ("0.667", "test accuracy")]
    stats_html = "".join(
        f"""<div class="card-dark" style="text-align:center; flex:1;">
            <div class="stat" style="font-size:1.5rem;">{v}</div>
            <div class="label-on-dark" style="font-size:0.68rem;">{l}</div></div>"""
        for v, l in stats
    )
    return f"""
    <div class="slide slide-light">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div><div class="kicker">Bonus — Beyond Scope</div><div class="title">ML: Flight Delay Prediction</div></div>
            <div class="icon-circle" style="width:58px; height:58px; font-size:1.8rem;">🧠</div>
        </div>
        <div class="grid cols-2" style="margin-top:16px; align-items:start;">
            <ul class="bullets" style="font-size:0.95rem;">
                <li>Built despite the mentor explicitly de-prioritizing ML performance as an evaluation criterion</li>
                <li>Kaggle Airlines Delay dataset — 539,382 flights, no missing values</li>
                <li>Three candidates compared; HistGradientBoostingClassifier selected on validation ROC-AUC</li>
                <li>Shipped as its own live FastAPI service — /predict and /predict/batch, deployed via Portainer</li>
            </ul>
            <div>
                <div style="display:flex; gap:8px; margin-bottom:14px;">{stats_html}</div>
                <div class="card">
                    <b style="color:{AMBER}; font-size:0.78rem; letter-spacing:1px;">⚗️ HONEST LIMITATION</b>
                    <p class="label" style="margin-top:6px;">An ROC-AUC around 0.72 is in line with published
                    results on this dataset: delays are driven heavily by factors it doesn't capture —
                    weather, ATC, mechanical issues, cascading delays from an aircraft's earlier leg.</p>
                </div>
            </div>
        </div>
    </div>
    """


def slide_results() -> str:
    tiles = [
        ("16", "ADRs documenting every major decision", True),
        ("2", "live ingestion sources, dual-stream", True),
        ("2", "independent Gold consumption stacks", True),
        ("1", "ML service live in production", False),
        ("0", "inbound web ports open on either VM", False),
        ("1", "full staging environment (Q) for PR previews", False),
    ]
    tiles_html = "".join(
        f"""<div class="{'card-dark' if dark else 'card'}" style="text-align:center; padding:18px 10px;">
            <div class="stat {'stat-dark' if not dark else ''}" style="font-size:2.4rem;">{v}</div>
            <div class="{'label-on-dark' if dark else 'label'}" style="margin-top:6px;">{l}</div></div>"""
        for v, l, dark in tiles
    )
    return f"""
    <div class="slide slide-light">
        <div class="kicker">Results</div>
        <div class="title">Where We Stand Today</div>
        <div class="grid cols-3" style="margin-top:20px;">{tiles_html}</div>
    </div>
    """


def slide_next_steps() -> str:
    roadmap = [
        ("Build the target star schema", "Promote map1 into fact_states + dim_aircraft / dim_airlines / dim_airports, as already designed in ADR 008/009."),
        ("Ship the planned FastAPI", "03-gold/api's /states, /aircraft, /airlines, /airports endpoints are designed but not yet built."),
        ("Route &amp; delay analytics", "Needs a data source with origin/destination and scheduled times — the live States feed doesn't carry them."),
        ("Orchestrated automation", "Move batch scheduling from a Docker sleep-loop toward Airflow as volume and complexity grow."),
        ("Redshift silver-history warehouse", "Chaithra's exploratory draft (PR #33) — a historical analytics store alongside the live Silver table."),
        ("Harden CI/CD", "Broaden automated test coverage and formalize the release pipeline beyond lint + build."),
    ]
    cards = "".join(
        f"""<div class="card" style="display:flex; gap:10px;">
            <div style="width:28px; height:28px; border-radius:50%; background:{CYAN_DIM}; color:white;
                        display:flex; align-items:center; justify-content:center; font-weight:700; flex-shrink:0;">{i+1}</div>
            <div><b style="font-size:0.85rem;">{t}</b><p class="label" style="margin-top:4px;">{b}</p></div>
        </div>"""
        for i, (t, b) in enumerate(roadmap)
    )
    return f"""
    <div class="slide slide-light">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div><div class="kicker">Conclusion</div><div class="title">Next Steps — Taking It Further</div></div>
            <div class="icon-circle" style="width:58px; height:58px; font-size:1.8rem;">🚀</div>
        </div>
        <div class="grid cols-2" style="margin-top:14px;">{cards}</div>
    </div>
    """


def slide_thanks() -> str:
    return f"""
    <div class="slide slide-dark" style="display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;">
        <div style="position:absolute; bottom:12%; left:8%; width:100px; height:100px;
                    border:1px solid {CYAN}55; border-radius:50%;"></div>
        <div class="title" style="font-size:3rem;">Thank You</div>
        <div class="subtitle">Questions &amp; Live Demo</div>
        <div class="label-on-dark" style="margin-top:40px;">airline-dashboard.matthiaskoehler.com &nbsp;·&nbsp; airlive.matthiaskoehler.com</div>
        <div style="font-weight:700; margin-top:8px;">Matthias Köhler &nbsp;·&nbsp; Pavel &nbsp;·&nbsp; Chaithra</div>
    </div>
    """


SLIDES: list[tuple[str, callable]] = [
    ("Title", slide_title),
    ("The Challenge", slide_challenge),
    ("The Team", slide_team),
    ("Milestones & Workflow", slide_workflow),
    ("Task Ownership", slide_ownership),
    ("Architecture Overview", slide_architecture),
    ("Pillar 1 — Bronze", lambda: pillar_slide(
        "Deep Dive — Pillar 1 of 4", "Bronze — Ingestion", "📡",
        [
            "Dual-stream: OpenSky /states/all (primary, OAuth2) + adsb.lol (secondary, no auth) — every cycle, both sources",
            "Lands raw and untransformed in MongoDB Atlas — “ingestion &ne; modeling,” Silver decides what to keep",
            "Frankfurt bounding box (~150&times;150 km); adsb.lol's radius was tuned down after it filled the free-tier cluster in under a day",
        ],
        "2 feeds", "every ~50 seconds",
        "WHY TWO SOURCES",
        "OpenSky is richer but gets blocked outright from the production VM's AWS IP range. adsb.lol needs no auth and covers the same geography — a safety net from day one.",
    )),
    ("Pillar 2 — Silver", lambda: pillar_slide(
        "Deep Dive — Pillar 2 of 4", "Silver — Transform & Warehouse", "🔄",
        [
            "silver.py flattens the freshest Bronze snapshot into a single live table, map1, on Supabase Postgres",
            "Freshest-wins fallback by fetched_at — no manual failover branching, no environment-specific code",
            "Real incident: OpenSky blocked the whole production VM IP range — adsb.lol took over automatically, dashboard never went dark",
            "Target star schema (fact_states + dimension tables) is designed and documented — build-out is next",
        ],
        "map1 live", "since 2026-06-09",
        "NEXT UP",
        "The flat map1 table works for a live map today. The dimensional model (dim_aircraft, dim_airlines, dim_airports) is the next Silver milestone.",
    )),
    ("Pillar 3 — Gold", slide_gold),
    ("Pillar 4 — Deployment", lambda: pillar_slide(
        "Deep Dive — Pillar 4 of 4", "Deployment & Infrastructure", "☁️",
        [
            "Every service is one Docker container, one Portainer GitOps stack, auto-pulled from main",
            "Images built once by CI and pushed to GHCR — nothing is ever built on the VM",
            "Cloudflare Tunnel is the only ingress: outbound-only, zero inbound web ports, nginx removed",
            "A full Q (staging) environment, Terraform-managed, mirrors production for PR previews",
        ],
        "0 open ports", "GitOps everywhere",
        "SECURITY POSTURE",
        "With cloudflared handling all public ingress, the only thing reachable from the open internet by IP is SSH — everything else is edge-routed.",
    )),
    ("Bonus — ML", slide_bonus_ml),
    ("Where We Stand Today", slide_results),
    ("Next Steps", slide_next_steps),
    ("Thank You", slide_thanks),
]

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

with st.sidebar:
    st.markdown("### ✈️ Airline Data Platform")
    st.caption("Final Defense — 20 July 2026")
    labels = [f"{i+1}. {name}" for i, (name, _) in enumerate(SLIDES)]
    choice = st.radio("Slides", labels, index=st.session_state.slide_idx, label_visibility="collapsed")
    st.session_state.slide_idx = labels.index(choice)

nav_l, nav_mid, nav_r = st.columns([2, 5, 2])
with nav_l:
    if st.button("⬅ Prev", disabled=st.session_state.slide_idx == 0, use_container_width=True):
        st.session_state.slide_idx -= 1
        st.rerun()
with nav_mid:
    st.markdown(
        f"<div style='text-align:center; color:{TEXT_MUTED};'>Slide {st.session_state.slide_idx + 1} of {len(SLIDES)}"
        f" — {SLIDES[st.session_state.slide_idx][0]}</div>",
        unsafe_allow_html=True,
    )
with nav_r:
    if st.button("Next ➡", disabled=st.session_state.slide_idx == len(SLIDES) - 1, use_container_width=True):
        st.session_state.slide_idx += 1
        st.rerun()

st.markdown(SLIDES[st.session_state.slide_idx][1](), unsafe_allow_html=True)
