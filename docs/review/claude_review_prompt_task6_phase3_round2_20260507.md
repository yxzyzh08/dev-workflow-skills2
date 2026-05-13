# Claude Review Prompt — Task 6 Phase 3 Round 2 (post-fix regression review)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成代码审查，并把评审报告保存到 `docs/review/task6_phase3_changelog_validate_round2_review_20260507.md`。Round 2 通过后才能进入 Phase 4 (`status_transition.py`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 3 Round 2 fixes** 做一次回归 review。Round 1 评审（Codex 出具）给出 **(B) fix before Phase 4** 结论；本轮请确认 1 High / 3 Medium / 2 Low 全部已修，并扫一眼新引入的代码 / 测试是否埋下新问题。

本轮是回归 review。范围：
- Round 1 review report：`docs/review/task6_phase3_changelog_validate_review_20260507.md`
- Round 1 实施代码：`skills/_shared/dev_workflow/changelog.py` / `skills/doc-guardian/scripts/changelog.py` / `skills/doc-guardian/scripts/validate.py` / `tests/test_changelog.py` / `tests/test_validate_file.py`
- Round 2 fixes 的所有 diff（git status 应该显示这些 untracked 文件未变 path，但内容已 amend）

**不要**要求 `status_transition.py` / `progress.py` / `validate.py all` / `validate.py consistency` 已实现；这些仍是 Phase 4 / 5 / 6 范围。

## Round 1 baseline

- Phase 3 Round 1 review report: `docs/review/task6_phase3_changelog_validate_review_20260507.md`
- Recommendation: **(B) fix before Phase 4**
- Findings: 1 High (H1) / 3 Medium (M1, M2, M3) / 2 Low (L1, L2)
- 当前测试运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 112 tests in 0.124s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK
```

测试总数：91 → 112，新增 21 条 regression test 覆盖每条 finding 的 reproduce case 与 happy path。

## Round 2 修复摘要（请逐条核对是否到位）

### H1 — Class 5 path references 收紧（必修）

- 修改：`skills/doc-guardian/scripts/validate.py` 新增 `_validate_path_reference(key, value, root)` helper；`check_class_5_cross_reference` 仅对 `(doc_type, key)` 是必含路径字段的组合调用：
  - `acceptance-plan.related_srs`
  - `architecture-delta.parent_architecture`
  - `cr.affected_doc`
- 拒绝条件：`None` / 非 string / 空 string / 含 `\` / 绝对路径（POSIX `/...` 或 Windows 盘符）/ 路径含 `.` / `..` / 空 segment / 解析后逃出 `--root` / 文件不存在。
- 触发字段以外的 doc type 不会运行该 check（避免误报）。
- `triggered_by_bug` ID lookup 行为保留（已是 ID 不是 path，单独 branch）。
- 新增 5 个 tests：`related_srs: null` / `affected_doc: /etc/passwd` / `parent_architecture: ../...` / `related_srs: docs\\..\\srs.md` / `related_srs: <relative but missing>`。

### M1 — CR `target_release` 格式校验（必修）

- 修改：`check_class_4_format` 新增 `if doc_type == "cr"` branch 校验 `target_release`：
  - `None` reject
  - 非 string reject（含 YAML float `0.2`）
  - 不匹配 `^\d+\.\d+$` reject
- 新增 4 个 tests：null / float / malformed string / happy path（`"0.2"`）。

### M2 — Change Log raw-line 严格 + 空 pending 仍 parse 已有 Change Log（必修）

- 修改：`skills/_shared/dev_workflow/changelog.py`：
  - `parse_changelog_section` 改为 raw-line matching：
    - 非空行不得有 leading whitespace（之前用 `.strip()` → 缩进的 heading/entry 误通过）
    - 同时按 `last_kind` 状态机要求 group 之间至少一空行
    - 只允许：blank / `### YYYY-MM-DD` / `<!-- ... -->`（inline 或 block）/ `- <ts> [<ref>]: <summary>`，其它一律 raise
  - `promote_text` 不再在 pending 为空时短路返回；总是 parse `existing Change Log`，malformed 则 raise（防 hand-edited Change Log 在 pending 空时 silent 通过）
- 新增 4 个 tests：indented heading / indented entry / missing blank line between groups / empty pending + malformed Change Log raises.

### M3 — Pending Changes 内 inline comment trailing 文本不再被吞（必修）

- 修改：`changelog.py` 新增 `_classify_comment_line(raw_line, in_block, context)` helper：
  - inline `<!-- ... --> trailing`：trailing 非空即 raise
  - multi-line `--> trail`：trailing 非空即 raise
- `parse_pending_section` 不再调 `markdown.non_comment_lines`（保留 helper 不变以兼容其它 caller），改为 inline strict 解析：blank / 缩进 reject / `<!--` 进入 comment branch / 否则当 entry 解析。
- 新增 3 个 tests：单行 inline trailing / inline 后藏一条 entry（`<!-- c --> - <ts> [...]`） / multi-line block 关闭行带 trailing。

### L1 — `title` 必须非空字符串（小修）

- 修改：`check_class_4_format` 顶部新增对 `title` 字段的 type + 非空校验。
- 新增 2 个 tests：`title=""` / `title=42`。

### L2 — `validate.py ids` 按目录限定 ID 前缀（小修）

- 修改：`check_ids_uniqueness` 改为 per-directory regex（`docs/cr/` 仅 `^CR-\d{3}\.md$`、`docs/bug/` 仅 `^BUG-`、`docs/incident/` 仅 `^INCIDENT-`）；错放 ID 文件直接报 `Class 7 (IDs)` 并 skip stem 收集（不当 unique 候选）。
- 新增 3 个 tests：`docs/bug/CR-001.md` / `docs/cr/BUG-001.md` / `docs/bug/INCIDENT-001.md`。

## 阅读顺序

1. `docs/review/task6_phase3_changelog_validate_review_20260507.md` — Round 1 findings 全文
2. `skills/_shared/dev_workflow/changelog.py` — 改动较多（M2/M3）
3. `skills/doc-guardian/scripts/validate.py` — 改动较多（H1/M1/L1/L2）
4. `tests/test_changelog.py` — 7 条新 tests（M2/M3 regression + happy）
5. `tests/test_validate_file.py` — 14 条新 tests（H1/M1/L1/L2 regression + happy）
6. `skills/doc-guardian/references/change-log-format.md` — Round 2 严格策略的 spec 来源
7. `skills/doc-guardian/references/frontmatter-schema.md` — H1/M1/L1 的 spec 来源
8. `skills/doc-guardian/references/directory-layout.md` — L2 的 spec 来源

## 重点 review 项

请严格按 Round 1 finding 顺序逐条核对：

### 1. Round 1 finding 闭环验证

- **H1**：是否所有 5 个 reject 维度都被覆盖（null / non-string / empty / `\` / absolute / `.`、`..` / 逃出 root / 缺文件）？是否对非 required 类型（如 `srs.related_srs` 字段当前不存在）误触发？路径解析时是否正确使用 `root.resolve()` 防止 symlink 干扰？
- **M1**：是否同时拒绝 null / float / 错格式？happy `"0.2"` 是否仍通过？是否与 `bug-report.target_release`（nullable）行为一致区分（CR 不可 null，bug-report 可 null）？
- **M2**：raw-line strict 是否完整覆盖 heading + entry + comment？blank-line-between-groups 状态机在 comment 行夹在 group 之间时是否仍正确（comment 后接 heading 应该 OK，因为 last_kind=comment）？`promote_text` 在 snapshot doc + 两 section 都存在 + 其中一个 malformed 的场景下行为？
- **M3**：inline trailing case 是否被精确捕获？我的 helper 接受 `<!-- a -->` (空 tail OK)、reject `<!-- a --> b`（trailing 非空）；multi-line `<!-- ... \n --> trail` 是否正确？unclosed comment（永远没 `-->`）是否 raise `unclosed HTML comment`？
- **L1**：是否避免 false-positive（title 字段缺失时不双报：class 3 报 missing，class 4 不该再报 non-empty）？
- **L2**：错放文件（如 `docs/bug/CR-001.md`）是否 (a) 报 prefix 错误 (b) 不被纳入 stem 重复检查（避免错放文件干扰 unique 判定）？

### 2. 是否新引入 regression / 边界遗漏

- `_classify_comment_line` 在 changelog.py 新增；helper 是否过于宽容或过于严格？
- `last_kind` 状态机在边界（首行直接是 entry / 首行是 heading / 首行是 comment）下行为是否合理？
- `_validate_path_reference` 把 path resolution 用 `root.resolve()` 后比较；如果 `value` 是空字符串、`/` 等 corner case 是否被前置 reject 拦住，不会到 resolution 阶段？
- 对 source-system-analysis 这种没列在 `required_path_refs` 里的 type，本身没有强 required path ref，是否依然正常？
- 错放 ID 文件触发 `Class 7 (IDs)` 后 skip 加入 seen — 同名 stem 又有第二份合法位置时，重复检查是否不会漏报？(题外：spec 只在 docs/cr|bug|incident 内部 unique；跨目录不要求 unique)

### 3. cross-doc 一致性

- `change-log-format.md` §2.3 / §3.1 / §3.3 与 changelog.py 现有严格策略是否字面匹配？特别是 §3.3 "日期块之间必须空一行"。
- `frontmatter-schema.md` §3.4（CR target_release 必含）/ §4.5（path refs 必须 forward slash + 项目根相对）/ §1（title 非空 string） 与 validate.py 实施一致？
- `directory-layout.md` §2.6 / §3.1（per-directory ID prefix） 与 ids subcommand 实施一致？
- `doc-guardian/SKILL.md` §5（8 类校验描述）是否仍与脚本行为一致？是否有需要 patch 的 spec wording（例如 SKILL.md 强调 ids 跨目录唯一性的措辞，我没动 SKILL.md，请判断是否需要）？

### 4. 测试质量

- 所有 21 条新 regression test 是否独立可读、不依赖前一个 test 的副作用？
- 是否 `tempfile.TemporaryDirectory()` 隔离？是否触碰真实 repo 的 `docs/` / `skills/`？
- 测试 assert 是否定位到精确错误片段（避免 "issues 非空" 这种 vague assertion）？
- 是否漏测：H1 的 backslash + multi-segment（如 `docs\\release0.1\\srs.md`）单独覆盖一次；M2 的 missing-blank-between-groups 情况下原有 happy fix 不退化；M3 的 unclosed comment（永远没 `-->`）是否独立覆盖；L2 的 happy（CR/BUG/INCIDENT 各自正确目录）是否仍通过原 test 覆盖？

### 5. 设计 / 可维护性

- `_classify_comment_line` 的设计是否便于 Phase 4 status_transition.py 在生成 frontmatter Pending entry 时复用同一 strict 策略（status_transition 也会拼一行 entry → 必须确保不引入 inline trailing）？
- 错误信息是否仍是 actionable（含 location / value / 修复指引）？
- exit code 契约是否仍 0 / 1 / 2 一致？

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase3_changelog_validate_round2_review_20260507.md
```

评审报告章节：

1. **Round 1 Findings 回归状态** — 6 项逐条 ✅ / ⚠️ / ❌
2. **New Findings (Round 2)**（如有）按 H/M/L 排序，每条含 location + issue + impact + recommendation
3. **Cross-Finding Consistency Check** — 8 类 reference / spec 与 implementation 横向一致性
4. **Round 2 Implementation Quality Spot-checks** — `_classify_comment_line` / `last_kind` 状态机 / `_validate_path_reference` / per-directory ids regex 的实现细节评估
5. **Checklist Results** — Round 1 各模块（changelog/validate/tests）的 ✅ / ⚠️ / ❌
6. **Open Questions / Assumptions**（如有）
7. **Recommendation** — 三选一：
   - **(A) accept regression and proceed to Phase 4 (`status_transition.py`)** — Phase 4 之前可选清理 list
   - **(B) fix before Phase 4** — 必修 list + 为何 Phase 4 不能在不修这些 finding 下推进
   - **(C) revisit design** — 哪些已闭环架构层决策被本批 implementation 触发了再设计需求

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 4 设计讨论；Phase 4 隐患记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
