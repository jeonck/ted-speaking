import streamlit as st
from streamlit_mic_recorder import mic_recorder
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai  # 최신 SDK 방식
import re

# 페이지 설정
st.set_page_config(page_title="TED 10-Step AI Trainer", layout="wide", page_icon="🎓")

# --- 1. 초기 세션 상태 설정 ---
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''
if 'last_video_url' not in st.session_state:
    st.session_state['last_video_url'] = "https://www.youtube.com/watch?v=0TI4O81gwhQ"
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- 2. 사이드바: 설정 및 퀵 메뉴 ---
with st.sidebar:
    st.title("⚙️ 설정 및 메뉴")
    
    # API 키 관리
    user_key = st.text_input("Gemini API Key", value=st.session_state['api_key'], type="password")
    if user_key:
        st.session_state['api_key'] = user_key

    st.divider()
    
    # 강연 선택 및 URL 입력 (기존 로직 유지)
    st.subheader("🎯 레전드 강연 추천")
    LEGEND_TED = {
        "직접 입력": st.session_state['last_video_url'],
        "취약성의 힘 (Brene Brown)": "https://www.youtube.com/watch?v=iCvmsMzlF7o",
        "위대한 리더의 조건 (Simon Sinek)": "https://www.youtube.com/watch?v=qp0HIF3SfI4",
        "미루기 끝판왕의 심리 (Tim Urban)": "https://www.youtube.com/watch?v=arj7oStGLkU"
    }
    selected_ted = st.selectbox("강연을 선택하세요", list(LEGEND_TED.keys()))
    if selected_ted != "직접 입력":
        st.session_state['last_video_url'] = LEGEND_TED[selected_ted]

    video_url = st.text_input("YouTube URL", value=st.session_state['last_video_url'])
    st.session_state['last_video_url'] = video_url
    video_id_match = re.search(r"v=([^&]+)", video_url)
    video_id = video_id_match.group(1) if video_id_match else None

# --- 3. 메인 화면 ---
st.title("🎓 TED 집요한 영어 공부 10단계")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📺 Video Player")
    if video_id: st.video(video_url)
    
    st.subheader("📝 1-3단계: 리스닝 노트")
    note_key = f"note_{video_id}"
    if note_key not in st.session_state: st.session_state[note_key] = ""
    st.session_state[note_key] = st.text_area("메모하세요", value=st.session_state[note_key], height=350)

with col2:
    st.subheader("🛠️ 단계별 학습 도구")
    tabs = st.tabs(["📜 스크립트", "🎙️ 섀도잉 녹음", "🤖 AI 피드백"])
    
    with tabs[2]:
        st.write("**10단계: AI 요약 교정**")
        user_summary = st.text_area("영어로 요약본을 입력하세요.", height=200)
        
        if st.button("AI 튜터에게 분석 요청"):
            if not st.session_state['api_key']:
                st.error("Gemini API Key를 입력해주세요.")
            elif not user_summary:
                st.warning("내용을 입력해주세요.")
            else:
                try:
                    # 요청하신 최신 SDK 클라이언트 생성 방식
                    client = genai.Client(api_key=st.session_state['api_key'])
                    
                    prompt = f"""
                    당신은 TED 강연 기반 영어 강사입니다. 사용자의 영어 요약문을 보고 다음을 수행하세요:
                    1. Grammar Check: 문법 오류 수정
                    2. Natural Refinement: 더 세련된 표현 제안
                    3. Vocabulary: 관련 핵심 단어 3개 추천
                    
                    사용자 입력: "{user_summary}"
                    """
                    
                    with st.spinner("Gemini가 분석 중..."):
                        # 최신 모델 'gemini-3-flash-preview"' 사용 (가장 안정적)
                        response = client.models.generate_content(
                            model="gemini-3-flash-preview", 
                            contents=prompt
                        )
                        st.markdown("---")
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"AI 분석 중 오류가 발생했습니다: {e}")
