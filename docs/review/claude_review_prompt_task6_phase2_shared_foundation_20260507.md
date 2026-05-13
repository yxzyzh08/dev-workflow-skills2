# Claude Review Prompt — Task 6 Phase 2 Shared Foundation

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成代码审查，并把评审报告保存到 `docs/review/task6_phase2_shared_foundation_review_20260507.md`。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 2 shared foundation implementation** 做一次代码 review。目标是在继续 Phase 3（`changelog.py` + `validate.py file`）之前，先确认刚新增的共享 Python foundation 是否正确、可维护、符合 references 和 Task 6 plan。

本轮是代码 review，但范围仅限共享模块和对应 unit tests。不要要求 `progress.py` / `validate.py` / `changelog.py` / `status_transition.py` CLI 已存在；这些是 Phase 3+ 的实现范围。请重点找 bug、spec mismatch、边界遗漏、测试不足、未来实现会被误导的 API 设计问题。

## 当前工作背景

项目根：`/home/cgs/github_projects/dev-workflow-skills2/`

Task 6 Phase 1 docs alignment 已经通过 Claude review：

- Review report: `docs/review/task6_phase1_docs_alignment_review_20260507.md`
- Recommendation: `(A) accept and proceed to Phase 2 shared foundation implementation`
- 3 个 Low 已由 Codex 修复：
  - design proposal 中 progress.py 11→12 命令 patch note
  - prerequisites 中 `bug-rework` 文案从 “exists” 改为 “script lands in Phase 5/6”
  - Task 6 plan Gap-4 ambiguous classification wording
  - 另加 bug-triage active retest fail/partial 不重 triage 边界说明

Phase 2 已新增共享 Python 模块与 focused unit tests。当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 18 tests ... OK

python3 -m compileall -q skills/_shared tests
# OK
```

## 本轮 Review Target

### Shared Foundation Modules

请重点审查：

- `skills/_shared/dev_workflow/__init__.py`
- `skills/_shared/dev_workflow/frontmatter.py`
- `skills/_shared/dev_workflow/markdown.py`
- `skills/_shared/dev_workflow/atomic.py`
- `skills/_shared/dev_workflow/conditions.py`
- `skills/_shared/dev_workflow/artifacts.py`
- `skills/_shared/dev_workflow/progress_state.py`
- `skills/_shared/dev_workflow/schema.py`

### Unit Tests

请审查测试是否覆盖 Phase 2 acceptance：

- `tests/test_frontmatter_markdown_atomic.py`
- `tests/test_conditions_artifacts.py`
- `tests/test_progress_schema.py`

## 必读参考材料

请按以下顺序阅读：

1. `docs/implementation/task6_plan_20260507.md`
   - 尤其 §3.2 shared modules、§10 Required Artifacts and Condition DSL、§12 Test Strategy、§13 Phase 2 acceptance。
2. `docs/review/task6_phase1_docs_alignment_review_20260507.md`
3. `skills/doc-guardian/references/required-artifacts.md`
   - 尤其 Condition DSL 规范、parser test cases、Stage 4 per-task required artifacts。
4. `skills/doc-guardian/references/frontmatter-schema.md`
5. `skills/doc-guardian/references/directory-layout.md`
6. `skills/doc-guardian/references/change-log-format.md`
7. `skills/workflow-protocol/references/command-reference.md`
   - 尤其 event whitelist、Stage 4 task transitions、Gap-3/4/5。
8. `skills/workflow-protocol/SKILL.md`
9. `skills/doc-guardian/SKILL.md`

可选：

- `docs/handoff/task6_progress_py_prerequisites_20260506.md`
- `docs/handoff/session_handoff_20260506_v4.md`

## Review Focus Areas

### A. frontmatter.py

检查：

- 是否正确解析 `---` YAML frontmatter + body？
- 是否拒绝缺失 opening / closing delimiter？
- 是否避免 PyYAML 自动把 ISO8601 timestamp 转成 datetime？这是 schema 要求 timestamp 字符串校验的关键。
- 是否保持 `release: "0.1"` 为字符串，并允许 validate.py 后续拒绝 float release？
- `render_markdown` 是否会生成合法 frontmatter 结构？
- 是否存在 body 前导换行、closing delimiter 单独成行、CRLF normalization 等隐患？

### B. markdown.py

检查：

- `find_section` 是否按 “下一个 same/higher heading” 截断 section？
- 对 `## Pending Changes` / `## Change Log` 的 replace 是否保留后续 section？
- `non_comment_lines` 是否符合 change-log-format 对 Pending Changes 空章节的定义（允许空白和 HTML comments）？
- 是否有 heading 同名、嵌套 heading、文件末尾无 newline 等边界问题需要补测？

### C. atomic.py

检查：

- `atomic_write_text` 是否使用 temp file + fsync + `os.replace`？
- `AtomicTransaction` rollback 是否能恢复已有文件并删除新建文件？
- 多文件 transaction 是否足以支撑后续 `status_transition.py` 和 `release-start` BUG frontmatter updates？
- 是否有目录 fsync、backup cleanup、Windows path、权限错误等重要风险？当前目标环境是 Linux/bash。

### D. conditions.py

这是本轮重点。检查 Condition DSL parser 是否严格匹配 `required-artifacts.md`：

- 允许变量是否只包含：
  - `scenario`
  - `scenario_subtype`
  - `current_stage`
  - `release`
  - `srs.is_multi_module`
  - `srs.architecture_change`
- 是否禁止 `eval` / `exec` / `ast.literal_eval`？
- 是否支持 `==`, `!=`, `&&`, `||`, parentheses？
- precedence 是否正确：`&&` 高于 `||`？
- 是否 reject unknown variable，如 `srs.unknown_field == true`？
- 是否 reject function call，如 `is_admin(scenario)`？
- 是否 reject unknown enum literal，如 `current_stage == not-a-stage`？
- 是否 reject assignment `scenario = S3`？
- 是否按 spec 处理 quoted enum：`scenario == "S3"` 应 reject。
- 是否正确处理 hyphenated enum literal 仅 RHS 合法？
- 是否错误接受 hyphenated variable / identifier？
- 是否正确处理 `scenario_subtype` 为 null 的比较边界？如果当前 DSL 没有 null literal，这是否与 references 一致？

请特别留意：`required-artifacts.md` 的 parser test case 3 是 `(scenario == S2) && (current_stage == srs-specification)`；当前 tests 里既有 `||` case，也用 scenario override 覆盖 `&&` true case。判断是否足够。

### E. artifacts.py

检查：

- `REQUIRED_ARTIFACTS` 是否与 `skills/doc-guardian/references/required-artifacts.md` 完全一致？
- Stage mapping 是否正确：
  - `prd-inception -> prd_inception`
  - `srs-specification -> srs_specification`
  - `architecture-design -> architecture_design`
  - `development -> development_stage_level + development_per_task`
  - `testing`, `delivery`, `project-retrospective`
- S3 Stage 1 是否包含 PRD + prd-level + feature-matrix？
- S3 Stage 2 是否包含 SRS + Acceptance + srs-level + module-level + reuse-replace，technical-debt 不必备？
- `srs.is_multi_module` 是否触发 Integration Plan？
- `srs.architecture_change` 是否触发 Architecture Delta？
- Stage 4 advance 是否无条件包含每个 task 的 4 个 per-task artifacts？
- `workflow_incident_analysis` 特殊 stage 当前返回 empty list 是否可接受？required-artifacts.md 说 incident 不走 P6 matrix，incident path 由 `progress.md incident_report_path` 指定。请判断是否需要更明确的 handling 或 docstring。
- `read_srs_condition_fields` 在 SRS exists 但 field 缺失时默认 false。Reference 表说 default false if SRS missing or field missing；frontmatter-schema 又要求字段必含。请判断当前 behavior 是否 acceptable for resolver vs validate.py later responsibility。
- 是否需要 preserve artifact metadata like `condition` in rendered artifacts？当前 rendered spec keeps original condition; assess if useful/confusing.

### F. progress_state.py

检查：

- Event whitelist 是否只有 4 个 events，没有 `issues-found`？
- Stage order / next stage 是否符合 workflow-protocol？
- Root cause to stage mapping 是否 excludes `prd-exception`（incident path special）？
- Stage 4 task transitions 是否包含 normal path + Gap-3 + Gap-4 protected transitions？
- 是否过度暴露 Gap-4 transitions as generic `is_valid_task_transition` without context/precondition? Future `progress.py update --task` must enforce protected owner/preconditions; assess whether comments/API should warn implementer.

### G. schema.py

检查：

- Incremental vs snapshot doc type classification 是否与 `change-log-format.md` 一致？
- Universal fields / status / gated approved types 是否与 frontmatter-schema 一致？
- Per-type required fields 是否覆盖 frontmatter-schema §5 table？
- Optional PRD supporting doc fields：当前 competitor / market / non-goals 等只 require universal。是否与 frontmatter-schema §3.5 PRD Supporting Artifacts 一致？
- `TYPE_PATHS` / `SOURCE_ANALYSIS_PATHS` 是否与 directory-layout.md 一致？
- 是否遗漏 `source-system-analysis` path handling in `TYPE_PATHS` because it is separately mapped? That is acceptable only if later validate.py uses `SOURCE_ANALYSIS_PATHS`.

### H. Tests

检查：

- 是否足以证明 Phase 2 acceptance？
- 是否应增加 tests for:
  - `scenario == S3 && current_stage == srs-specification` exact parser case
  - `srs.detail.is_multi == true` rejects property chain > 2
  - hyphenated token as variable rejects
  - Stage 3 architecture delta false path
  - S1/S2 no S3 source-system artifacts
  - Markdown nested headings / same-level cutoff
  - AtomicTransaction rollback after second write failure simulation
- 不要求补所有低价值 tests，但请指出哪些测试缺失会影响 Phase 3 confidence。

## Important Constraints

- Do not implement fixes unless explicitly asked; this review should produce findings only and save the report.
- Do not delete untracked `docs/`, `skills/`, or `tests/` files.
- Do not mutate `progress.md` / `progress-history.md` if present.
- Do not treat missing runtime CLI scripts as findings; they are Phase 3+.
- Review with a code-review mindset: bugs, spec mismatches, behavioral regressions, missing tests.

## Output Requirements

请把评审报告保存到：

`docs/review/task6_phase2_shared_foundation_review_20260507.md`

请使用以下格式：

```markdown
# Task 6 Phase 2 Shared Foundation Review

**Review Target**: `skills/_shared/dev_workflow/*.py` + `tests/test_*.py`
**Review Date**: 2026-05-07
**Reviewer**: Claude
**Baseline**: Task 6 Phase 1 accepted docs + Task 6 implementation plan Phase 2
**Recommendation**: (A) accept and proceed to Phase 3 / (B) fix before Phase 3 / (C) revisit design
**Status**: findings: <H/M/L counts>; blockers: <yes/no>

## Executive Summary

[2-5 bullets. State clearly whether Phase 3 may proceed.]

## Findings

[Primary output. List findings ordered High → Medium → Low. For each finding include:]

### <Severity>: <Title>

- **Location**: `<file>:<line>`
- **Issue**: ...
- **Impact**: ...
- **Recommendation**: ...

If no findings, explicitly state: “No blocking or non-blocking findings discovered.”

## Checklist Results

| Area | Status | Notes |
|------|--------|-------|
| frontmatter.py | ✅/⚠️/❌ | ... |
| markdown.py | ✅/⚠️/❌ | ... |
| atomic.py | ✅/⚠️/❌ | ... |
| conditions.py DSL | ✅/⚠️/❌ | ... |
| artifacts.py required artifacts | ✅/⚠️/❌ | ... |
| progress_state.py constants | ✅/⚠️/❌ | ... |
| schema.py constants | ✅/⚠️/❌ | ... |
| unit tests | ✅/⚠️/❌ | ... |

## Open Questions / Assumptions

[Only if needed.]

## Recommendation

[Choose A/B/C. If A, say: “Proceed to Phase 3 changelog.py + validate.py file implementation.” If B/C, list exact files that must be fixed first.]
```
