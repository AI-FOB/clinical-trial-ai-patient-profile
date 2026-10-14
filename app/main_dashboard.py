"""Clinical Patient Profile – enterprise review dashboard.

Layout:
    Top bar  : title + horizontal controls (theme, arm, USUBJID, refresh, clear chat)
    Header   : patient hero card
    Row 1    : demographic KPI cards
    Row 2    : full-width AE vs EX timeline
    Row 3    : [1.5 | 1] split -> deep-dive tabs (AE/CM/MH/LB) | pinned AI agent
"""
import os
import sqlite3
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.agent.text_to_sql_agent import get_schema, query_agent  # noqa: E402
from src.agent.llm_config import get_llm  # noqa: E402

st.set_page_config(page_title="Clinical Patient Profile | AI Review", page_icon="🧬", layout="wide")

DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "clinical_data.db")

ACCENTS = {
    "Clinical Blue": ("#1d4ed8", "#e0e7ff"),
    "Teal": ("#0f766e", "#ccfbf1"),
    "Indigo": ("#4338ca", "#e0e7ff"),
    "Crimson": ("#be123c", "#ffe4e6"),
}
SEV_COLORS = {"MILD": "#16a34a", "MODERATE": "#f59e0b", "SEVERE": "#dc2626"}


# ============================================================================
# Resources (cached once per server process)
# ============================================================================
@st.cache_resource(show_spinner=False)
def get_connection() -> sqlite3.Connection | None:
    """One shared read-only SQLite connection for the whole app."""
    if not os.path.exists(DB_PATH):
        return None
    uri = f"file:{DB_PATH.replace(os.sep, '/')}?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


@st.cache_resource(show_spinner=False)
def get_agent_llm():
    """LLM client is built once, not on every chat message."""
    return get_llm()


@st.cache_data(show_spinner=False)
def table_names() -> set[str]:
    conn = get_connection()
    if conn is None:
        return set()
    return {r[0].lower() for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


@st.cache_data(show_spinner=False, ttl=3600)
def load_data(query: str, params: tuple = ()) -> pd.DataFrame:
    """Parameterized query -> DataFrame (cached per query+params)."""
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception:
        return pd.DataFrame()


def load_domain(table: str, subject: str) -> pd.DataFrame:
    if table not in table_names():
        return pd.DataFrame()
    # Table name comes from a fixed whitelist (table_names), subject is bound.
    return load_data(f"SELECT * FROM {table} WHERE USUBJID = ?", (subject,))


# ============================================================================
# Top title + horizontal control bar
# ============================================================================
dm_all = load_data("SELECT * FROM dm")
if dm_all.empty:
    st.error("Database not found or empty. Run the data pipeline first.")
    st.stop()

title_slot = st.empty()  # filled after controls so it can show the subject count

col1, col2, col3, col4, col5 = st.columns([1, 1, 1.5, 0.75, 0.75], vertical_alignment="bottom")
with col1:
    accent_name = st.selectbox("🎨 Theme accent", list(ACCENTS), key="accent")
    ACCENT, ACCENT_SOFT = ACCENTS[accent_name]
with col2:
    arms = ["All arms"] + sorted(dm_all["ARM"].dropna().unique().tolist())
    arm_filter = st.selectbox("💊 Treatment arm", arms, key="arm_filter")
    pool = dm_all if arm_filter == "All arms" else dm_all[dm_all["ARM"] == arm_filter]
with col3:
    subject = st.selectbox("🧑‍⚕️ Subject (USUBJID)", pool["USUBJID"].tolist(), key="subject")
with col4:
    if st.button("🔄 Refresh", use_container_width=True, key="btn_refresh"):
        st.cache_data.clear()
        get_schema.cache_clear()
        st.rerun()
with col5:
    if st.button("🧹 Clear chat", use_container_width=True, key="btn_clear_chat"):
        st.session_state.messages = []
        st.rerun()

title_slot.markdown(
    f"<div class='topbar'><span class='brand'>🧬 Patient Profile</span>"
    f"<span class='brand-sub'>Clinical Data Review Platform • Subjects in view: "
    f"<b>{len(pool)}</b> / {len(dm_all)} • LLM: NVIDIA Nemotron-3 Super 120B</span></div>",
    unsafe_allow_html=True,
)


# ============================================================================
# CSS – bright, high-contrast palette (explicit dark text everywhere)
# ============================================================================
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stText {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%); color: #0f172a; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 1rem; max-width: 100%; }}
section[data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display: none; }}

.topbar {{ display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; margin-bottom: 4px; }}
.topbar .brand {{ color: #0f172a; font-size: 1.35rem; font-weight: 800; }}
.topbar .brand-sub {{ color: #64748b; font-size: .82rem; }}
.topbar .brand-sub b {{ color: {ACCENT}; }}
.stSelectbox label p {{ color: #334155 !important; font-weight: 600; font-size: .8rem; }}

.hero {{
  background: linear-gradient(120deg, {ACCENT} 0%, #0ea5e9 100%);
  border-radius: 16px; padding: 18px 26px; margin-bottom: 18px;
  box-shadow: 0 10px 25px -10px {ACCENT}88;
}}
.hero h1 {{ color: #ffffff !important; font-size: 1.55rem; font-weight: 800; margin: 0; }}
.hero p  {{ color: #e0f2fe !important; margin: 4px 0 0 0; font-size: .92rem; }}

.kpi {{
  background: #ffffff; border-radius: 14px; padding: 16px 18px;
  border: 1px solid #e2e8f0; border-top: 4px solid {ACCENT};
  box-shadow: 0 4px 14px rgba(15, 23, 42, .06);
  transition: transform .18s ease, box-shadow .18s ease; height: 100%;
  min-height: 120px; box-sizing: border-box;
  display: flex; flex-direction: column; justify-content: center;
}}
.kpi:hover {{ transform: translateY(-3px); box-shadow: 0 10px 24px rgba(15, 23, 42, .12); }}
.kpi .label {{ color: #64748b; font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
.kpi .value {{ color: #0f172a; font-size: 1.45rem; font-weight: 800; margin-top: 4px; line-height: 1.2; }}
.kpi .sub   {{ color: {ACCENT}; font-size: .78rem; font-weight: 600; margin-top: 2px; }}
.kpi.alert  {{ border-top-color: #dc2626; }}
.kpi.alert .value {{ color: #b91c1c; }}

.section-title {{
  color: #0f172a; font-weight: 700; font-size: 1.05rem; margin: 8px 0 8px 0;
  display: flex; align-items: center; gap: 8px;
}}
.section-title::before {{ content: ""; width: 4px; height: 18px; background: {ACCENT}; border-radius: 2px; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: #ffffff; border-radius: 14px !important; border-color: #e2e8f0 !important;
  box-shadow: 0 4px 14px rgba(15, 23, 42, .05);
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 6px; background: #f1f5f9; padding: 5px; border-radius: 12px; }}
.stTabs [data-baseweb="tab"] {{
  background: transparent; border-radius: 9px; padding: 6px 14px; color: #334155; font-weight: 600;
}}
.stTabs [aria-selected="true"] {{ background: #ffffff !important; color: {ACCENT} !important;
  box-shadow: 0 2px 6px rgba(15,23,42,.08); }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

.agent-head {{ background: {ACCENT_SOFT}; color: #0f172a; border-radius: 10px; padding: 10px 14px;
  font-size: .85rem; margin-bottom: 8px; border: 1px solid {ACCENT}33; }}
.agent-head b {{ color: {ACCENT}; }}
[data-testid="stChatMessage"] {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; }}
[data-testid="stChatMessage"] * {{ color: #0f172a; }}
</style>
""",
    unsafe_allow_html=True,
)


def kpi(col, label: str, value, sub: str = "", alert: bool = False):
    col.markdown(
        f"<div class='kpi {'alert' if alert else ''}'><div class='label'>{label}</div>"
        f"<div class='value'>{value}</div><div class='sub'>{sub or '&nbsp;'}</div></div>",
        unsafe_allow_html=True,
    )


def section(title: str):
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)


# ============================================================================
# Data for selected subject
# ============================================================================
dm = dm_all[dm_all["USUBJID"] == subject].iloc[0]
ae_df = load_domain("ae", subject)
ex_df = load_domain("ex", subject)
cm_df = load_domain("cm", subject)
mh_df = load_domain("mh", subject)
lb_df = load_domain("lb", subject)

n_ae = len(ae_df)
n_sev = int((ae_df.get("AESEV", pd.Series(dtype=str)).astype(str).str.upper() == "SEVERE").sum())
n_ser = int((ae_df.get("AESER", pd.Series(dtype=str)).astype(str).str.upper() == "Y").sum())

# ============================================================================
# Header + Row 1: KPIs
# ============================================================================
st.markdown(
    f"<div class='hero'><h1>Patient {subject}</h1>"
    f"<p>Site {dm.get('SITEID', '—')} • {dm.get('RACE', '—')} • {dm.get('COUNTRY', '') or ''}</p></div>",
    unsafe_allow_html=True,
)

k = st.columns(5)
kpi(k[0], "Age", f"{dm.get('AGE', '—')} <span style='font-size:.9rem;color:#64748b'>{dm.get('AGEU', 'yrs')}</span>")
kpi(k[1], "Sex", {"M": "Male", "F": "Female"}.get(str(dm.get("SEX")), dm.get("SEX", "—")))
kpi(k[2], "Treatment Arm", dm.get("ARM", "—"), dm.get("ARMCD", "") or "")
kpi(k[3], "Adverse Events", n_ae, f"{n_ser} serious", alert=n_ser > 0)
kpi(k[4], "Severe AEs", n_sev, "AESEV = SEVERE", alert=n_sev > 0)

st.write("")

# ============================================================================
# Master split: [Timeline + Deep Dive] | AI agent
# ============================================================================
_tl_rows = (ae_df["AETERM"].nunique() if "AETERM" in ae_df.columns else 0) + \
           (ex_df["EXTRT"].nunique() if "EXTRT" in ex_df.columns else 0)
TIMELINE_H = max(280, 34 * _tl_rows + 120)
DEEP_DIVE_H = 620
# Agent panel spans timeline card (+ chrome) + gap + deep-dive card.
AGENT_H = TIMELINE_H + 90 + 16 + DEEP_DIVE_H

left_col, right_col = st.columns([1.8, 1], gap="medium")

# --- Left: Clinical timeline ---------------------------------------------------
with left_col, st.container(border=True):
    section("📅 Clinical Timeline — Adverse Events vs Exposure")
    if ae_df.empty and ex_df.empty:
        st.info("No AE or exposure records for this subject.")
    else:
        fig = go.Figure()

        # Exposure bars (EX)
        if not ex_df.empty and {"EXSTDY"}.issubset(ex_df.columns):
            for _, r in ex_df.iterrows():
                if pd.isnull(r["EXSTDY"]):
                    continue
                s = float(r["EXSTDY"])
                e = float(r["EXENDY"]) if pd.notnull(r.get("EXENDY")) else s + 1
                label = f"💊 {r.get('EXTRT', 'Study drug')}"
                dose = f"{r.get('EXDOSE', '')} {r.get('EXDOSU', '') or ''}".strip()
                fig.add_trace(go.Scatter(
                    x=[s, e], y=[label, label], mode="lines",
                    line=dict(color=ACCENT, width=14), opacity=0.55, showlegend=False,
                    hovertemplate=f"<b>{label}</b><br>Dose: {dose}<br>Day {s:.0f} → {e:.0f}<extra></extra>",
                ))

        # Adverse events (AE)
        shown = set()
        for _, r in ae_df.iterrows():
            s = r.get("AESTDY")
            s = float(s) if pd.notnull(s) else 0.0
            ongoing = pd.isnull(r.get("AEENDY"))
            e = s + 15 if ongoing else float(r["AEENDY"])
            sev = str(r.get("AESEV", "")).upper()
            color = SEV_COLORS.get(sev, "#3b82f6")
            term = str(r.get("AETERM", "AE"))
            fig.add_trace(go.Scatter(
                x=[s, e], y=[term, term], mode="lines+markers",
                line=dict(color=color, width=4, dash="dot" if ongoing else "solid"),
                marker=dict(size=11, color=color, line=dict(color="#ffffff", width=2)),
                name=sev.title() or "Unknown", legendgroup=sev,
                showlegend=sev not in shown,
                hovertemplate=(f"<b>{term}</b><br>Severity: {sev}<br>Serious: {r.get('AESER', '—')}"
                               f"<br>Day {s:.0f} → {'ongoing' if ongoing else f'{e:.0f}'}<extra></extra>"),
            ))
            shown.add(sev)

        fig.add_vline(x=0, line_dash="dash", line_color="#475569",
                      annotation_text="Day 1", annotation_font_color="#334155")
        fig.update_layout(
            template="plotly_white", height=TIMELINE_H,
            margin=dict(l=10, r=10, t=10, b=10), hovermode="closest",
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(family="Inter", color="#0f172a"),
            xaxis=dict(title="Study Day", gridcolor="#e2e8f0", zeroline=False),
            yaxis=dict(gridcolor="#f1f5f9", autorange="reversed"),
            legend=dict(orientation="h", y=1.08, x=1, xanchor="right", title_text="Severity: "),
        )
        st.plotly_chart(fig, use_container_width=True)

# --- Left: Deep-dive tabs (same width as timeline) -----------------------------
with left_col:
    with st.container(border=True, height=DEEP_DIVE_H):
        section("🔬 Deep Dive")
        t_ae, t_lb, t_cm, t_mh = st.tabs(
            [f"⚠️ AE ({n_ae})", f"🧪 Labs ({lb_df['LBTEST'].nunique() if 'LBTEST' in lb_df else 0})",
             f"💊 Con-Meds ({len(cm_df)})", f"📋 Med History ({len(mh_df)})"]
        )

        with t_ae:
            if ae_df.empty:
                st.info("No adverse events recorded.")
            else:
                cols = [c for c in ["AETERM", "AEDECOD", "AESEV", "AESER", "AEREL", "AESTDY", "AEENDY", "AEOUT"]
                        if c in ae_df.columns]
                st.dataframe(ae_df[cols], use_container_width=True, hide_index=True, height=480)

        with t_lb:
            if lb_df.empty or "LBTEST" not in lb_df.columns:
                st.info("No laboratory data available.")
            else:
                test = st.selectbox("Lab parameter", sorted(lb_df["LBTEST"].dropna().unique()), key="lab_test")
                d = lb_df[lb_df["LBTEST"] == test].dropna(subset=["LBSTRESN"]).sort_values("LBDTC")
                unit = d["LBSTRESU"].iloc[0] if "LBSTRESU" in d and not d.empty else ""
                fig_lb = go.Figure(go.Scatter(
                    x=d["LBDTC"], y=d["LBSTRESN"], mode="lines+markers",
                    line=dict(color=ACCENT, width=3, shape="spline"),
                    marker=dict(size=9, color="#ffffff", line=dict(color=ACCENT, width=2.5)),
                    fill="tozeroy", fillcolor=f"{ACCENT}14",
                    hovertemplate="%{x}<br><b>%{y}</b> " + str(unit) + "<extra></extra>",
                ))
                lo = d["LBSTNRLO"].dropna().iloc[0] if "LBSTNRLO" in d and d["LBSTNRLO"].notna().any() else None
                hi = d["LBSTNRHI"].dropna().iloc[0] if "LBSTNRHI" in d and d["LBSTNRHI"].notna().any() else None
                if lo is not None and hi is not None:
                    fig_lb.add_hrect(y0=lo, y1=hi, fillcolor="#22c55e", opacity=0.08, line_width=0)
                for y, txt in ((hi, "ULN"), (lo, "LLN")):
                    if y is not None:
                        fig_lb.add_hline(y=y, line_dash="dash", line_color="#dc2626",
                                         annotation_text=txt, annotation_font_color="#dc2626")
                fig_lb.update_layout(
                    template="plotly_white", height=340, margin=dict(l=10, r=10, t=20, b=10),
                    font=dict(family="Inter", color="#0f172a"),
                    yaxis_title=f"{test} ({unit})", xaxis_title="Date",
                    xaxis=dict(gridcolor="#e2e8f0"), yaxis=dict(gridcolor="#e2e8f0"),
                )
                st.plotly_chart(fig_lb, use_container_width=True)
                with st.expander("All lab results (pivot)"):
                    try:
                        st.dataframe(lb_df.pivot_table(index="LBTEST", columns="LBDTC", values="LBSTRESN",
                                                       aggfunc="first"), use_container_width=True)
                    except Exception:
                        st.dataframe(lb_df, use_container_width=True, hide_index=True)

        with t_cm:
            if cm_df.empty:
                st.info("No concomitant medications recorded.")
            else:
                cols = [c for c in ["CMTRT", "CMDECOD", "CMINDC", "CMDOSE", "CMDOSU", "CMROUTE", "CMSTDTC", "CMENDTC"]
                        if c in cm_df.columns]
                st.dataframe(cm_df[cols], use_container_width=True, hide_index=True, height=480)

        with t_mh:
            if mh_df.empty:
                st.info("No medical history recorded.")
            else:
                cols = [c for c in ["MHTERM", "MHDECOD", "MHBODSYS", "MHSTDTC", "MHENDTC"] if c in mh_df.columns]
                st.dataframe(mh_df[cols], use_container_width=True, hide_index=True, height=480)

# --- Right: AI agent, stretched alongside timeline + deep dive ----------------
with right_col:
    with st.container(border=True, height=AGENT_H):
        section("🤖 Medical Reviewer AI Agent")
        st.markdown(
            f"<div class='agent-head'>Ask questions across the <b>entire trial database</b>. "
            f"Current subject: <b>{subject}</b></div>",
            unsafe_allow_html=True,
        )

        if "messages" not in st.session_state:
            st.session_state.messages = []

        chat_box = st.container(height=AGENT_H - 230, border=False)
        with chat_box:
            if not st.session_state.messages:
                st.caption("💡 Try: *“How many subjects are in each ARM?”* or "
                           f"*“List severe AEs for {subject}”*")
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        if prompt := st.chat_input("Ask the reviewer agent…", key="agent_input"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Generating SQL with Nemotron…"):
                        reply = query_agent(prompt, llm=get_agent_llm(), schema=get_schema())
                    st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
