# 🗂️ 공모전 / 대외활동 트래커

여러 활동(공모전·대외활동·과제·실험·시험)의 마감일과 진행 상태를 D-day 카드로 한눈에 관리하는 Streamlit 앱.

- **로컬 실행**: `activities.csv`에 저장 (PC에서만)
- **클라우드 배포**: 구글 시트에 저장 → 폰 포함 어디서든 접속

---

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```
또는 `실행.bat` 더블클릭. 브라우저에서 http://localhost:8501

---

## 모바일에서 쓰기 (Streamlit Cloud 배포)

### 1단계. 구글 시트 만들기
1. https://sheets.google.com 새 시트 생성, 이름 예: `activity-tracker`
2. 맨 아래 시트 탭 이름을 **`activities`** 로 변경
3. 1행에 헤더 입력: `이름  카테고리  마감일  상태  중요도  링크  메모`
4. 주소창의 시트 URL 복사해 둠

### 2단계. 서비스 계정 키 발급 (구글 클라우드)
1. https://console.cloud.google.com → 새 프로젝트 생성
2. **API 및 서비스 → 라이브러리** 에서 `Google Sheets API` 와 `Google Drive API` 둘 다 사용 설정
3. **사용자 인증 정보 → 사용자 인증 정보 만들기 → 서비스 계정** 생성
4. 만든 서비스 계정 → **키 → 키 추가 → JSON** 다운로드
5. JSON 안의 `client_email` (…iam.gserviceaccount.com) 복사
6. **1단계 구글 시트로 가서 이 이메일을 편집자로 공유**

### 3단계. GitHub에 올리기
1. https://github.com/new 에서 빈 레포 생성 (이름 `activity-tracker`, README 추가 체크 해제)
2. 이 폴더에서:
```bash
git init
git add .
git commit -m "activity tracker"
git branch -M main
git remote add origin https://github.com/<내아이디>/activity-tracker.git
git push -u origin main
```
> 처음 push 시 브라우저로 GitHub 로그인 창이 뜨면 인증하면 됩니다.
> `.gitignore` 가 `secrets.toml` 과 `activities.csv` 를 제외하므로 비밀키는 안 올라감.

### 4단계. Streamlit Cloud 배포
1. https://share.streamlit.io 에 GitHub로 로그인
2. **New app** → 위 레포 선택, main 브랜치, `app.py`
3. **Advanced settings → Secrets** 칸에 `.streamlit/secrets.toml.example` 형식대로
   2단계 JSON 값 + 1단계 시트 URL 을 채워 붙여넣기
4. Deploy → 몇 분 뒤 `https://...streamlit.app` 주소 완성. 폰 홈화면에 추가하면 앱처럼 사용.

---

## 데이터 컬럼
`이름 / 카테고리 / 마감일(YYYY-MM-DD) / 상태 / 중요도 / 링크 / 메모`
