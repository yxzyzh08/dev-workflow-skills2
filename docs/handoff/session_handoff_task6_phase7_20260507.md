# Session Handoff — Task 6 Phase 7 (Closure: Smoke + Entry Docs + Task 6 Wrap-up)

**Handoff Date**: 2026-05-07
**Handoff By**: Claude (claude-opus-4-7[1m])
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`
**Current Task**: Task 6 implementation — **Phase 7 (final closure)**
**Current Phase**: **Phase 1-6 全部 (A) closed; Task 6 implementation 整体闭环**；Phase 7 是 Task 6 的封顶（managed-project happy-path smoke + reference 文档微修 + entry docs + Task 6 closure handoff）。
**Important Status**: 781 tests pass; compileall clean; 12 progress.py 子命令；4 validate.py 子命令；no repo-root progress files leak。

---

## 0. New Session Read Order

读这些（按顺序）：

1. **本 handoff**（你现在读的这份）
2. `docs/review/task6_phase6_4_advance_consistency_round2_review_20260507.md` — Phase 6.4 round 2 review (A)，**0 H / 0 M / 0 L**，明确 "Task 6 implementation closes; ready for Phase 7"
3. `docs/implementation/task6_plan_20260507.md` §13 Phase 7 + §15 Acceptance Criteria — Phase 7 scope 与验收清单
4. `docs/handoff/session_handoff_20260506_v4.md` §7.4 entry docs + §8 新 session 第一指令风格 — Task 6 整体规划的最后一段
5. `skills/workflow-protocol/references/command-reference.md`（全文，作为最终对照源）
6. `skills/doc-guardian/references/required-artifacts.md`（P6 资源，smoke 测试构造 fixture 用）
7. `skills/_shared/dev_workflow/progress_state.py` 全部 `apply_*` 函数集合 + `progress_replay.py` 14 + 1 = 15 handler 表（作为 smoke 设计前的全景参考）
8. **Open Questions / Hardening Options** — 见 §7（汇总 Phase 6.1-6.4 review 留下的所有 non-blocking open questions，新 session 决定哪些升入 Phase 7 scope）

可选背景：
- `docs/handoff/session_handoff_task6_phase6_{2,3,4}_20260507.md` — 各子 phase handoff（含 watch-points 风格）
- `memory/MEMORY.md` — 项目框架记忆
- 全部 `docs/review/task6_*_review_*.md` 14 份评审报告（作为决策审计trail）

---

## 1. Critical Constraints

- 本 repo 不是被 workflow 管理的项目；**Phase 7 的 smoke 测试必须在 `tempfile.TemporaryDirectory` 隔离**——绝不可创建 / 修改 repo-root `progress.md` / `progress-history.md`。
- 当前 git 工作树仍是大量 untracked（`docs/`, `skills/`, `tests/`, `startclaude.sh`, `startcode.sh`, `temp.md`）。**不要 reset / clean / rm** 这些。
- Phase 6 已完整闭环（4 子 phase 全 (A) + 各自 round 2 polish 全 landed）。本 phase 不能 re-open Phase 6.x 任何已闭合的设计决定。
- Phase 7 范围严格按 task6_plan §13 Phase 7 四项：
  1. Run full test suite ✅（Phase 6.4 round 2 已通过；Phase 7 启动时 sanity 重跑）
  2. **Run temp managed-project happy path smoke**（核心新工作）
  3. Patch reference wording discovered during implementation（找 + 修）
  4. Prepare Task 6 closure handoff for AGENTS/CLAUDE/plugin metadata（**写 entry docs**）
- Phase 7 **不**实现：
  - `validate.py all`（Phase 7 内部仍是 deferred；考虑放到 Task 7+ 或 v0.7 spec 决定后再做）
  - 任何 `progress_state.py` / `progress_replay.py` / `validate.py file` / `progress.py` 命令的新逻辑
  - Vertical skill scripts（PRD/SRS/Architecture/Development/Testing/Delivery/Retrospective write/review）—— 那是 Task 7+ 范围
  - SKILL.md 大改（Phase 7 仅小修：reference 用词与实现对齐）

---

## 2. Current Repository State

Project root: `/home/cgs/github_projects/dev-workflow-skills2`

### 2.1 Implementation 文件清单（Task 6 全交付）

```
skills/_shared/dev_workflow/
├── atomic.py              (Phase 2)
├── frontmatter.py         (Phase 2)
├── markdown.py            (Phase 2)
├── changelog.py           (Phase 3)
├── schema.py              (Phase 2)
├── conditions.py          (Phase 2 — DSL parser, no eval)
├── artifacts.py           (Phase 2 — get_required_artifacts + ProgressLike)
├── progress_lock.py       (Phase 5.1)
├── progress_history.py    (Phase 5.1)
├── progress_replay.py     (Phase 5-6 — 15 handlers; TERMINAL_EVENTS={"incident-resolve"} action-aware gate)
├── progress_artifacts.py  (Phase 5.3-6.4 — loaders + BUG triage parser; _PATH_TEMPLATES 含 7 doc types 包括 installation-result)
└── progress_state.py      (Phase 5-6 — 11 apply_* + 2 helpers; ~1980 行)

skills/doc-guardian/scripts/
├── validate.py            (Phase 3-6.4 — file/ids/consistency 实装；all 标 deferred to Phase 7)
├── changelog.py           (Phase 3 — promote/validate)
└── status_transition.py   (Phase 4)

skills/workflow-protocol/scripts/
└── progress.py            (Phase 5-6.4 — 12 子命令 + 3 update modes (event/task/advance); ~1750 行)

tests/
├── test_apply_*.py            (10 文件，纯 state-machine 单测)
├── test_progress_*.py         (12 文件，CLI integration)
├── test_progress_replay.py    (replay handler 集成)
├── test_progress_recover.py   (recover roundtrip)
├── test_progress_history.py   (history parser)
├── test_progress_lock.py      (file lock)
├── test_progress_artifacts.py (artifact loaders)
├── test_progress_schema.py    (frontmatter schema)
├── test_changelog.py          (changelog helper)
├── test_validate_file.py      (validate.py file 1-7)
├── test_validate_consistency.py (Phase 6.4 — Class 8)
├── test_status_transition.py
├── test_conditions_artifacts.py
└── test_frontmatter_markdown_atomic.py
```

**总计**：13 shared modules + 3 doc-guardian scripts + 1 workflow-protocol script + 27 测试文件 = **781 tests** 全过；compileall 干净；no repo-root pollution。

### 2.2 12 progress.py 子命令

`init / query / recover / update (--event/--task/--advance) / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework / incident-start / incident-resolve`

### 2.3 4 validate.py 子命令

`file <doc>` (1-7) / `ids` (uniqueness) / `consistency` (Class 8) / `all` (deferred to Phase 7)

### 2.4 15 replay events（Phase 6.4 final）

`init / write-complete / review-issues / review-passed / human-confirmed / update-task / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework / incident-start / incident-resolve / update-advance`

`TERMINAL_EVENTS = {"incident-resolve"}` 含 action-aware gate（`abort` / `reconstruct` 终态；`continue` 非终态）。

### 2.5 当前 baseline

```bash
python3 -m unittest discover -s tests
# Ran 781 tests in 7.0s — OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

# Smoke (smoke 之前手动跑过)
python3 skills/workflow-protocol/scripts/progress.py --help     # 12 子命令
python3 skills/doc-guardian/scripts/validate.py --help          # 4 子命令

# Repo cleanliness
test ! -e progress.md && test ! -e progress-history.md && echo "ROOT CLEAN"
# ROOT CLEAN
```

---

## 3. Completed Work Before This Handoff

### Phase 1-4（closed）

- Phase 1: docs alignment
- Phase 2: shared foundation（frontmatter / markdown / atomic / conditions / artifacts / progress_state base / schema）
- Phase 3: `changelog.py` + `validate.py file/ids`
- Phase 4: `status_transition.py`

### Phase 5（closed; 4 子 phase）

- 5.1: progress.py foundation
- 5.2: `update --event`（4 events + M1 history-parse-and-replay-consistency + M2 review_iteration ≤ 7 entry guard）
- 5.3: `update --task`（Stage 4 task state machine; `validate_artifacts=True` forward / `False` replay）
- 5.4: `release-close` + `release-start` + `bug-intake`

### Phase 6（closed; 4 子 phase 全 (A) + polish）

- 6.1 ✅: `bug-start` + `bug-close` + Gap-3 update --task（含 round 2 fixes）
- 6.2 ✅: `bug-rework` + Gap-4/5 reuse（含 3 Low polish）
- 6.3 ✅: `incident-start` + `incident-resolve` + `TERMINAL_EVENTS` 首次激活 + Option B action-aware terminal gate（含 round 2 + 1 non-blocking Low fix）
- 6.4 ✅: `update --advance`（P6 matrix forward path）+ `validate.py consistency`（Class 8 cross-progress）（含 round 2 fixes：H1 installation-result loader + M1 P6-under-lock + M2 malformed progress 防御 + L1 doc/help + L2 SKILL P6 matrix）

### 评审报告时间线（共 14 份）

| Phase | Round | 文件 | 结论 |
|-------|-------|------|------|
| 1 | - | task6_phase1_docs_alignment_review_*.md | (A) |
| 2 | 1+2 | task6_phase2_shared_foundation_*_review_*.md | (B)→(A) |
| 3 | 1+2 | task6_phase3_changelog_validate_*_review_*.md | (B)→(A) |
| 4 | 1+2 | task6_phase4_status_transition_*_review_*.md | (B)→(A) |
| 5.1 | 1+2 | task6_phase5_1_progress_core_*_review_*.md | (B)→(A) |
| 5.2 | 1+2 | task6_phase5_2_update_event_*_review_*.md | (B)→(A) |
| 5.3 | 1+2 | task6_phase5_3_update_task_*_review_*.md | (B)→(A) |
| 5.4 | 1+2 | task6_phase5_4_release_lifecycle_*_review_*.md | (B)→(A) |
| 6.1 | 1+round2 | task6_phase6_1_bug_flow_entry_*_review_*.md | (B)→(A) |
| 6.2 | 1 + 3 Low polish | task6_phase6_2_bug_rework_review_*.md | (A) |
| 6.3 | 1+2 + 1 doc-fix | task6_phase6_3_incident_*_review_*.md | (B)→(A) |
| 6.4 | 1+2 | task6_phase6_4_advance_consistency_*_review_*.md | (B)→(A) |

**Task 6 实现整体（A）闭环**。

---

## 4. Phase 7 Scope

### 4.1 Item 1: Re-confirm baseline

只是 sanity：

```bash
python3 -m unittest discover -s tests           # 期望 781 OK
python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
test ! -e progress.md && test ! -e progress-history.md
```

如果有任何 regression（不应该有），先解决再继续。

### 4.2 Item 2: Managed-project happy-path smoke（核心新工作）

**目标**：在 `tempfile.TemporaryDirectory` 隔离下，模拟一个真实的 S1 项目从 `init` 走到 `release-close`，所有命令都用真 doc fixtures（不 mock validate_doc），验证 happy path 全链路通过。

**Scope**：S1 (从 0 打造) 全程：

```
init S1 release=0.1
    ↓
prd-inception write → write-complete → review-passed → human-confirmed → update --advance
    ↓
srs-specification write → write-complete → review-passed → human-confirmed → update --advance
    ↓
architecture-design write → write-complete → review-passed → human-confirmed → update --advance
    ↓
development write → (per-task: planning-done → test-writing → ... → verified) × N → update --advance
    ↓
testing write → write-complete → review-passed → update --advance
    ↓
delivery write → write-complete → review-passed → update --advance
    ↓
project-retrospective write → write-complete → review-passed → release-close
```

**实现方式**：写 `tests/test_smoke_managed_project.py`（**新文件**），里面一个或几个长 testcase 把全流程串起来。每步都构造合规 doc fixtures（含 frontmatter + Change Log），让 doc-guardian validate.py file 真实通过；不允许 patch validate_doc。

**Bug Flow / Incident smoke**（次要但应有）：
- S1 主线后再加 1 个 testcase: 走到 testing 阶段后注入 BUG（root_cause=development），走 bug-start → 修复 → bug-close → 退回 testing pass → advance；这测 Bug Flow + Gap-4 dev rollback 真实链路
- 1 个 testcase: PRD-exception path → incident-start → workflow-evolution finalization → incident-resolve --action continue → 回 testing；测 incident lifecycle 真实链路

**S2 / S3 smoke**：可选；spec 上 S1 全程是必备，S2/S3 的 release-start 通过现有 `tests/test_progress_release_lifecycle.py` 已 cover 入口。Phase 7 主线先把 S1 走通；S2/S3 端到端如果时间允许加 1 testcase（从 close 走 release-start 后 SRS 增量）。

**Acceptance**：
- 新增 1 个 smoke 测试文件，至少 3 testcases（S1 main + Bug Flow + Incident），全部用真 doc fixtures + validate.py 真校验
- 全套测试 781 + new ≈ 790+，全过
- compileall 干净
- 发现的任何 reference 用词不准确处 → 加入 Phase 7 Item 3 修复列表

**重要约束**：
- smoke 测试**必须**用 `_FakeClock` patch（保证 timestamp 稳定）+ `tempfile.TemporaryDirectory` 隔离
- 不能 mock progress_lock / validate_doc（要真跑全链路）
- 每步如果失败给出具体 stderr + 当前 progress.md 状态便于 debug
- 测试文件名 `test_smoke_managed_project.py`（与现有 `test_progress_*` 命名风格一致）

### 4.3 Item 3: Reference wording polish

实现过程中已经积累了一些 reference vs implementation 的用词漂移（部分已在 Phase 6.x round 2 修），但仍有遗漏。Phase 7 启动后系统性扫一遍：

**应该 grep / 扫的位置**：
- `skills/workflow-protocol/references/command-reference.md`（全文，但重点 §11/§12 incident + §2.2 advance 已 polish 过，新一轮主要看 §1-§10 是否有 stale wording）
- `skills/workflow-protocol/SKILL.md`（P6 matrix 已修；但 §1-§4 / §6+ 可能漏）
- `skills/doc-guardian/references/required-artifacts.md`（§12 consistency algorithm sketch 现已被 Phase 6.4 实现，可能需要更新 prose）
- `skills/doc-guardian/references/frontmatter-schema.md`（与 Phase 6.x 加 strict 校验后的实际行为对齐）
- `skills/doc-guardian/references/directory-layout.md`（与 _PATH_TEMPLATES 实际包含 7 类 doc 对齐）
- `skills/doc-guardian/SKILL.md`（command matrix 是否含 consistency 实装状态）
- `docs/implementation/task6_plan_20260507.md`（§5 / §6 / §7 等实现节，最终描述与代码对齐）
- 历史 review prompts 已经标注的 Open Questions 是否还有未消化的 prose

**做法**：每发现一处不准确就 inline 修，commit 时附 1-2 行说明（Phase 7 polish: <reason>）。不要把 polish 当作大重写——只调用词，不改语义。

**界限**：
- 不动 design decision（不 re-litigate 已闭合的争议）
- 不引入新概念
- 不把 Phase 7 polish 滑入 Phase 8 / Task 7+ 设计讨论

### 4.4 Item 4: Entry docs + Task 6 closure handoff

**Entry docs**（v4 §7.4 列出但 Task 6 实现期没动）：
- `AGENTS.md`（root）—— Codex / agent-tooling 入口；当前 repo 尚无
- `CLAUDE.md`（root）—— Claude Code / agent 入口；当前 repo 尚无
- `.codex-plugin/plugin.json` 或 plugin marketplace metadata —— 仅当 user 决定项目目标仍是 Codex plugin 才做；handoff 不强制

参考 v4 §5 D1/D2/D3：
- D1 doc 校验 = doc-guardian binary（已实现）
- D2 CLAUDE.md 形态 = foreman 模式：CLAUDE.md = `@AGENTS.md` + AGENTS.md 治理层 + workflow-protocol skill 操作层
- D3 SessionStart Hook = 不要

所以最小 entry docs：

**`AGENTS.md`** 内容草案（最简版）：
```markdown
# AGENTS.md

This project follows the dev-workflow-skills2 workflow specification.

## When you start a session

1. Read the active project's `progress.md` and `progress-history.md` (if they exist).
2. Determine current_stage, sub_state, and any active bug_flow / incident state.
3. The state machine is owned by `skills/workflow-protocol/scripts/progress.py`.
   Do NOT hand-edit progress.md / progress-history.md — every mutation goes
   through progress.py subcommands.
4. Doc validation is owned by `skills/doc-guardian/scripts/validate.py`.

## Mandatory contracts

- Never bypass `progress.py` for state mutations.
- Never bypass `validate.py file` for doc-guardian checks before committing a doc.
- Refer to `skills/workflow-protocol/references/command-reference.md` for all
  state transitions.
- Refer to `skills/doc-guardian/references/` for frontmatter schema, directory
  layout, required-artifacts P6 matrix, and change-log format.

## Workflow specification source of truth

- `docs/workflow/workflow_specification_claude.md` (v0.2 merged) — top-level
  workflow including 7 stages, 4 scenarios, Bug Flow, Incident Flow.
- `docs/implementation/task6_plan_20260507.md` — implementation plan for the
  scripts behind workflow-protocol + doc-guardian skills.
```

**`CLAUDE.md`** 内容草案：
```markdown
# CLAUDE.md

@AGENTS.md
```

或如果 v4 D2 的 foreman 模式更严格，CLAUDE.md 可以用：
```markdown
# CLAUDE.md

This file is auto-loaded by Claude Code at session start.

@AGENTS.md
```

具体哪个 minimal 形态用户决定 — 在 §6 work order 让 user 选。

**Task 6 closure handoff**（`docs/handoff/session_handoff_task6_closed_<date>.md`）：
- 全 Task 6 交付清单（implementation + tests + reviews + 经验教训）
- Phase 6.x 留下的 hardening options（见 §7）
- 下一阶段 scope 候选（Task 7+: vertical skill 实现 / 或 user 决定其它优先级）
- 建议下一 session 第一条用户指令

---

## 5. Code Patterns to Follow（Phase 7 不引入新模式）

Phase 7 主体是测试 + doc 修，所以遵循已建立的 §5 patterns：

- 测试用 `tempfile.TemporaryDirectory()` + `_FakeClock` + 真实 fixture
- doc 修只调用词、不改 spec
- entry docs 用 v4 §5 决定的最小形态（CLAUDE.md → @AGENTS.md → workflow-protocol skill）

---

## 6. Recommended Phase 7 Work Order

**步骤 1**: re-confirm baseline（5 分钟）

```bash
python3 -m unittest discover -s tests | tail -3
python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
test ! -e progress.md && test ! -e progress-history.md
```

期望：781 OK + compileall 干净 + ROOT CLEAN。任何不符立刻 stop，先 debug 再继续。

**步骤 2**: 写 smoke 测试 — `tests/test_smoke_managed_project.py`（核心，**最大工作量**）

子步骤：
- 2a 设计 fixture helpers（写 PRD/SRS/Architecture/Development plan/Test report 等的 minimal 合规 frontmatter）
- 2b S1 main happy path testcase
- 2c Bug Flow with Gap-4 dev rollback testcase
- 2d Incident continue testcase
- 2e（可选）S2-1 增量 release testcase
- 2f run + iterate

每步遇到失败 → 检查 stderr → 一般 3 类原因：(a) reference 描述与代码不符（→ Item 3 polish 列表）/ (b) fixture 缺字段（→ 调 fixture）/ (c) 真 bug（→ 罕见，但若是真 bug 必须先 root cause + 决定是 Phase 7 修还是回滚到 Phase 6.x re-open）。

**步骤 3**: 询问 user 决定 entry docs 形态

提供 2 个备选：
- A: 最小双文件（AGENTS.md + CLAUDE.md → @AGENTS.md）—— 推荐
- B: 仅 AGENTS.md（CLAUDE.md 由 Claude Code 默认行为加载 AGENTS.md）

**步骤 4**: 写 entry docs（按 user 选）

**步骤 5**: 跑一遍 reference wording 扫描（Phase 7 Item 3）

逐文件 grep + 修。每个 commit 写清原因。

**步骤 6**: 写 Task 6 closure handoff `docs/handoff/session_handoff_task6_closed_<date>.md`

包含：
- Task 6 全 6 phase 交付清单
- 781 测试 + 14 review reports 总览
- §7 hardening options 清单
- 下一 task scope 候选

**步骤 7**: 写 Phase 7 review prompt（如果 user 想走 review cycle 才做）

可选：Phase 7 主要是 smoke + docs，未必需要正式 review；如果 user 不要走 review，可跳过这步直接报告 Task 6 closure。

**Phase 7 acceptance**：
- ✅ 781 → 790+ tests 全过（smoke 加 3-5 testcases）
- ✅ compileall 干净
- ✅ AGENTS.md / CLAUDE.md 创建
- ✅ 所有 reference wording 与实现对齐
- ✅ Task 6 closure handoff 完成
- ✅ no repo-root progress.md / progress-history.md leak

---

## 7. Open Hardening Options（Phase 7 决定哪些升入 scope）

汇总 Phase 6.1-6.4 review 留下的所有 non-blocking 选项，按可能价值排：

### 7.1 Higher-value hardening（建议 Phase 7 做或明确 defer）

1. **`from=` token 严格校验**（Phase 6.4 review 提到）：当前 `_apply_update_advance_handler` 仅 presence-check `from=`；可加显式比较 `tokens["from"] == state["current_stage"]` 防 hand-authored history 篡改。1-line + 1 test。
2. **`root_cause=prd-exception` token 严格校验**（Phase 6.3 review L1 wording 留下）：当前 `_apply_incident_start_handler` 也仅 presence-check `root_cause=`；同上 1-line + 1 test。
3. **`validate_doc` 防御 ImportError**（Phase 6.3 round 1 open question）：当前 progress.py `validate_doc` lazy import `validate` 模块时若 ImportError 直接抛；可改为捕获 + 返回 list[str] 让 progress.py 走 exit-1 路径。视为安装问题就保持 hard fail；视为 user-facing rare error 就改。

### 7.2 Lower-value hardening（建议 defer 到 Task 7+ 或 v0.7 spec）

4. **`_INCIDENT_RESOLVE_ACTIONS` public 化**（Phase 6.3 open question）：仅当 vertical skills 或外部 tooling 需要消费 enum 才必要。
5. **更广义 Class 8 consistency check**（Phase 6.4 review 提到）：含 progress.md current_stage / sub_state 与 doc statuses 兼容性、Stage 4 task counts 与 breakdown.total_tasks 一致性。当前 Class 8 只校 required-artifact 存在 + 文件级合规，未覆盖 cross-field consistency。这是真正的 v0.7 / Task 7+ 工作。
6. **Stage 4 → 5 advance 时再读 per-task verification_result.md**（Phase 6.4 prompt 标 deferred）：当前用 surrogate "all task_states verified"；额外 defense-in-depth 但增加 advance 成本。
7. **`progress.md artifacts:` dict per-stage mutation**（Phase 6.4 user 决定 defer）：advance 时给新 stage 添加默认 mutable artifact entries。涉及 stage skill / progress.md schema 变化，应当配套 stage skill 实现一并设计。
8. **`validate.py all`** subcommand: full-project sweep over every doc type. Phase 7 内部仍 deferred；v0.7 时实现。

### 7.3 不再考虑 / closed

- Gap-1 reopen event（v4 §6 / task6_plan §14 #4：用户已决定 keep out of MVP）。
- 历史 prose-only entries 自动 infer（v4 §14 #5：MVP recover reject 而非 infer）。

---

## 8. Watch Points / Common Pitfalls

- **Phase 6.x 已闭合的设计决定不要 re-open**。Open Questions 列表中的 hardening 是 strict 选项，做与不做都 OK；做了别 re-open 已 (A) 部分。
- **Smoke 测试要用真 doc fixtures**——不要 patch validate_doc / validate_file / progress_lock。Phase 6.x 的单元 + CLI 测试已经把 mock 路径覆盖完了；Phase 7 smoke 的价值就在真链路。
- **Phase 7 不要扩 progress_state.py / progress_replay.py 的 apply / handler 数量**。15 events / 11 apply 是 Task 6 的 final state。如发现真 bug 需要新 event/handler 才能修，先 root cause 是不是 Phase 6.x 设计漏洞 → 走 round-3 fix 再回到 Phase 7。
- **Entry docs 别写得太多**。AGENTS.md ~50 行 / CLAUDE.md 一行 `@AGENTS.md` 就够。具体内容由 user 决定，handoff §4.4 给的草案是参考起点。
- **reference wording 扫描别变成大重写**。每处只调用词。
- **Task 6 closure handoff 要列 exhaustively**。但是要保持简洁：表格 + 链接，而非长 prose。下一 session 才能在合理时间把全 Task 6 状态吸收完。
- **`progress.md artifacts:` dict 不动**：Phase 6.4 user 决定保留 spec 模糊性；smoke 测试中如果命中"advance 后 artifacts: dict 是否应增字段"问题，记入 Open Hardening §7.2 而不是临时改实现。
- **Stage 4 smoke 复杂度高**：development 阶段每个 task 4 类 artifact + 4 transitions（planning-done → test-writing → test-review → test-done → code-writing → code-review → code-review-passed → verifying → verified），fixture 量大；建议 smoke 只做 1 个 task 走全程，不要做 N 个 task 满矩阵。
- **不要在 smoke 中调 `release-start`** 除非已经 release-close 当前 release；S1 main 路径只是 0.1 单 release。S2 测试需要先 release-close 再 release-start，是另一独立 testcase。
- **`progress_history.py` field 白名单仍是 `agent / result / next`**，不要加新字段。

---

## 9. Reference Anchors

### 9.1 全 Task 6 实现锚点（quick lookup）

| 概念 | 文件 | 函数 / 字段 |
|------|------|-------------|
| 11 apply_* state machines | `progress_state.py` | `build_initial_state` / `apply_update_event` / `apply_update_task` / `apply_release_close` / `apply_release_start` / `apply_bug_intake` / `apply_bug_start` / `apply_bug_close` / `apply_bug_rework` / `apply_incident_start` / `apply_incident_resolve` / `apply_update_advance` |
| 15 replay handlers | `progress_replay.py` | `_HANDLERS` dict; `supported_events()` |
| Terminal gate | `progress_replay.py` | `TERMINAL_EVENTS = {"incident-resolve"}` + `TERMINAL_INCIDENT_ACTIONS = {"abort", "reconstruct"}` + `replay_history` action-aware logic |
| Shared Gap-4 helper | `progress_state.py` | `compute_dev_bug_rollback(state, triage)` |
| Doc path shape | `progress_state.py` | `_validate_doc_path_shape` (private helper) + `_validate_bug_path_shape` / `_validate_incident_path_shape` (public wrappers) |
| Artifact loader | `progress_artifacts.py` | `_PATH_TEMPLATES` (7 doc types) + `load_artifact_frontmatter` / `load_test_report` / `load_bug_report` / `parse_bug_triage_analysis` |
| P6 matrix DSL | `_shared/conditions.py` + `_shared/artifacts.py` | `evaluate(ast, vars)` + `get_required_artifacts(progress, root)` + `progress_from_mapping(progress)` |
| validate.py 8 classes | `validate.py` | classes 1-7 = `validate_file`; class 8 = `check_consistency` |
| Atomic update pipeline | `progress.py` | `_run_update_pipeline(args, root, event_name, compute_outcome, ...)` |
| Locked compute_outcome 模式 | `progress.py` | `_advance_compute_outcome` + `_run_p6_advance_preflight`（Phase 6.4 round 2 引入） |
| Lock | `progress_lock.py` | `progress_lock(root, *, timeout)` |
| History serialization | `progress_history.py` | `parse_history_text` / `append_history_text` / 字段白名单 |

### 9.2 Phase 7 重要文件位置（创建 / 编辑）

| Phase 7 写集候选 | 路径 | 说明 |
|-------------|------|------|
| smoke 测试 | `tests/test_smoke_managed_project.py` | NEW — 步骤 2 |
| AGENTS.md | `AGENTS.md` (repo root) | NEW — 步骤 4 |
| CLAUDE.md | `CLAUDE.md` (repo root) | NEW — 步骤 4 |
| reference polish | scattered（步骤 5 决定） | EDIT — 步骤 5 |
| Task 6 closure handoff | `docs/handoff/session_handoff_task6_closed_<date>.md` | NEW — 步骤 6 |
| Phase 7 review prompt | `docs/review/claude_review_prompt_task6_phase7_*.md` | OPTIONAL — 步骤 7 |

### 9.3 完整 review 报告 trail（14 份）

详见 §3 表格 + `docs/review/` 目录。

---

## 10. Final Checklist Before New Session Codes

新 session 应：

- [ ] 读 §0 列出的 8 项（含 review 报告 + Phase 7 spec + open hardening 列表）
- [ ] 跑 `python3 -m unittest discover -s tests` 确认 781 OK + compileall 干净 + ROOT CLEAN
- [ ] 决定 §7 Open Hardening 哪些升 Phase 7 scope（推荐 7.1 #1-#3 任选其一或全部；7.2 全部 defer 到 Task 7+）
- [ ] 决定 entry docs 是 §4.4 中 A 或 B 形态
- [ ] **核心工作**：写 `tests/test_smoke_managed_project.py`，至少 3 testcases（S1 main + Bug Flow + Incident continue），用真 doc fixtures
- [ ] 跑 reference wording polish 扫描（Phase 7 Item 3）
- [ ] 写 entry docs
- [ ] 写 Task 6 closure handoff
- [ ] （可选）写 Phase 7 review prompt 走 review cycle

**当 Phase 7 全部完成后**，user 决定下一阶段 scope：
- **Task 7+**: 实现 vertical skills（PRD/SRS/Architecture/Development/Testing/Delivery/Retrospective × write+review × scenario）
- 或：dogfood 当前 Task 6 交付，用 Claude Code 真实跑一个项目 → 暴露的 issues 反馈给 v0.7 spec 再开 Task 7+
- 或：user 决定的其它优先级

---

## 11. 给新 session 的第一条用户指令建议

可以直接让新 session 这样开场：

> 请读取 `docs/handoff/session_handoff_task6_phase7_20260507.md`，然后按 §6 work order 开始 Phase 7：
>
> 步骤 1（confirm baseline）+ 步骤 2（写 `tests/test_smoke_managed_project.py` 至少 S1 main + Bug Flow + Incident 3 个 testcase，用真 doc fixtures，不 mock validate_doc / progress_lock）。
>
> 完成步骤 2 后报告 smoke test 跑通的结果（含发现的任何 reference wording polish 候选），由我决定后续 entry docs / reference polish / Task 6 closure handoff 怎么做。


