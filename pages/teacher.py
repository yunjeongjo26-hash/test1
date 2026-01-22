import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import altair as alt

# ── 1. 페이지 설정 ──
st.set_page_config(
    page_title="서술형 평가 교사 대시보드",
    page_icon="👨‍🏫",
    layout="wide"
)

# ── 2. Supabase 연결 설정 (캐싱 사용) ──
@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
        return create_client(url, key)
    except KeyError:
        st.error("Secrets 설정이 누락되었습니다. .streamlit/secrets.toml을 확인하세요.")
        st.stop()

# ── 3. 데이터 로드 함수 ──
def load_data():
    supabase = get_supabase_client()
    try:
        # created_at 기준 내림차순 정렬 (최신순)
        response = supabase.table("student_submissions").select("*").order("created_at", desc=True).execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# ── 4. UI: 사이드바 & 제목 ──
st.title("👨‍🏫 서술형 평가 결과 대시보드")
st.markdown("학생들의 서술형 답안 제출 현황과 AI 채점 결과를 실시간으로 모니터링합니다.")

if st.button("🔄 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

# ── 5. 데이터 처리 및 대시보드 구현 ──
df = load_data()

if df.empty:
    st.info("아직 제출된 데이터가 없습니다. 학생들에게 제출을 요청하세요.")
else:
    # 날짜 포맷 변환 (ISO string -> readable)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['display_time'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 통계 요약", "📋 상세 데이터 조회", "📥 데이터 다운로드"])

    # --- Tab 1: 통계 요약 ---
    with tab1:
        # 상단 메트릭
        col1, col2, col3 = st.columns(3)
        col1.metric("총 제출 건수", f"{len(df)}건")
        col2.metric("최근 제출", df['display_time'].iloc[0])
        unique_students = df['student_id'].nunique()
        col3.metric("참여 학생 수", f"{unique_students}명")

        st.markdown("### 문항별 정답(O)/오답(X) 현황")
        
        # 정답률 계산 로직 (피드백 문자열이 'O:'로 시작하는지 확인)
        # 데이터가 문자열이 아닐 경우를 대비해 str() 처리
        results = []
        for i in range(1, 4):
            col_name = f'feedback_{i}'
            if col_name in df.columns:
                pass_count = df[col_name].apply(lambda x: str(x).strip().startswith("O")).sum()
                fail_count = len(df) - pass_count
                results.append({"문항": f"문제 {i}", "결과": "정답(O)", "학생 수": pass_count})
                results.append({"문항": f"문제 {i}", "결과": "보완필요(X)", "학생 수": fail_count})
        
        chart_df = pd.DataFrame(results)

        # Altair 차트 그리기
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X('문항:N', title=None),
            y=alt.Y('학생 수:Q'),
            color=alt.Color('결과:N', scale=alt.Scale(domain=['정답(O)', '보완필요(X)'], range=['#4caf50', '#ff5252'])),
            tooltip=['문항', '결과', '학생 수']
        ).properties(height=350)

        st.altair_chart(chart, use_container_width=True)

    # --- Tab 2: 상세 데이터 조회 ---
    with tab2:
        st.subheader("학생별 답안 및 피드백 상세")
        
        # 검색 필터
        search_id = st.text_input("학번 검색", placeholder="학번을 입력하세요 (예: 10130)")
        
        filtered_df = df
        if search_id:
            filtered_df = df[df['student_id'].str.contains(search_id)]

        # 데이터프레임 표시 (요약본)
        st.dataframe(
            filtered_df[['student_id', 'display_time', 'answer_1', 'feedback_1', 'answer_2', 'feedback_2', 'answer_3', 'feedback_3']],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.markdown("##### 🔍 개별 카드 뷰")
        
        # 개별 카드로 보기 (Expandable)
        for idx, row in filtered_df.iterrows():
            with st.expander(f"[{row['display_time']}] 학번: {row['student_id']}"):
                c1, c2, c3 = st.columns(3)
                
                # 문제 1
                with c1:
                    st.markdown("**Q1. 기체 운동과 온도**")
                    st.info(f"학생 답안:\n{row.get('answer_1', '')}")
                    fb1 = row.get('feedback_1', '')
                    if fb1.startswith("O"):
                        st.success(f"AI 피드백:\n{fb1}")
                    else:
                        st.error(f"AI 피드백:\n{fb1}")

                # 문제 2
                with c2:
                    st.markdown("**Q2. 보일 법칙**")
                    st.info(f"학생 답안:\n{row.get('answer_2', '')}")
                    fb2 = row.get('feedback_2', '')
                    if fb2.startswith("O"):
                        st.success(f"AI 피드백:\n{fb2}")
                    else:
                        st.error(f"AI 피드백:\n{fb2}")

                # 문제 3
                with c3:
                    st.markdown("**Q3. 열에너지 이동**")
                    st.info(f"학생 답안:\n{row.get('answer_3', '')}")
                    fb3 = row.get('feedback_3', '')
                    if fb3.startswith("O"):
                        st.success(f"AI 피드백:\n{fb3}")
                    else:
                        st.error(f"AI 피드백:\n{fb3}")

    # --- Tab 3: 데이터 다운로드 ---
    with tab3:
        st.subheader("데이터 내보내기")
        st.write("전체 데이터를 CSV 파일로 다운로드하여 엑셀에서 분석할 수 있습니다.")
        
        csv = df.to_csv(index=False).encode('utf-8-sig') # 엑셀 한글 깨짐 방지(utf-8-sig)
        
        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name=f"student_submissions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
