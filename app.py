import json
import re
import html

import streamlit as st
import google.generativeai as genai


# =========================
# 基本設定
# =========================

st.set_page_config(
    page_title="AI Translation Review Assistant",
    page_icon="🌐",
    layout="wide"
)


# =========================
# Gemini API 設定
# =========================

def setup_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", None)

    if not api_key:
        st.error("找不到 GEMINI_API_KEY。請確認 Streamlit Secrets 是否設定 GEMINI_API_KEY。")
        return None

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("models/gemini-2.5-flash")


model = setup_gemini()


# =========================
# 預設案例
# =========================

CASES = {
    "Students may rely too heavily on AI-generated translations without checking the original meaning.": {
        "source": "Students may rely too heavily on AI-generated translations without checking the original meaning.",
        "original_tone": "提醒與警示",
        "risk": "使用者可能在沒有確認原文意思或上下文的情況下，直接採用 AI 翻譯結果。",
        "warning": "此句中的 original meaning 可能依上下文指「原文意思」或「作者原本想表達的論點」，採納前請確認上下文。",
        "fixed_translation": "學生可能在沒有檢查原意的情況下，過度依賴 AI 生成的翻譯。"
    },
}


# =========================
# Gemini 翻譯函式
# =========================

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
- 不要加拼音
- 不要加任何前言或結語

英文句子：
{source_text}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # 如果模型仍輸出多行，只取第一個非空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            return lines[0]

        return text

    except Exception as e:
        st.error(f"Gemini 翻譯失敗：{e}")
        return ""


# =========================
# Gemini 語氣分析函式
# 自訂輸入時使用
# =========================

def clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


def analyze_tone_with_gemini(source_text: str, translation: str) -> dict:
    default_result = {
        "source_tone": "需人工判斷",
        "translation_tone": "需人工判斷",
        "risk": "此翻譯可能存在語氣或原意偏移，建議使用者自行確認。",
        "warning": "採納前請確認 AI 翻譯是否保留原文的語氣、禮貌程度與不確定性。"
    }

    if model is None:
        return default_result

    prompt = f"""
請你分析以下英文原文與繁體中文翻譯之間是否可能有語氣偏移。

請只輸出 JSON，不要解釋，不要加 markdown。

JSON 格式如下：
{{
  "source_tone": "原文語氣，用 10 字以內描述",
  "translation_tone": "譯文語氣，用 10 字以內描述",
  "risk": "可能的語氣偏移風險，用一句話描述",
  "warning": "給使用者的採納前提醒，用一句話描述"
}}

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
            "source_tone": data.get("source_tone", default_result["source_tone"]),
            "translation_tone": data.get("translation_tone", default_result["translation_tone"]),
            "risk": data.get("risk", default_result["risk"]),
            "warning": data.get("warning", default_result["warning"]),
        }

    except Exception:
        return default_result


# =========================
# Session State 初始化
# =========================

if "translation" not in st.session_state:
    st.session_state.translation = ""

if "tone_info" not in st.session_state:
    st.session_state.tone_info = None

if "current_source_key" not in st.session_state:
    st.session_state.current_source_key = ""


# =========================
# 頁面標題
# =========================

st.title("AI Translation Review Assistant")


# =========================
# Sidebar 設定
# =========================

st.sidebar.header("介面設定")

condition = st.sidebar.radio(
    "選擇介面版本",
    [
        "A｜情境A｜只有翻譯結果",
        "B｜情境B｜翻譯結果＋解釋",
        "C｜情境C｜翻譯結果＋解釋＋不確定性提示"
    ]
)

input_mode = st.sidebar.radio(
    "選擇輸入方式",
    [
        "使用預設案例",
        "自行輸入英文句子"
    ]
)


# =========================
# 決定輸入來源
# =========================

case = None
source_text = ""

if input_mode == "使用預設案例":
    selected_case_name = st.sidebar.selectbox(
        "選擇翻譯案例",
        list(CASES.keys())
    )

    case = CASES[selected_case_name]
    source_text = case["source"]
    source_key = f"preset::{selected_case_name}"

else:
    source_text = st.text_area(
        "請輸入想翻譯的英文句子：",
        value="",
        height=120,
        placeholder="例如：Could you possibly send it by Friday?"
    )

    source_key = f"custom::{source_text}"


# 如果換了輸入內容，就清空前一次翻譯
if st.session_state.current_source_key != source_key:
    st.session_state.translation = ""
    st.session_state.tone_info = None
    st.session_state.current_source_key = source_key


# =========================
# 主畫面：左右雙欄
# =========================

left_col, right_col = st.columns([1, 1])


with left_col:
    st.subheader("Original Text")

    if source_text.strip():
        safe_source_text = html.escape(source_text)

        st.markdown(
            f"""
            <div style="
                border:1px solid #ddd;
                padding:18px;
                border-radius:12px;
                background-color:#fafafa;
                font-size:18px;">
                <b>English Source:</b><br><br>
                {safe_source_text}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("請先輸入英文句子，或選擇預設案例。")

    if input_mode == "使用預設案例" and case is not None:
        st.markdown("### 原文語氣資訊")
        st.write(f"原文語氣：**{case['original_tone']}**")
        st.write(f"可能風險：{case['risk']}")


with right_col:
    st.subheader("AI Translation")

    if st.button("Translate with Gemini"):
        if not source_text.strip():
            st.warning("請先輸入英文句子。")
        else:
            with st.spinner("Gemini 翻譯中..."):
                ai_translation = translate_with_gemini(source_text)

            if input_mode == "使用預設案例" and not ai_translation:
                ai_translation = case["fixed_translation"]

            st.session_state.translation = ai_translation

            if input_mode == "自行輸入英文句子" and ai_translation:
                with st.spinner("分析語氣偏移中..."):
                    st.session_state.tone_info = analyze_tone_with_gemini(
                        source_text,
                        ai_translation
                    )

            elif input_mode == "使用預設案例" and case is not None:
                st.session_state.tone_info = {
                    "source_tone": case["original_tone"],
                    "translation_tone": "依 AI 翻譯結果判斷",
                    "risk": case["risk"],
                    "warning": case["warning"],
                }

    if st.session_state.translation:
        safe_translation = html.escape(st.session_state.translation)

        st.markdown(
            f"""
            <div style="
                border:1px solid #ddd;
                padding:18px;
                border-radius:12px;
                background-color:#ffffff;
                font-size:18px;">
                <b>AI Translation:</b><br><br>
                {safe_translation}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("請按下 Translate with Gemini。")


# =========================
# 介面提示區
# =========================

if st.session_state.translation:
    st.divider()
    st.subheader("介面提示區")

    tone_info = st.session_state.tone_info

    if condition.startswith("A"):
        st.info("A 版：此版本只顯示 AI 翻譯，不提供額外語氣提示。")

    elif condition.startswith("B"):
        st.markdown("### Tone Label")

        if tone_info:
            st.markdown(
                f"""
                - 原文語氣：**{tone_info['source_tone']}**
                - 譯文語氣：**{tone_info['translation_tone']}**
                - 可能風險：**{tone_info['risk']}**
                """
            )
        else:
            st.info("尚未產生語氣分析。")

    elif condition.startswith("C"):
        if tone_info:
            st.warning(tone_info["warning"])
        else:
            st.warning("採納前請確認 AI 翻譯是否保留原文語氣與原意。")

        st.markdown(
            """
            **採納前確認：**  
            請先確認此翻譯是否保留原文語氣，再決定是否採納或修改。
            """
        )
