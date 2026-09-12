import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client
from datetime import date
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape

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
  .stApp { background: #0b1220; color: #e8edf5; }
  .block-container { max-width: 780px; padding-top: 2rem; }
  [data-testid='stCaptionContainer'] { color: #b4c0d2 !important; }
  .indicator-heading { display:flex; flex-wrap:wrap; gap:12px; justify-content:space-between; font-size:16px; }
  [data-testid='stVerticalBlockBorderWrapper'] { border-radius:14px; }
  [role='radiogroup'] { display:flex; gap:8px; flex-wrap:wrap; }
  [role='radiogroup'] label { padding:10px 12px; border:1px solid #344158; border-radius:10px; min-height:44px; }
  .score-track { position:relative; height:8px; margin:24px 10px 12px; border-radius:8px; background:linear-gradient(to right,#ff4d6a 0% 20%,#ff9a4d 20% 40%,#f5c842 40% 60%,#7ee0b0 60% 80%,#00e5a0 80%); }
  .score-track span { position:absolute; width:4px; height:20px; top:-6px; background:white; transform:translateX(-50%); border-radius:4px; }
  [class^='hist-chip-'] { display:inline-block; margin-bottom:8px; }
  @media(max-width:600px) { .block-container { padding:1rem; } .score-big { font-size:52px !important; } }
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

def get_client():
    # Auth state must never be shared between browser sessions.
    if "sb_client" not in st.session_state:
        st.session_state["sb_client"] = create_client(SUPABASE_URL, SUPABASE_KEY)
    return st.session_state["sb_client"]

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

def today_jst():
    return datetime.now(ZoneInfo("Asia/Tokyo")).date()

def current_dirs():
    return {ind["key"]: {"↑": "up", "→": "flat", "↓": "down"}[
        st.session_state.get(f"radio_{ind['key']}", "→")
    ] for ind in INDICATORS}

def impact(ind, direction):
    if direction == "flat":
        return "中立 · 0", "#a7b4c9", "flat"
    if direction == ind["good"]:
        return "追い風 · +1", "#00e5a0", "up"
    return "逆風 · −1", "#ff4d6a", "down"

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
            .eq("user_id", st.session_state["user"].id)\
            .order("date", desc=True)\
            .execute()
        return data.data or []
    except Exception:
        st.error("履歴を取得できませんでした。通信状態やログイン状態を確認してください。")
        return None

def save_score(dirs, score, note):
    try:
        sb.auth.set_session(
            st.session_state["session"].access_token,
            st.session_state["session"].refresh_token
        )
        today = str(today_jst())
        sb.table("market_scores").upsert({
            "date": today,
            "user_id": st.session_state["user"].id,
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
        sb.table("market_scores").delete().eq("id", row_id).eq("user_id", st.session_state["user"].id).execute()
        return True
    except Exception:
        st.error("削除できませんでした。再度お試しください。")
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
            st.session_state.clear()
            st.rerun()

    tab1, tab2 = st.tabs(["📝 スコア入力", "📈 履歴"])
    history = load_history()

    # ── TAB 1: INPUT ──
    with tab1:
        # Initialize dirs in session state
        if "dirs" not in st.session_state:
            st.session_state["dirs"] = {ind["key"]: "flat" for ind in INDICATORS}

        # Widget state is updated before this rerun: calculate before rendering.
        dirs = current_dirs()
        score = calc_score(dirs)
        regime = get_regime(score)
        jp_name = {"RISK-ON": "強い追い風", "CONSTRUCTIVE": "やや追い風", "NEUTRAL": "中立", "CAUTIOUS": "やや逆風", "RISK-OFF": "強い逆風"}[regime["name"]]
        previous = next((r for r in (history or []) if r["date"] < str(today_jst())), None)
        delta_text = f"前回記録比 {score - previous['score']:+d} 点（{previous['date']}）" if previous else "前回記録なし"

        # Score gauge
        st.markdown(f"""
        <div style='background:#111318;border:1px solid #1f2535;border-radius:4px;padding:28px 20px;text-align:center;margin-bottom:16px'>
          <div class='regime-label'>CURRENT REGIME</div>
          <div class='score-big' style='color:{regime["color"]}'>{score}</div>
          <div style='font-family:monospace;font-size:11px;color:#5a6275;margin:4px 0'>/ 100</div>
          <div class='regime-name' style='color:{regime["color"]}'>{jp_name}</div>
          <div class='regime-desc'>{regime["name"]} · {delta_text}</div>
          <div class='score-track'><span style='left:{score}%'></span></div>
          <div class='regime-desc'>0 逆風 ⟷ 100 追い風</div>
        </div>
        """, unsafe_allow_html=True)
        counts = [sum(impact(i, dirs[i["key"]])[2] == kind for i in INDICATORS) for kind in ["up", "flat", "down"]]
        st.caption(f"追い風 {counts[0]} ｜ 中立 {counts[1]} ｜ 逆風 {counts[2]}　·　手動評価 / 日本時間")

        # Indicators
        st.markdown('<div class="section-title">指標評価 — 直近の方向性</div>', unsafe_allow_html=True)

        for ind in INDICATORS:
            good_arrow = "↑が追い風" if ind["good"] == "up" else "↓が追い風"
            contrib = dirs.get(ind["key"], "flat")
            contrib_str = "+1" if contrib == ind["good"] and contrib != "flat" else ("−1" if contrib != "flat" else "0")

            with st.container(border=True):
                label, color, _ = impact(ind, dirs[ind["key"]])
                st.markdown(f"<div class='indicator-heading'><strong>{ind['name']}</strong><span style='color:{color}'>{label}</span></div>", unsafe_allow_html=True)
                st.caption(f"{ind['ticker']} · {good_arrow}")
                st.radio(
                    label=ind["name"],
                    options=["↑", "→", "↓"],
                    index=["↑", "→", "↓"].index(DIR_LABELS[dirs.get(ind["key"], "flat")]),
                    horizontal=True,
                    key=f"radio_{ind['key']}",
                    label_visibility="collapsed"
                    , format_func=lambda value: {"↑": "↑ 上昇", "→": "→ 横ばい", "↓": "↓ 下落"}[value]
                )
                with st.expander("評価の説明"):
                    st.write(ind["desc"])

        # Note
        st.markdown('<div class="section-title">メモ（任意）</div>', unsafe_allow_html=True)
        note = st.text_input("", placeholder="FOMC前の様子見、CPI受けてリスクオン...", key="note_input", label_visibility="collapsed")

        saved = next((r for r in (history or []) if r["date"] == str(today_jst())), None)
        unchanged = saved is not None and saved.get("dirs") == dirs and saved.get("note", "") == note
        st.caption("保存済み・変更なし" if unchanged else "未保存の入力があります。同日の記録は上書きされます。")
        if st.button("本日の評価を保存 →", key="save_btn", disabled=history is None):
            # Re-read dirs from session state
            final_dirs = {}
            for ind in INDICATORS:
                radio_val = st.session_state.get(f"radio_{ind['key']}", "→")
                final_dirs[ind["key"]] = {"↑": "up", "→": "flat", "↓": "down"}[radio_val]
            final_score = calc_score(final_dirs)
            if save_score(final_dirs, final_score, note):
                st.session_state["save_notice"] = f"{today_jst()} のスコア {final_score} を保存しました ✓"
                st.rerun()
        if "save_notice" in st.session_state:
            st.success(st.session_state.pop("save_notice"))

    # ── TAB 2: HISTORY ──
    with tab2:
        if history is None:
            st.warning("履歴の読み込みに失敗しています。記録なしとは異なります。")
        elif not history:
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
            df["week"]  = pd.to_datetime(df["date"]).dt.strftime("%G-W%V")
            df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-title">週ごとの平均スコア</div>', unsafe_allow_html=True)
                wk = df.groupby("week")["score"].agg(["mean","count"]).reset_index()
                wk.columns = ["週", "平均スコア", "件数"]
                wk["平均スコア"] = wk["平均スコア"].round(0).astype(int)
                st.dataframe(wk, hide_index=True, use_container_width=True)
            with col2:
                st.markdown('<div class="section-title">月ごとの平均スコア</div>', unsafe_allow_html=True)
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
                    impact_label, _, kind = impact(ind, d)
                    cls = f"hist-chip-{kind}"
                    chips += f'<span class="{cls}">{ind["ticker"]} {sym} {impact_label}</span>'

                note_html = f'<div style="font-size:14px;color:#b9c5d8;margin-top:8px">{escape(str(row["note"]))}</div>' if row.get("note") else ""

                with st.expander(f"{row['date']} · {row['score']} 点 · {get_regime(row['score'])['name']}"):
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
                    confirm = st.checkbox("この記録を削除する", key=f"confirm_{row['id']}")
                    if st.button("削除を確定", key=f"del_{row['id']}", disabled=not confirm):
                        if delete_score(row["id"]):
                            st.rerun()

# ── ROUTER ──
if "user" not in st.session_state:
    login_screen()
else:
    main_app()
