🧪 AI 기반 서술형 평가 시스템 (Science Essay Assessment)

이 프로젝트는 Streamlit을 활용하여 학생들의 서술형 답안을 수집하고, OpenAI (GPT) API를 통해 실시간으로 자동 채점 및 피드백을 제공하며, 결과 데이터를 Supabase 데이터베이스에 저장하는 올인원 학습 도구입니다.

📊 시스템 흐름도 (System Flow)

사용자(학생)가 답안을 제출하고 피드백을 받는 전체 과정을 시각화했습니다.

graph TD
    User[👩‍🎓 학생] -->|1. 학번 & 답안 입력| Web[💻 Streamlit 웹 페이지]
    Web -->|2. 제출 버튼 클릭| Validation{입력 확인}
    
    Validation -- 미입력 --x Alert[경고 메시지]
    Validation -- 정상 --ok State[제출 완료 상태 전환]
    
    State -->|3. GPT 피드백 버튼 활성화| GPT_Btn[🤖 피드백 요청]
    
    GPT_Btn -->|4. 답안 전송| OpenAI[🧠 OpenAI API (GPT)]
    OpenAI -->|5. 채점 & 피드백 반환| Web
    
    Web -->|6. 결과 화면 표시| Result[📝 O/X 및 첨삭 내용]
    Result -->|7. 자동 저장| DB[(🗄️ Supabase DB)]


🛠️ 주요 기능

학생용 인터페이스: 학번 입력 및 3가지 과학 서술형 문항(기체, 보일 법칙, 열에너지) 답안 작성 폼 제공.

실시간 AI 채점: GPT 모델이 사전에 정의된 채점 기준(Grading Guidelines)에 따라 O/X 판정 및 200자 이내의 친절한 피드백 생성.

데이터베이스 연동: 채점 결과, 학생 답안, 피드백 내용을 클라우드 DB(Supabase)에 영구 저장.

오류 방지 로직: 빈칸 제출 방지, API 키 누락 확인, 피드백 형식(O:/X:) 자동 보정 기능 포함.

⚙️ 설치 및 설정 (Setup)

1. 필수 라이브러리 설치

터미널에서 아래 명령어를 실행하여 필요한 패키지를 설치합니다.

pip install streamlit openai supabase


2. Secrets 설정 (.streamlit/secrets.toml)

프로젝트 최상위 폴더에 .streamlit 폴더를 만들고 그 안에 secrets.toml 파일을 생성하여 API 키를 입력하세요.

# .streamlit/secrets.toml

# OpenAI API 설정
OPENAI_API_KEY = "sk-..."

# Supabase 설정
SUPABASE_URL = "[https://your-project.supabase.co](https://your-project.supabase.co)"
SUPABASE_SERVICE_ROLE_KEY = "eyJ..."


📂 코드 구조 설명

이 코드는 크게 **UI 구성(Step 1)**과 **백엔드 로직(Step 2)**으로 나뉩니다.

1️⃣ Step 1: UI 및 입력 폼 (Streamlit)

st.form: 학생의 오입력을 방지하기 위해 입력란과 제출 버튼을 하나의 폼으로 묶었습니다.

문항 구성:

Q1: 기체 입자의 운동

Q2: 보일 법칙

Q3: 열에너지 이동 (전도/대류/복사)

상태 관리: submitted_ok 세션 상태를 통해 제출이 완료된 후에만 AI 피드백 버튼을 누를 수 있도록 제어합니다.

2️⃣ Step 2: AI 채점 및 DB 저장

OpenAI 연동:

gpt-5-mini (또는 gpt-4o-mini) 모델을 사용하여 교사 페르소나로 채점을 진행합니다.

Prompt Engineering: 출력이 반드시 "O: ..." 또는 "X: ..." 형식이 되도록 강제합니다.

Supabase 연동:

save_to_supabase 함수가 채점 완료 직후 데이터를 student_submissions 테이블에 INSERT 합니다.

후처리 함수 (normalize_feedback):

AI의 응답이 형식을 벗어날 경우 코드가 깨지지 않도록 강제로 포맷팅하고 길이를 조절합니다.

📝 데이터베이스 테이블 구조 (예시)

Supabase에서 student_submissions 테이블을 아래와 같이 생성해야 합니다.

컬럼명

데이터 타입

설명

id

int8

Primary Key (Auto increment)

student_id

text

학번

answer_1 ~ 3

text

학생 제출 답안

feedback_1 ~ 3

text

AI 피드백 결과

model

text

사용된 AI 모델명

created_at

timestamptz

생성 시간 (Default: now())

🚀 실행 방법

터미널에서 다음 명령어를 입력하여 앱을 실행합니다.

streamlit run app.py
