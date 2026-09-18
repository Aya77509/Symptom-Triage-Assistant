"""
Streamlit UI: type symptoms in plain language, see the hybrid (rule-verified)
result next to the raw-LLM baseline, side by side, with icon-based status
badges instead of emoji.

Run with:
    streamlit run app.py
"""

import re
import textwrap

import streamlit as st

from hybrid import run_hybrid
from baseline import run_baseline
from icons import icon

st.set_page_config(page_title="Symptom Triage Assistant (Prototype)", page_icon=":material/monitor_heart:")

# ---------------------------------------------------------------------------
# Level metadata: which icon + color token each triage level renders with.
# ---------------------------------------------------------------------------
LEVEL_META = {
    "EMERGENCY": {"icon": "alert_triangle", "class": "lvl-emergency"},
    "URGENT": {"icon": "clock", "class": "lvl-urgent"},
    "ROUTINE": {"icon": "calendar_check", "class": "lvl-routine"},
    "SELF_CARE": {"icon": "home", "class": "lvl-self-care"},
}

st.markdown(
    re.sub(
        r"\n\s*\n",
        "\n",
        textwrap.dedent(
            """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@600;700&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      :root {
        --ink: #14171B;
        --ink-soft: #3D454C;
        --icon-muted: #6B7580;
        --surface: #FFFFFF;
        --border: #E4E9ED;
        --accent: #0BA0C7;
        --accent-soft: #E7F6FC;
        --mint: #E9F6F5;
        --mint-border: #AEDBD5;
        --hybrid-tint: #EAF8FC;
        --neutral-tint: #E1EBED;
        --verified-green: #3E7D5A;
        --emergency-bg: #FADADD; --emergency-fg: #973D3D; --emergency-bd: #F0C2C2;
        --urgent-bg: #FDF0DA;    --urgent-fg: #93600F;    --urgent-bd: #F3DBAA;
        --routine-bg: #E5EEFC;   --routine-fg: #2C528F;   --routine-bd: #C6D8F6;
        --selfcare-bg: #E4F5E8;  --selfcare-fg: #337048;  --selfcare-bd: #BFE5C9;
      }
      @media (prefers-color-scheme: dark) {
        :root {
          --ink: #ECEEF3; --ink-soft: #C2C8D1; --icon-muted: #98A1AC;
          --surface: #1D2129; --border: #333846;
          --accent: #55C2EE; --accent-soft: #133042;
          --mint: #123833; --mint-border: #1F5147;
          --hybrid-tint: #13303D; --neutral-tint: #262B33;
          --verified-green: #7FC79B;
          --emergency-bg: #3A2020; --emergency-fg: #F2A29C; --emergency-bd: #5A2E2C;
          --urgent-bg: #3A2E17;    --urgent-fg: #F0C888;    --urgent-bd: #59461F;
          --routine-bg: #1E2740;   --routine-fg: #A9BDF5;   --routine-bd: #2C3B63;
          --selfcare-bg: #17301F;  --selfcare-fg: #8FD6A6;  --selfcare-bd: #234A2F;
        }
      }

      html, body, [class*="css"] { font-family: 'Nunito', system-ui, sans-serif; }

      /* ---- decorative background blobs (purely cosmetic, sit behind content) ---- */
      .bg-decor { position: fixed; inset: 0; z-index: -1; overflow: hidden; pointer-events: none; }
      .bg-decor .blob {
        position: absolute; border-radius: 50%; filter: blur(2px); opacity: 0.55;
      }
      .bg-decor .b1 { width: 170px; height: 170px; left: -60px; top: 40px; background: var(--accent-soft); }
      .bg-decor .b2 { width: 140px; height: 140px; left: 10px; bottom: 60px; background: var(--neutral-tint); }
      .bg-decor .b3 { width: 190px; height: 190px; right: -70px; bottom: -40px; background: var(--mint); }
      .bg-decor .cross {
        position: absolute; right: 60px; top: 70px; width: 26px; height: 26px; opacity: 0.6;
      }
      .bg-decor .cross::before, .bg-decor .cross::after {
        content: ""; position: absolute; background: var(--accent);
      }
      .bg-decor .cross::before { width: 26px; height: 6px; top: 10px; left: 0; border-radius: 3px; }
      .bg-decor .cross::after  { width: 6px; height: 26px; top: 0; left: 10px; border-radius: 3px; }

      .app-header { display:flex; align-items:center; gap:12px; color:var(--ink); margin-bottom:2px; }
      .app-header svg { color:var(--accent); }
      .app-header h1 {
        font-family:'Quicksand', system-ui, sans-serif; font-weight:700;
        font-size:1.7rem; margin:0; letter-spacing:-0.01em;
      }
      .app-subtitle {
        font-family:'Quicksand', system-ui, sans-serif; font-weight:600;
        color: var(--ink-soft); font-size:0.95rem; margin: 0 0 10px 52px;
      }

      /* input card + button */
      div[data-testid="stForm"] {
        border: 1px solid var(--border) !important; border-radius: 18px !important;
        padding: 22px 22px 18px !important; background: var(--surface);
      }
      .stTextArea textarea {
        background: var(--mint) !important; border: 1px solid var(--mint-border) !important;
        border-radius: 12px !important; color: var(--ink) !important;
      }
      .stTextArea label p { font-family:'Nunito', system-ui, sans-serif; font-weight:700; color:var(--ink); }
      div[data-testid="stFormSubmitButton"] button {
        border-radius: 999px !important; background: var(--accent) !important;
        color: #FFFFFF !important; border: none !important; font-weight:700 !important;
        padding: 0.5rem 1.4rem !important;
      }

      .panel {
        border:1px solid var(--border); border-radius:16px; padding:18px 20px;
        height:100%;
      }
      .panel-hybrid   { background: var(--hybrid-tint); }
      .panel-baseline { background: var(--neutral-tint); }
      .panel-title {
        display:flex; align-items:center; gap:8px; font-weight:700;
        font-family:'Quicksand', system-ui, sans-serif;
        color:var(--ink); margin-bottom:12px; font-size:0.98rem;
      }
      .panel-title svg { color:var(--icon-muted); }
      .panel-title .icon-verified svg { color: var(--verified-green); }

      .level-badge {
        display:inline-flex; align-items:center; gap:8px;
        padding:6px 14px; border-radius:999px; font-weight:700;
        font-size:1rem; border:1px solid; margin-bottom:10px;
      }
      .lvl-emergency { background:var(--emergency-bg); color:var(--emergency-fg); border-color:var(--emergency-bd); }
      .lvl-urgent    { background:var(--urgent-bg);    color:var(--urgent-fg);    border-color:var(--urgent-bd); }
      .lvl-routine   { background:var(--routine-bg);   color:var(--routine-fg);   border-color:var(--routine-bd); }
      .lvl-self-care { background:var(--selfcare-bg);  color:var(--selfcare-fg);  border-color:var(--selfcare-bd); }

      .meta-line {
        display:flex; align-items:flex-start; gap:7px; color:var(--ink-soft);
        font-size:0.82rem; margin-bottom:4px; line-height:1.4;
      }
      .meta-line svg { flex-shrink:0; margin-top:2px; }
      .meta-line a { color: var(--accent); }

      .explanation { color:var(--ink); font-size:0.92rem; line-height:1.5; margin-top:12px; }

      .banner {
        display:flex; align-items:center; gap:10px; border-radius:12px;
        padding:12px 16px; font-size:0.88rem; margin-top:16px; border:1px solid;
      }
      .banner-agree    { background:var(--selfcare-bg); color:var(--selfcare-fg); border-color:var(--selfcare-bd); }
      .banner-disagree { background:var(--urgent-bg);   color:var(--urgent-fg);   border-color:var(--urgent-bd); }
    </style>
    <div class="bg-decor">
      <div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div>
      <div class="cross"></div>
    </div>
    """
        ),
    ),
    unsafe_allow_html=True,
)


def level_badge(level: str) -> str:
    meta = LEVEL_META.get(level, {"icon": "help_circle", "class": ""})
    return (
        f'<span class="level-badge {meta["class"]}">'
        f'{icon(meta["icon"], size=18)} {level}</span>'
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="app-header">{icon("pulse", size=34, stroke_width=2.2)}'
    f'<h1>Symptom Triage Assistant &mdash; Prototype</h1></div>'
    f'<div class="app-subtitle">Powered by AI &amp; Verifiable Knowledge</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Educational demo only. NOT a real diagnostic or medical tool. "
    "If this were real and you're having a medical emergency, call your local "
    "emergency number immediately."
)

with st.form("symptom_form"):
    text = st.text_area(
        ":material/edit: Describe your symptoms in your own words",
        placeholder="e.g. I'm 52 and I've had crushing chest pain for the last hour, and I feel short of breath.",
        height=120,
    )
    submitted = st.form_submit_button(":material/search: Analyze")

if submitted and text.strip():
    col1, col2 = st.columns(2)

    with st.spinner("Running hybrid pipeline (LLM extraction + rule engine)..."):
        hybrid_result = run_hybrid(text)
    with st.spinner("Running raw-LLM baseline (no rules)..."):
        baseline_level = run_baseline(text)

    with col1:
        panel = f'<div class="panel panel-hybrid">'
        panel += f'<div class="panel-title"><span class="icon-verified">{icon("shield_check")}</span> Hybrid (rules-verified)</div>'
        panel += level_badge(hybrid_result["level"])
        panel += (
            f'<div class="meta-line">{icon("list_check", size=14)} '
            f'<span><b>{hybrid_result["rule_id"]}</b> &mdash; {hybrid_result["rule_description"]}</span></div>'
        )
        if hybrid_result.get("source_url"):
            source_html = (
                f'<a href="{hybrid_result["source_url"]}" target="_blank" '
                f'rel="noopener noreferrer">{hybrid_result["source_title"]}</a>'
            )
        else:
            source_html = hybrid_result["source_title"]
        panel += (
            f'<div class="meta-line">{icon("link", size=14)} '
            f'<span>{source_html}</span></div>'
        )
        panel += f'<div class="explanation">{hybrid_result["explanation"]}</div>'
        panel += '</div>'
        st.markdown(panel, unsafe_allow_html=True)
        with st.expander("Extracted structured data"):
            st.json(hybrid_result["structured_data"])

    with col2:
        panel = f'<div class="panel panel-baseline">'
        panel += f'<div class="panel-title">{icon("help_circle")} Raw LLM (no rules)</div>'
        panel += level_badge(baseline_level)
        panel += (
            f'<div class="meta-line">{icon("list_check", size=14)} '
            f'<span>No rule, no source &mdash; this is just the model\'s direct guess.</span></div>'
        )
        panel += '</div>'
        st.markdown(panel, unsafe_allow_html=True)

    if hybrid_result["level"] != baseline_level:
        st.markdown(
            f'<div class="banner banner-disagree">{icon("alert_octagon", size=20)} '
            f'<span>The two approaches disagree: hybrid says <b>{hybrid_result["level"]}</b>, '
            f'raw LLM says <b>{baseline_level}</b>. Worth logging for your evaluation '
            f'(see compare.py).</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="banner banner-agree">{icon("check_circle", size=20)} '
            f'<span>Both approaches agree on this case.</span></div>',
            unsafe_allow_html=True,
        )

elif submitted:
    st.error("Please describe some symptoms first.")

st.divider()
st.caption(
    "This prototype demonstrates a neurosymbolic pattern: an LLM extracts structured "
    "facts from free text, a fixed rule book (not the LLM) makes the triage decision, "
    "and the LLM explains that decision in plain language."
)