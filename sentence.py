import streamlit as st
import random
import time
import requests
import asyncio
from googletrans import Translator
import pykakasi
import re

# ================== HELPERS ==================
def contains_kanji(text):
    return bool(re.search(r'[\u4e00-\u9faf]', text))

async def get_random_sentence():
    try:
        response = requests.get("https://random-word-api.vercel.app/api?words=1")
        word = response.json()[0] if response.status_code == 200 else "word"
    except:
        word = "word"

    translator = Translator()
    try:
        translation = await translator.translate(word, src='en', dest='ja')
        japanese_text = translation.text
    except:
        japanese_text = word

    # Kanji → Hiragana
    if contains_kanji(japanese_text):
        kakasi = pykakasi.kakasi()
        kakasi.setMode("J", "H")
        kakasi.setMode("K", "K")
        kakasi.setMode("H", "H")
        conv = kakasi.getConverter()
        kana_text = conv.do(japanese_text)
    else:
        kana_text = japanese_text

    # Kana → Romaji
    kakasi = pykakasi.kakasi()
    kakasi.setMode("J", "H")
    kakasi.setMode("H", "a")
    kakasi.setMode("K", "a")
    kakasi.setMode("r", "Hepburn")
    conv = kakasi.getConverter()
    romaji_text = conv.do(kana_text).replace(" ", "")

    return {
        "english": word,
        "japanese": japanese_text,
        "kana": kana_text,
        "romaji": romaji_text
    }

# ================== STREAMLIT UI ==================
st.set_page_config(page_title="Sentence Trainer", layout="centered")
st.markdown("""
<style>
.card {
    border: 2px solid #444;
    border-radius: 14px;
    padding: 28px;
    height: 180px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.kana-main {
    display: block;
    font-size: 48px;
    line-height: 1.2;
}

.kana-sub {
    display: block;
    font-size: 32px;
    opacity: 0.7;
    margin-top: 4px;
}

.kana-label {
    display: block;
    font-size: 20px;
    opacity: 0.6;
    margin-top: 6px;
}

input {
    autocomplete: off !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Japanese Sentence Trainer")

# ================== SESSION STATE ==================
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.total = 10
    st.session_state.current = None
    st.session_state.feedback = ""
    st.session_state.input_key = 0

# ================== START ==================
if not st.session_state.started:
    total = st.number_input("Number of Questions", 1, 50, 10)
    if st.button("Start"):
        st.session_state.started = True
        st.session_state.total = total
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.feedback = ""
        st.session_state.input_key += 1
        st.rerun()

# ================== QUIZ ==================
else:
    if st.session_state.index >= st.session_state.total:
        st.success(f"Finished! Score: {st.session_state.score}/{st.session_state.total}")
        if st.button("Restart"):
            st.session_state.started = False
            st.rerun()
    else:
        if not st.session_state.current:
            st.session_state.current = asyncio.run(get_random_sentence())

        sentence = st.session_state.current
        st.caption(f"Question {st.session_state.index + 1} / {st.session_state.total}")
        col_left, col_right = st.columns([2, 1])

        # ---------- LEFT: SENTENCE DISPLAY ----------
        with col_left:
            sub_html = ""
            # Show Hiragana under Kanji if Kanji exists
            if contains_kanji(sentence['japanese']):
                sub_html = f"<div class='kana-sub'>{sentence['kana']}</div>"

            # English word label
            label_html = f"<div class='kana-label'>{sentence['english']}</div>"

            st.markdown(
                f"""
                <div class='card'>
                    <div class='kana-main'>{sentence['japanese']}</div>
                    {sub_html}
                    {label_html}
                </div>
                """,
                unsafe_allow_html=True
            )

        # ---------- RIGHT: INPUT / FEEDBACK ----------
        with col_right:
            if not st.session_state.feedback:
                with st.form("answer_form"):
                    answer = st.text_input(
                        "Romaji",
                        key=f"answer_{st.session_state.input_key}",
                        autocomplete="off"
                    )
                    submit = st.form_submit_button("Submit")

                if submit:
                    if answer.strip().lower() == sentence['romaji']:
                        st.session_state.score += 1
                        st.session_state.feedback = "✔ Correct"
                    else:
                        st.session_state.feedback = f"✘ Correct: {sentence['romaji']}"
                    st.session_state.input_key += 1
                    st.rerun()
            else:
                st.info(st.session_state.feedback)
                time.sleep(1)
                st.session_state.index += 1
                st.session_state.current = None
                st.session_state.feedback = ""
                st.session_state.input_key += 1
                st.rerun()
