import json
import re
import html

import streamlit as st
import google.generativeai as genai


st.set_page_config(
    page_title="AI Translation Review Assistant",
    page_icon="🌐",
    layout="wide"
)


def setup_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", None)

    if not api_key:
        st.warning("尚未設定 GEMINI_API_KEY。使用預設案例仍可操作；自行輸入句子需要 Gemini API。")
        return None

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("models/gemini-2.5-flash")


model = setup_gemini()


STUDY_CASE = {
    "source": "Students may rely too heavily on AI-generated translations without checking the original meaning.",
    "translation": "學生可能在沒有檢查原意的情況下，過度依賴 AI 生成的翻譯。",
    "explanation": "此處將 rely too heavily on 翻譯為「過度依賴」，因為它表示使用者可能在缺乏充分檢查或判斷的情況下直接採用 AI 結果。",
    "uncertainty": "此句中的 original meaning 可能依上下文指「原文意思」或「作者原本想表達的論點」，建議確認上下文後再採納。"
}


def translate_with_gemini(source_text: str) -> str:
    if model is None:
        return ""

    prompt = f"""
你是一個 AI 翻譯工具。

請將以下英文句子翻譯成自然的繁體中文。

限制：
- 只輸出一個最適合的繁體中文翻譯
- 不要解釋
- 不要列點
- 不要提供多個版本
- 不要加任何前言或結語

英文句子：
{source_text}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines[0] if lines else text

    except Exception as e:
        st.error(f"Gemini 翻譯失敗：{e}")
        return ""


def clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


def generate_feedback_with_gemini(source_text: str, translation: str) -> dict:
    default_result = {
        "explanation": "此翻譯看起來自然，但仍建議使用者確認關鍵詞與上下文是否符合原意。",
        "uncertainty": "此句可能存在語境差異，採納前建議回到原文確認關鍵詞、語氣與上下文。"
    }

    if model is None:
        return default_result

    prompt = f"""
請你根據英文原文與繁體中文翻譯，產生「翻譯解釋」與「不確定性提示」。

請只輸出 JSON，不要解釋，不要加 markdown。

JSON 格式如下：
{{
  "explanation": "用 1 句話說明 AI 為什麼可以這樣翻譯，需提到關鍵詞或語氣",
  "uncertainty": "用 1 句話提醒此翻譯可能需要依上下文確認的地方"
}}

要求：
- 使用繁體中文
- explanation 要幫助使用者理解翻譯依據
- uncertainty 不要說 AI 一定錯，而是提醒可能需要覆核
- 不要超過兩句話
- 不要列點

英文原文：
{source_text}

中文翻譯：
{translation}
"""

    try:
        response = model.generate_content(prompt)
        text = clean_json_text(response.text)
        data = json.loads(text)

        return {
            "explanation": data.get("explanation", default_result["explanation"]),
            "uncertainty": data.get("uncertainty", default_result["uncertainty"]),
        }

    except Exception:
        return default_result


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


if "translation" not in st.session_state:
    st.session_state.translation = STUDY_CASE["translation"]

if "feedback_info" not in st.session_state:
    st.session_state.feedback_info = {
        "explanation": STUDY_CASE["explanation"],
        "uncertainty": STUDY_CASE["uncertainty"],
    }

if "current_source_key" not in st.session_state:
    st.session_state.current_source_key = "preset"


st.title("AI Translation Review Assistant")

st.markdown(
    """
    本介面為 HCI 期末專題問卷使用的 AI 翻譯回饋原型。  
    請依照問卷指示，從左側選擇 A、B、C 三種介面版本，閱讀畫面內容後回到問卷作答。
    """
)


st.sidebar.header("介面版本")

condition = st.sidebar.radio(
    "請依照問卷區段選擇版本",
    [
        "A｜只有翻譯結果",
        "B｜翻譯結果＋解釋",
        "C｜翻譯結果＋解釋＋不確定性提示"
    ]
)

st.sidebar.header("輸入方式")

input_mode = st.sidebar.radio(
    "選擇輸入方式",
    [
        "使用預設案例",
        "自行輸入英文句子"
    ]
)


if input_mode == "使用預設案例":
    source_text = STUDY_CASE["source"]
    source_key = "preset"

    if st.session_state.current_source_key != source_key:
        st.session_state.translation = STUDY_CASE["translation"]
        st.session_state.feedback_info = {
            "explanation": STUDY_CASE["explanation"],
            "uncertainty": STUDY_CASE["uncertainty"],
        }
        st.session_state.current_source_key = source_key

else:
    source_text = st.text_area(
        "請輸入想翻譯的英文句子：",
        value="",
        height=120,
        placeholder="例如：The argument is not entirely convincing."
    )

    source_key = f"custom::{source_text}"

    if st.session_state.current_source_key != source_key:
        st.session_state.translation = ""
        st.session_state.feedback_info = None
        st.session_state.current_source_key = source_key


st.subheader("目前查看版本")
st.info(condition)

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Original Text")

    if source_text.strip():
        render_card("English Source", source_text, bg_color="#fafafa")
    else:
        st.info("請先輸入英文句子。")

with right_col:
    st.subheader("AI Translation")

    if input_mode == "自行輸入英文句子":
        if st.button("Translate"):
            if not source_text.strip():
                st.warning("請先輸入英文句子。")
            else:
                with st.spinner("Gemini 翻譯中..."):
                    translation = translate_with_gemini(source_text)

                if translation:
                    with st.spinner("產生翻譯解釋與不確定性提示中..."):
                        feedback_info = generate_feedback_with_gemini(source_text, translation)

                    st.session_state.translation = translation
                    st.session_state.feedback_info = feedback_info

    if st.session_state.translation:
        render_card("AI Translation", st.session_state.translation)
    else:
        st.info("請按下 Translate。")


if st.session_state.translation:
    st.divider()
    st.subheader("AI 翻譯回饋呈現")

    feedback_info = st.session_state.feedback_info or {
        "explanation": "此翻譯看起來自然，但仍建議使用者確認關鍵詞與上下文是否符合原意。",
        "uncertainty": "此句可能存在語境差異，採納前建議回到原文確認關鍵詞、語氣與上下文。"
    }

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


st.divider()
st.caption("閱讀完成後，請回到 Google 表單填寫對應區段。")
