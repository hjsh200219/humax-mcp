# Humax AX 강의 계획서

> **대상**: Humax 재무팀 실무자 (1차 강의 수강 완료)
> **목적**: 고정비 결산 자동화 완성 + 전사 확대 인재 양성
> **구성**: 2차 (Cowork + MCP 제작) + 3차 (Code/바이브) 2개 차수
> **케이스 스터디**: Humax 고정비 결산 워크플로우 (file #1) 단일 자산 활용
> **핵심 전략**: Python 결정론 처리를 MCP로 감싸 Cowork에서 자연어 호출 → 실무자가 CLI 학습 없이 5개 에러 모두 해결

---

## 강의 철학

### 핵심 메시지

**"파일이 큰 게 문제다. AI가 못 하는 건 없다."**

1차 강의 후 실무자가 고정비 결산에 Claude 적용 시도 → 워킹데이 1일 단축에 머무름. 원인은 LLM 한계가 아니라 **raw data 토큰 폭발 + 데이터 분할 전략 부재**.

본 강의는 이 진단을 출발점으로 한다.

### 진단 (강의 출발점)

| 기존 인식 | 실제 원인 |
|---|---|
| "AI가 적요 인식 못 함" | raw 26BP `예산+실적` 시트 15,007행×63열 = 945K 셀 ≈ 3-5M 토큰 / Claude 컨텍스트 200K의 15-25배 초과 → 적요 컬럼이 후순위로 잘림 |
| "디자인 드리프트로 10회 이상 재명령" | 골든 템플릿 패턴 부재 + 빈 양식 채우기 미숙 |
| "원본 파일 훼손" | LLM 통째 재생성 구조 자체가 원인. Code 단계까지 필요 |
| "숫자 검토 부담" | 자동 검증 명령어 미설계 |
| "워킹데이 1일 한계" | Cowork 전략 미완성 (3일 가능) |

### 데이터 발견 (강의 자산)

raw `예산+실적` 시트에 **이미 있는 것**:
- C25 Text(적요): 60% 채움
- C29 비고: 4% (실무자 코멘트)
- C30 배부기준 + C31~34 배부율 (STB/Mobility/EVCS국내/해외)
- CC 마스터 시트: Description 77% (CC 한국어명 lookup)

→ **SAP API 없이도 Cowork만으로 건별 배부/적요 분류 가능**. 진단 시연이 강의 hook.

---

## 2차 강의 (Cowork + MCP 제작) — 총 9시간 25분

### 모듈 1: 진단 + 토큰 절약 (1.5h)

**목표**: "왜 안 됐나" 라이브 시연 + 토큰 한계 직관 습득

**내용**:
- 1차 강의 후 실무 적용 결과 회고 (워킹데이 1일)
- file #1 한계란 원문 인용
- **라이브 데모 1**: 26BP raw 첨부 시 토큰 사용량 즉시 표시 → 컨텍스트 초과 확인
- **라이브 데모 2**: raw `예산+실적` C25 Text 컬럼 직접 열기 → 적요 60% 채워진 것 시연
- **반전**: "Claude가 못 읽은 게 아니라, 못 받은 것"
- 컬럼 후순위 잘림 시뮬레이션
- C30 배부기준 / C31~34 배부율 / CC Description 발견

**실습**:
- 토큰 측정 도구 사용
- raw → 시트별 분할 → 월별 분할 → 회사별 분할
- 같은 작업을 분할 전/후로 실행 → 결과 비교

**산출**: 토큰 절약 원칙 5종 (시트 분할 / 월 필터 / 회사 필터 / 컬럼 우선순위 / 2-pass)

---

### 모듈 2: 서식·디자인 커스텀 스킬 (1.5h)

**목표**: 디자인 드리프트 차단 + 스킬화로 재현성 확보

**내용**:
- 골든 템플릿 패턴 = 전월 산출물 → 빈 양식 변환 → 채우기
- 시트 구성 보존 (당월/누계/Diff)
- (A+B+C) 헤더 구조 유지
- 셀 서식 명시 프롬프트 (날짜/숫자/통화)
- 시트 폭 119/213 column 대응 패턴

**실습**:
- file #1 Step 5 명령어를 골든 프롬프트로 재작성 (Before-After)
- Humax 배부판 빈 템플릿 생성 → 데이터만 채워넣기 시연
- "shumax-format-skill" 커스텀 스킬 빌드 → 슬래시 호출

**산출**: 골든 프롬프트 4종 (Step 2/5/6/7) + 서식 스킬 1개

---

### 모듈 3: 프로젝트 + 공통 파일 (1h)

**목표**: 매번 첨부 안 하고 영구 참조

**내용**:
- Claude Projects 기능 활용
- 공통 자산 첨부 패턴:
  - 배부율 마스터 (월별 변동)
  - CC 마스터 (조직-사업부 매핑)
  - 계정 코드 사전 (G/L Account 한국어명)
  - 골든 템플릿 (Humax 배부판 / EVCS 계정별 / Humax 계정별)
  - SOP 지침 (검증 룰, 코멘트 작성 가이드)
- 지침에 lookup 우선순위 명시

**실습**:
- "Humax 고정비 결산" 프로젝트 생성
- 5종 공통 자산 첨부
- 모듈 2에서 만든 골든 프롬프트 → 프로젝트 안에서 실행 → 첨부 불필요 확인

**산출**: Humax 고정비 결산 Claude Project 셋업 완료

---

### 모듈 4: K-Public-Data MCP 활용 (1h)

**목표**: 외부 데이터 수기 작업 제거

**내용**:
- K-Public-Data MCP 소개 (강사 제작 자산)
- 환율 조회 (수출입은행, 한국은행)
- 사옥운영 외부 데이터 조회 (필요 시)
- DART 공시 조회 (자회사 실적 대사 등)
- Step 3 수기 편집 중 환율 부분 자동화

**실습**:
- "이번 달 USD/EUR/CNY 환율 조회해서 26BP 통화 행에 적용해줘" 라이브
- 매월 1영업일 자동 환율 갱신 스케줄 등록

**산출**: 환율 조회 + 자동 갱신 스킬 1개

---

### 모듈 5: 적요·배부율 활용 PoC (1h)

**목표**: 모듈 1에서 발견한 raw 자산을 결산에 직접 사용

**내용**:
- raw `예산+실적` C25 Text + C30 배부기준 + C31~34 배부율 활용
- 시트 분할 → 적요 우선 전송 패턴
- CC 마스터 lookup → 한국어 부서명 자동 매핑
- 건별 배부 자동화: 지급수수료 / 소모성경비 / 인증대행료
- 결과를 산출물 비고란에 자동 채움 → 이중 작업 제거

**실습**:
- raw 1월 본사 데이터만 분할 → Claude에 전송
- 적요 + 배부율로 건별 분류 실행
- 결과 비교 (수기 vs AI)

**산출**: 적요 활용 스킬 1개 + 한계 2번 제거 확인 보고서

---

### 모듈 6: 검증 자동화 + 코멘트 초안 (1h)

**목표**: 숫자 검증 부담 + Diff 코멘트 작성 자동화

**내용**:
- 합계 크로스체크 명령어 (조직 5계층 합산 일치 검증)
- |10백만원| 이상 이상치 자동 탐지
- Diff 시트 코멘트 초안 작성 룰
  - 패턴: `[코드] [계정명] [+/-금액]` (예: "11 급여 -85백만")
- 코멘트 작성자 = 실무자 (AI 초안 + 사람 confirm)
- 스케줄러 등록 (매월 1영업일)

**실습**:
- 합계 검증 명령어 실행 → 불일치 항목 탐지
- 3월 누계 Diff 시트 코멘트 초안 자동 생성 → 실무자 검토/수정

**산출**: 검증 스킬 1개 + 코멘트 초안 스킬 1개 + 스케줄러 설정

---

### 모듈 7: Python MCP 제작 입문 (2h 25min) — **핵심 차별화 모듈**

**목표**: Python 결정론 처리를 MCP로 감싸 Cowork에서 자연어 호출. 원본 훼손/숫자 검토 + 환율 수기 입력 + 배부율 수기 편집 문제 근본 해결.

**왜 필요한가**:
- 5개 에러 중 #1 원본 훼손 / #5 숫자 검토는 Cowork만으로 30% 해결. 근본 해결은 Python 결정론 필수
- file #1 Step 3 수기 편집의 환율/배부율 update 자동화 = 외부 API + raw 셀 단위 편집 필요
- Claude Code(CLI) 학습은 부담 큼. 실무자는 Cowork(자연어) 환경 유지하고 싶음
- **해결**: Python 결정론을 MCP 서버로 감싸면 Cowork에서 자연어로 호출 가능
- 1차 강의에서 본 K-Public-Data MCP / 사주 MCP / 유튜브 MCP와 동일 패턴 = 실무자 친숙

**내용**:
- MCP 개념 재정리 (1차 강의 복습): AI ↔ 외부 도구 표준 프로토콜
- Python `mcp` SDK 기본 (FastMCP)
- MCP tool 작성 패턴: `@mcp.tool()` 데코레이터 + 타입 힌트
- Humax Excel MCP 설계 (**도구 7개**):
  - `extract_filtered(file, sheet, month, company, columns)` → 필터링 추출
  - `verify_sums(file, sheet, levels)` → 조직 5계층 합계 검증
  - `write_cells(file, sheet, updates)` → openpyxl 결정론 셀 편집 (원본 보존)
  - `generate_diff_candidates(prev, curr, threshold=10)` → |10백만| 이상 추출
  - `get_allocation_rates(file, month, company?)` → 26BP raw 배부율 조회 + 합 100% 검증
  - `update_allocation_rates(file, month, updates, output_path, dry_run)` → 배부율 변경 (write_cells 안전 정책)
  - `get_exchange_rates(search_date?, target_currencies?, fallback_to_previous=True)` → 한국수출입은행 환율 API 조회 (휴일 fallback + JPY/IDR 정규화 + 12h 캐시)
- 전 도구 공통: `render_format: "excel" | "live_artifact" | "both"` Live Artifact 출력 옵션 + `artifact_hints` 자동 생성
- Claude Desktop에 커스텀 커넥터로 등록
- 실무자가 자연어로 호출하는 패턴

**라이브 데모 (3개)**:

**데모 1 — 추출 + 검증** (extract_filtered + verify_sums):
```
실무자: "26BP 3월 raw에서 본사 인건비만 추출해서 합계 검증해줘"
Claude Desktop: [extract_filtered 호출] → [verify_sums 호출]
결과: "본사 인건비 3월 합계 X백만원, 조직 5계층 합산 일치 확인"
```

**데모 2 — 배부율 조회 + Live Artifact** (get_allocation_rates):
```
실무자: "3월 배부율 Live Artifact로 보여줘"
Claude Desktop: [get_allocation_rates(render_format="live_artifact") 호출]
결과: stacked bar chart (CC별 STB/Mobility/EVCS국내/EVCS해외 비율) + 합계 100% 검증 카드
```

**데모 3 — 환율 조회 + 적용 + 검증** (chained 워크플로우):
```
실무자: "오늘 환율 조회해서 26BP 환율 시트에 USD/EUR/JPY 적용하고 외화 환산 합계 검증해줘"
Claude Desktop:
  1. [get_exchange_rates(target_currencies=["USD","EUR","JPY(100)"])] → 매매기준율 조회
  2. [write_cells(file=26BP, sheet=환율, updates=...)] → 셀 단위 적용
  3. [verify_sums(file=26BP, sheet=환율)] → 외화 환산 합계 검증
결과: "환율 적용 완료. USD=1393, EUR=1488, JPY=8.99. 외화 환산 합계 일치 확인"
```

**실습**:
- mcp SDK 설치 (`pip install mcp`)
- 10개 도구 중 **2개 hands-on + 1개 demo + 4개 사후 학습** (v0.1):
  - hands-on: `extract_filtered` (35min) + `get_exchange_rates` (10min)
  - demo: `verify_sums` (5min)
  - 사후 (강사 템플릿 기반): `write_cells` / `generate_diff_candidates` / `get_allocation_rates` / `update_allocation_rates`
- Claude Desktop에 등록
- 자연어로 호출 → 동작 확인
- file #1 한계란 5개 에러 중 #1, #5 해결 시연 + Step 3 환율/배부율 수기 작업 제거 시연

**사내 배포 전략**:
- GitHub Private repo 기반 (`git clone` + `install.ps1`)
- 코드 변경 시 `update.ps1` (git pull + pip install)
- 다른 부서 실무자는 Claude Desktop 커넥터 추가만 → 즉시 사용
- 1명 제작 → 전사 사용 가능 (Q3 전사 확대의 기술적 핵심)
- `.env`에 `EXCHANGE_RATE_API_KEY` 보관, `.gitignore` 강제

**산출**:
- `humax-excel-mcp` 1개 (도구 최소 3개 동작: extract + verify + exchange)
- Claude Desktop 등록 가이드 문서
- 5개 에러 해결도 + Step 3 환율/배부율 자동화 재측정 보고서

**참고 — Cowork+MCP vs Claude Code 비교**:

| 항목 | Cowork+MCP | Claude Code |
|---|---|---|
| 인터페이스 | 자연어 | CLI |
| 실무자 학습 곡선 | 낮음 | 중간 |
| Python 결정론 | ✅ MCP tool | ✅ 직접 |
| 자기 수정 | 사람 수정 | 자동 |
| cron 무인 | △ (사람 트리거) | ✅ |
| 사내 배포 | MCP 1회 → 전사 | 각자 설치 |

→ **결산 = Cowork+MCP로 충분. 진정한 무인 자동화 = 3차 강의 Claude Code 단계**.

---

### 모듈 8: 고정비 결산 플러그인 통합 (30분)

**목표**: 모듈 2-6에서 만든 스킬 7개를 1개 플러그인으로 묶음

**내용**:
- 스킬 묶음 → "Humax 고정비 결산 플러그인"
- 7단계 매핑:
  - `/raw-prep`: Step 1 Raw 분할
  - `/v1-build`: Step 2 자동 연결
  - `/v2-edit-assist`: Step 3 수기 편집 가이드 + 환율 자동
  - `/bp-merge`: Step 4 통합
  - `/humax-allocation`: Step 5 배부판
  - `/evcs-account`: Step 6 EVCS 계정별
  - `/humax-account`: Step 7 Humax 계정별
- 워킹데이 효과 측정 (Baseline 1일 → Phase 1 목표 3일)

**산출**: 플러그인 완성 + 효과 측정 베이스라인

---

### 2차 강의 클로징 메시지 (5분)

> "오늘 고정비 결산을 1일에서 4일까지 단축했다. 5개 에러 중 원본 훼손/숫자 검토까지 Python MCP로 해결됐다. file #1 Step 3 수기 편집의 환율 update와 배부율 update까지 자연어 1줄로 끝낸다. 같은 패턴(스킬 + Project + MCP)을 변동비/매출/자금/인건비 결산에 그대로 적용 가능하다. 하지만 SAP에서 raw 추출은 여전히 수기다. 매월 사람이 트리거해야 한다. 다음 강의에서 SAP API를 직접 호출하고, Python으로 전 과정을 무인 자동화한다. 그리고 이 능력은 재무를 넘어 회사 전 부서로 확대된다."

---

## 3차 강의 (Code / 바이브 코딩) — 총 10시간

### 모듈 1: Claude Code + MCP 환경 (1h)

**목표**: Cowork와 다른 환경 적응

**내용**:
- Claude Code 설치 (CLI 기반)
- Cowork(데스크탑) vs Code(CLI) 차이
- MCP 서버 등록 패턴
- 1차 강의에서 본 K-Public-Data MCP를 Code 환경에서 호출
- 작업 디렉터리 / Git 기본

**실습**:
- 설치, 첫 명령 실행
- K-Public-Data MCP 등록 후 환율 조회

**산출**: Code 환경 셋업 완료

---

### 모듈 2: 수출입은행 API 직접 호출 (1.5h)

**목표**: MCP 없이 외부 API 직접 사용

**내용**:
- 수출입은행 환율 API 구조
- Python `requests` 기본
- API 키 관리 (.env)
- 응답 데이터 가공
- 26BP Excel 환율 행에 자동 입력 (openpyxl)
- 매월 cron 등록

**실습**:
- 수출입은행 API 호출 코드 Claude Code가 작성
- 환율 → 26BP 시트 자동 갱신
- cron 등록 후 다음 달 자동 실행 확인

**산출**: 환율 자동화 스크립트 + cron

---

### 모듈 3: Python + openpyxl 결정론 편집 (2h)

**목표**: 원본 훼손 차단 + 서식 100% 보존

**내용**:
- openpyxl 기본 (워크북/시트/셀)
- 셀 단위 read-modify-write
- 서식 보존 패턴
- 수식 셀 처리
- 머지 셀 처리
- Git 버전관리 (매월 산출물 diff)
- 원본 훼손 시 복구

**실습**:
- file #1 Step 5 시트 생성을 Python으로 재현
- 당월/당월누계/Diff 3종 시트 결정론 생성
- Git commit → 매월 변경 추적

**산출**: 결정론 셀 편집 스크립트 + Git 저장소

---

### 모듈 4: JSON/CSV 경량화 (1h)

**목표**: 토큰 절약을 Code 단계로 끌어올림

**내용**:
- 26BP Excel 945K 셀 → CSV 변환
- 필요 컬럼/행만 추출
- JSON Lines 변환 (스트리밍 처리)
- 토큰 90% 감소 비교
- Claude에 전송 시 CSV/JSON 우선

**실습**:
- raw `예산+실적` → CSV로 export
- 컬럼 필터링 (필요한 25컬럼만)
- 토큰 측정 비교

**산출**: 경량화 스크립트 + 토큰 절감 보고서

---

### 모듈 5: SAP API export 자동화 (2h)

**목표**: Step 1 Raw Update 완전 무인화

**내용**:
- SAP 접근 4계층 비교:
  - L1: SAP GUI Scripting (VBScript, Basis 권한 불필요)
  - L2: OData / RFC (Basis 권한 필요)
  - L3: ABAP 배치
  - L4: BTP / Joule (사내 LLM)
- Humax 환경에서 시작 단계 (L1)
- 회사별 자동 추출 (HMX/HUS/HUK/HBR/HSZ)
- CSV/JSON으로 export (Excel 우회)
- 01.Source 폴더 자동 적재

**실습**:
- SAP GUI Script 작성 (Claude Code가 코드 생성)
- FBL3N 자동 export 시연 (또는 녹화)
- CSV 결과물을 모듈 4 경량화에 연결

**산출**: SAP 자동 export 스크립트

---

### 모듈 6: 전 과정 자동화 파이프라인 (1.5h)

**목표**: SAP → 환율 → 결정론 편집 → 산출물 → 알림 무인 체인

**내용**:
- Python 파이프라인 구조
- 단계: SAP export → CSV 변환 → 환율 API → 26BP 갱신 → 산출물 3종 생성 → Git commit → Slack 알림
- 에러 처리 / 재시도
- 매월 1영업일 cron
- 실패 시 fallback (수기 모드)

**실습**:
- 1월~3월 데이터로 풀 파이프라인 1회 실행
- 실행 시간 측정 (목표: 1시간 이내)
- 실패 시나리오 시뮬레이션

**산출**: 무인 자동화 파이프라인 1개

---

### 모듈 7: 검증·모니터링·Git (1h)

**목표**: 자동화의 안정성 확보

**내용**:
- 자동 합계 검증 (Python assertions)
- 이상치 자동 알림 (|10백만| 이상)
- Git diff로 매월 변경 추적
- 산출물 변경 시 Slack 통지
- 실패 시 메일 알림

**실습**:
- 검증 룰 정의
- Slack 웹훅 설정
- 의도적 오류 주입 → 알림 확인

**산출**: 모니터링 체계

---

### 모듈 8: 전사 확대 — 바이브 코딩의 진짜 가치 (1h)

**목표**: 재무 1개 워크플로우 → 회사 전역으로 확장 시각화

**내용**:
- 부서별 자동화 후보 맵
  - 영업: 매출 일보 + 거래처 분석 + 미수금 알림
  - 구매: 발주서 자동 생성 + 단가 비교
  - HR: 근태 분석 + 인건비 변동
  - 마케팅: 광고 카피 + 경쟁사 모니터링
  - SCM: 재고 회전율 + 발주 예측
  - 법무: 계약서 리스크 + 판례 조회
  - 품질: 불량률 분석 + 시정조치
  - 전략: KPI 대시보드 + 경영진 리포트
  - IT: 헬프데스크 1차 응대
- 같은 패턴 (스킬 + MCP + Python + cron) 적용
- 사내 도구 마켓플레이스 구상
- 부서 인재 양성 단계 (재무 → 5-10명 → 전사)

**라이브 데모**:
- 강사가 받는 자리에서 부서 1개 도구 즉석 빌드 (예: 매출 일보)
- 강의실에서 30분 이내 작동 시연

**산출**: 전사 확대 로드맵 + 각자 부서 적용 후보 1개 선정

---

### 3차 강의 클로징 메시지

> "고정비 결산을 자동화한 것은 시작이다. 같은 도구로 재무 외 9개 부서 업무를 자동화할 수 있다. Humax 26개 회사·5개 사업부·다수 부서. 각자가 부서로 돌아가 도구 1개씩 만들면 회사 전체로 수십~수백 개 자동화 자산이 누적된다. 외주 개발에 수천만원, 수개월 걸리던 일을 본인이 1-2주에 끝낸다. AI를 잘 쓰는 사람이 못 쓰는 사람의 업무를 대체하는 게 아니라, **본인이 만든 도구가 본인을 더 큰 일에 쓰게 만든다**."

---

## 산출물 (컨설팅 deliverables)

| # | 산출물 | 합격 기준 | 형태 |
|---|---|---|---|
| 1 | Humax 고정비 결산 SOP | 7단계 표준 절차, 실무자 자력 수행 | Word + Excel |
| 2 | 골든 프롬프트 라이브러리 | 최소 10개 (Step 2/5/6/7 Before-After 포함) | 텍스트 + Claude Project |
| 3 | 고정비 결산 플러그인 | 스킬 7개 + 1 플러그인 + 스케줄러 | Claude Cowork |
| 4 | **Humax Excel MCP** | **Python 도구 7개 (extract / verify / write / diff / allocation_get / allocation_set / exchange), 전 도구 Live Artifact 옵션, Claude Desktop 등록 + 자연어 호출 동작** | **Python 서버 + 등록 가이드 + GitHub Private Repo** |
| 5 | Python 무인 자동화 파이프라인 | SAP → 환율 → 산출물 → 알림 cron 체인 | Git 저장소 |
| 6 | 검증·모니터링 체계 | 합계/이상치 자동 + Slack 알림 | Python + 웹훅 |
| 7 | 전사 확대 로드맵 | 9개 부서 자동화 후보 맵 + 인재 양성 단계 | 문서 |
| 8 | 효과 측정 보고서 | 베이스라인 1일 → 측정 결과 (목표 4-5일) | 측정 데이터 + 보고 |

---

## 효과 가설

| 단계 | 워킹데이 | 누적 자동화 자산 |
|---|---|---|
| 현재 (1차 강의 후) | 1일 | Claude 대화 수준 |
| 2차 강의 후 (Cowork + MCP) | **4일** | 스킬 7개 + 플러그인 1 + Project 1 + **Python MCP 1개** |
| 3차 강의 후 (Code 무인) | 4.5-5일 | Python 파이프라인 + SAP API + cron + Git + 알림 |
| 6개월 후 (전사 확대) | 부서당 효과 | 10개 부서 × 1-2 도구/MCP = 누적 30-50 인일/월 절감 |
| 1년 후 | - | 50+ 사내 자동화 자산 + MCP 마켓플레이스 |

---

## 강의 운영

| 항목 | 내용 |
|---|---|
| 2차 (Cowork + MCP) 인원 | 재무팀 실무자 + 결산 관련 인력 5-10명 |
| 3차 (Code) 인원 | 부서별 핵심 인력 5-10명 (재무 + 영업 + HR + SCM 등) |
| 사전 준비 | Claude Pro/Team 라이선스, Python 3.10+ 설치, mcp SDK (`pip install mcp`), Claude Code 설치 (3차), K-Public-Data MCP 접근, SAP Basis팀 사전 협의 (3차) |
| 실습 데이터 | 실 raw (Phase 0 거버넌스 통과 후) 또는 합성/마스킹 데이터 |
| 강의실 환경 | 각자 노트북 (Python 실행 가능) + 사내 SAP 접근 가능 |
| 평가 | 2차: 스킬 1개 + MCP tool 1개 직접 제작 / 3차: 부서 적용 도구 1개 기획서 |

---

## Q&A — RFP 3개 질문 답변

### Q1. 더 효율적/정교한 명령어 개선

→ **2차 모듈 1, 2, 6 응답**.
- 토큰 절약 5원칙 + 골든 프롬프트 5단 구조 + 검증 자동화 명령어
- Step 2/5/6/7 명령어 Before-After 라이브 변환

### Q2. 결과물이 기대치에 못 미침 — 더 개선 가능?

→ **2차 모듈 1, 2, 3, 5, 7 + 3차 모듈 3, 7 응답**.
- 진짜 원인 = 토큰 폭발 + 데이터 분할 부재. LLM 한계 아님
- raw에 적요/배부율 이미 있음 → 활용 가능
- 5개 에러 중 #1 원본 훼손/#5 숫자 검토는 **2차 모듈 7 (Python MCP)** 가 근본 해결
- Cowork+MCP 합산 시 4일, Code 무인 합산 시 4.5-5일

### Q3. 기타 유사 업무 활용 가능성

→ **3차 모듈 8 응답**.
- 핵심 답: **바이브 코딩 학습이 전사 확대 키**
- 부서별 1명 학습 → 1-2개 도구 제작 → 회사 전역에 자동화 자산 누적
- 외주 의존 제거, 도메인 전문가 = 도구 제작자
