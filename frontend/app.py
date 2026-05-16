"""
app.py · 智能私厨助手 · 单页聊天界面
配色：低饱和度亮色系 —— 暖米白主色 / 燕麦侧边栏 / 陶土点缀
"""

import streamlit as st
import uuid, time, base64, sys, os

sys.path.insert(0, os.path.dirname(__file__))
from api_client import (
    vision_chat, agent_chat_stream,
    clear_agent_session, get_rag_status,
)

# ══ 页面配置 ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="智能私厨助手",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══ 全局样式 ═══════════════════════════════════════════════════════
# 配色体系（低饱和度亮色）
# ┌─────────────────────────────────────────────────────────────────
# │ 主背景     #f2ede4  暖米白    侧边栏  #e9e4da → #dfd9ce  燕麦
# │ 主色调     #8b7965  暖棕灰    点缀    #c07f62  低饱陶土橙
# │ 辅助绿     #87a88b  雾霾绿    辅助蓝  #7899ae  烟蓝
# │ 辅助黄     #c2a45e  麦秆黄   文字主  #3b3028  深暖棕
# └─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+SC:wght@300;400;500&display=swap');

/* ── CSS 变量 ─────────────────────────────────────────────────── */
:root {
    --bg:          #f2ede4;
    --bg-card:     #faf7f2;
    --bg-input:    #ffffff;
    --bg-user:     #ffffff;
    --bg-ai:       #f6f1ea;
    --sb-top:      #e9e4da;
    --sb-bot:      #dfd9ce;
    --accent:      #c07f62;
    --accent-h:    #a86a4e;
    --accent-lt:   #f0d8cc;
    --primary:     #8b7965;
    --green:       #87a88b;
    --blue:        #7899ae;
    --gold:        #c2a45e;
    --txt:         #3b3028;
    --txt-sub:     #857769;
    --txt-muted:   #b0a497;
    --border:      #d6cfc4;
    --border-lt:   #e4ddd4;
    --sh-sm:       0 1px 4px rgba(139,121,101,.09);
    --sh-md:       0 4px 18px rgba(139,121,101,.14);
    --r-sm: 8px; --r-md: 14px; --r-lg: 20px;
}

/* ── 全局 ──────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Noto Sans SC', sans-serif;
    color: var(--txt);
}
#MainMenu, footer, header { visibility: hidden; }

/* ── 主背景（带微妙纹理渐变） ─────────────────────────────────── */
.stApp {
    background-color: var(--bg);
    background-image:
        radial-gradient(ellipse at 12% 18%, #e5ddd280 0%, transparent 52%),
        radial-gradient(ellipse at 88% 82%, #dce5da80 0%, transparent 52%),
        radial-gradient(ellipse at 55% 55%, #f0e8e080 0%, transparent 60%);
}
.main .block-container {
    padding: 1.5rem 2.2rem 6rem 2.2rem;
    max-width: 860px;
}

/* ── 侧边栏 ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, var(--sb-top) 0%, var(--sb-bot) 100%);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"],
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {
    color: var(--txt) !important;
}
.sidebar-logo {
    font-family: 'Noto Serif SC', serif;
    font-size: 1.22rem;
    font-weight: 700;
    color: var(--accent) !important;
    letter-spacing: .05em;
}
[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: .75rem 0 !important;
}

/* 侧边栏按钮 */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,.55);
    border: 1px solid var(--border);
    color: var(--txt) !important;
    border-radius: var(--r-sm);
    font-size: .87rem;
    font-family: 'Noto Sans SC', sans-serif;
    box-shadow: var(--sh-sm);
    transition: all .18s ease;
    backdrop-filter: blur(4px);
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,.85);
    border-color: var(--accent);
    color: var(--accent) !important;
    transform: translateX(3px);
    box-shadow: var(--sh-md);
}
/* 侧边栏进度条 */
[data-testid="stSidebar"] [data-testid="stProgressBar"] > div {
    background: var(--green) !important;
}

/* ── 页头 ─────────────────────────────────────────────────────── */
.page-header {
    font-family: 'Noto Serif SC', serif;
    font-size: 1.68rem;
    font-weight: 700;
    color: var(--txt);
    line-height: 1.3;
    margin-bottom: .1rem;
}
.page-sub {
    font-size: .9rem;
    color: var(--txt-sub);
    margin-bottom: .5rem;
}
.page-hr {
    border: none;
    border-top: 1.5px solid var(--border-lt);
    margin: .6rem 0 .9rem;
}

/* ── 聊天气泡（亮色系）────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    border-radius: var(--r-md);
    margin-bottom: .35rem;
    border: 1px solid var(--border-lt);
}
/* 用户 */
.stChatMessage:has([aria-label*="user"]),
.stChatMessage:has([data-testid*="user"]) {
    background: #ffffff;
    box-shadow: var(--sh-sm);
    border: 1.5px solid #e8e2d8;
}
/* AI */
.stChatMessage:has([aria-label*="assistant"]),
.stChatMessage:has([data-testid*="assistant"]) {
    background: #fefcf8;
    border: 1.5px solid #ede8e0;
}

/* ── 来源徽章 ─────────────────────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 2px 11px;
    border-radius: 20px;
    font-size: .73rem;
    font-weight: 500;
    margin-top: 5px;
    letter-spacing: .02em;
}
.badge-local { background:#deeedd; color:#3b6340; border:1px solid #b8d4bc; }
.badge-web   { background:#d6e8f4; color:#2a5e7a; border:1px solid #aecde0; }
.badge-vision{ background:#f5e8cc; color:#785520; border:1px solid #ddd09a; }

/* ── 识别提示条 ───────────────────────────────────────────────── */
.rec-hint {
    font-size: .83rem;
    color: #785520;
    background: #fdf2d8;
    border: 1px solid #e8d898;
    border-left: 3px solid var(--gold);
    border-radius: var(--r-sm);
    padding: .4rem .9rem;
    margin-bottom: .55rem;
}

/* ── 欢迎卡片 ─────────────────────────────────────────────────── */
.welcome-wrap {
    display: flex;
    justify-content: center;
    margin: 1.5rem 0;
}
.welcome-card {
    background: linear-gradient(145deg, #fdfaf4 0%, #f5efe4 100%);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    padding: 2.1rem 2.6rem;
    text-align: center;
    max-width: 500px;
    width: 100%;
    box-shadow: var(--sh-md);
}
.welcome-icon { font-size: 3.6rem; margin-bottom: .5rem; line-height: 1; }
.welcome-title {
    font-family: 'Noto Serif SC', serif;
    font-size: 1.13rem;
    font-weight: 600;
    color: var(--txt);
    margin-bottom: .9rem;
}
.welcome-tips {
    font-size: .86rem;
    color: var(--txt-sub);
    line-height: 2.1;
    text-align: left;
}
.welcome-tips b { color: var(--accent); font-weight: 500; }
.welcome-tips .tip-icon { margin-right: 4px; }

/* ── 上传展开器 ───────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    box-shadow: var(--sh-sm);
    margin-bottom: .6rem;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    font-size: .87rem;
    color: var(--txt-sub);
}
[data-testid="stExpander"] summary:hover p {
    color: var(--accent);
}

/* ── 统一聊天输入容器（白色圆角框，内含上传 + 输入）─────────── */
div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) {
    background: #ffffff;
    border: 2px solid #dcd6cc;
    border-radius: var(--r-md);
    padding: 4px 10px 4px 4px;
    transition: border-color .2s ease, box-shadow .2s ease;
    margin-top: .4rem;
}
div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]):hover {
    border-color: #c9b99a;
    box-shadow: 0 0 0 4px rgba(192,127,98,.10);
}
div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]):focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 4px rgba(192,127,98,.16);
}

[data-testid="stChatInput"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
}
[data-testid="stChatInput"]:hover,
[data-testid="stChatInput"]:focus-within {
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent;
    border: none;
    border-radius: 0;
    color: var(--txt);
    font-family: 'Noto Sans SC', sans-serif;
    caret-color: var(--accent);
    caret-shape: bar;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #b8aa98;
    transition: color .2s ease;
}
[data-testid="stChatInput"]:hover textarea::placeholder {
    color: #9b8b76;
}
[data-testid="stChatInput"] button {
    color: var(--accent) !important;
    transition: transform .15s;
}
[data-testid="stChatInput"] button:hover {
    transform: scale(1.15);
}

/* ── 集成在聊天框内的上传按钮 ───────────────────────────────── */
[data-testid="stFileUploader"] {
    display: flex;
    align-items: center;
    flex-shrink: 0;
}
[data-testid="stFileUploader"] section {
    background: #f8f4ee;
    border: 1.5px solid #e4ddd4;
    border-radius: 8px;
    padding: 0;
    min-height: 40px;
    width: 42px;
    height: 42px;
    cursor: pointer;
    transition: all .2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}
[data-testid="stFileUploader"] section:hover {
    background: #fdf2e8;
    border-color: var(--accent);
}
[data-testid="stFileUploader"] button {
    font-size: 1.15rem;
    color: var(--accent);
    background: transparent;
    border: none;
    padding: 0;
}

/* ── 图片待发送提示条 ─────────────────────────────────────────── */
.img-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #fef8f4;
    border: 1px solid #e8d0be;
    border-radius: 20px;
    padding: 3px 12px 3px 6px;
    font-size: .79rem;
    color: var(--accent);
    margin-bottom: .35rem;
}


/* ── 普通按钮 ─────────────────────────────────────────────────── */
.main .stButton > button {
    font-family: 'Noto Sans SC', sans-serif;
    border-radius: var(--r-sm);
    border: 1.5px solid var(--border);
    background: var(--bg-card);
    color: var(--txt);
    box-shadow: var(--sh-sm);
    transition: all .18s ease;
}
.main .stButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
    box-shadow: var(--sh-md);
    transform: translateY(-1px);
}

/* ── 滚动条 ───────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--txt-muted); }
</style>
""", unsafe_allow_html=True)


# ══ Session State ══════════════════════════════════════════════════
def _new_sid(): return str(uuid.uuid4())[:8]

if "sessions" not in st.session_state:
    sid = _new_sid()
    st.session_state.sessions    = {sid: {"title": "新对话", "messages": []}}
    st.session_state.current_sid = sid
if "pending_img" not in st.session_state:
    st.session_state.pending_img  = None
if "pending_name" not in st.session_state:
    st.session_state.pending_name = ""
if "up_key" not in st.session_state:
    st.session_state.up_key = 0

def cur_sid():  return st.session_state.current_sid
def cur_msgs(): return st.session_state.sessions[cur_sid()]["messages"]

def push(role, content, img=None, source="", recognized=None):
    m = {"role": role, "content": content, "source": source}
    if img:       m["img_b64"]    = base64.b64encode(img).decode()
    if recognized:m["recognized"] = recognized
    cur_msgs().append(m)

def new_sess():
    s = _new_sid()
    n = len(st.session_state.sessions) + 1
    st.session_state.sessions[s]  = {"title": f"新对话 {n}", "messages": []}
    st.session_state.current_sid  = s
    st.session_state.pending_img  = None
    st.session_state.up_key += 1

def switch(sid):
    st.session_state.current_sid = sid
    st.session_state.pending_img = None
    st.session_state.up_key += 1

def remove(sid):
    clear_agent_session(sid)
    del st.session_state.sessions[sid]
    if not st.session_state.sessions: new_sess()
    else: st.session_state.current_sid = list(st.session_state.sessions.keys())[0]

def auto_name(text):
    t = text[:16] + ("…" if len(text) > 16 else "")
    st.session_state.sessions[cur_sid()]["title"] = t


# ══ 侧边栏 ═════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🍳 智能私厨助手</div>', unsafe_allow_html=True)
    st.markdown("---")

    if st.button("➕  新建对话", use_container_width=True):
        new_sess(); st.rerun()

    st.markdown(
        "<p style='font-size:.81rem;color:var(--txt-sub);margin:.3rem 0 .15rem;'>历史会话</p>",
        unsafe_allow_html=True,
    )
    for sid, info in list(st.session_state.sessions.items()):
        active = sid == cur_sid()
        c1, c2 = st.columns([5, 1])
        with c1:
            lbl = ("▸ " if active else "   ") + info["title"]
            if st.button(lbl, key=f"sw_{sid}", use_container_width=True):
                switch(sid); st.rerun()
        with c2:
            if st.button("✕", key=f"rm_{sid}", help="删除"):
                remove(sid); st.rerun()

    st.markdown("---")
    if st.button("🧹  清除当前记忆", use_container_width=True):
        ok, msg = clear_agent_session(cur_sid())
        st.toast("✅ 记忆已清除" if ok else f"❌ {msg}")

    st.markdown("---")
    ok, status, _ = get_rag_status()
    st.markdown(
        "<p style='font-size:.81rem;font-weight:500;margin-bottom:.25rem;'>📚 菜谱知识库</p>",
        unsafe_allow_html=True,
    )
    if ok:
        n = status.get("totalChunks", 0)
        st.markdown(
            f"<p style='font-size:.8rem;color:var(--txt-sub);'>已收录 <b>{n}</b> 个片段</p>",
            unsafe_allow_html=True,
        )
        st.progress(min(n / 200, 1.0))
    else:
        st.warning("⚠️ 后端未连接")

    st.markdown("---")
    st.markdown("""
<div style='font-size:.77rem;color:#857769;line-height:2.1;'>
💡 <b style='color:#8b7965;'>使用提示</b><br>
· 直接输入食材描述<br>
· 上传冰箱或食材照片<br>
· 可多轮追问调整方案<br>
· 🏠 优先本地库 · 🌐 联网兜底
</div>""", unsafe_allow_html=True)


# ══ 主区域 ═════════════════════════════════════════════════════════
st.markdown('<div class="page-header">🍳 智能私厨助手</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">描述你有什么食材，或上传照片，我来规划今天的菜单</div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="page-hr">', unsafe_allow_html=True)

msgs = cur_msgs()

# ── 欢迎空态 ──────────────────────────────────────────────────────
if not msgs:
    st.markdown("""
<div class="welcome-wrap">
<div class="welcome-card">
    <div class="welcome-icon">🥘</div>
    <div class="welcome-title">你好，我是你的私厨助手</div>
    <div class="welcome-tips">
        <span class="tip-icon">🥚</span>「我有<b>鸡蛋、西红柿、土豆</b>，推荐一道晚餐」<br>
        <span class="tip-icon">📷</span>上传冰箱照片，我<b>自动识别食材</b><br>
        <span class="tip-icon">🌶️</span>「来道简单的<b>川菜</b>，食材不要太多」<br>
        <span class="tip-icon">⏱️</span>「<b>15 分钟</b>内能做什么菜？」
    </div>
</div>
</div>""", unsafe_allow_html=True)

# ── 渲染历史 ──────────────────────────────────────────────────────
for m in msgs:
    role, content = m["role"], m["content"]
    src   = m.get("source", "")
    ava   = "🧑‍🍳" if role == "user" else "🤖"

    with st.chat_message(role, avatar=ava):
        if "img_b64" in m:
            st.image(base64.b64decode(m["img_b64"]), width=200, caption="上传的图片")
        if m.get("recognized"):
            st.markdown(
                f'<div class="rec-hint">🔍 识别到食材：{"、".join(m["recognized"])}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(content)
        if src == "rag":
            st.markdown('<span class="badge badge-local">🏠 本地菜谱库</span>', unsafe_allow_html=True)
        elif src == "web_search":
            st.markdown('<span class="badge badge-web">🌐 网络搜索</span>', unsafe_allow_html=True)
        elif src == "vision":
            st.markdown('<span class="badge badge-vision">📷 图片识别</span>', unsafe_allow_html=True)


# ── 底部输入区（上传按钮集成在聊天框内）──────────────────────────
has_img = st.session_state.pending_img is not None

# 图片待发送提示条（显示在输入框上方）
if has_img:
    c_chip, c_rmchip = st.columns([0.94, 0.06])
    with c_chip:
        st.markdown(
            f'<div class="img-chip">'
            f'📷 已选：<b>{st.session_state.pending_name}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c_rmchip:
        if st.button("✕", key="rm_img_chip", help="移除图片"):
            st.session_state.pending_img  = None
            st.session_state.pending_name = ""
            st.session_state.up_key += 1
            st.rerun()

# 集成上传按钮的聊天输入框（统一白色容器）
col_upload, col_input = st.columns([0.06, 0.94], gap="small")
with col_upload:
    f = st.file_uploader(
        "上传图片",
        type=["jpg","jpeg","png","webp"],
        key=f"up_{st.session_state.up_key}",
        label_visibility="collapsed",
    )
    if f:
        st.session_state.pending_img  = f.read()
        st.session_state.pending_name = f.name
        st.rerun()
with col_input:
    user_input = st.chat_input(
        "📷 有图直接发送，我来识别食材…"
        if has_img else
        "输入食材或问题，例：我有鸡蛋、西红柿和土豆…"
    )


# ══ 发送处理 ═══════════════════════════════════════════════════════
send = (user_input is not None and user_input.strip()) or \
       (has_img and user_input is not None)

if send:
    sid   = cur_sid()
    img   = st.session_state.pending_img
    iname = st.session_state.pending_name
    text  = (user_input or "").strip()
    disp  = text or "请识别图片中的食材并推荐合适的菜谱"

    # 1. 用户气泡
    with st.chat_message("user", avatar="🧑‍🍳"):
        if img: st.image(img, width=200, caption=iname)
        st.markdown(disp)
    push("user", disp, img=img)
    if len(cur_msgs()) == 1: auto_name(disp)

    # 清除图片
    st.session_state.pending_img  = None
    st.session_state.pending_name = ""
    st.session_state.up_key += 1

    # 2. AI 回复
    with st.chat_message("assistant", avatar="🤖"):
        ph   = st.empty()
        rep  = ""
        src  = ""
        recs = []

        if img:
            # 图片对话（非流式）
            with st.spinner("📷 正在识别图片中的食材…"):
                ok, data, err = vision_chat(
                    image_bytes=img, session_id=sid,
                    message=text, filename=iname or "upload.jpg",
                )
            if ok:
                recs = data.get("recognizedIngredients", [])
                rep  = data.get("reply", "")
                src  = data.get("recipeSource", "vision")
                if recs:
                    st.markdown(
                        f'<div class="rec-hint">🔍 识别到食材：{"、".join(recs)}</div>',
                        unsafe_allow_html=True,
                    )
                ph.markdown(rep)
            else:
                rep = f"抱歉，图片处理出错：{err}"
                ph.markdown(rep)
        else:
            # 纯文字流式
            buf = ""
            for tok in agent_chat_stream(sid, disp):
                buf += tok
                ph.markdown(buf + "▌")
                time.sleep(0.008)
            rep = buf
            ph.markdown(rep)
            src = "web_search" if "网络搜索" in rep else "rag"

        # 来源徽章
        if src == "rag":
            st.markdown('<span class="badge badge-local">🏠 本地菜谱库</span>', unsafe_allow_html=True)
        elif src == "web_search":
            st.markdown('<span class="badge badge-web">🌐 网络搜索</span>', unsafe_allow_html=True)
        elif src == "vision":
            st.markdown('<span class="badge badge-vision">📷 图片识别</span>', unsafe_allow_html=True)

    push("assistant", rep, source=src, recognized=recs or None)
    st.rerun()