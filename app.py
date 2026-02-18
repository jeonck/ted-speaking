import streamlit as st
from streamlit_mic_recorder import mic_recorder
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re

# --- 1. 초기 세션 상태 설정 (로컬 스토리지 대용) ---
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''
if 'last_video_url' not in st.session_state:
    st.session_state['last_video_url'] = "https://www.youtube.com/watch?v=0TI4O81gwhQ"
if 'history' not in st.session_state:
    st.session_state['history'] = []

# 페이지 설정
st.set_page_config(page_title="TED 10-Step AI Trainer", layout="wide", page_icon="🎓")

# --- 2. 사이드바: 설정 및 퀵 메뉴 ---
with st.sidebar:
    st.title("⚙️ 설정 및 메뉴")
    
    # API 키 관리
    user_key = st.text_input("Gemini API Key", value=st.session_state['api_key'], type="password")
    if user_key:
        st.session_state['api_key'] = user_key
        genai.configure(api_key=user_key)

    st.divider()

    # 레전드 강연 추천 리스트 (퀵 액세스)
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

    # 유튜브 URL 입력
    video_url = st.text_input("YouTube URL", value=st.session_state['last_video_url'])
    st.session_state['last_video_url'] = video_url
    
    video_id_match = re.search(r"v=([^&]+)", video_url)
    video_id = video_id_match.group(1) if video_id_match else None

    if st.button("🌟 현재 영상 학습 목록에 저장"):
        if video_url not in st.session_state['history']:
            st.session_state['history'].append(video_url)
            st.success("저장 완료!")

    if st.session_state['history']:
        st.subheader("📜 학습 기록")
        h_url = st.selectbox("최근 공부한 영상", st.session_state['history'])
        if st.button("이동하기"):
            st.session_state['last_video_url'] = h_url
            st.rerun()

# --- 3. 메인 화면: 학습 대시보드 ---
st.title("🎓 TED 집요한 영어 공부 10단계")
st.info("영상을 보며 메모하고, AI 선생님에게 교정을 받으세요.")

col1, col2 = st.columns([1, 1])

# 왼쪽 칼럼: 비디오 및 메모장
with col1:
    st.subheader("📺 Video Player")
    if video_id:
        st.video(video_url)
    
    st.subheader("📝 1-3단계: 리스닝 노트")
    # 영상별 개별 노트 보관
    note_key = f"note_{video_id}"
    if note_key not in st.session_state:
        st.session_state[note_key] = ""
    
    user_note = st.text_area(
        "중심 내용과 키워드를 적으세요 (자동 저장)",
        value=st.session_state[note_key],
        height=350,
        key="note_input"
    )
    st.session_state[note_key] = user_note

# 오른쪽 칼럼: 분석 및 AI 도구
with col2:
    st.subheader("🛠️ 단계별 학습 도구")
    tabs = st.tabs(["📜 스크립트", "🎙️ 섀도잉 녹음", "🤖 AI 피드백"])
    
    with tabs[0]:
        st.write("**4-5단계: 문장 분석**")
        if video_id:
            if st.button("자막 불러오기"):
                try:
                    ts = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ko'])
                    for line in ts[:30]: # 상위 30문장만 예시로 출력
                        st.text(f"[{line['start']:.1f}s] {line['text']}")
                except:
                    st.warning("이 영상은 자동 자막을 지원하지 않거나 스크립트를 가져올 수 없습니다.")

    with tabs[1]:
        st.write("**9단계: 내 목소리 녹음**")
        audio = mic_recorder(start_prompt="🔴 녹음 시작", stop_prompt="⏹️ 녹음 중지", key='my_recorder')
        if audio:
            st.audio(audio['bytes'])
            st.caption("자신의 발음과 원어민의 발음을 비교해보세요.")

    with tabs[2]:
        st.write("**10단계: Gemini AI 요약 교정**")
        user_summary = st.text_area("영어로 작성한 요약본을 입력하세요.", height=200, placeholder="In this talk, the speaker claims that...")
        
        if st.button("AI 튜터에게 분석 요청"):
            if not st.session_state['api_key']:
                st.error("사이드바에 Gemini API Key를 입력해주세요.")
            elif not user_summary:
                st.warning("요약본을 작성해주세요.")
            else:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    당신은 TED 강연 기반 영어 강사입니다. 사용자의 영어 요약문을 보고 다음을 수행하세요:
                    1. 문법 오류 수정 (Grammar Check)
                    2. 더 세련된 원어민식 표현 제안 (Natural Refinement)
                    3. 영상 주제와 관련된 핵심 단어 3개 추천
                    
                    사용자 입력: "{user_summary}"
                    """
                    with st.spinner("AI 선생님이 확인 중..."):
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.markdown(response.text)
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

# 하단 도구
st.divider()
st.caption("도움말: 6단계 어원 공부는 [Etymonline](https://www.etymonline.com/)을 활용하는 것을 추천합니다.")
