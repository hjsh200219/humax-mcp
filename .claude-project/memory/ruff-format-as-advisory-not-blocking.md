---
name: ruff-format-as-advisory-not-blocking
description: 기존 코드 스타일이 ruff format 기본과 다른 프로젝트에서는 ruff format을 블로킹 게이트로 두지 말고 advisory로 처리. 신규 파일만 자동 포맷.
type: feedback
created: 2026-05-19
---

humax-excel-mcp는 ruff `check`만 사용해 왔고 `ruff format`은 미적용. `ruff format --check .`을 gc.sh 게이트에 넣으면 30+ 기존 파일이 "would reformat"으로 차단됨.

선택지:
1. 전체 `ruff format` apply — 거대 diff, author 의도 손상 가능, "기존 패턴 존중" 원칙 위반
2. ruff format을 advisory(비차단)로 — 신규 파일만 pre-commit에서 자동 포맷

**선택**: 2. `gc.sh`에서:

```bash
ruff format --check . > /dev/null 2>&1 \
  && LOG+=("PASS ruff format") \
  || LOG+=("WARN ruff format (advisory)")
```

`.pre-commit-config.yaml`의 `ruff-format` hook은 그대로 두면 **새로 staged된 파일에만** format 적용 (commit 시 자동 reformat → 재staging 필요).

**Why**: 기존 234 tests 가 통과하는 코드를 blanket format으로 바꾸면 git blame 어지러워지고 surgical changes 원칙 위반. 새 파일은 자동 포맷되니 시간 지나면 자연 통일.

**How to apply**: 기존 Python 프로젝트에 ruff format 도입 시 동일 패턴. 처음부터 적용된 프로젝트면 blocking으로 두는게 맞음.
