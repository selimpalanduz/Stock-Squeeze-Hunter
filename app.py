import streamlit as st
import pandas as pd
from ssh import run_scan

st.set_page_config(page_title="Stock Squeeze Hunter", page_icon="📈", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; background-color: #0a0a0f; color: #e0e0e0; }
.stApp { background: #0a0a0f; }
.title-block { padding: 2rem 0 1rem 0; border-bottom: 1px solid #1e1e2e; margin-bottom: 2rem; }
.title-block h1 { font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.8rem; color: #ffffff; letter-spacing: -1px; margin: 0; }
.title-block p { font-family: 'Courier New', monospace; font-size: 0.8rem; color: #555577; margin-top: 0.3rem; }
.ssh-tag { background: #1a1a2e; border: 1px solid #2a2a4a; color: #7b7bff; padding: 0.2rem 0.6rem; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.75rem; display: inline-block; margin-bottom: 1rem; }
.metric-card { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 8px; padding: 1.2rem 1.5rem; text-align: center; }
.metric-card .value { font-family: 'Courier New', monospace; font-size: 2rem; font-weight: 700; color: #7b7bff; }
.metric-card .label { font-size: 0.75rem; color: #555577; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.3rem; }
.section-header { font-family: 'Courier New', monospace; font-size: 0.75rem; color: #555577; text-transform: uppercase; letter-spacing: 2px; margin: 2rem 0 0.8rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid #1e1e2e; }
.stButton > button { background: #7b7bff !important; color: #ffffff !important; border: none !important; border-radius: 6px !important; font-family: 'Courier New', monospace !important; font-size: 0.85rem !important; padding: 0.6rem 2rem !important; width: 100% !important; }
.stButton > button:hover { background: #5a5aee !important; }
.status-bar { font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #555577; margin-top: 0.5rem; }
.failed-tag { color: #ff5555; font-family: 'Space Mono', monospace; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
    <div class="ssh-tag">SSH v1.1 · BIST</div>
    <h1>Stock Squeeze Hunter</h1>
    <p>Detects squeeze patterns across all BIST stocks using ADX + RSI + Bollinger/Keltner or Percentile method.</p>
</div>
""", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = None
if "scan_mode" not in st.session_state:
    st.session_state.scan_mode="classic"

st.markdown('<div class="section-header">Scan Mode</div>', unsafe_allow_html=True)
b1, b2, b3 = st.columns([1, 1, 1])
with b1:
    if st.button("⚡ Classic — BB / Keltner"):
        st.session_state.scan_mode = "classic"
        st.session_state.results = None
        st.rerun()
with b2:
    if st.button("🎯 Percentile — Price Range"):
        st.session_state.scan_mode = "percentile"
        st.session_state.results = None
        st.rerun()
with b3:
    mode_label = "BB / Keltner" if st.session_state.scan_mode == "classic" else "Percentile (25th)"
    st.markdown(f'<div class="metric-card" style="padding:0.7rem 1rem;"><div class="value" style="font-size:1rem;">{mode_label}</div><div class="label">Active Mode</div></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🎯 Start Scan"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_callback(ticker, i, total):
            status_text.markdown(f'<div class="status-bar">Scanning {ticker} · {i}/{total}</div>', unsafe_allow_html=True)
            progress_bar.progress(i / total)

        now, last30, failed,total_scanned = run_scan(progress_callback=progress_callback,mode=st.session_state.scan_mode)
        st.session_state.results = (now, last30, failed,total_scanned)
        progress_bar.empty()
        status_text.markdown('<div class="status-bar">✓ Scan complete</div>', unsafe_allow_html=True)

if st.session_state.results:
    now, last30, failed,total_scanned= st.session_state.results

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="value">{len(now)}</div><div class="label">Squeeze Now</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="value">{len(last30)}</div><div class="label">Last 30 Days</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="value">{total_scanned}</div><div class="label">Scanned</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="value">{len(failed)}</div><div class="label">Failed</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">⚡ Squeeze Now</div>', unsafe_allow_html=True)
    if now:
        df_now = pd.DataFrame(now).sort_values("30d Squeeze Days", ascending=False)
        df_now["Chart"] = df_now["Ticker"].apply(lambda t: f"https://www.tradingview.com/chart/?symbol=BIST:{t}")
        st.dataframe(df_now, use_container_width=True, hide_index=True,
                     column_config={"Chart": st.column_config.LinkColumn("Chart", display_text="📈 Open")})
    else:
        st.markdown('<div class="status-bar">No stocks in squeeze right now.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">📅 Squeezed in Last 30 Days</div>', unsafe_allow_html=True)
    if last30:
        df_last30 = pd.DataFrame(last30).sort_values("30d Squeeze Days", ascending=False)
        df_last30["Chart"] = df_last30["Ticker"].apply(lambda t: f"https://www.tradingview.com/chart/?symbol=BIST:{t}")
        st.dataframe(df_last30, use_container_width=True, hide_index=True,
                     column_config={"Chart": st.column_config.LinkColumn("Chart", display_text="📈 Open")})
    else:
        st.markdown('<div class="status-bar">No stocks squeezed in last 30 days.</div>', unsafe_allow_html=True)

    if failed:
        with st.expander(f"⚠️ {len(failed)} tickers failed"):
            st.markdown(f'<div class="failed-tag">{", ".join(failed)}</div>', unsafe_allow_html=True)