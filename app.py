import html

import streamlit as st


# =========================
# 基本設定
# =========================

st.set_page_config(
    page_title="AI Translation Review Assistant",
    page_icon="🌐",
    layout="wide"
)


# =========================
# 正式問卷使用案例
# 只保留問卷 A / B / C 會用到的固定句子
# =========================

STUDY_CASE = {
    "source": "Students may rely too heavily on AI-generated translations without checking the original meaning.",
    "translation": "學生可能在沒有檢查原意的情況下，過度依賴 AI 生成的翻譯。",
    "explanation": "此處將 rely too heavily on 翻譯為「過度依賴」，因為它表示使用者可能在缺乏充分檢查或判斷的情況下直接採用 AI 結果。",
    "uncertainty": "此句中的 original meaning 可能依上下文指「原文意思」或「作者原本想表達的論點」，建議確認上下文後再採納。"
}


# =========================
# HTML 顯示元件
# =========================

def render_card(title: str, content: str, bg_color: str = "#ffffff", border_color: str = "#dddddd"):
    safe_title = html.escape(title)
    safe_content = html.escape(content).replace("\n", "<br>")

    st.markdown(
        f"""
        <div style="
            border:1px solid {border_color};
            padding:18px;
            border-radius:12px;
            background-color:{bg_color};
            font-size:17px;
            line-height:1.65;">
            <b>{safe_title}</b><br><br>
            {safe_content}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# 頁面標題與操作說明
# =========================

st.title("AI Translation Review Assistant")

st.markdown(
    """
    本介面為 HCI 期末專題問卷使用的 AI 翻譯回饋原型。  
    請依照問卷指示，從左側選擇 A、B、C 三種介面版本，閱讀畫面內容後回到問卷作答。
    """
)


# =========================
# Sidebar：只保留正式問卷需要的 A / B / C 條件
# =========================

st.sidebar.header("介面版本")

condition = st.sidebar.radio(
    "請依照問卷區段選擇版本",
    [
        "A｜只有翻譯結果",
        "B｜翻譯結果＋解釋",
        "C｜翻譯結果＋解釋＋不確定性提示"
    ]
)

st.sidebar.divider()
st.sidebar.markdown(
    """
    **操作順序建議**  
    1. 選擇 A 版，填寫問卷 A 區  
    2. 選擇 B 版，填寫問卷 B 區  
    3. 選擇 C 版，填寫問卷 C 區  
    """
)


# =========================
# 固定案例內容
# =========================

source_text = STUDY_CASE["source"]
ai_translation = STUDY_CASE["translation"]
feedback_info = {
    "explanation": STUDY_CASE["explanation"],
    "uncertainty": STUDY_CASE["uncertainty"],
}


# =========================
# 主畫面：原文與翻譯
# =========================

st.subheader("目前查看版本")
st.info(condition)

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Original Text")
    render_card("English Source", source_text, bg_color="#fafafa")

with right_col:
    st.subheader("AI Translation")
    render_card("AI Translation", ai_translation)


# =========================
# A / B / C 版本回饋區
# =========================

st.divider()
st.subheader("AI 翻譯回饋呈現")

if condition.startswith("A"):
    st.info("A 版：此版本只顯示 AI 翻譯結果，不提供翻譯解釋或不確定性提示。")

elif condition.startswith("B"):
    st.markdown("### 翻譯解釋")
    render_card(
        "Explanation",
        feedback_info["explanation"],
        bg_color="#f7fbff",
        border_color="#cfe3ff"
    )

elif condition.startswith("C"):
    st.markdown("### 翻譯解釋")
    render_card(
        "Explanation",
        feedback_info["explanation"],
        bg_color="#f7fbff",
        border_color="#cfe3ff"
    )

    st.markdown("### 不確定性提示")
    st.warning(feedback_info["uncertainty"])

    st.markdown("### 採納前確認")
    render_card(
        "Before Adoption",
        "請先確認此翻譯是否符合原文脈絡，再決定是否直接採納、修改後使用，或回頭檢查原文。",
        bg_color="#fffaf0",
        border_color="#ffd37a"
    )


# =========================
# 問卷提醒
# =========================

st.divider()
st.caption("閱讀完成後，請回到 Google 表單填寫對應區段。")
