"""
Edge Finder v4 -- Interactive Demo
Peter Wilson | Built with Sinton.ia
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import json

# --- Page Config ---
st.set_page_config(
    page_title="Edge Finder v4",
    page_icon="EF",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session State Init ---
if "bankroll" not in st.session_state:
    st.session_state.bankroll = {
        "balance": 1000.00,
        "starting": 1000.00,
        "daily_risk": 0.00,
        "pending": 0.00,
    }
if "parlay_legs" not in st.session_state:
    st.session_state.parlay_legs = []
if "bet_log" not in st.session_state:
    st.session_state.bet_log = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "selected_game" not in st.session_state:
    st.session_state.selected_game = None


# --- API Check ---
def _check_api():
    try:
        ep = st.secrets.get("AZURE_OPENAI_ENDPOINT", "")
        k = st.secrets.get("AZURE_OPENAI_KEY", "")
        return bool(ep and k)
    except Exception:
        return False


# --- Demo Data ---
DEMO_NBA_GAMES = [
    {"away": "Lakers", "home": "Celtics", "spread": "BOS -6.5", "total": "224", "ml_away": "+220", "ml_home": "-270",
     "time": "7:30 PM ET", "edge": "D", "edge_reason": "No situational advantage. Two rested teams, line is fair.",
     "why_wrong": "None identified. Both teams healthy, no schedule edge.", "why_right": "Line reflects talent gap accurately. Public money balanced.",
     "gut_data": "neutral"},
    {"away": "Heat", "home": "Bucks", "spread": "MIL -4", "total": "218", "ml_away": "+155", "ml_home": "-185",
     "time": "8:00 PM ET", "edge": "B", "edge_reason": "Heat on B2B, 3rd game in 5 nights. Bucks fully rested at home.",
     "why_wrong": "Fatigue not fully priced into -4. Heat shooting 38% on B2Bs this season. Bucks rest advantage undervalued.",
     "why_right": "Heat have covered 3 of last 5 as road dog. Butler historically performs on short rest.",
     "gut_data": "supports"},
    {"away": "Mavericks", "home": "Warriors", "spread": "GSW -3", "total": "228.5", "ml_away": "+135", "ml_home": "-155",
     "time": "10:00 PM ET", "edge": "B+", "edge_reason": "Line opened GSW -5, moved to -3. Sharp money on Dallas.",
     "why_wrong": "Reverse line movement signals sharp action on Mavs. Luka averaging 34.2 in last 5 vs Warriors.",
     "why_right": "Warriors 12-3 at home this month. Curry shooting 48% from 3 at Chase Center.",
     "gut_data": "supports"},
    {"away": "Nuggets", "home": "Suns", "spread": "DEN -2.5", "total": "231", "ml_away": "-140", "ml_home": "+120",
     "time": "9:00 PM ET", "edge": "C", "edge_reason": "Jokic vs Booker always delivers, but line is efficient.",
     "why_wrong": "Suns missing Beal (hamstring). Not yet reflected in total.", "why_right": "Nuggets on road B2B after playing in LA.",
     "gut_data": "neutral"},
    {"away": "Pacers", "home": "Knicks", "spread": "NYK -5.5", "total": "225.5", "ml_away": "+190", "ml_home": "-230",
     "time": "7:00 PM ET", "edge": "A", "edge_reason": "Pacers missing Haliburton + Turner. Knicks revenge game after playoff loss.",
     "why_wrong": "Two key Pacers out, line only -5.5. Market slow to adjust. Knicks 8-1 ATS at home vs injured opponents.",
     "why_right": "Pacers have covered without Haliburton before (3-1 ATS). Siakam usage spikes.",
     "gut_data": "strong"},
]

DEMO_NHL_GAMES = [
    {"away": "Rangers", "home": "Bruins", "spread": "BOS -1.5", "total": "5.5", "ml_away": "+140", "ml_home": "-165",
     "time": "7:00 PM ET", "edge": "B", "edge_reason": "Bruins backup goalie confirmed. Not yet reflected in line.",
     "why_wrong": "Backup goalie Korpisalo starts. His .891 save % not priced into -165 ML.",
     "why_right": "Bruins defense limits shots regardless of goalie. Rangers on B2B.",
     "gut_data": "supports"},
    {"away": "Avalanche", "home": "Stars", "spread": "DAL -1.5", "total": "6", "ml_away": "+125", "ml_home": "-150",
     "time": "8:30 PM ET", "edge": "C", "edge_reason": "MacKinnon GTD. Line hasn't moved yet.",
     "why_wrong": "If MacKinnon sits, Avs lose their engine. Line is stale.", "why_right": "Avs depth has covered before. Stars cold at home lately.",
     "gut_data": "neutral"},
    {"away": "Panthers", "home": "Lightning", "spread": "TBL -1.5", "total": "6.5", "ml_away": "+110", "ml_home": "-130",
     "time": "7:30 PM ET", "edge": "B+", "edge_reason": "Panthers on 3-game win streak, Lightning missing Kucherov.",
     "why_wrong": "Kucherov out 2-3 weeks. Lightning ML still only -130. Public hasn't adjusted.",
     "why_right": "Lightning have Vasilevskiy. Home ice. Rivalry game.",
     "gut_data": "supports"},
]

DEMO_NFL_GAMES = [
    {"away": "Chiefs", "home": "Ravens", "spread": "BAL -2.5", "total": "47.5", "ml_away": "+120", "ml_home": "-140",
     "time": "4:25 PM ET", "edge": "C", "edge_reason": "Offseason. Use for reference only.",
     "why_wrong": "N/A (offseason)", "why_right": "N/A", "gut_data": "neutral"},
]

DEMO_CFB_GAMES = [
    {"away": "Ohio State", "home": "Michigan", "spread": "MICH -3", "total": "44.5", "ml_away": "+130", "ml_home": "-155",
     "time": "12:00 PM ET", "edge": "C", "edge_reason": "Offseason. Use for reference only.",
     "why_wrong": "N/A (offseason)", "why_right": "N/A", "gut_data": "neutral"},
]

DEMO_PROPS = [
    {"player": "Nikola Jokic", "sport": "NBA", "team": "Nuggets", "prop": "Rebounds", "line": "O/U 11.5",
     "edge": "A", "reason": "Playing Spurs (worst rebounding team). Averages 14.2 vs bottom-10 teams. 2.7 rebounds of cushion.",
     "recommendation": "OVER 11.5 -- This is the play.", "matchup": "vs Suns (29th in opp. rebounds allowed)"},
    {"player": "Luka Doncic", "sport": "NBA", "team": "Mavericks", "prop": "Points", "line": "O/U 30.5",
     "edge": "B+", "reason": "Averaging 34.2 vs Warriors in last 5. Curry draws attention, Luka exploits mismatches.",
     "recommendation": "OVER 30.5 -- Matchup driven.", "matchup": "vs Warriors (25th in perimeter D)"},
    {"player": "Jalen Brunson", "sport": "NBA", "team": "Knicks", "prop": "Assists", "line": "O/U 6.5",
     "edge": "B", "reason": "Pacers missing Haliburton. Knicks will control pace. Brunson usage up 8% without pressure.",
     "recommendation": "OVER 6.5 -- Pace control edge.", "matchup": "vs Pacers (shorthanded backcourt)"},
    {"player": "Tyrese Haliburton", "sport": "NBA", "team": "Pacers", "prop": "PRA", "line": "O/U 32.5",
     "edge": "D", "reason": "INJURED -- DNP expected. Do not bet.", "recommendation": "NO BET -- Player injured.",
     "matchup": "N/A"},
    {"player": "Anthony Edwards", "sport": "NBA", "team": "Timberwolves", "prop": "3-Pointers Made", "line": "O/U 3.5",
     "edge": "C", "reason": "Edwards shooting 31% from 3 this month. Volume is there but accuracy is cold.",
     "recommendation": "PASS -- Cold stretch, no edge.", "matchup": "vs Clippers (12th in 3PT D)"},
    {"player": "Connor McDavid", "sport": "NHL", "team": "Oilers", "prop": "Points", "line": "O/U 1.5",
     "edge": "B", "reason": "Playing Sharks (worst GAA in league). McDavid has 8 points in last 3 vs SJ.",
     "recommendation": "OVER 1.5 -- Matchup gold.", "matchup": "vs Sharks (32nd in GAA)"},
]

DEMO_WEEKLY_PL = [
    {"week": "Week 1", "starting": 1000, "ending": 1085, "bets": 6, "record": "4-2", "net": 85},
    {"week": "Week 2", "starting": 1085, "ending": 1220, "bets": 5, "record": "4-1", "net": 135},
    {"week": "Week 3", "starting": 1220, "ending": 1145, "bets": 7, "record": "3-4", "net": -75},
    {"week": "Week 4", "starting": 1145, "ending": 1310, "bets": 5, "record": "4-1", "net": 165},
    {"week": "Week 5", "starting": 1310, "ending": 1430, "bets": 6, "record": "4-2", "net": 120},
    {"week": "Week 6", "starting": 1430, "ending": 1365, "bets": 4, "record": "2-2", "net": -65},
    {"week": "Week 7", "starting": 1365, "ending": 1530, "bets": 5, "record": "4-1", "net": 165},
    {"week": "Week 8", "starting": 1530, "ending": 1480, "bets": 6, "record": "3-3", "net": -50},
]

DEMO_BET_LOG = [
    {"date": "2026-02-24", "game": "Bucks -4 vs Heat", "type": "Spread", "grade": "B", "risk": 100,
     "result": "W", "payout": 195, "edge_real": True, "notes": "Fatigue edge was real. Heat shot 38%."},
    {"date": "2026-02-24", "game": "Jokic O11.5 reb", "type": "Prop", "grade": "A", "risk": 50,
     "result": "W", "payout": 140, "edge_real": True, "notes": "Finished with 15 rebounds. Matchup edge validated."},
    {"date": "2026-02-24", "game": "3-Leg Parlay", "type": "Parlay", "grade": "B", "risk": 50,
     "result": "L", "payout": 0, "edge_real": True, "notes": "Lost on Bills/Pats UNDER. Fluke TDs in garbage time."},
    {"date": "2026-02-23", "game": "Knicks -5.5 vs Pacers", "type": "Spread", "grade": "A", "risk": 150,
     "result": "W", "payout": 295, "edge_real": True, "notes": "Pacers missing 2 starters. Line was too low."},
    {"date": "2026-02-23", "game": "Panthers ML vs Lightning", "type": "ML", "grade": "B+", "risk": 75,
     "result": "W", "payout": 158, "edge_real": True, "notes": "Kucherov out. Panthers dominated."},
    {"date": "2026-02-22", "game": "Lakers -8 vs Hornets", "type": "Spread", "grade": "C", "risk": 50,
     "result": "L", "payout": 0, "edge_real": False, "notes": "No real edge. Should have passed. Grade C = pass."},
]

EDGE_COLORS = {"A": "#22c55e", "B+": "#3b82f6", "B": "#3b82f6", "B-": "#3b82f6",
               "C": "#eab308", "D": "#f97316", "F": "#ef4444"}

EDGE_BG = {"A": "rgba(34,197,94,0.15)", "B+": "rgba(59,130,246,0.15)", "B": "rgba(59,130,246,0.15)",
           "B-": "rgba(59,130,246,0.15)", "C": "rgba(234,179,8,0.15)", "D": "rgba(249,115,22,0.15)",
           "F": "rgba(239,68,68,0.15)"}


def edge_badge(grade):
    color = EDGE_COLORS.get(grade, "#6b7280")
    bg = EDGE_BG.get(grade, "rgba(107,114,128,0.15)")
    return f'<span style="background:{bg};color:{color};padding:4px 12px;border-radius:6px;font-weight:700;font-size:14px;border:1px solid {color}40;">{grade}</span>'


def get_games(sport):
    if sport == "NBA":
        return DEMO_NBA_GAMES
    elif sport == "NHL":
        return DEMO_NHL_GAMES
    elif sport == "NFL":
        return DEMO_NFL_GAMES
    elif sport == "CFB":
        return DEMO_CFB_GAMES
    return []


# --- Custom CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0a0a1a; }
    .main-header {
        background: linear-gradient(135deg, #0d0d1e 0%, #1a1428 50%, #2a1a0a 100%);
        padding: 20px 28px; border-radius: 12px; margin-bottom: 8px;
        border: 1px solid #3a2a0a;
    }
    .main-header h1 { color: #ffffff; font-size: 28px; margin: 0; font-weight: 700; letter-spacing: -0.5px; }
    .main-header .subtitle { color: #D4A017; font-size: 13px; margin: 4px 0 0 0; font-weight: 500; }
    .main-header .version { color: #8890b0; font-size: 11px; margin: 2px 0 0 0; }
    .status-bar {
        background-color: #0d0d1e; border: 1px solid #2a2a3a; border-radius: 8px;
        padding: 8px 16px; margin-bottom: 12px; display: flex; gap: 20px; align-items: center;
    }
    .status-item { font-size: 12px; display: inline-flex; align-items: center; gap: 6px; }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .status-on { background-color: #22c55e; }
    .status-off { background-color: #ef4444; }
    .status-label { color: #8890b0; }
    .stTabs [data-baseweb="tab-list"] { gap: 0px; background-color: #0d0d1e; border-radius: 8px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { color: #8890b0; background-color: transparent; border-radius: 6px; padding: 8px 16px; font-size: 13px; }
    .stTabs [aria-selected="true"] { color: #D4A017 !important; background-color: #1a1428 !important; }
    [data-testid="stExpander"] { background-color: #141420; border: 1px solid #2a2a3a; border-radius: 8px; }
    .stChatMessage { background-color: #141420 !important; border: 1px solid #2a2a3a !important; border-radius: 8px !important; }
    .stChatMessage p, .stChatMessage span, .stChatMessage li, .stChatMessage td { color: #e2e8f0 !important; }
    .stChatMessage h1, .stChatMessage h2, .stChatMessage h3, .stChatMessage h4 { color: #D4A017 !important; }
    .stChatMessage strong { color: #D4A017 !important; }
    .stChatMessage code { color: #D4A017 !important; background-color: #1e1e30 !important; padding: 2px 6px !important; border-radius: 4px !important; }
    .stChatMessage pre { background-color: #0d0d1e !important; border: 1px solid #2a2a3a !important; border-radius: 6px !important; }
    .stChatMessage pre code { color: #e2e8f0 !important; background-color: transparent !important; }
    .stChatMessage table th { background-color: #1a1428 !important; color: #D4A017 !important; padding: 8px 12px !important; }
    .stChatMessage table td { padding: 6px 12px !important; border-bottom: 1px solid #2a2a3a !important; color: #e2e8f0 !important; }
    div[data-testid="stChatInput"] textarea { background-color: #141420 !important; border: 1px solid #2a2a3a !important; color: #e2e8f0 !important; }
    .stButton button { background-color: #1a1428 !important; color: #D4A017 !important; border: 1px solid #3a2a0a !important; }
    .stButton button:hover { background-color: #2a1a0a !important; color: #ffffff !important; }
    [data-testid="stMetric"] { background-color: #141420; border: 1px solid #2a2a3a; border-radius: 8px; padding: 12px; }
    [data-testid="stMetricLabel"] { color: #8890b0 !important; }
    [data-testid="stMetricValue"] { color: #D4A017 !important; }
    .stProgress > div > div { background-color: #D4A017 !important; }
    .game-card {
        background: #141420; border: 1px solid #2a2a3a; border-radius: 10px;
        padding: 16px; margin-bottom: 10px; transition: border-color 0.2s;
    }
    .game-card:hover { border-color: #D4A017; }
    .game-card .teams { font-size: 16px; font-weight: 600; color: #e2e8f0; margin-bottom: 8px; }
    .game-card .odds-row { display: flex; gap: 16px; font-size: 13px; color: #8890b0; }
    .game-card .time { font-size: 11px; color: #6b7280; }
    .edge-box {
        border-radius: 10px; padding: 20px; margin: 10px 0;
        border: 1px solid #2a2a3a;
    }
    .section-label { color: #D4A017; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
    .prop-card {
        background: #141420; border: 1px solid #2a2a3a; border-radius: 10px;
        padding: 16px; margin-bottom: 8px;
    }
    .sidebar-bankroll {
        background: linear-gradient(180deg, #141420 0%, #1a1428 100%);
        border: 1px solid #3a2a0a; border-radius: 10px; padding: 16px; margin-bottom: 12px;
    }
    .footer { color: #4a4a5a; font-size: 11px; text-align: center; padding: 20px; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1>Edge Finder v4</h1>
    <p class="subtitle">Find Edge. Not Winners.</p>
    <p class="version">Interactive Demo | Built with Sinton.ia</p>
</div>
""", unsafe_allow_html=True)

# --- Status Bar ---
has_api = _check_api()
ai_dot = "status-on" if has_api else "status-off"
ai_label = "Azure OpenAI" if has_api else "Azure OpenAI (Demo Mode)"
st.markdown(f"""
<div class="status-bar">
    <span class="status-item"><span class="status-dot status-on"></span><span class="status-label">Edge Engine</span></span>
    <span class="status-item"><span class="status-dot status-on"></span><span class="status-label">Bankroll Tracker</span></span>
    <span class="status-item"><span class="status-dot {ai_dot}"></span><span class="status-label">{ai_label}</span></span>
    <span class="status-item"><span class="status-dot status-on"></span><span class="status-label">Demo Data Active</span></span>
</div>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR -- Bankroll Tracker
# ============================================================
with st.sidebar:
    st.markdown('<p class="section-label">Bankroll Tracker</p>', unsafe_allow_html=True)

    bal = st.session_state.bankroll["balance"]
    starting = st.session_state.bankroll["starting"]
    daily_risk = st.session_state.bankroll["daily_risk"]
    net = bal - starting
    net_pct = (net / starting * 100) if starting > 0 else 0

    st.metric("Current Balance", f"${bal:,.2f}", f"{'+' if net >= 0 else ''}{net_pct:.1f}%")

    max_single = bal * 0.05
    max_daily = bal * 0.15
    stop_loss = bal * 0.10

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Max Single (5%)", f"${max_single:,.2f}")
    with col2:
        st.metric("Max Daily (15%)", f"${max_daily:,.2f}")

    # Daily exposure bar
    exposure_pct = (daily_risk / max_daily * 100) if max_daily > 0 else 0
    st.markdown(f'<p class="section-label">Daily Exposure</p>', unsafe_allow_html=True)
    st.progress(min(exposure_pct / 100, 1.0))
    exposure_color = "#22c55e" if exposure_pct < 60 else ("#eab308" if exposure_pct < 85 else "#ef4444")
    st.markdown(f'<p style="color:{exposure_color};font-size:13px;margin-top:-10px;">${daily_risk:,.2f} / ${max_daily:,.2f} ({exposure_pct:.0f}%)</p>', unsafe_allow_html=True)

    # Stop-loss
    session_pl = net
    sl_color = "#22c55e" if session_pl >= 0 else ("#eab308" if abs(session_pl) < stop_loss else "#ef4444")
    sl_status = "ACTIVE" if abs(session_pl) < stop_loss or session_pl >= 0 else "TRIGGERED"
    st.markdown(f"""
    <div style="background:#141420;border:1px solid #2a2a3a;border-radius:8px;padding:12px;margin-top:8px;">
        <p style="color:#8890b0;font-size:11px;margin:0;">Stop-Loss (-10%)</p>
        <p style="color:{sl_color};font-size:16px;font-weight:700;margin:4px 0 0 0;">-${stop_loss:,.2f} | {sl_status}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Bankroll adjuster
    st.markdown('<p class="section-label">Set Bankroll</p>', unsafe_allow_html=True)
    new_bal = st.number_input("Balance ($)", min_value=0.0, value=bal, step=50.0, key="bal_input")
    if new_bal != bal:
        st.session_state.bankroll["balance"] = new_bal

    st.divider()

    # Quick rules
    with st.expander("Bankroll Rules"):
        st.markdown("""
**Hard Stops:**
- Max single bet: 5% of balance
- Max daily risk: 15% of balance
- Stop-loss: -10% in a session

**Violation = STOP. No new bets until next session.**

No rollover. No bonus traps. Clean money.
        """)

    # Betting profiles
    with st.expander("Betting Profiles"):
        st.markdown(f"""
**Profile A -- Heavy Hitter**
- Clear edge, bet straight
- Grade A or strong B only
- Risk: ${max_single:,.2f} max
- 1-3 per week

**Profile B -- Value Builder**
- 2-3 leg parlays, each with edge
- +400 to +1000 target
- Each leg Grade B+ minimum

**Profile C -- Long Shot**
- 3-4 legs, higher risk
- +800 to +2500 target
- Small risk, 1-2 per week
        """)


# ============================================================
# TABS
# ============================================================
tab_slate, tab_edge, tab_parlay, tab_props, tab_audit, tab_chat = st.tabs([
    "Tonight's Slate",
    "Edge Analyzer",
    "Parlay Builder",
    "Player Props",
    "My Audit",
    "AI Chat",
])


# ============================================================
# TAB 1: TONIGHT'S SLATE
# ============================================================
with tab_slate:
    st.markdown("### Tonight's Slate")
    st.markdown(f'<p style="color:#8890b0;font-size:12px;">Demo data for {datetime.now().strftime("%A, %B %d, %Y")} | All times ET</p>', unsafe_allow_html=True)

    sport = st.selectbox("Sport", ["NBA", "NHL", "NFL", "CFB"], key="slate_sport")
    games = get_games(sport)

    if sport in ["NFL", "CFB"]:
        st.warning(f"{sport} is currently offseason. Showing reference data only.")

    if sport == "NBA":
        st.info("NBA is PRIMARY focus. Spreads, totals, ML, player props. Daily action.")
    elif sport == "NHL":
        st.info("NHL is SECONDARY focus. ML and totals preferred. Goalie situations, B2Bs, weekend heavy.")

    for i, g in enumerate(games):
        grade_color = EDGE_COLORS.get(g["edge"], "#6b7280")
        grade_bg = EDGE_BG.get(g["edge"], "rgba(107,114,128,0.15)")

        col_main, col_edge = st.columns([4, 1])
        with col_main:
            st.markdown(f"""
            <div class="game-card">
                <div class="time">{g['time']}</div>
                <div class="teams">{g['away']} @ {g['home']}</div>
                <div class="odds-row">
                    <span>Spread: <strong style="color:#e2e8f0;">{g['spread']}</strong></span>
                    <span>Total: <strong style="color:#e2e8f0;">{g['total']}</strong></span>
                    <span>ML: <strong style="color:#e2e8f0;">{g['ml_away']}/{g['ml_home']}</strong></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_edge:
            st.markdown(f"""
            <div style="text-align:center;padding-top:20px;">
                <div style="font-size:11px;color:#8890b0;margin-bottom:4px;">EDGE</div>
                {edge_badge(g['edge'])}
            </div>
            """, unsafe_allow_html=True)

        if st.button(f"Analyze {g['away']} @ {g['home']}", key=f"analyze_{sport}_{i}", use_container_width=True):
            st.session_state.selected_game = g

    if st.session_state.selected_game:
        g = st.session_state.selected_game
        st.divider()
        st.markdown(f"### Quick Analysis: {g['away']} @ {g['home']}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class="edge-box" style="background:{EDGE_BG.get(g['edge'], 'rgba(107,114,128,0.15)')};">
                <p class="section-label">Edge Grade</p>
                <div style="font-size:48px;font-weight:700;color:{EDGE_COLORS.get(g['edge'], '#6b7280')};margin:8px 0;">{g['edge']}</div>
                <p style="color:#e2e8f0;font-size:14px;">{g['edge_reason']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            action = "Full unit" if g["edge"] == "A" else ("Half unit" if g["edge"] in ["B", "B+"] else ("Small or pass" if g["edge"] == "C" else "NO BET"))
            action_color = EDGE_COLORS.get(g["edge"], "#6b7280")
            st.markdown(f"""
            <div class="edge-box" style="background:#141420;">
                <p class="section-label">Recommendation</p>
                <div style="font-size:24px;font-weight:700;color:{action_color};margin:8px 0;">{action}</div>
                <p style="color:#8890b0;font-size:13px;">Spread: {g['spread']} | Total: {g['total']}</p>
                <p style="color:#8890b0;font-size:13px;">ML: {g['ml_away']} / {g['ml_home']}</p>
            </div>
            """, unsafe_allow_html=True)

        col_w, col_r = st.columns(2)
        with col_w:
            st.markdown(f"""
            <div class="edge-box" style="background:#141420;">
                <p class="section-label">Why Market Might Be Wrong</p>
                <p style="color:#22c55e;font-size:14px;">{g['why_wrong']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col_r:
            st.markdown(f"""
            <div class="edge-box" style="background:#141420;">
                <p class="section-label">Why Market Might Be Right</p>
                <p style="color:#ef4444;font-size:14px;">{g['why_right']}</p>
            </div>
            """, unsafe_allow_html=True)

        gut_icon = "STRONG ALIGNMENT" if g["gut_data"] == "strong" else ("SUPPORTS" if g["gut_data"] == "supports" else "NEUTRAL")
        gut_color = "#22c55e" if g["gut_data"] in ["strong", "supports"] else "#eab308"
        st.markdown(f"""
        <div class="edge-box" style="background:#141420;">
            <p class="section-label">Gut + Data Alignment</p>
            <p style="color:{gut_color};font-size:18px;font-weight:700;">{gut_icon}</p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TAB 2: EDGE ANALYZER
# ============================================================
with tab_edge:
    st.markdown("### Edge Analyzer")
    st.markdown('<p style="color:#8890b0;font-size:13px;">Deep dive into any matchup. Answer the core question: Why is the market wrong?</p>', unsafe_allow_html=True)

    # Game selector
    all_games = DEMO_NBA_GAMES + DEMO_NHL_GAMES
    game_labels = [f"{g['away']} @ {g['home']}" for g in all_games]
    selected_idx = st.selectbox("Select a matchup", range(len(game_labels)), format_func=lambda i: game_labels[i], key="edge_game_select")
    game = all_games[selected_idx]

    # Thesis input
    st.markdown('<p class="section-label" style="margin-top:16px;">Your Thesis</p>', unsafe_allow_html=True)
    thesis = st.text_area("What's your read on this game?", placeholder="e.g., I like the Bucks tonight. Heat looked gassed last game...", key="thesis_input", height=80)

    if st.button("Run Edge Analysis", key="run_edge", use_container_width=True):
        st.divider()

        # Deep dive layout
        st.markdown(f"""
        <div style="text-align:center;margin:20px 0;">
            <div style="font-size:12px;color:#8890b0;">DEEP DIVE</div>
            <div style="font-size:24px;font-weight:700;color:#e2e8f0;margin:4px 0;">{game['away']} @ {game['home']}</div>
            <div style="font-size:14px;color:#8890b0;">{game['spread']} | O/U {game['total']} | ML {game['ml_away']}/{game['ml_home']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Edge grade
        st.markdown(f"""
        <div style="text-align:center;margin:20px 0;">
            <div style="font-size:72px;font-weight:800;color:{EDGE_COLORS.get(game['edge'], '#6b7280')};">{game['edge']}</div>
            <div style="font-size:14px;color:{EDGE_COLORS.get(game['edge'], '#6b7280')};">{game['edge_reason']}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="edge-box" style="background:rgba(34,197,94,0.08);border-color:#22c55e30;">
                <p class="section-label" style="color:#22c55e;">Why Market Might Be Wrong</p>
                <p style="color:#e2e8f0;font-size:14px;line-height:1.6;">{game['why_wrong']}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="edge-box" style="background:rgba(239,68,68,0.08);border-color:#ef444430;">
                <p class="section-label" style="color:#ef4444;">Why Market Might Be Right</p>
                <p style="color:#e2e8f0;font-size:14px;line-height:1.6;">{game['why_right']}</p>
            </div>
            """, unsafe_allow_html=True)

        # Gut + Data check
        if thesis:
            gut_color = "#22c55e" if game["gut_data"] in ["strong", "supports"] else "#eab308"
            gut_label = "STRONG ALIGNMENT" if game["gut_data"] == "strong" else ("PARTIAL ALIGNMENT" if game["gut_data"] == "supports" else "NEUTRAL -- Need more data")
            st.markdown(f"""
            <div class="edge-box" style="background:#141420;">
                <p class="section-label">Gut + Data Check</p>
                <p style="color:#8890b0;font-size:13px;">Your read: "{thesis}"</p>
                <p style="color:{gut_color};font-size:20px;font-weight:700;margin-top:8px;">{gut_label}</p>
                <p style="color:#8890b0;font-size:12px;margin-top:4px;">Your instinct {'aligns with' if game['gut_data'] != 'neutral' else 'needs more data to align with'} the available data.</p>
            </div>
            """, unsafe_allow_html=True)

        # Action recommendation
        action_map = {"A": ("Full unit. Clear edge.", "#22c55e"), "B+": ("Half to full unit. Edge exists.", "#3b82f6"),
                      "B": ("Half unit. Moderate confidence.", "#3b82f6"), "B-": ("Small bet. Edge is thin.", "#3b82f6"),
                      "C": ("Small bet or PASS. Low confidence.", "#eab308"), "D": ("NO BET. No edge identified.", "#f97316"),
                      "F": ("NO BET. Market is right. Trap.", "#ef4444")}
        action_text, action_clr = action_map.get(game["edge"], ("NO BET", "#6b7280"))
        max_s = st.session_state.bankroll["balance"] * 0.05

        st.markdown(f"""
        <div class="edge-box" style="background:rgba(212,160,23,0.08);border-color:#D4A01730;">
            <p class="section-label">Verdict</p>
            <p style="color:{action_clr};font-size:20px;font-weight:700;">{action_text}</p>
            <p style="color:#8890b0;font-size:13px;margin-top:4px;">Max risk: ${max_s:,.2f} (5% of bankroll)</p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TAB 3: PARLAY BUILDER
# ============================================================
with tab_parlay:
    st.markdown("### Parlay Builder")
    st.markdown('<p style="color:#8890b0;font-size:13px;">Each leg needs its own edge. Not random teams stapled together.</p>', unsafe_allow_html=True)

    # Add legs
    all_options = DEMO_NBA_GAMES + DEMO_NHL_GAMES
    option_labels = [f"{g['away']} @ {g['home']} -- {g['spread']} (Edge: {g['edge']})" for g in all_options]

    bet_type = st.selectbox("Bet Type", ["Spread", "Total (Over)", "Total (Under)", "Moneyline"], key="parlay_bet_type")
    selected_leg_idx = st.selectbox("Select a game", range(len(option_labels)), format_func=lambda i: option_labels[i], key="parlay_leg_select")

    if st.button("Add Leg", key="add_leg"):
        g = all_options[selected_leg_idx]
        if len(st.session_state.parlay_legs) >= 4:
            st.error("HARD STOP: Max 4 legs. More is stupid. Remove a leg first.")
        elif len(st.session_state.parlay_legs) >= 3:
            st.warning("3 legs is the recommended max. Adding a 4th is absolute maximum.")
            st.session_state.parlay_legs.append({"game": f"{g['away']} @ {g['home']}", "type": bet_type,
                                                  "spread": g["spread"], "edge": g["edge"], "odds": g.get("ml_home", "-110")})
        else:
            st.session_state.parlay_legs.append({"game": f"{g['away']} @ {g['home']}", "type": bet_type,
                                                  "spread": g["spread"], "edge": g["edge"], "odds": g.get("ml_home", "-110")})
            st.success(f"Added: {g['away']} @ {g['home']} ({bet_type})")

    # Display legs
    if st.session_state.parlay_legs:
        st.divider()
        st.markdown(f'<p class="section-label">Parlay Legs ({len(st.session_state.parlay_legs)})</p>', unsafe_allow_html=True)

        for i, leg in enumerate(st.session_state.parlay_legs):
            col_leg, col_rm = st.columns([5, 1])
            with col_leg:
                st.markdown(f"""
                <div class="prop-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="color:#e2e8f0;font-weight:600;">Leg {i+1}: {leg['game']}</span>
                            <span style="color:#8890b0;font-size:12px;margin-left:12px;">{leg['type']} | {leg['spread']}</span>
                        </div>
                        <div>{edge_badge(leg['edge'])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_rm:
                if st.button("Remove", key=f"rm_leg_{i}"):
                    st.session_state.parlay_legs.pop(i)
                    st.rerun()

        # Validation: Would you bet each straight?
        st.markdown(f"""
        <div class="edge-box" style="background:#141420;">
            <p class="section-label">Straight Bet Validation</p>
            <p style="color:#8890b0;font-size:13px;">Would you place each leg as a straight bet?</p>
        </div>
        """, unsafe_allow_html=True)

        all_valid = True
        for leg in st.session_state.parlay_legs:
            if leg["edge"] in ["D", "F"]:
                st.markdown(f'<p style="color:#ef4444;font-size:13px;">WARNING: {leg["game"]} has Grade {leg["edge"]}. No edge = no leg.</p>', unsafe_allow_html=True)
                all_valid = False
            elif leg["edge"] == "C":
                st.markdown(f'<p style="color:#eab308;font-size:13px;">CAUTION: {leg["game"]} has Grade {leg["edge"]}. Weak edge for a parlay leg.</p>', unsafe_allow_html=True)
                all_valid = False

        if all_valid:
            st.markdown('<p style="color:#22c55e;font-size:13px;">All legs have independent edge. Parlay is valid.</p>', unsafe_allow_html=True)

        # Combined odds (simplified demo calculation)
        st.divider()
        num_legs = len(st.session_state.parlay_legs)
        # Demo combined odds based on leg count
        combined_map = {1: 100, 2: 264, 3: 485, 4: 890}
        combined_odds = combined_map.get(num_legs, 485)

        profile = "Value Builder (+400 to +1000)" if 2 <= num_legs <= 3 else ("Long Shot (+800 to +2500)" if num_legs == 4 else "Straight Bet")
        max_risk = st.session_state.bankroll["balance"] * 0.05

        col_o, col_p, col_r = st.columns(3)
        with col_o:
            st.metric("Combined Odds", f"+{combined_odds}")
        with col_p:
            st.metric("Profile", profile.split(" (")[0])
        with col_r:
            suggested_risk = max_risk * 0.5 if num_legs <= 3 else max_risk * 0.25
            st.metric("Suggested Risk", f"${suggested_risk:,.2f}")

        payout = suggested_risk * (combined_odds / 100)
        st.markdown(f"""
        <div class="edge-box" style="background:rgba(212,160,23,0.08);border-color:#D4A01730;">
            <p style="color:#D4A017;font-size:16px;font-weight:700;">Risk ${suggested_risk:,.2f} to win ${payout:,.2f}</p>
            <p style="color:#8890b0;font-size:12px;">Max daily risk: ${st.session_state.bankroll['balance'] * 0.15:,.2f} | Currently exposed: ${st.session_state.bankroll['daily_risk']:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Clear All Legs", key="clear_legs"):
            st.session_state.parlay_legs = []
            st.rerun()
    else:
        st.markdown('<p style="color:#6b7280;font-size:14px;text-align:center;padding:40px 0;">No legs added yet. Select a game above to start building.</p>', unsafe_allow_html=True)


# ============================================================
# TAB 4: PLAYER PROPS
# ============================================================
with tab_props:
    st.markdown("### Player Props")
    st.markdown('<p style="color:#8890b0;font-size:13px;">Props are about matchups, not just talent. Matchup-driven thesis required.</p>', unsafe_allow_html=True)

    # Search / filter
    col_search, col_sport_filter = st.columns([3, 1])
    with col_search:
        search = st.text_input("Search player", placeholder="e.g., Jokic, Luka, McDavid...", key="prop_search")
    with col_sport_filter:
        sport_filter = st.selectbox("Sport", ["All", "NBA", "NHL"], key="prop_sport_filter")

    filtered_props = DEMO_PROPS
    if search:
        filtered_props = [p for p in filtered_props if search.lower() in p["player"].lower()]
    if sport_filter != "All":
        filtered_props = [p for p in filtered_props if p["sport"] == sport_filter]

    if not filtered_props:
        st.markdown('<p style="color:#6b7280;font-size:14px;text-align:center;padding:20px;">No props found matching your search.</p>', unsafe_allow_html=True)

    for p in filtered_props:
        grade_color = EDGE_COLORS.get(p["edge"], "#6b7280")
        grade_bg = EDGE_BG.get(p["edge"], "rgba(107,114,128,0.15)")

        st.markdown(f"""
        <div class="prop-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
                        <span style="color:#e2e8f0;font-size:16px;font-weight:600;">{p['player']}</span>
                        <span style="color:#8890b0;font-size:12px;">{p['team']} | {p['sport']}</span>
                        {edge_badge(p['edge'])}
                    </div>
                    <div style="margin-bottom:8px;">
                        <span style="color:#D4A017;font-weight:600;">{p['prop']}: {p['line']}</span>
                        <span style="color:#6b7280;font-size:12px;margin-left:12px;">{p['matchup']}</span>
                    </div>
                    <p style="color:#8890b0;font-size:13px;margin:4px 0;">{p['reason']}</p>
                    <p style="color:{grade_color};font-size:13px;font-weight:600;margin:4px 0;">{p['recommendation']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TAB 5: MY AUDIT
# ============================================================
with tab_audit:
    st.markdown("### My Audit")
    st.markdown('<p style="color:#8890b0;font-size:13px;">Grade process, not outcome. No excuses. Loss is a loss.</p>', unsafe_allow_html=True)

    # Summary metrics
    total_bets = len(DEMO_BET_LOG)
    wins = sum(1 for b in DEMO_BET_LOG if b["result"] == "W")
    losses = total_bets - wins
    total_risk = sum(b["risk"] for b in DEMO_BET_LOG)
    total_payout = sum(b["payout"] for b in DEMO_BET_LOG)
    net_pl = total_payout - total_risk
    edge_accuracy = sum(1 for b in DEMO_BET_LOG if b["edge_real"]) / total_bets * 100 if total_bets > 0 else 0

    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("Record", f"{wins}-{losses}")
    with col_m2:
        st.metric("Net P/L", f"${net_pl:+,.2f}")
    with col_m3:
        roi = (net_pl / total_risk * 100) if total_risk > 0 else 0
        st.metric("ROI", f"{roi:+.1f}%")
    with col_m4:
        st.metric("Edge Accuracy", f"{edge_accuracy:.0f}%")
    with col_m5:
        process_grade = "A" if edge_accuracy >= 80 else ("B+" if edge_accuracy >= 70 else ("B" if edge_accuracy >= 60 else "C"))
        st.metric("Process Grade", process_grade)

    st.divider()

    # Bet log table
    st.markdown('<p class="section-label">Recent Bets</p>', unsafe_allow_html=True)

    log_data = []
    for b in DEMO_BET_LOG:
        result_icon = "W" if b["result"] == "W" else "L"
        pl = b["payout"] - b["risk"]
        log_data.append({
            "Date": b["date"],
            "Game": b["game"],
            "Type": b["type"],
            "Grade": b["grade"],
            "Risk": f"${b['risk']}",
            "Result": result_icon,
            "P/L": f"${pl:+,}",
            "Edge Real?": "Yes" if b["edge_real"] else "No",
        })

    df_log = pd.DataFrame(log_data)
    st.dataframe(df_log, use_container_width=True, hide_index=True)

    # "Was the edge real?" section
    st.divider()
    st.markdown('<p class="section-label">Was The Edge Real? -- Honest Review</p>', unsafe_allow_html=True)

    for b in DEMO_BET_LOG:
        pl = b["payout"] - b["risk"]
        icon_color = "#22c55e" if b["result"] == "W" else "#ef4444"
        edge_label = "Edge was real" if b["edge_real"] else "No real edge"
        edge_color = "#22c55e" if b["edge_real"] else "#ef4444"

        st.markdown(f"""
        <div class="prop-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="color:{icon_color};font-weight:700;margin-right:8px;">{'W' if b['result'] == 'W' else 'L'}</span>
                    <span style="color:#e2e8f0;font-weight:600;">{b['game']}</span>
                    <span style="color:#8890b0;font-size:12px;margin-left:12px;">{b['date']}</span>
                </div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="color:{icon_color};font-weight:600;">${pl:+,}</span>
                    {edge_badge(b['grade'])}
                    <span style="color:{edge_color};font-size:12px;font-weight:600;">{edge_label}</span>
                </div>
            </div>
            <p style="color:#8890b0;font-size:12px;margin-top:6px;">{b['notes']}</p>
        </div>
        """, unsafe_allow_html=True)

    # Weekly P/L Chart
    st.divider()
    st.markdown('<p class="section-label">Weekly P/L</p>', unsafe_allow_html=True)

    df_weekly = pd.DataFrame(DEMO_WEEKLY_PL)

    fig = go.Figure()

    # Net P/L bars
    colors = ["#22c55e" if n >= 0 else "#ef4444" for n in df_weekly["net"]]
    fig.add_trace(go.Bar(
        x=df_weekly["week"], y=df_weekly["net"],
        marker_color=colors, name="Net P/L",
        text=[f"${n:+,}" for n in df_weekly["net"]],
        textposition="outside", textfont=dict(color="#e2e8f0", size=11),
    ))

    # Balance line
    fig.add_trace(go.Scatter(
        x=df_weekly["week"], y=df_weekly["ending"],
        mode="lines+markers", name="Balance",
        line=dict(color="#D4A017", width=2),
        marker=dict(size=6, color="#D4A017"),
        yaxis="y2",
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a1a",
        plot_bgcolor="#0a0a1a",
        font=dict(color="#8890b0"),
        height=350,
        margin=dict(l=40, r=40, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Net P/L ($)", gridcolor="#1e1e30", zeroline=True, zerolinecolor="#2a2a3a"),
        yaxis2=dict(title="Balance ($)", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"),
        bargap=0.3,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Log a new bet
    st.divider()
    st.markdown('<p class="section-label">Log a Bet</p>', unsafe_allow_html=True)

    with st.form("log_bet_form"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            log_game = st.text_input("Game / Bet", placeholder="e.g., Bucks -4 vs Heat")
        with col_f2:
            log_type = st.selectbox("Type", ["Spread", "ML", "Total", "Prop", "Parlay"])
        with col_f3:
            log_grade = st.selectbox("Edge Grade", ["A", "B+", "B", "B-", "C", "D", "F"])

        col_f4, col_f5, col_f6 = st.columns(3)
        with col_f4:
            log_risk = st.number_input("Risk ($)", min_value=0.0, step=5.0)
        with col_f5:
            log_result = st.selectbox("Result", ["Pending", "W", "L", "Push"])
        with col_f6:
            log_payout = st.number_input("Payout ($)", min_value=0.0, step=5.0)

        log_thesis = st.text_area("Thesis / Why is the market wrong?", height=60)
        submitted = st.form_submit_button("Log Bet", use_container_width=True)

        if submitted and log_game:
            st.session_state.bet_log.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "game": log_game, "type": log_type, "grade": log_grade,
                "risk": log_risk, "result": log_result, "payout": log_payout,
                "thesis": log_thesis,
            })
            st.session_state.bankroll["daily_risk"] += log_risk
            st.success(f"Logged: {log_game} | Grade {log_grade} | ${log_risk}")


# ============================================================
# TAB 6: AI CHAT
# ============================================================
with tab_chat:
    st.markdown("### Edge Finder AI")
    st.markdown('<p style="color:#8890b0;font-size:13px;">Ask me anything. "What\'s the play today?" | "I like the Bucks tonight" | "Run audit"</p>', unsafe_allow_html=True)

    SYSTEM_PROMPT = """You are Edge Finder v4, Peter's betting analyst. Your job is to find edge -- situations where the market is wrong.

Core Rule: If you can't answer "Why is the market wrong?" the answer is NO BET.

Bet Grades:
A = Clear edge, high confidence (Full unit)
B = Edge exists, moderate confidence (Half unit)
C = Possible edge, low confidence (Small or pass)
D = No edge identified (NO BET)
F = Market is right (NO BET + flag trap)

Default is D. Bets earn their way up.

When user says "I like X" -- look for data that supports or contradicts. Gut + data alignment = upgrade. Data contradicts gut = flag conflict.

Output Quick Take format by default:
[BET]
Edge: Yes/No/Maybe
Grade: A-F
Why: [1 sentence]
Risk: [amount per bankroll rules]

Style: Short answers. Honest. Skeptical. "No bet" is a valid answer. Never say "lock" or "guaranteed." No excuses as analysis.

Sports focus (Feb/March 2026): NBA primary, NHL secondary. NFL/CFB offseason. NCAA banned unless user initiates.

Red flags (auto-pass): Heavy favorite (-300+), "should win" logic, consensus pick with no contrarian angle, chasing losses, volume plays.

Parlay rules: Max 3 legs for value, max 4 EVER, each leg needs own edge.

Set it and forget it. Place the bet, walk away. No live betting, no hedging, no cash-out panic."""

    # Demo responses for common queries
    DEMO_RESPONSES = {
        "what's the play today": """**TONIGHT'S EDGE PLAYS**

**STRAIGHT BETS (Heavy Hitter):**

1. **Knicks -5.5 vs Pacers** -- Grade A | $50
   Edge: Pacers missing Haliburton + Turner. Line hasn't adjusted enough.

2. **Bucks -4 vs Heat** -- Grade B | $25
   Edge: Heat on B2B, 3rd game in 5 nights. Fatigue not fully priced.

**VALUE PARLAY ($25 to win $121):**
- Bucks -4
- Mavericks ML +135
- Combined: +485

**PLAYER PROP:**
- Jokic OVER 11.5 reb -- Grade A | $25
  Edge: Playing worst rebounding team. 2.7 rebounds of cushion.

**PASS:**
- Lakers/Celtics -- no edge, line is fair
- Nuggets/Suns -- efficient line

Total suggested risk: $125
Expected edge plays: 3-4""",

        "i like the bucks": """**DEEP DIVE: Heat @ Bucks**

**THE LINE:** Bucks -4
**ML:** MIL -185 / MIA +155

**WHY MARKET MIGHT BE WRONG:**
- Heat on B2B, 3rd game in 5 nights
- Heat shooting 38% on B2Bs this season
- Bucks fully rested at home
- Fatigue not fully priced into -4

**WHY MARKET MIGHT BE RIGHT:**
- Heat covered 3 of last 5 as road dog
- Butler historically performs on short rest

**YOUR GUT:** You like the Bucks
**DATA:** Supports your read

**GUT + DATA: ALIGNMENT**

**VERDICT: Grade B**
Half unit. Edge is real but not overwhelming.
Risk: $25 (half unit at current bankroll)""",

        "run audit": """**WEEKLY AUDIT**

**RECORD:** 4-2
**NET P/L:** +$263
**ROI:** +18.4%
**EDGE ACCURACY:** 83%

**BY TYPE:**
| Type | W-L | P/L |
|------|-----|-----|
| Spreads | 2-0 | +$240 |
| Props | 1-0 | +$90 |
| Parlays | 0-1 | -$50 |
| ML | 1-1 | -$17 |

**PROCESS GRADE: A-**
Edge identification was strong. Only miss was a C-grade bet that should have been a pass.

**LESSON:** Grade C = pass. Stop betting them.

**WHAT'S WORKING:**
- Rest/fatigue edges (3-0)
- Injury-based edges (2-0)

**WHAT'S NOT:**
- Parlays (0-1, variance but monitor)""",
    }

    # Initialize chat
    if not st.session_state.chat_messages:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": "Edge Finder v4 online. What's the play today?\n\nI can analyze any matchup, build parlays, check player props, or run your audit. Give me a game, a gut feeling, or just ask what's worth betting tonight."
        })

    # Display messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask Edge Finder..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Try Azure OpenAI, fall back to demo
        response = None
        if has_api:
            try:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
                    api_key=st.secrets["AZURE_OPENAI_KEY"],
                    api_version=st.secrets.get("AZURE_OPENAI_API_VERSION", "2024-06-01"),
                )
                deployment = st.secrets.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.chat_messages[-10:]:
                    messages.append({"role": m["role"], "content": m["content"]})

                with st.chat_message("assistant"):
                    with st.spinner("Finding edge..."):
                        completion = client.chat.completions.create(
                            model=deployment, messages=messages, temperature=0.7, max_tokens=1000,
                        )
                        response = completion.choices[0].message.content
                        st.markdown(response)
            except Exception as e:
                response = None

        if response is None:
            # Demo mode fallback
            prompt_lower = prompt.lower().strip()
            demo_response = None

            for key, val in DEMO_RESPONSES.items():
                if key in prompt_lower:
                    demo_response = val
                    break

            if demo_response is None:
                # Generic demo response
                demo_response = f"""**QUICK TAKE**

Analyzing: "{prompt}"

Edge: Maybe
Grade: C
Why: Need more specific matchup data to identify edge. Give me a specific game or player and I'll dig deeper.

Try:
- "What's the play today?" for full slate analysis
- "I like the Bucks tonight" for specific game deep dive
- "Jokic rebounds?" for prop analysis
- "Run audit" for performance review

*Demo mode active. Connect Azure OpenAI for live analysis.*"""

            with st.chat_message("assistant"):
                st.markdown(demo_response)
            response = demo_response

        st.session_state.chat_messages.append({"role": "assistant", "content": response})


# --- Footer ---
st.markdown(f"""
<div class="footer">
    Edge Finder v4 | Interactive Demo | No edge = No bet. Period.<br>
    Built with Sinton.ia | {datetime.now().strftime("%Y")}
</div>
""", unsafe_allow_html=True)
