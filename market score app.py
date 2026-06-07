import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
from datetime import date
import json

# ── PAGE CONFIG ──
st.set_page_config(
    page_title="MARKET REGIME",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ──
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
  
  .main { background: #0a0c0f; }
  
  .metric-card {
    background: #111318;
    border: 1px solid #1f2535;
    border-radius: 4px;
    padding: 16px 20px;
    margin: 4px 0;
  }
  .score-big {
    font-family: 'Space Mono', monospace;
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    text-align: center;
    margin: 0;
  }
  .regime-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.2em;
    text-align: center;
    color: #5a6275;
    margin-bottom: 4px;
  }
  .regime-name {
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 8px;
  }
  .regime-desc {
    font-size: 13px;
    color: #8b92a8;
    text-align: center;
    line-height: 1.6;
  }
  .ind-row {
    background: #111318;
    border: 1px solid #1f2535;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 6px 0;
  }
  .ind-name {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    color: #e8eaf0;
  }
  .ind-ticker { color: #00e5a0; }
  .ind-desc { font-size: 11px; color: #5a6275; margin-top: 2px; }
  .section-title {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #00e5a0;
    border-bottom: 1px solid #1f2535;
    padding-bottom: 8px;
    margin: 20px 0 12px 0;
  }
  .hist-chip-up   { background: rgba(0,229,160,0.12); color: #00e5a0; border: 1px solid rgba(0,229,160,0.4); border-radius: 3px; padding: 2px 8px; font-family: monospace; font-size: 12px; font-weight: 700; margin-right: 4px; }
  .hist-chip-down { background: rgba(255,77,106,0.12); color: #ff4d6a; border: 1px solid rgba(255,77,106,0.4); border-radius: 3px; padding: 2px 8px; font-family: monospace; font-size: 12px; font-weight: 700; margin-right: 4px; }
  .hist-chip-flat { background: rgba(90,98,117,0.15); color: #8b92a8; border: 1px solid #1f2535; border-radius: 3px; padding: 2px 8px; font-family: monospace; font-size: 12px; font-weight: 700; margin-right: 4px; }
  .stButton > button {
    background: #00e5a0 !important;
    color: #0a0c0f !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    border: none !important;
    width: 100%;
  }
</style>
""", unsafe_allow_html=True)

# ── SUPABASE ──
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

@st.cache_resource
def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb = get_client()

# ── INDICATORS ──
INDICATORS = [
    {"key": "dxy",    "name": "ドル指数",           "ticker": "DXY",     "desc": "ドル高は米株に逆風",          "good": "down"},
    {"key": "tlt",    "name": "米長期国債ETF",       "ticker": "TLT",     "desc": "TLT↑=金利低下=株に追い風",   "good": "up"},
    {"key": "hyg",    "name": "ハイイールド債ETF",   "ticker": "HYG",     "desc": "リスクオン=株と順相関",       "good": "up"},
    {"key": "baa",    "name": "クレジットスプレッド","ticker": "BAA-AAA", "desc": "拡大=信用不安=逆風",          "good": "down"},
    {"key": "curve",  "name": "長短金利差",           "ticker": "10Y-2Y",  "desc": "スティープ化=景気期待",       "good": "up"},
    {"key": "screen", "name": "スクリーニング数",     "ticker": "前週比",  "desc": "増加=物色拡大=ポジティブ",   "good": "up"},
]

DIR_LABELS = {"up": "↑", "flat": "→", "down": "↓"}

def calc_score(dirs):
    n = len(INDICATORS)
    total = 0
    for ind in INDICATORS:
        d = dirs.get(ind["key"], "flat")
        if d == "flat":
            continue
        total += 1 if d == ind["good"] else -1
    return round((total + n) / (2 * n) * 100)

def get_regime(score):
    if score >= 80: return {"name": "RISK-ON",      "color": "#00e5a0", "desc": "強い追い風。積極的にポジションを取れる環境。"}
    if score >= 60: return {"name": "CONSTRUCTIVE", "color": "#7ee0b0", "desc": "やや良好。リスクは取れるが逆風の指標にも注意。"}
    if score >= 40: return {"name": "NEUTRAL",      "color": "#f5c842", "desc": "方向感に乏しい。サイズを抑えてシグナル待ち。"}
    if score >= 20: return {"name": "CAUTIOUS",     "color": "#ff9a4d", "desc": "やや逆風。守りを優先し縮小を検討。"}
    return              {"name": "RISK-OFF",     "color": "#ff4d6a", "desc": "強い逆風。現金比率を高め防御的に。"}

# ── AUTH ──
def login_screen():
    st.markdown("## 🔐 ログイン")
    email = st.text_input("メールアドレス", key="email")
    password = st.text_input("パスワード", type="password", key="password")
    if st.button("ログイン →"):
        try:
            res = sb.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = res.user
            st.session_state["session"] = res.session
            st.rerun()
        except Exception as e:
            st.error("メールアドレスまたはパスワードが違います")

# ── LOAD / SAVE ──
def load_history():
    try:
        res = sb.auth.set_session(
            st.session_state["session"].access_token,
            st.session_state["session"].refresh_token
        )
        data = sb.table("market_scores")\
            .select("*")\
            .order("date", desc=True)\
            .execute()
        return data.data or []
    except:
        return []

def save_score(dirs, score, note):
    try:
        sb.auth.set_session(
            st.session_state["session"].access_token,
            st.session_state["session"].refresh_token
        )
        today = str(date.today())
        sb.table("market_scores").upsert({
            "date": today,
            "score": score,
            "dirs": dirs,
            "note": note,
        }, on_conflict="user_id,date").execute()
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

def delete_score(row_id):
    try:
        sb.auth.set_session(
            st.session_state["session"].access_token,
            st.session_state["session"].refresh_token
        )
        sb.table("market_scores").delete().eq("id", row_id).execute()
        return True
    except:
        return False

# ── MAIN APP ──
def main_app():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""<div style='font-family:Space Mono,monospace;font-size:13px;font-weight:700;letter-spacing:0.2em;color:#00e5a0'>
            MARKET<span style='color:#5a6275'>/</span>REGIME</div>""", unsafe_allow_html=True)
    with col2:
        if st.button("ログアウト", key="logout"):
            sb.auth.sign_out()
            del st.session_state["user"]
            del st.session_state["session"]
            st.rerun()

    tab1, tab2 = st.tabs(["📝 スコア入力", "📈 履歴"])

    # ── TAB 1: INPUT ──
    with tab1:
        # Initialize dirs in session state
        if "dirs" not in st.session_state:
            st.session_state["dirs"] = {ind["key"]: "flat" for ind in INDICATORS}

        dirs = st.session_state["dirs"]
        score = calc_score(dirs)
        regime = get_regime(score)

        # Score gauge
        st.markdown(f"""
        <div style='background:#111318;border:1px solid #1f2535;border-radius:4px;padding:28px 20px;text-align:center;margin-bottom:16px'>
          <div class='regime-label'>CURRENT REGIME</div>
          <div class='score-big' style='color:{regime["color"]}'>{score}</div>
          <div style='font-family:monospace;font-size:11px;color:#5a6275;margin:4px 0'>/ 100</div>
          <div class='regime-name' style='color:{regime["color"]}'>{regime["name"]}</div>
          <div class='regime-desc'>{regime["desc"]}</div>
        </div>
        """, unsafe_allow_html=True)

        # Indicators
        st.markdown('<div class="section-title">指標評価 — 直近の方向性</div>', unsafe_allow_html=True)

        for ind in INDICATORS:
            good_arrow = "↑が追い風" if ind["good"] == "up" else "↓が追い風"
            contrib = dirs.get(ind["key"], "flat")
            contrib_str = "+1" if contrib == ind["good"] and contrib != "flat" else ("−1" if contrib != "flat" else "0")

            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(f"""<div style='padding:8px 0'>
                  <span style='font-family:monospace;font-size:13px;font-weight:700;color:#e8eaf0'>{ind["name"]}</span>
                  <span style='font-family:monospace;font-size:11px;color:#00e5a0;margin-left:6px'>{ind["ticker"]}</span><br>
                  <span style='font-size:11px;color:#5a6275'>{ind["desc"]} · <span style="color:#00e5a0">{good_arrow}</span></span>
                </div>""", unsafe_allow_html=True)
            with c2:
                direction = st.radio(
                    label=ind["key"],
                    options=["↑", "→", "↓"],
                    index=["↑", "→", "↓"].index(DIR_LABELS[dirs.get(ind["key"], "flat")]),
                    horizontal=True,
                    key=f"radio_{ind['key']}",
                    label_visibility="collapsed"
                )
                # Map back to key
                dir_map = {"↑": "up", "→": "flat", "↓": "down"}
                st.session_state["dirs"][ind["key"]] = dir_map[direction]
            with c3:
                color = "#00e5a0" if contrib_str == "+1" else ("#ff4d6a" if contrib_str == "−1" else "#5a6275")
                st.markdown(f"<div style='text-align:center;font-family:monospace;font-size:14px;font-weight:700;color:{color};padding-top:10px'>{contrib_str}</div>", unsafe_allow_html=True)

            st.divider()

        # Note
        st.markdown('<div class="section-title">メモ（任意）</div>', unsafe_allow_html=True)
        note = st.text_input("", placeholder="FOMC前の様子見、CPI受けてリスクオン...", key="note_input", label_visibility="collapsed")

        if st.button("この環境を記録する →", key="save_btn"):
            # Re-read dirs from session state
            final_dirs = {}
            for ind in INDICATORS:
                radio_val = st.session_state.get(f"radio_{ind['key']}", "→")
                final_dirs[ind["key"]] = {"↑": "up", "→": "flat", "↓": "down"}[radio_val]
            final_score = calc_score(final_dirs)
            if save_score(final_dirs, final_score, note):
                st.success(f"{date.today()} のスコア {final_score} を保存しました ✓")
                st.cache_data.clear()

    # ── TAB 2: HISTORY ──
    with tab2:
        history = load_history()

        if not history:
            st.info("まだ記録がありません")
        else:
            # Chart
            df = pd.DataFrame(history).sort_values("date")
            colors = [get_regime(s)["color"] for s in df["score"]]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["score"],
                mode="lines+markers",
                line=dict(color="#00e5a0", width=2),
                marker=dict(color=colors, size=8, line=dict(color="#0a0c0f", width=2)),
                fill="tozeroy",
                fillcolor="rgba(0,229,160,0.06)",
                hovertemplate="%{x}<br>Score: %{y}<extra></extra>"
            ))
            fig.add_hline(y=50, line_dash="dash", line_color="#f5c842", opacity=0.4)
            fig.update_layout(
                paper_bgcolor="#111318",
                plot_bgcolor="#111318",
                font=dict(family="Space Mono", color="#8b92a8", size=10),
                xaxis=dict(gridcolor="#1f2535", showgrid=True),
                yaxis=dict(gridcolor="#1f2535", range=[0,100], showgrid=True),
                margin=dict(l=32, r=16, t=16, b=16),
                height=220,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Weekly / Monthly win rates
            df["week"]  = pd.to_datetime(df["date"]).dt.strftime("%Y-W%V")
            df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-title">週ごとの勝率</div>', unsafe_allow_html=True)
                wk = df.groupby("week")["score"].agg(["mean","count"]).reset_index()
                wk.columns = ["週", "平均スコア", "件数"]
                wk["平均スコア"] = wk["平均スコア"].round(0).astype(int)
                st.dataframe(wk, hide_index=True, use_container_width=True)
            with col2:
                st.markdown('<div class="section-title">月ごとの勝率</div>', unsafe_allow_html=True)
                mo = df.groupby("month")["score"].agg(["mean","count"]).reset_index()
                mo.columns = ["月", "平均スコア", "件数"]
                mo["平均スコア"] = mo["平均スコア"].round(0).astype(int)
                st.dataframe(mo, hide_index=True, use_container_width=True)

            # History list
            st.markdown('<div class="section-title">履歴一覧</div>', unsafe_allow_html=True)
            for row in history:
                regime = get_regime(row["score"])
                dirs = row.get("dirs", {})
                chips = ""
                for ind in INDICATORS:
                    d = dirs.get(ind["key"], "flat")
                    sym = DIR_LABELS[d]
                    cls = f"hist-chip-{d}"
                    chips += f'<span class="{cls}">{ind["ticker"]} {sym}</span>'

                note_html = f'<div style="font-size:12px;color:#8b92a8;margin-top:8px;background:#0a0c0f;border:1px solid #1f2535;border-radius:3px;padding:6px 10px">{row["note"]}</div>' if row.get("note") else ""

                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"""
                    <div style='background:#111318;border:1px solid #1f2535;border-left:3px solid {regime["color"]};border-radius:4px;padding:12px 16px;margin-bottom:6px'>
                      <div style='display:flex;align-items:center;gap:12px;margin-bottom:10px'>
                        <span style='font-family:monospace;font-size:12px;color:#e8eaf0'>{row["date"]}</span>
                        <span style='font-family:monospace;font-size:20px;font-weight:700;color:{regime["color"]}'>{row["score"]}</span>
                        <span style='font-family:monospace;font-size:9px;padding:3px 8px;border-radius:2px;background:{regime["color"]}22;color:{regime["color"]}'>{regime["name"]}</span>
                      </div>
                      <div>{chips}</div>
                      {note_html}
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("削除", key=f"del_{row['id']}"):
                        if delete_score(row["id"]):
                            st.rerun()

# ── ROUTER ──
if "user" not in st.session_state:
    login_screen()
else:
    main_app()
