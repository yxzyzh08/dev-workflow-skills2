# Claude Review Prompt — Task 6 Phase 3 changelog.py + validate.py

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成代码审查，并把评审报告保存到 `docs/review/task6_phase3_changelog_validate_review_20260507.md`。评审通过后才能进入 Phase 4 (`status_transition.py`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 3 implementation** 做一次代码 review。目标是在继续 Phase 4（`status_transition.py`）之前，先确认刚新增的 doc-guardian binary 校验脚本（`changelog.py` + `validate.py file/ids`）是否正确、可维护、符合 references 与 Task 6 plan。

本轮是代码 review。范围仅限：
- 新增 shared module `skills/_shared/dev_workflow/changelog.py`
- 新增 CLI `skills/doc-guardian/scripts/changelog.py`
- 新增 CLI `skills/doc-guardian/scripts/validate.py`
- 新增 tests `tests/test_changelog.py` + `tests/test_validate_file.py`

**不要**要求 `status_transition.py` / `progress.py` 已实现 — 那些是 Phase 4 / 5 / 6 的范围。Phase 3 也明确**不**实现 `validate.py all` 与 `validate.py consistency`（仅 stub 返回 exit 2 + deferred 提示，因为这两个 subcommand 依赖 progress.py）。

## 当前工作背景

项目根：`/home/cgs/github_projects/dev-workflow-skills2/`

Task 6 Phase 1（docs alignment）和 Phase 2（shared foundation）均已通过 Claude review：

- Phase 1 review: `docs/review/task6_phase1_docs_alignment_review_20260507.md`（accept）
- Phase 2 round 1 review: `docs/review/task6_phase2_shared_foundation_review_20260507.md`（accept Phase 3，预留 Phase 4/5/6 fix points）
- Phase 2 round 2 regression review: `docs/review/task6_phase2_shared_foundation_round2_review_20260507.md`（accept）
- 已采纳的 Round 2 后 trivial fixes：
  - `tests/test_conditions_artifacts.py` precedence test 加入 discriminator case
  - `skills/_shared/dev_workflow/atomic.py` cleanup 改为只 catch OSError
  - `skills/_shared/dev_workflow/markdown.py` docstring 显式 multi-line comment 限制

Phase 3 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 91 tests in 0.095s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK
```

## 阅读顺序（请严格按序读，不要跳读）

1. `docs/handoff/session_handoff_task6_phase3_20260507.md` — Phase 3 起点 & 约束
2. `docs/implementation/task6_plan_20260507.md` — 总实施计划（§7-§8 是 Phase 3 关键章节）
3. `docs/review/task6_phase2_shared_foundation_round2_review_20260507.md` — Phase 2 acceptance + 残留 Low
4. `skills/doc-guardian/references/change-log-format.md`
5. `skills/doc-guardian/references/frontmatter-schema.md`
6. `skills/doc-guardian/references/directory-layout.md`
7. `skills/doc-guardian/references/required-artifacts.md`（Phase 3 仅需扫一眼，仍是 Phase 4/5/6 数据源）
8. `skills/doc-guardian/SKILL.md`
9. `skills/_shared/dev_workflow/changelog.py`（新）
10. `skills/_shared/dev_workflow/__init__.py`（已加 `changelog` 进 `__all__`）
11. `skills/doc-guardian/scripts/changelog.py`（新）
12. `skills/doc-guardian/scripts/validate.py`（新）
13. `tests/test_changelog.py`（新）
14. `tests/test_validate_file.py`（新）

可选背景：

- `skills/_shared/dev_workflow/{frontmatter,markdown,atomic,schema}.py`（Phase 2 已 review 过；Phase 3 复用，未修改）

## Phase 3 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 3 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。
2. 工作树大量 untracked 是项目内容，不得 delete/clean/reset/revert。
3. tests 必须用 temp dirs / fixtures，不得 mutate 真实 `docs/` / `skills/` 当 managed project。
4. **写集** 仅限：
   - `skills/_shared/dev_workflow/changelog.py`
   - `skills/_shared/dev_workflow/__init__.py`（`__all__` 加 changelog）
   - `skills/doc-guardian/scripts/changelog.py`
   - `skills/doc-guardian/scripts/validate.py`
   - `tests/test_changelog.py`
   - `tests/test_validate_file.py`
5. `progress.py` / `status_transition.py` / `validate.py consistency` 不在 Phase 3 范围。Phase 3 stub 了 `validate.py all` 与 `validate.py consistency`，CLI 命中时 exit 2 并打印 deferred message。
6. event whitelist 仍精确为 `write-complete` / `review-issues` / `review-passed` / `human-confirmed`；`issues-found` 是业务措辞、不是 event。
7. `bug-rework` 是 active Bug Flow retest fail/partial 专用命令；本 Phase 不实现。

## 重点 review 项

请按以下维度逐条核对，不要跳过：

### A. shared `changelog.py` (`skills/_shared/dev_workflow/changelog.py`)

- 入口函数 `parse_pending_section` / `parse_changelog_section` / `merge_groups` / `render_changelog_body` / `promote_text` / `validate_text` 是否纯 in-memory（无 file IO）？
- entry regex `^- {timestamp} \[{section_ref}\]: {summary}$` 与 change-log-format.md §2.2 的字面量是否一致：
  - timestamp 必带 `Z`、必精确到秒
  - section_ref ∈ `Section X` / `Section X.Y` / `frontmatter` / `全文`
  - summary 必非空（regex 要求 `\S` 起始）
- date heading regex `^### (\d{4}-\d{2}-\d{2})$` 是否完整匹配 §3.1？
- promote_text 对 unknown doc type / incremental 缺章节 / pending 中非法 entry / changelog 中非法 entry 是否都 raise `ChangelogError`？
- promote_text 对 snapshot 类 doc 在两个 section 都存在时是否仍执行 promote（spec §1 + handoff §5.2）？两个 section 都缺时是否 no-op？
- merge_groups 是否：(a) 同日期 entries 合并到同一 group、(b) 同 group 内按 timestamp 升序、(c) date group 整体按日期降序？render_changelog_body 是否符合 spec §3.1 的 `### YYYY-MM-DD` + 空行 + entries 排版？
- validate_text 是否独立于 promote_text 工作（即 caller 可以只 validate 不 promote）？snapshot doc 缺 section 时是否不报错？incremental doc 缺 section 时是否报 “Missing '## ...'”？
- 时间单调性：`Change Log entries within ... must be ascending` 是否真的逐 entry 比较 timestamp？date 单调性：`date groups must be sorted descending` 是否在 `date >= prev_date` 时报（即既禁等又禁升）？
- 是否存在通过编辑 `## Change Log` 章节 / 不调 `promote` 直接写 entry 来 silent 通过的可能？validate_text 至少能在 entry 格式不严格、heading 不严格、单调性不对时报错。

### B. CLI `skills/doc-guardian/scripts/changelog.py`

- `--root` 默认 cwd；relative doc 路径相对 `--root` 解析；absolute doc 路径直接使用 — 行为是否清晰？
- `validate` 子命令仅 read，不写；任何 issue → exit 1 + stderr 列条目。
- `promote` 子命令：
  - 读 file → in-memory promote → atomic_write_text 写回 → 重 validate；
  - pending 为空时 no-op、不写文件；
  - in-memory promote 失败时不写文件；
  - 写后 validate 失败时返回 exit 1 + 提示（这是 Phase 3 的 self-validate gate）。
- `--help` 是否清晰；exit code 契约（0 / 1 / 2）是否一致。
- 是否有 `python3 ...` invocation 期间不可解析的 import bootstrap bug（例如 `_REPO_ROOT` 计算）？

### C. CLI `skills/doc-guardian/scripts/validate.py`

请逐 class 核对：

- **Class 1 (Path)**：基于 `schema.TYPE_PATHS` 与 `schema.SOURCE_ANALYSIS_PATHS`；source-system-analysis 按 `analysis_kind` 选模板；ID 类用 `cr_id`/`bug_id`/`incident_id` 字段值渲染；项目级（prd/architecture/retrospective）路径硬编码无字段依赖。`_expected_path` 在缺字段时返回 None → Class 1 报 “cannot derive expected path” 而非崩溃。
- **Class 2 (Naming)**：仅校验 filename 形态（`^[a-z][a-z0-9_]*\.md$` 或 `^(CR|BUG|INCIDENT)-\d{3}\.md$`）。`./` / `..` 等路径风格问题被路径 resolution 吞掉是否合理？(注：`Path.resolve()` 会把这两类前缀消解；class 2 现在仅卡 filename，class 1 卡路径不一致)
- **Class 3 (Frontmatter Schema)**：universal 6 字段 + per-type 必含字段全在；`approved` 仅 PRD/SRS/Architecture/CR；source-system-analysis 校验 `analysis_kind`；status / type 等 enum 合法。**field 必须存在**（key in fm），但**值可以为 null**（对 nullable 字段）—— 与 frontmatter-schema.md §5 的 “值可为 null ≠ 字段可省略” 是否一致？
- **Class 4 (Frontmatter Format)**：
  - timestamp regex `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`
  - release **必须为 quoted YAML string**；`release: 0.1` 被 YAML 解析为 float 时 reject（关键 bypass 防御）
  - owner `^[^/]+/[^/]+$`（agent_id 含 hyphen，不能用 `[a-z0-9_]+/[a-z0-9_]+`）
  - cr_id / bug_id / incident_id：3 位 zero-padded（`^(CR|BUG|INCIDENT)-\d{3}$`）；null 或 4 位均 reject
  - task_id `^T\d+$`
  - srs.is_multi_module / architecture_change：必须是 YAML bool（不接受 string `"false"`）
  - verification_status / review_status / max_severity / root_cause / resolution_action：enum 校验
  - test-report：`total_test_cases == passed + failed + (skipped if present)` 强制
  - code-review-report / test-review-report 三态：`pass ⇒ blocking_findings_count == 0`；`pending` 豁免；`fail` 任意
  - workflow-incident.triggered_by_bug：必须是 BUG-NNN ID（不接受 path）；triggered_in_release 非空 release；resolution_action ∈ {continue, abort, reconstruct, null}
  - bug-report.target_release / consumed_in_release：nullable release；root_cause：nullable enum；found_in_release：non-null release
- **Class 5 (Cross-Reference)**：`affected_doc` / `parent_architecture` / `related_srs` 路径文件存在；`triggered_by_bug` ID 渲染为 `docs/bug/{value}.md` 后查文件存在。Class 4 已经卡了 `triggered_by_bug` 不能是 path，Class 5 进一步卡 ID 必须能 resolve 到实际文件。
- **Class 6 (Change Log Discipline)**：incremental doc 必须有两个 section + pending 已 promote + change log 严格；snapshot doc 缺 section 不报错（仅当 author 主动加了 section 才校验格式）。
- **Class 7 (ID Uniqueness)**：单文件层面验 filename 与 ID field 字面相等（`{cr_id}.md`）；多文件层面 `ids` subcommand 扫 `docs/cr/` / `docs/bug/` / `docs/incident/` 检查 stem 重复。

### D. tests

- `tests/test_changelog.py`：promote happy path + 排序 + merge 同日 + invalid timestamp / section_ref / 缺 section / unknown type；validate happy + 各类 reject + html comment 容忍 + snapshot 缺 section 不报；CLI integration（promote 真写、validate exit 1 提示）。
- `tests/test_validate_file.py`：每个 doc type 至少一条 happy path（PRD / SRS / code-review pass / code-review pending / test-report skipped / workflow-incident with BUG / bug-report null fields / source-system-analysis prd-level + srs-level / snapshot test-preparation 不要 changelog）；class 1-7 各至少一条 reject case；ids subcommand 三种情形（unique / 坏 filename / 跨目录干扰）；CLI integration（pass / fail / ids / all-deferred）。
- 是否有用 `tempfile.TemporaryDirectory()` 隔离？是否触碰真实 repo 的 `docs/` / `skills/`？

### E. cross-doc 一致性

- `change-log-format.md §1 / §2.2 / §3 / §4 / §5` 与 `changelog.py` 实现严格一致（incremental/snapshot 分类、entry 格式、date heading、promote 算法、validate 算法）
- `frontmatter-schema.md §1-§7` 与 `validate.py` Class 3-5 / 7 严格一致
- `directory-layout.md §2-§3` 与 `validate.py` Class 1-2 严格一致
- `doc-guardian/SKILL.md §5-§6` 描述的 8 类校验 / `changelog.py` 子命令 / 失败处理 与脚本行为一致
- `task6_plan_20260507.md §7 / §8` 描述的 file 子命令 / promote / validate 算法逐条核对

### F. 设计 / 可维护性

- `changelog.py` 共享 helper 是否便于 Phase 4 `status_transition.py` 在 multi-doc transaction 内复用 in-memory promote？是否给 Phase 4 留了清晰 API？(题外：spec change-log-format.md §7.1 + SKILL.md §6.7 要求 status helper "在同一 transaction 内追加 [frontmatter] entry → promote 内存中 → 写回")
- script 的 `--root` 处理是否在 absolute / relative doc path 下都正确？
- script `_REPO_ROOT = parents[3]` 是否在脚本被 symlink 调用时仍正确？(题外：v0.6 要求 `.claude/skills/` + `.agents/skills/` symlink；脚本被 symlink 时 `__file__.resolve()` 返回原始路径，OK)
- exit code 契约：0 success / 1 validation+promote 失败 / 2 CLI usage error（含 deferred subcommand）— 是否一致清晰？
- import 顺序与 `noqa: E402` 注释是否合理？

### G. 已知 Phase 4+ 后续工作（不在本 review 评判范围）

仅供参考、避免误评：

- Phase 4 `status_transition.py` 会基于 Phase 3 changelog.py 的 in-memory API 实现 multi-doc all-or-nothing apply
- Phase 5 `progress.py update --task` 会按 progress_state.py 的 NORMAL_TASK_TRANSITIONS / PROTECTED_TASK_TRANSITIONS 区分实施 Stage 4 task 状态机；caller-side 在调 `is_valid_task_transition(..., allow_protected=True)` 前必须先核对 verification_result / active Bug Flow / Affected Task(s) / owner
- Phase 6 `bug-rework` 命令 + Gap-3/4/5 protected rollback 在 progress.py 内实施
- Phase 6+7 `validate.py consistency` 跨 progress.md 校验

这些不应作为 Phase 3 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase3_changelog_validate_review_20260507.md
```

评审报告需要包含以下章节（参考 Phase 1 / Phase 2 review report 的结构）：

1. **Executive Summary** — Phase 3 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 4
2. **Findings**（按 H / M / L 排序，每条含 location + issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — change-log-format.md / frontmatter-schema.md / directory-layout.md / SKILL.md / task6_plan §7-§8 与脚本行为一致性
4. **Checklist Results** — 按本 prompt 列出的 review 维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 4 (`status_transition.py`)**（Phase 4 之前可选清理 list）
   - **(B) fix before Phase 4**（必修 list；为何 Phase 4 不能在不修这些 finding 下推进）
   - **(C) revisit design**（哪些已闭环架构层决策被本批 implementation 触发了再设计需求）

如果 recommendation 是 (B)，请明确：
- 哪些 finding 必须在进 Phase 4 前修
- 哪些可以推迟到 Phase 5/6/7
- 修复路径估计（行数级粗估）

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 4 设计讨论；如发现 Phase 4 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
