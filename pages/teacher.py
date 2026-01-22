"""
교사용 대시보드 - teacher.py
─────────────────────────────────────────────────────────────────
• student_submissions 테이블 실시간 모니터링 (Supabase 연동)
• "새로고침" 버튼 → 최신 데이터 즉시 갱신
• 학번(부분) 검색, 날짜 범위 필터, CSV 다운로드 제공
• 실행 방법: 터미널에서 `streamlit run teacher.py`
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# [필수] Supabase 라이브러리 임포트
try:
    from supabase import create_client, Client
except ImportError:
    st.error("supabase 라이브러리가 없습니다. 터미널에 `pip install supabase`를 입력하세요.")
    st.stop()

# UI 레이아웃
st.set_page_config(page_title="교사용 대시보드", layout="wide") 

# [추가] 간단한 비밀번호 보호 기능
password = st.sidebar.text_input("교사 인증 암호", type="password")
if password != "1234":  # 원하는 비밀번호로 변경하세요
    st.warning("선생님만 접근할 수 있습니다.")
    st.stop()  # 암호가 틀리면 여기서 코드 실행 중단

# ─────────────────────────────────────────────
# 1. DB 클라이언트 연결 (exam3.py와 동일)
# ─────────────────────────────────────────────
@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        # 대시보드는 모든 데이터를 봐야 하므로 Service Role Key 사용 권장
        # (없으면 일반 키 사용하되 RLS 정책 확인 필요)
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"] 
        return create_client(url, key)
    except KeyError:
        st.error("Secrets 설정 오류: .streamlit/secrets.toml 파일을 확인하세요.")
        st.stop()

# ─────────────────────────────────────────────
# 2. 데이터 로드 (Supabase Query Chain 사용)
# ─────────────────────────────────────────────
# ttl=0 or None: 캐시를 짧게 두거나, 새로고침 버튼으로 clear_cache를 호출하는 전략 사용
@st.cache_data(show_spinner=False) 
def fetch_data(search_id, days):
    supabase = init_connection()
    
    # 2-1. 기본 쿼리: 모든 컬럼(*) 선택
    query = supabase.table("student_submissions").select("*")
    
    # 2-2. 학번 검색 필터 (MySQL의 LIKE %...% 와 동일)
    if search_id:
        # ilike: 대소문자 구분 없는 포함 검색
        query = query.ilike("student_id", f"%{search_id}%")
        
    # 2-3. 날짜 범위 필터 (MySQL의 >= 와 동일)
    if days > 0:
        limit_date = datetime.now() - timedelta(days=int(days))
        # Supabase는 ISO 8601 날짜 문자열 포맷을 권장
        query = query.gte("created_at", limit_date.isoformat())

    # 2-4. 정렬 및 실행 (최신순)
    # execute()를 호출해야 실제 API 요청이 전송됨
    try:
        response = query.order("created_at", desc=True).execute()
        
        # 데이터가 있으면 DataFrame으로 변환
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"데이터 조회 중 오류 발생: {e}")
        return pd.DataFrame()

# ─────────────────────────────────────────────
# 3. UI 레이아웃
# ─────────────────────────────────────────────
st.set_page_config(page_title="교사용 대시보드", layout="wide") # 넓은 화면 사용
st.title("📊 교사용 대시보드 — 서술형 평가 결과")
st.markdown("학생들의 제출 현황과 AI 피드백을 실시간으로 확인하고 엑셀로 저장하세요.")
st.markdown("---")

# --- 검색·필터 바 ---
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_input = st.text_input("🔍 학번 검색", placeholder="예: 10130 (부분 검색 가능)")

with col2:
    days_input = st.number_input("📅 조회 기간 (최근 N일)", min_value=0, max_value=365, value=30, step=1)

with col3:
    st.write("") # 버튼 줄맞춤용 공백
    st.write("") 
    if st.button("🔄 새로고침", use_container_width=True):
        # 캐시를 비워서 다시 데이터를 불러오게 함
        st.cache_data.clear()
        st.rerun()

# --- 데이터 가져오기 ---
with st.spinner("데이터를 불러오는 중입니다..."):
    df = fetch_data(search_input, days_input)

# --- 결과 표시 ---
st.write(f"### 조회 결과: 총 **{len(df)}** 건")

if df.empty:
    st.info("조건에 해당하는 제출 데이터가 없습니다.")
else:
    # 1. 보기 좋게 컬럼 순서 재배치 (원하는 순서대로)
    # 실제 존재하는 컬럼만 선택하여 표시 (에러 방지)
    desired_columns = [
        "created_at", "student_id", 
        "answer_1", "feedback_1", 
        "answer_2", "feedback_2", 
        "answer_3", "feedback_3", 
        "model"
    ]
    # 실제 DF에 있는 컬럼만 필터링 (DB 구조 변경 대비)
    display_cols = [c for c in desired_columns if c in df.columns]
    
    # 2. 데이터프레임 표시
    st.dataframe(
        df[display_cols], 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "created_at": st.column_config.DatetimeColumn("제출 일시", format="YYYY-MM-DD HH:mm"),
            "student_id": "학번",
            "answer_1": "Q1 답안",
            "feedback_1": "Q1 피드백",
            # 나머지 컬럼은 기본값 사용
        }
    )

    # 3. CSV 다운로드 버튼
    csv = df.to_csv(index=False).encode("utf-8-sig") # 엑셀 한글 깨짐 방지(utf-8-sig)
    
    # 현재 시간으로 파일명 생성
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    
    st.download_button(
        label="📥 엑셀(CSV)로 다운로드",
        data=csv,
        file_name=f"student_submissions_{current_time}.csv",
        mime="text/csv",
    )
