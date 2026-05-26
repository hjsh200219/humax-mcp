# Humax AX 강의 계획서 v2

## 강의 철학

### 핵심 메시지

**"Claude를 1개 앱(Cowork)으로 쓰지 말고, 전체 생태계로 써서 업무를 자동화하라."**

기존 인식: Claude = 채팅창 + 파일 업로드. 실제 가치: Desktop(자연어 자동화) → Remote(무인 스케줄 실행) → IDE(Code로 풀 자동화 빌드) 3단계 진화.

**업무 자동화 정의 (본 강의 기준)**:
- ❌ "Claude에게 매번 물어봄" (= 수동 보조)
- ✅ "트리거(시간/이벤트/명령) → 결과(파일/DB/알림) 자동 실행" (= 자동화 자산)

매 회차 산출물은 위 ✅ 기준을 만족해야 함.

### 강의 출발점

| 1회차 후 인식 | 4회차 후 능력 |
|---|---|
| "Claude = Chat" | DRI 전체 활용 (Chat / Cowork / Skill / MCP / Schedule / Dispatch / Extension) |
| "코드는 개발자 영역" | VS Code + Claude 확장으로 본인이 도구 빌드 |
| "데이터는 수기 입력" | data.go.kr · SAP API · 크롤링으로 자동 수집 |
| "결과는 엑셀로 끝" | Supabase DB → Next.js → Vercel 웹 배포 |

### DRI 모델 (강의 척추)

| 단계 | 명칭 | 환경 | 학습 곡선 | 강의 회차 |
|---|---|---|---|---|
| **D** | Desktop | Claude Desktop (Chat, Cowork, Extension) | 낮음 | 1회 |
| **R** | Remote | Schedule + Dispatch (무인 실행) | 중간 | 1회 후반 + 3회 응용 |
| **I** | IDE | Claude Code (Terminal / VS Code / Desktop 내부) | 중간~높음 | 2회 본격 + 3-4회 심화 |

---

## 1회차: Claude Desktop 풀활용 — DRI 중 D + R 일부 (2h)

### 모듈 1-1: DRI 모델 소개 (15min)

**목표**: 4회 강의 전체 지도 + 본 회차 위치 명확화

**내용**:
- DRI 도식: Desktop → Remote → IDE 진화 경로
- 1회 = D 풀활용 + R 도입 / 2회 = I 본격 / 3-4회 = 응용
- 각 단계 학습 곡선·산출물·실무 효과 비교

---

### 모듈 1-2: Claude Desktop의 Chat vs Cowork (20min)

**목표**: 두 모드 차이와 사용 분기점 체득

**내용**:
- **Chat**: 단일 대화, 컨텍스트 휘발성, 빠른 질의
- **Cowork**: Projects 기반 영속 컨텍스트, 공통 자산 첨부, 결산 같은 반복 작업 적합
- 5개 에러 진단(file #1 한계란 인용) → Cowork가 해결하는 부분
- 토큰 한계 직관 (945K 셀 = 200K 컨텍스트 15-25배)

**실습**:
- "Humax 고정비 결산" Cowork Project 생성
- 공통 자산 첨부: 배부율 마스터 / CC 마스터 / 골든 템플릿 / SOP

**산출**: Cowork Project 1개

---

### 모듈 1-3: Show Me · Skill · MCP · Schedule · Dispatch · Computer Use · Live Artifact (45min)

**목표**: Claude Desktop 7대 기능 1회 시연 + 실무 매칭

| # | 기능 | 정의 | Humax 실무 매칭 |
|---|---|---|---|
| 1 | **Show Me** | Claude가 산출물을 시각화해서 보여줌 | 배부율 stacked bar chart |
| 2 | **Skill** | 슬래시 명령어(`/`)로 재사용 워크플로우 호출 | `/humax-allocation` 배부판 생성 |
| 3 | **MCP** | 외부 도구/API와 표준 프로토콜로 연결 | humax-excel-mcp (도구 10개) |
| 4 | **Schedule** | 정해진 시간에 자동 실행 (cron 유사) | 매월 1영업일 환율 갱신 |
| 5 | **Dispatch** | 외부 트리거(이메일/웹훅)로 실행 | SAP export 완료 시 자동 결산 |
| 6 | **Computer Use** | Claude가 사용자 컴퓨터 화면 직접 조작 | SAP GUI 자동 export (GUI Scripting 대체) |
| 7 | **Live Artifact** | 실시간 갱신되는 인터랙티브 산출물 | 배부율 변경 시 차트 즉시 반영 |

**실습**:
- humax-excel-mcp 등록 (MCP 1회 등록 → 7개 도구 활성)
- Skill 1개 호출 (`/get_allocation_rates` → Live Artifact)
- Schedule 1개 등록 (매월 1영업일 환율 조회)

**산출**: MCP 등록 완료 + Skill 1개 + Schedule 1개

---

### 모듈 1-4: Claude Extension (Chrome · Word · Excel · PPT) (30min)

**목표**: 일상 도구에 Claude 직접 삽입

**내용**:
- **Chrome Extension**: 웹페이지 요약 / 번역 / 데이터 추출 → DART 공시 조회 자동화
- **Word Extension**: SOP 문서 작성 + AI 교정
- **Excel Extension**: 셀 단위 AI 함수 (`=CLAUDE(...)`) → 적요 분류 셀 함수화
- **PPT Extension**: 결산 보고서 슬라이드 초안 자동 생성

**실습**:
- Chrome Extension 설치 → 한국수출입은행 환율 페이지 자동 요약
- Excel Extension으로 raw 적요 컬럼 1열 AI 분류 시연

**산출**: 4개 Extension 설치 + 각 1회 사용 경험

---

## 2회차: Claude Code 본격 도입 — DRI 중 I (2h)

### 모듈 2-1: Claude Code 실행 환경 비교 (15min)

**목표**: 3개 환경 차이와 권장 환경 결정

| 환경 | 특징 | 추천 사용처 |
|---|---|---|
| Claude Desktop 내부 | GUI 통합, 가장 친숙 | 가벼운 코드 실험 |
| Terminal | 순수 CLI, 자동화 cron 적합 | 무인 배치 |
| **VS Code + 확장** | IDE 통합, Git/디버거/터미널 한 화면 | **본 강의 주력** |

**결론**: VS Code + Claude 확장이 실무자 진입 부담 최저 + 풀 IDE 기능.

---

### 모듈 2-2: 필수 프로그램 설치 (25min)

**목표**: 개발 환경 0 → 1

**설치 목록**:
1. **Git** — 버전관리 (3회 본격 사용)
2. **Node.js** — Claude Code CLI 런타임
3. **VS Code** — 메인 IDE
4. **Claude Code CLI** — Terminal에서 `npm install -g @anthropic-ai/claude-code`
5. **VS Code Claude 확장** — Marketplace에서 설치

**실습**:
- macOS/Windows 분기 설치 가이드
- 설치 검증: `claude --version`, `git --version`, `node --version`

**산출**: 개발 환경 셋업 완료

---

### 모듈 2-3: OMC (Oh, My Claude Code) 설치 (20min)

**목표**: Claude Code 워크플로우 가속기 도입

**내용**:
- OMC = Claude Code 멀티 에이전트 오케스트레이션 레이어
- 설치: 1줄 명령
- 핵심 스킬 2개 집중:
  - **ralph** — 자가 참조 루프 (목표 달성까지 반복 수정)
  - **ralplan** — 합의 기반 계획 게이트 (모호 요청 자동 게이팅)

**실습**:
- OMC 설치 → `/oh-my-claudecode:omc-setup`
- `/ralph` 1회 시연 (간단 버그 자동 수정 루프)

**산출**: OMC 설치 + ralph/ralplan 사용 경험

---

### 모듈 2-4: PRD 개념 이해 (20min)

**목표**: 좋은 요청서 = 좋은 산출물

**내용**:
- PRD (Product Requirements Document) 구조: 목적 / 사용자 / 시나리오 / 합격 기준 / 비목표
- 나쁜 요청 ("결산 자동화해줘") vs 좋은 PRD (목표·입력·출력·검증 명시)
- Humax 실 사례: `docs/prd/mcp-design-plan.md` 구조 분석

**실습**:
- "월말 환율 자동 갱신" 작은 PRD 1개 작성

**산출**: PRD 1개 (실습용)

---

### 모듈 2-5: 멀티 모델 리뷰 — Codex · Gemini 확장 (30min)

**목표**: 단일 모델 의존 탈피, 교차 검증 도입

**내용**:
- VS Code에 Codex 확장 + Gemini 확장 설치
- ralplan 워크플로우에 3개 모델 합의 (Claude + Codex + Gemini = CCG)
- 같은 PRD에 대해 3개 모델 응답 비교 → 의견 충돌 해소 패턴

**실습**:
- 모듈 2-4 PRD를 ralplan으로 실행 → Codex/Gemini 리뷰 받기
- 의견 불일치 1개 발견 → 합의 도출

**산출**: VS Code 멀티 모델 환경 + ralplan 1회 실행

---

### 모듈 2-6: 숙제 안내 (10min)

**숙제**: 본인 부서·업무에서 자동화 후보 1개 선정 → ralplan으로 계획 → 다음 회차 발표

**가이드**:
- 너무 큰 범위 금지 (1-2시간짜리 작업 1개)
- 입력/출력 명확
- 합격 기준 측정 가능

---

## 3회차: API · 크롤링 · Git · 환경변수 · 테스트 (2h)

### 모듈 3-1: API 개념 이해 (15min)

**목표**: REST API 기본 + 인증 패턴

**내용**:
- API = 프로그램이 호출하는 함수의 인터넷 버전
- HTTP 메서드 (GET/POST), JSON 응답, 인증(API Key, OAuth) 개요
- Rate limit / 에러 코드 / 캐시 전략

---

### 모듈 3-2: data.go.kr 데이터 받아오기 (20min)

**목표**: 공공 데이터 1회 호출 완주

**내용**:
- data.go.kr 회원가입 → 활용신청 → API Key 발급
- Claude Code에게 "이 데이터 받아와줘" 자연어 요청 → Python `requests` 코드 자동 생성
- 응답 파싱 → CSV 저장

**실습**:
- 한국수출입은행 환율 API (강의 자산 humax-excel-mcp 내부 코드 참조)
- 본인 부서 관련 공공 데이터 1개 호출

**산출**: 공공 데이터 1회 호출 스크립트

---

### 모듈 3-3: SAP API 연결 (20min)

**목표**: 사내 핵심 시스템 연결 진입

**내용**:
- SAP 접근 4계층 비교:
  - L1: SAP GUI Scripting (Basis 권한 불필요, Computer Use로 대체 가능)
  - L2: OData / RFC (Basis 권한 필요)
  - L3: ABAP 배치
  - L4: BTP / Joule (사내 LLM)
- Humax 현재 단계 = L1 (Basis 협의 후 L2 점진)
- FBL3N 자동 export 시연

**실습**:
- SAP GUI Script 1개 (Claude Code 코드 생성)
- 결과 CSV → 01.Source 폴더 자동 적재

**산출**: SAP export 자동화 1개

---

### 모듈 3-4: 크롬 개발자 도구로 크롤링 (15min)

**목표**: API 없는 사이트도 데이터 추출

**내용**:
- 크롬 개발자 도구 (F12) → Network 탭 → API 호출 가로채기
- Elements 탭 → 셀렉터 추출
- Claude Code에 "이 사이트 크롤링" + 셀렉터 전달 → BeautifulSoup/Playwright 코드 생성
- robots.txt / 약관 준수 안내

**실습**:
- 경쟁사 IR 페이지 / DART 공시 1건 크롤링

**산출**: 크롤링 스크립트 1개

---

### 모듈 3-5: Git 개념 + GitHub 사용법 (20min)

**목표**: 버전관리 + 협업 진입

**내용**:
- Git 핵심 5개 명령: `clone` / `add` / `commit` / `push` / `pull`
- GitHub Private repo 생성 → VS Code 연결
- 매월 산출물 commit → 변경 추적 (file diff 시연)
- `.gitignore` 패턴 (사내 데이터 차단)

**실습**:
- GitHub Private repo 1개 생성
- humax-excel-mcp clone → 첫 commit/push
- `.gitignore`에 raw 파일 패턴 추가

**산출**: GitHub repo 1개 + 첫 commit

---

### 모듈 3-6: 환경변수 관리 (15min)

**목표**: API 키 안전 보관

**내용**:
- `.env` 파일 패턴 (`EXCHANGE_RATE_API_KEY=...`)
- `.gitignore`에 `.env` 강제
- python-dotenv 로딩
- 키 노출 시나리오 + 폐기 절차
- 사내 데이터 git push 금지 (humax-mcp `.gitignore` + 정규식 스캔 2중 차단 패턴 인용)

**실습**:
- `.env` 생성 + API 키 이동
- 코드에서 `os.getenv()` 호출
- `git status`로 `.env` 추적 안 됨 확인

**산출**: `.env` 셋업 + 키 안전 보관

---

### 모듈 3-7: 테스트 + 로그 분석 (15min)

**목표**: "동작하는 것 같다" → "동작한다" 증명

**내용**:
- pytest 기본 (assert / fixture)
- 실패 테스트 작성 → Green → Refactor (TDD)
- Claude Desktop 로그 파일 위치:
  - macOS: `~/Library/Logs/Claude/`
  - Windows: `%APPDATA%\Claude\logs\`
- MCP 호출 실패 시 로그 추적 패턴

**실습**:
- 모듈 3-2 환율 호출 코드에 pytest 추가
- 의도적 에러 주입 → 로그에서 원인 추적

**산출**: 테스트 1개 + 로그 분석 1회

---

## 4회차: SQL · DB · Next.js · 웹 배포 (2h)

### 모듈 4-1: SQL 소개 (20min)

**목표**: Excel을 넘어 DB 사고로

**내용**:
- SQL = 데이터 질의 표준 언어
- 핵심 4개: `SELECT` / `INSERT` / `UPDATE` / `DELETE`
- JOIN 1개 시연 (raw + CC 마스터 합치기)
- Claude Code에 자연어 → SQL 변환 요청 패턴

**실습**:
- SQLite 로컬 DB에 CC 마스터 적재
- "본사 인건비 합계" SQL 1개 작성

---

### 모듈 4-2: Supabase DB 연결 (25min)

**목표**: 클라우드 DB로 다중 사용자 공유

**내용**:
- Supabase = PostgreSQL 기반 BaaS (회원가입 1분)
- 테이블 생성 (배부율 / CC 마스터 / 결산 결과)
- API Key 발급 → `.env` 보관
- Python `supabase-py` 클라이언트
- 권한 (RLS, Row Level Security) 기본

**실습**:
- Supabase 프로젝트 1개 생성
- humax-excel-mcp 결산 결과를 Supabase에 INSERT
- Supabase 대시보드에서 데이터 조회

**산출**: Supabase 프로젝트 + 테이블 3개 + 데이터 1건

---

### 모듈 4-3: TypeScript · Next.js 소개 (25min)

**목표**: 웹 화면 만들기 진입

**내용**:
- **TypeScript** = JavaScript + 타입 안전성 (Python의 type hint 유사)
- **Next.js** = React 기반 풀스택 웹 프레임워크
- 프로젝트 생성: `npx create-next-app@latest`
- 페이지 구조 (`app/page.tsx`) 기본
- Supabase 클라이언트로 데이터 fetch + 화면 렌더링
- Claude Code에 "이 데이터 표로 보여주는 페이지" 자연어 요청

**실습**:
- Next.js 프로젝트 생성
- 모듈 4-2 Supabase 데이터를 표로 표시하는 페이지 1개

**산출**: Next.js 페이지 1개 (로컬 실행)

---

### 모듈 4-4: Vercel 웹 배포 + GitHub 연결 (25min)

**목표**: 로컬 → 인터넷 (URL 발급)

**내용**:
- Vercel = Next.js 만든 회사의 호스팅 (무료 시작)
- GitHub repo 연결 → push 시 자동 배포
- 환경변수 등록 (`.env` 값 → Vercel 대시보드)
- 도메인 발급 (`xxx.vercel.app`)
- Preview vs Production 환경 분리

**실습**:
- 모듈 4-3 Next.js 프로젝트를 GitHub push
- Vercel 연결 → 자동 배포
- 발급된 URL에서 데이터 확인

**산출**: 배포된 웹사이트 URL 1개

---

### 모듈 4-5: 웹 기반 테스트 + 로그 (15min)

**목표**: 배포 후 디버깅 능력

**내용**:
- **로컬 dev 서버**: `npm run dev` → 터미널 로그 실시간 확인
- **크롬 개발자 도구 Console**: 클라이언트 에러 / API 호출 실패 추적
- **Network 탭**: API 응답 확인 + 상태 코드 / payload 분석
- Vercel 대시보드 Logs 탭 (서버 로그)

**실습**:
- 의도적 에러 주입 (예: 잘못된 Supabase 키) → Console + Vercel 로그 양쪽에서 원인 추적
- 수정 → push → 자동 재배포 → 정상 확인

**산출**: 디버깅 1회 + 재배포 1회

---

## 회차 요약표 (업무 자동화 관점)

| 회차 | 주제 | DRI 단계 | 자동화 트리거 → 결과 | 핵심 산출물 |
|---|---|---|---|---|
| 1회 (2h) | Claude Desktop 풀활용 | D + R 일부 | Schedule(매월 1영업일) → 환율 자동 갱신 / Skill 1줄 → 배부판 생성 | Cowork Project + MCP 등록 + Skill/Schedule 1개씩 + Extension 4종 |
| 2회 (2h) | Claude Code 본격 도입 | I | PRD 1장 → ralph 루프 자동 코드 생성·수정 | VS Code + OMC + ralph/ralplan + CCG 멀티 모델 환경 |
| 3회 (2h) | API · 크롤링 · Git · 환경변수 · 테스트 | I 응용 | cron/이벤트 → 외부 데이터 자동 수집 → 저장소 자동 commit | 공공 API + SAP + 크롤링 + GitHub repo + `.env` + pytest |
| 4회 (2h) | SQL · Supabase · Next.js · Vercel 배포 | I 풀스택 | DB 변경 → 웹 화면 자동 반영 / git push → 자동 배포 | Supabase DB + Next.js 페이지 + Vercel 배포 URL |

---

## 산출물 (4회 누적)

| # | 산출물 | 합격 기준 |
|---|---|---|
| 1 | Cowork Project | "Humax 고정비 결산" Project 셋업 + 공통 자산 5종 첨부 |
| 2 | MCP 활용 | humax-excel-mcp 등록 + Skill 1개 + Schedule 1개 |
| 3 | Extension 4종 | Chrome / Word / Excel / PPT 각 1회 사용 |
| 4 | VS Code 환경 | Claude 확장 + Codex + Gemini + OMC 설치 완료 |
| 5 | PRD + ralplan | 본인 부서 자동화 후보 1개 PRD + ralplan 실행 |
| 6 | API 스크립트 3종 | 공공(data.go.kr) + SAP + 크롤링 각 1개 |
| 7 | GitHub repo | Private repo + `.gitignore` + `.env` 안전 셋업 + 첫 commit |
| 8 | pytest + 로그 분석 | 테스트 1개 + Claude Desktop 로그 추적 1회 |
| 9 | Supabase + Next.js | DB 3 테이블 + 페이지 1개 + 데이터 fetch 동작 |
| 10 | Vercel 배포 URL | GitHub 연결 + 자동 배포 + 환경변수 등록 + 디버깅 1회 |

---

## 강의 운영

| 항목 | 내용 |
|---|---|
| 인원 | 재무팀 실무자 5-10명 |
| 사전 준비 | Claude Pro/Team 라이선스 / 노트북 (macOS or Windows) / GitHub 계정 / Supabase 계정 / data.go.kr 계정 |
| 사후 설치 | Git / Node.js / VS Code / Claude Code CLI (2회 모듈 2-2에서 함께 설치) |
| 실습 데이터 | 합성/마스킹 데이터 우선 (사내 raw는 Phase 0 거버넌스 통과 후) |
| 강의실 환경 | 각자 노트북 + 안정적 인터넷 (Supabase/Vercel/GitHub 접속) |
| 평가 | 1-2회: 환경 셋업 / 3회: API 호출 스크립트 1개 / 4회: 배포된 URL 1개 |
