import streamlit as st
import pandas as pd
from ssh import run_scan
import streamlit.components.v1 as components

st.set_page_config(page_title="Stock Squeeze Hunter", page_icon="📈", layout="wide")

st.markdown("""
<style>
/* --- GENEL TEMA VE YAZI TİPLERİ --- */
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; background-color: #0a0a0f; color: #e0e0e0; }
.stApp { background: #0a0a0f; }

/* --- BAŞLIK KISMI --- */
.title-block { padding: 2rem 0 0 0; margin-bottom: 0; }
.title-block h1 { font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.8rem; color: #ffffff; letter-spacing: -1px; margin: 0; }
.title-block p { font-family: 'Courier New', monospace; font-size: 0.8rem; color: #555577; margin-top: 0.3rem; }
.ssh-tag { background: #1a1a2e; border: 1px solid #2a2a4a; color: #7b7bff; padding: 0.2rem 0.6rem; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.75rem; display: inline-block; margin-bottom: 1rem; }

/* --- METRİK KARTLARI --- */
.metric-card { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 8px; padding: 1.2rem 1.5rem; text-align: center; }
.metric-card .value { font-family: 'Courier New', monospace; font-size: 2rem; font-weight: 700; color: #7b7bff; }
.metric-card .label { font-size: 0.75rem; color: #555577; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.3rem; }
.section-header { font-family: 'Courier New', monospace; font-size: 0.75rem; color: #555577; text-transform: uppercase; letter-spacing: 2px; margin: 2rem 0 0.8rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid #1e1e2e; }

/* status-bar ortalandı ve biraz üstten boşluk bırakıldı */
.status-bar { font-family: 'Space Mono', monospace; font-size: 0.75rem; color: #555577; margin-top: 1rem; text-align: center; }
.failed-tag { color: #ff5555; font-family: 'Space Mono', monospace; font-size: 0.75rem; }

/* --- YENİ NESİL BUTON TASARIMI VE RIPPLE EFEKTİ --- */
.stButton > button { 
    background: transparent !important; 
    color: #7b7bff !important; 
    border: 1px solid #7b7bff !important; 
    border-radius: 6px !important; 
    font-family: 'Courier New', monospace !important; 
    font-size: 0.85rem !important; 
    padding: 0.6rem 2rem !important; 
    width: 100% !important; 
    position: relative !important; 
    overflow: hidden !important; 
    z-index: 1 !important;
    transition: all 0.3s ease !important;
}

.stButton > button::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 150px;
    height: 150px;
    background: rgba(123, 123, 255, 0.4); 
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0); 
    opacity: 0;
    z-index: -1; 
}

.stButton > button:hover {
    color: #ffffff !important; 
    box-shadow: 0 0 15px rgba(123, 123, 255, 0.3) !important; 
}

.stButton > button:hover::after {
    animation: ripple-effect 1.2s infinite ease-out; 
}

@keyframes ripple-effect {
    0% { transform: translate(-50%, -50%) scale(0); opacity: 0.8; }
    100% { transform: translate(-50%, -50%) scale(3); opacity: 0; }
}
</style>
""", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = None
if "scan_mode" not in st.session_state:
    st.session_state.scan_mode="classic"

# 1. BAŞLIK VE ACTIVE MODE KARTINI YAN YANA KOYUYORUZ
header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown("""
    <div class="title-block">
        <div class="ssh-tag">SSH v0.1 · BIST</div>
        <h1>Stock Squeeze Hunter</h1>
        <p>Detects squeeze patterns across all BIST stocks using ADX + RSI + Bollinger/Keltner or Percentile method.</p>
    </div>
    """, unsafe_allow_html=True)

with header_right:
    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    mode_label = "BB / Keltner" if st.session_state.scan_mode == "classic" else "Percentile (25th)"
    st.markdown(f'<div class="metric-card" style="padding:0.7rem 1rem;"><div class="value" style="font-size:1rem;">{mode_label}</div><div class="label">Active Mode</div></div>', unsafe_allow_html=True)

st.markdown('<div style="border-bottom: 1px solid #1e1e2e; margin-bottom: 2rem; padding-top: 1rem;"></div>', unsafe_allow_html=True)

st.markdown('<div class="section-header">Scan Mode</div>', unsafe_allow_html=True)

# 2. BUTONLAR
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
    
    start_scan = st.button("🚀 Start Scan")


if start_scan:
    
    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(ticker, i, total):
        status_text.markdown(f'<div class="status-bar">Scanning {ticker} · {i}/{total}</div>', unsafe_allow_html=True)
        progress_bar.progress(i / total)

    now, last30, failed, total_scanned = run_scan(progress_callback=progress_callback, mode=st.session_state.scan_mode)
    st.session_state.results = (now, last30, failed, total_scanned)
    
    progress_bar.empty()
    status_text.markdown('<div class="status-bar" style="color: #7b7bff;">✓ Scan complete</div>', unsafe_allow_html=True)

# 4. SONUÇLARIN GÖSTERİLMESİ
if st.session_state.results:
    now, last30, failed, total_scanned = st.session_state.results

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
        btn_col, _ = st.columns([1, 4])
        with btn_col:
            if st.button("🌐 Open All on TradingView"):
               #window.open for all windows
                js_code = "<script>"
                for ticker in df_now["Ticker"]:
                    js_code += f"window.open('https://www.tradingview.com/chart/?symbol=BIST:{ticker}', '_blank');"
                js_code += "</script>"
                
                
                components.html(js_code, height=0)

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