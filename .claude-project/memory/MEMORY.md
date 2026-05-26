# Memory Index

- [Humax 결산 워크플로우 컨텍스트](humax-closing-workflow.md) — file #1 7단계 + 5개 에러 + 한계 2종 진단
- [26BP raw 스키마 핵심](bp26-schema-key-findings.md) — 예산+실적 시트 컬럼 매핑 + 적요/배부율/CC 마스터 위치
- [도구 7개 핵심 spec](mcp-tools-overview.md) — extract/verify/write/diff/alloc_get/alloc_set/exchange 요약
- [pytest-httpx 0.36 API](pytest-httpx-036-api.md) — url=re.compile(...) 사용, url__regex 금지
- [검증 순서: schema → empty → rule](validation-order-schema-first.md) — SCHEMA_MISMATCH가 empty 체크보다 먼저
- [다중 키 diff fixture 변형 규칙](pandas-multi-key-diff-pattern.md) — key 컬럼은 양쪽 동기 변경
- [Excel write 4중 안전 패턴](write-tool-output-path-safety.md) — backup + output_path 검증 + dry_run + post-verify
- [골든 템플릿 엔진 패턴 (v0.1.1)](golden-template-engine-pattern.md) — 디자인 드리프트 차단: binding + sidecar + fixture build
- [audited() file_path_arg 확장 (v0.1.1)](audited-file-path-arg-extension.md) — 신규 도구의 첫 인자 매핑 파라미터
- [큰 xlsx source read_only (v0.1.2)](excel-io-readonly-source-large-file.md) — 30s+ → 0.2s, 15k+ rows formula evaluation 회피
- [EVCS expand_evcs per-call flag (v0.1.2)](aggregator-evcs-per-call-flag.md) — additive is_virtual 거부, 구조적 double-count 방지
- [bp26 vs raw_bp26 schema 분리 (v0.1.2)](raw-vs-aggregated-schema-separation.md) — frozen schema + 별도 raw 파일 + aggregator 변환 layer
- [vulture + pydantic v2 false positives](vulture-pydantic-v2-false-positives.md) — ignore_names에 cls/model_config 추가, path 인자 제거
- [ruff format은 advisory (기존 프로젝트)](ruff-format-as-advisory-not-blocking.md) — blanket format 회피, 신규 파일만 pre-commit으로 자동 포맷
- [DRI 모델 강의 척추](dri-model-claude-ecosystem-pedagogy.md) — Desktop/Remote/IDE 3단계 진화로 Claude 생태계 교육 구조화, 자동화 자산 기준 평가
- [비개발자 문서 스타일 — 비유 우선](non-dev-doc-style-analogy-first.md) — docs/prd/ 문서는 비유+ASCII 다이어그램+Before/After 표 우선, 코드 최소화
- [Python vs LLM 역할 분담 canon](python-vs-llm-role-split-canon.md) — "숫자는 Python, 말은 LLM" — 외부 설명 시 표준 프레이밍
- [docs/ 디렉터리 청중 라우팅](docs-prd-audience-routing.md) — prd=비개발자, design-docs=개발자. 신규 문서 위치 결정 기준
