"""
ui.py
-----
Barkavi Textiles UI kit — one place for the colourful theme used on every page:
page setup (config + logo + CSS + auth), hero header, gradient KPI cards,
section titles, status pills, progress bars and a branded Plotly template.

Usage in a page:
    from utils.ui import setup_page, kpi_row, section, chart
    setup_page("Dashboard", "📊", "Live overview of production, stock and profit")
"""

import html
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

from utils.branding import BRAND_NAME, page_icon, apply_sidebar_logo

# ------------------------------------------------------------------ palette
GOLD = "#B07A1E"
INDIGO = "#1A1446"
PALETTE = ["#6366F1", "#14B8A6", "#F59E0B", "#F43F5E", "#10B981",
           "#0EA5E9", "#A855F7", "#B07A1E", "#EC4899", "#84CC16"]

GRADIENTS = {
    "indigo":  ("#4F46E5", "#7C3AED"),
    "teal":    ("#0D9488", "#2DD4BF"),
    "amber":   ("#D97706", "#FBBF24"),
    "rose":    ("#E11D48", "#FB7185"),
    "emerald": ("#059669", "#34D399"),
    "sky":     ("#0284C7", "#38BDF8"),
    "violet":  ("#7C3AED", "#D946EF"),
    "gold":    ("#8A5A12", "#D4A445"),
    "slate":   ("#334155", "#64748B"),
    "orange":  ("#EA580C", "#FB923C"),
}

SEVERITY = {
    "Critical": ("#FEE2E2", "#B91C1C", "🔴"),
    "High":     ("#FFEDD5", "#C2410C", "🟠"),
    "Medium":   ("#FEF3C7", "#A16207", "🟡"),
    "Low":      ("#DCFCE7", "#15803D", "🟢"),
    "Info":     ("#E0E7FF", "#4338CA", "🔵"),
}

# ------------------------------------------------------------------ plotly template
_tpl = go.layout.Template()
_tpl.layout = go.Layout(
    colorway=PALETTE,
    font=dict(family="Poppins, Segoe UI, sans-serif", size=13, color="#1F1B2E"),
    title=dict(font=dict(size=16, color=INDIGO), x=0.01, xanchor="left"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=56, b=10),
    hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#E5DCC8"),
    legend=dict(orientation="h", yanchor="top", y=-0.16, xanchor="center", x=0.5, title_text=""),
    xaxis=dict(gridcolor="#EFE8DA", zerolinecolor="#E5DCC8", linecolor="#E5DCC8"),
    yaxis=dict(gridcolor="#EFE8DA", zerolinecolor="#E5DCC8", linecolor="#E5DCC8"),
)
pio.templates["barkavi"] = _tpl
pio.templates.default = "plotly_white+barkavi"
px.defaults.template = "plotly_white+barkavi"
px.defaults.color_discrete_sequence = PALETTE
px.defaults.color_continuous_scale = ["#FEF3C7", "#FBBF24", "#F97316", "#E11D48", "#7C3AED"]

SEQ_SCALE = ["#EEF2FF", "#A5B4FC", "#6366F1", "#4338CA", "#1E1B4B"]
GOLD_SCALE = ["#FFF7E6", "#F5D58C", "#D4A445", "#B07A1E", "#6B4710"]


# ------------------------------------------------------------------ CSS
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, textarea, select {
    font-family: 'Poppins', 'Segoe UI', sans-serif;
}
.stApp { background: #FBF8F2; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }
h1, h2, h3, h4 { color: #1A1446; font-weight: 700; letter-spacing: -0.01em; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1446 0%, #2A1B5E 55%, #3B1F5C 100%);
    border-right: 3px solid #B07A1E;
}
section[data-testid="stSidebar"] * { color: #EDE9FE !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    border-radius: 10px; margin: 2px 6px; padding: 6px 10px; transition: all .15s ease;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: rgba(212,164,69,0.18);
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(90deg, #B07A1E, #D4A445);
    box-shadow: 0 4px 14px rgba(176,122,30,.45);
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span {
    color: #1A1446 !important; font-weight: 700;
}
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.15); }
section[data-testid="stSidebar"] div.stButton > button {
    background: rgba(255,255,255,.08); border: 1px solid rgba(212,164,69,.6);
}
section[data-testid="stSidebar"] input { color: #1F1B2E !important; }
section[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(255,255,255,.07); border: 1px solid rgba(212,164,69,.35);
}
section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background: rgba(255,255,255,.06); }
/* rename the entry page "app" -> "Home" in the navigation */
[data-testid="stSidebarNav"] ul li:first-child a span { font-size: 0 !important; }
[data-testid="stSidebarNav"] ul li:first-child a span::after { content: "🏠 Home"; font-size: .95rem; }
[data-testid="stSidebarHeader"] img, [data-testid="stLogo"] {
    height: 3.4rem !important; max-width: 100% !important;
}
.user-chip {
    display:flex; align-items:center; gap:.7rem; padding:.7rem .8rem; margin:.2rem 0 .6rem 0;
    background: rgba(255,255,255,.07); border:1px solid rgba(212,164,69,.35); border-radius:14px;
}
.user-chip .avatar {
    width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center;
    background: linear-gradient(135deg,#B07A1E,#F5D58C); color:#1A1446 !important; font-weight:800; font-size:1.05rem;
}
.user-chip .name { font-weight:600; font-size:.92rem; line-height:1.1; }
.user-chip .role { font-size:.75rem; opacity:.8; }

/* ---------- Buttons ---------- */
div.stButton > button, div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #B07A1E 0%, #D4A445 100%);
    color: #fff; border: none; border-radius: 12px; padding: .55em 1.3em; font-weight: 600;
    box-shadow: 0 4px 12px rgba(176,122,30,.30); transition: all .18s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-1px); box-shadow: 0 8px 20px rgba(176,122,30,.40); color:#fff; border:none;
}
div.stButton > button p, div.stDownloadButton > button p,
div[data-testid="stFormSubmitButton"] > button p { color:#fff; }

/* ---------- Containers / forms / tabs ---------- */
[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] {
    border-radius: 16px;
}
[data-testid="stForm"] {
    background: #FFFFFF; border: 1px solid #EDE4D3; box-shadow: 0 6px 24px rgba(26,20,70,.06);
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {
    border-radius: 18px;
}
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: #F3EDE1; padding: 6px; border-radius: 14px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 10px; padding: 8px 16px; background: transparent; font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#1A1446,#4F46E5) !important; color: #fff !important;
}
.stTabs [aria-selected="true"] p { color:#fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none; }
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; border: 1px solid #EDE4D3; }
[data-testid="stMetric"] {
    background: #fff; border: 1px solid #EDE4D3; border-radius: 16px; padding: 14px 18px;
    box-shadow: 0 4px 16px rgba(26,20,70,.05);
}
[data-testid="stExpander"] { background:#fff; border-radius: 14px; border: 1px solid #EDE4D3; }
[data-testid="stAlert"] { border-radius: 14px; }

/* ---------- Hero ---------- */
.hero {
    position: relative; overflow: hidden; border-radius: 22px; padding: 26px 30px; margin-bottom: 22px;
    background: linear-gradient(120deg, #1A1446 0%, #3B2A8C 45%, #B07A1E 100%);
    box-shadow: 0 14px 40px rgba(26,20,70,.25);
}
.hero::after {
    content:""; position:absolute; right:-60px; top:-60px; width:260px; height:260px; border-radius:50%;
    background: radial-gradient(circle, rgba(245,213,140,.45), rgba(245,213,140,0) 70%);
}
.hero::before {
    content:""; position:absolute; inset:0;
    background: repeating-linear-gradient(115deg, rgba(255,255,255,.035) 0 2px, transparent 2px 14px);
}
.hero .eyebrow { color:#F5D58C; font-size:.78rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; position:relative; }
.hero h1 { color:#fff; margin:.15rem 0 .2rem 0; font-size:2rem; font-weight:800; position:relative; padding:0; }
.hero p { color:#E9E3FF; margin:0; font-size:.98rem; position:relative; }

/* ---------- KPI cards ---------- */
.kpi {
    position:relative; overflow:hidden; border-radius:18px; padding:18px 18px 16px 18px; color:#fff;
    min-height: 128px; box-shadow: 0 10px 26px rgba(26,20,70,.16); transition: transform .18s ease;
}
.kpi:hover { transform: translateY(-3px); }
.kpi::after {
    content:""; position:absolute; right:-28px; bottom:-28px; width:110px; height:110px; border-radius:50%;
    background: rgba(255,255,255,.14);
}
.kpi .k-icon { font-size:1.5rem; position:absolute; right:16px; top:14px; opacity:.95; }
.kpi .k-label { font-size:.78rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; opacity:.92; }
.kpi .k-value { font-size:1.75rem; font-weight:800; margin:.25rem 0 .2rem 0; line-height:1.1; }
.kpi .k-delta { display:inline-block; font-size:.78rem; font-weight:700; padding:2px 9px; border-radius:20px;
                background: rgba(255,255,255,.22); }
.kpi .k-sub { font-size:.75rem; opacity:.85; margin-top:.35rem; }

/* ---------- Section title ---------- */
.sec { display:flex; align-items:center; gap:.6rem; margin: 1.4rem 0 .7rem 0; }
.sec .bar { width:6px; height:26px; border-radius:6px; background: linear-gradient(180deg,#B07A1E,#6366F1); }
.sec .t { font-size:1.2rem; font-weight:700; color:#1A1446; }
.sec .s { font-size:.85rem; color:#6B6580; margin-left:.3rem; }

/* ---------- Pills / alerts / progress ---------- */
.pill { display:inline-block; padding:3px 11px; border-radius:20px; font-size:.75rem; font-weight:700; }
.alert-card {
    display:flex; gap:.9rem; align-items:flex-start; padding:14px 16px; border-radius:14px; margin-bottom:10px;
    border-left: 6px solid; background:#fff; box-shadow: 0 4px 14px rgba(26,20,70,.05);
}
.alert-card .a-title { font-weight:700; font-size:.95rem; }
.alert-card .a-body { font-size:.86rem; color:#4B4560; }
.alert-card .a-meta { font-size:.72rem; color:#8A8499; margin-top:3px; }
.prog-row { margin: 8px 0 14px 0; }
.prog-head { display:flex; justify-content:space-between; font-size:.86rem; font-weight:600; color:#2D2650; }
.prog-track { height:12px; background:#F1EADB; border-radius:10px; overflow:hidden; margin-top:5px; }
.prog-fill { height:100%; border-radius:10px; }
.tile {
    border-radius:18px; padding:18px; background:#fff; border:1px solid #EDE4D3; min-height:168px;
    box-shadow: 0 6px 18px rgba(26,20,70,.05); transition: all .18s ease;
}
.tile:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(26,20,70,.12); }
.tile .ti { width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center;
            font-size:1.4rem; margin-bottom:10px; }
.tile .tt { font-weight:700; color:#1A1446; font-size:1rem; }
.tile .td { font-size:.83rem; color:#6B6580; margin-top:3px; }
.tile .tag { font-size:.68rem; font-weight:700; color:#B07A1E; letter-spacing:.08em; text-transform:uppercase; }
.footer { text-align:center; color:#8A8499; font-size:.78rem; margin-top:2.5rem; }
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ page setup
def setup_page(title: str, icon: str = "", subtitle: str = "", eyebrow: str = "",
               roles=None, show_hero: bool = True, layout: str = "wide"):
    """set_page_config + theme + logo + login check + sidebar user chip + hero."""
    from utils.auth import is_logged_in, get_current_role

    st.set_page_config(page_title=f"{title} | {BRAND_NAME}", page_icon=page_icon(),
                       layout=layout, initial_sidebar_state="expanded")
    inject_css()
    apply_sidebar_logo()

    if not is_logged_in():
        hero(title, icon, "Please log in from the home page to access this module.", eyebrow or BRAND_NAME)
        st.warning("⚠️ Please log in to access this page.")
        st.stop()

    if roles and get_current_role() not in roles:
        hero(title, icon, subtitle, eyebrow or BRAND_NAME)
        st.error(f"🚫 This page is available only for: {', '.join(roles)}.")
        st.stop()

    sidebar_user()
    if show_hero:
        hero(title, icon, subtitle, eyebrow or BRAND_NAME)


def sidebar_user():
    from utils.auth import logout_user
    name = st.session_state.get("full_name", "") or st.session_state.get("username", "")
    role = st.session_state.get("role", "")
    initials = "".join(p[0] for p in name.split()[:2]).upper() or "U"
    with st.sidebar:
        st.markdown(
            f"<div class='user-chip'><div class='avatar'>{html.escape(initials)}</div>"
            f"<div><div class='name'>{html.escape(name)}</div><div class='role'>{html.escape(role)}</div></div></div>",
            unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            logout_user()
            st.rerun()


def hero(title: str, icon: str = "", subtitle: str = "", eyebrow: str = ""):
    st.markdown(
        f"<div class='hero'><div class='eyebrow'>{html.escape(eyebrow or BRAND_NAME)}</div>"
        f"<h1>{icon} {html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>",
        unsafe_allow_html=True)


def section(title: str, subtitle: str = ""):
    sub = f"<span class='s'>{html.escape(subtitle)}</span>" if subtitle else ""
    st.markdown(f"<div class='sec'><div class='bar'></div><div class='t'>{html.escape(title)}</div>{sub}</div>",
                unsafe_allow_html=True)


# ------------------------------------------------------------------ KPI cards
def kpi_html(label, value, icon="", color="indigo", delta=None, delta_good_when_up=True, sub=""):
    c1, c2 = GRADIENTS.get(color, GRADIENTS["indigo"])
    delta_html = ""
    if delta is not None:
        try:
            d = float(delta)
            arrow = "▲" if d > 0 else ("▼" if d < 0 else "■")
            good = (d >= 0) == delta_good_when_up
            mark = "" if d == 0 else (" ✓" if good else " !")
            delta_html = f"<span class='k-delta'>{arrow} {abs(d):.1f}%{mark}</span>"
        except (TypeError, ValueError):
            delta_html = f"<span class='k-delta'>{html.escape(str(delta))}</span>"
    sub_html = f"<div class='k-sub'>{html.escape(sub)}</div>" if sub else ""
    return (f"<div class='kpi' style='background:linear-gradient(135deg,{c1} 0%,{c2} 100%);'>"
            f"<div class='k-icon'>{icon}</div><div class='k-label'>{html.escape(str(label))}</div>"
            f"<div class='k-value'>{html.escape(str(value))}</div>{delta_html}{sub_html}</div>")


def money(v, unit="L"):
    """Indian-style rupee formatting with sign in front: −₹2,033.3 L / ₹12.4 Cr / ₹1,250."""
    sign = "−" if v < 0 else ""
    a = abs(v)
    if unit == "L":
        return f"{sign}₹{a / 1e5:,.2f} L"
    if unit == "Cr":
        return f"{sign}₹{a / 1e7:,.2f} Cr"
    return f"{sign}₹{a:,.0f}"


def kpi_card(*args, **kwargs):
    st.markdown(kpi_html(*args, **kwargs), unsafe_allow_html=True)


def kpi_row(items, cols=None):
    """items: list of dicts with keys label, value, icon, color, delta, delta_good_when_up, sub."""
    cols = cols or len(items)
    columns = st.columns(cols)
    for i, item in enumerate(items):
        with columns[i % cols]:
            kpi_card(**item)


def pill(text, severity="Info"):
    bg, fg, _ = SEVERITY.get(severity, SEVERITY["Info"])
    return f"<span class='pill' style='background:{bg};color:{fg};'>{html.escape(str(text))}</span>"


def alert_card(title, body, severity="Info", meta=""):
    bg, fg, dot = SEVERITY.get(severity, SEVERITY["Info"])
    st.markdown(
        f"<div class='alert-card' style='border-left-color:{fg};'>"
        f"<div style='font-size:1.3rem'>{dot}</div><div style='flex:1'>"
        f"<div class='a-title' style='color:{fg}'>{html.escape(title)} &nbsp;{pill(severity, severity)}</div>"
        f"<div class='a-body'>{html.escape(body)}</div>"
        + (f"<div class='a-meta'>{html.escape(meta)}</div>" if meta else "") +
        "</div></div>", unsafe_allow_html=True)


def progress_bar(label, value, maximum, right_text="", color=None):
    pct = 0 if maximum <= 0 else max(0.0, min(100.0, value / maximum * 100))
    if color is None:
        color = ("linear-gradient(90deg,#E11D48,#FB7185)" if pct < 30 else
                 "linear-gradient(90deg,#D97706,#FBBF24)" if pct < 60 else
                 "linear-gradient(90deg,#059669,#34D399)")
    st.markdown(
        f"<div class='prog-row'><div class='prog-head'><span>{html.escape(label)}</span>"
        f"<span>{html.escape(right_text)}</span></div>"
        f"<div class='prog-track'><div class='prog-fill' style='width:{pct:.1f}%;background:{color};'></div></div></div>",
        unsafe_allow_html=True)


def tile(icon, title, desc, color="indigo", tag=""):
    c1, c2 = GRADIENTS.get(color, GRADIENTS["indigo"])
    tag_html = f"<div class='tag'>{html.escape(tag)}</div>" if tag else ""
    st.markdown(
        f"<div class='tile'><div class='ti' style='background:linear-gradient(135deg,{c1},{c2});'>{icon}</div>"
        f"{tag_html}<div class='tt'>{html.escape(title)}</div><div class='td'>{html.escape(desc)}</div></div>",
        unsafe_allow_html=True)


def footer():
    st.markdown(f"<div class='footer'>© {BRAND_NAME} · AI-Powered Smart Powerloom Production System</div>",
                unsafe_allow_html=True)


# ------------------------------------------------------------------ charts
def style_fig(fig, height=None, title=None):
    fig.update_layout(template="plotly_white+barkavi")
    if title is not None:
        fig.update_layout(title=title)
    if height:
        fig.update_layout(height=height)
    return fig


def chart(fig, height=None, key=None):
    """Render a Plotly figure with the Barkavi template (Streamlit's own theme off)."""
    style_fig(fig, height=height)
    st.plotly_chart(fig, use_container_width=True, theme=None, key=key)


def gauge(value, title, max_value=100, suffix="%", bands=None, color=GOLD, height=240):
    bands = bands or [(0, 0.6, "#FEE2E2"), (0.6, 0.8, "#FEF3C7"), (0.8, 1.0, "#DCFCE7")]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number={"suffix": suffix, "font": {"size": 34, "color": INDIGO}},
        title={"text": title, "font": {"size": 14, "color": "#4B4560"}},
        gauge={"axis": {"range": [0, max_value], "tickcolor": "#B8AFA0"},
               "bar": {"color": color, "thickness": 0.28},
               "bgcolor": "white", "borderwidth": 0,
               "steps": [{"range": [a * max_value, b * max_value], "color": c} for a, b, c in bands]},
    ))
    fig.update_layout(height=height, margin=dict(l=34, r=34, t=50, b=10))
    return fig
