# Task 6 Phase 2 Shared Foundation Review

**Review Target**: `skills/_shared/dev_workflow/*.py` + `tests/test_*.py`
**Review Date**: 2026-05-07
**Reviewer**: Claude (claude-opus-4-7[1m])
**Baseline**: Task 6 Phase 1 accepted docs (`docs/review/task6_phase1_docs_alignment_review_20260507.md`) + Task 6 implementation plan Phase 2 (`docs/implementation/task6_plan_20260507.md` §3.2 / §10 / §12 / §13)
**Recommendation**: **(A) accept and proceed to Phase 3 changelog.py + validate.py file implementation** — 但 Phase 4 (status_transition.py) 之前必须修 M2；Phase 5/6 (progress.py update --task / bug-start / bug-rework) 之前必须处理 M1
**Status**: findings: 0 High / 2 Medium / 6 Low; blockers: no (针对 Phase 3)

---

## Executive Summary

- 8 个共享模块全部可 import、`python3 -m unittest discover -s tests` 18/18 pass、`python3 -m compileall -q skills/_shared tests` exit=0；DSL 6 个 spec required parser tests 全过；artifacts 解析器对 S3 / multi-module / architecture-change / Stage 4 per-task 4 artifacts 行为正确。
- Phase 1 三条 LOW（design proposal 11→12 patch note、prerequisites §6 line 100 wording、plan §6.2 step 3 wording）+ bug-triage active retest 边界，全部已被 Codex 修复，cross-doc 一致性好。
- 实证测试发现一个真实 Medium BUG（M2）：`AtomicTransaction.rollback()` 仅 `except FileNotFoundError`，对 `NotADirectoryError` / `PermissionError` 等 OSError 子类不容错；reverse 迭代过程中任一 unlink 抛出非 FileNotFoundError 会**中断 rollback**，留下部分修改文件。Phase 3 (changelog.py 单文件 atomic_write_text) 不会暴露此 bug，但 Phase 4 (status_transition.py multi-doc) 与 release-start (progress.md + history + 多 BUG frontmatter) 必然依赖 transaction 的 all-or-nothing 保证 → **必须在 Phase 4 实现前修 M2**。
- 一个 Medium 设计风险（M1）：`progress_state.is_valid_task_transition()` 把 Gap-3 / Gap-4 protected transitions 与 normal transitions 放在同一 `TASK_TRANSITIONS` set，没有 context 参数；Phase 5/6 实现 `progress.py update --task` / `bug-start` / `bug-rework` 时若仅依赖此函数做合法性判断，会漏掉 active Bug Flow + `root_cause==development` + BUG body `Affected Task(s)` 等 protected 前置 → **必须在 Phase 5/6 protected transition 实现时配合 caller-side 显式校验或拆分 set**。
- 6 条 Low 都是 robustness / spec ambiguity / test coverage 类，不阻塞 Phase 3。**结论：可以进入 Phase 3 changelog.py + validate.py file 实现**；M1 / M2 在 Phase 4-6 各自必须修。

---

## Findings

### Medium: `AtomicTransaction.rollback()` 仅 catch `FileNotFoundError`，遇到其他 OSError 子类会中断 rollback，违背 all-or-nothing 保证

- **Location**: `skills/_shared/dev_workflow/atomic.py:67-75`
- **Issue**: 当前 rollback 实现：
  ```python
  def rollback(self) -> None:
      for target, backup_path in reversed(list(self._backups.items())):
          if backup_path is None:
              try:
                  target.unlink()
              except FileNotFoundError:
                  pass
          else:
              target.parent.mkdir(parents=True, exist_ok=True)
              shutil.copy2(backup_path, target)
  ```

  实证测试（无显式 raise，仅由 `atomic_write_text` 内部 `tempfile.mkstemp(dir=target.parent)` 在 target.parent 是文件时抛 `NotADirectoryError`）：

  ```python
  with transaction() as tx:
      tx.write_text(a, 'A1')              # _backups[a] = backup-0  (existed → backup saved)
      tx.write_text(b, 'B1')              # _backups[b] = None      (b 不存在)
      blocked = root / 'a.txt' / 'subfile'  # parent is a regular file
      tx.write_text(blocked, 'X')         # raises NotADirectoryError; _backups[blocked] = None
  # 应该：rollback 完成 → a=A0 (restored), b=MISSING (deleted)
  # 实际：a=A1 (NOT restored), b exists with 'B1' (NOT deleted)
  ```

  原因：rollback 反向迭代 `[blocked, b, a]`：
  1. `blocked.unlink()` 抛 `NotADirectoryError`（因为 `a.txt/subfile` 中 `a.txt` 是文件，`unlink` 在路径解析时报错），**未被 except 捕获** → rollback 函数立即终止；
  2. `b.unlink()` 与 `a` 的 `shutil.copy2` 永远不会执行；
  3. `transaction()` context manager 的 `except Exception: tx.rollback(); raise` 子句把 rollback 中抛出的 `NotADirectoryError` 视为 secondary exception（替换或 chain 原 exception，具体取决于 Python 版本）；外层 caller 收到的可能是 rollback 自身的异常，原始 atomic write 失败信息丢失。
- **Impact**:
  - Phase 3 changelog.py promote 是单文件 atomic_write_text，**不直接依赖 transaction.rollback()** → Phase 3 不阻塞。
  - Phase 4 `status_transition.py apply` 多 doc all-or-nothing transaction（task6 plan §9.3 / §11.3）、Phase 6 `release-start` 多 BUG frontmatter + progress.md + progress-history.md 原子改动（task6 plan §11.2）**直接依赖 transaction**。当某个目标路径出现意外文件系统状态（被另外的 process 删了目录、权限错、symlink loop、 类似 NotADirectoryError 的 corner case）时，rollback 会失败，留下部分修改的文件 → managed-project state corruption。
  - 这违反 task6 plan §4.4 "Atomic writes: every mutating script writes via backup + temporary file + atomic rename; multi-file operations roll back on failure" 的硬约束。
- **Recommendation**: 把 rollback 改为容错：每个 target 的 unlink/copy2 catch `OSError`（不仅 `FileNotFoundError`），失败的目标记录到 `errors` 列表，**继续处理后续 target**，最后若 errors 非空 raise aggregated `AtomicWriteError(errors)`。示例（diff 概念）：
  ```python
  def rollback(self) -> None:
      errors = []
      for target, backup_path in reversed(list(self._backups.items())):
          try:
              if backup_path is None:
                  try:
                      target.unlink()
                  except FileNotFoundError:
                      pass
              else:
                  target.parent.mkdir(parents=True, exist_ok=True)
                  shutil.copy2(backup_path, target)
          except OSError as exc:
              errors.append((target, exc))
      if errors:
          raise AtomicWriteError(f"Rollback partially failed: {errors}")
  ```
  并把回归测试加到 `tests/test_frontmatter_markdown_atomic.py`：用 mock 或合成路径（如本 review 中 `a.txt/subfile`）模拟"第二次/第三次写失败"，验证 rollback 仍能恢复前面的写入。

### Medium: `progress_state.is_valid_task_transition()` 把 Gap-3/Gap-4 protected transitions 与 normal transitions 混入同一 set，没有 context 参数

- **Location**: `skills/_shared/dev_workflow/progress_state.py:60-79` (`TASK_TRANSITIONS`) + `progress_state.py:123-124` (`is_valid_task_transition`)
- **Issue**: `TASK_TRANSITIONS` 包含：
  - Normal transitions（`planning-done → test-writing`、`test-review → test-done`、`code-review-passed → verifying`、`verifying → verified` 等 14 条）
  - Gap-3 transition（`verifying → code-revising`，`development-code-write` verification retry 触发；前置：`verification_result.md verification_status ∈ {fail, partial}`）
  - Gap-4 protected transitions（`verified → test-revising`、`verified → code-revising`、`code-review-passed → code-revising`，三条；前置：active Bug Flow + `root_cause==development` + BUG body `Affected Task(s)` 包含 `Tn` + 分类明确；owner 仅限 `bug-start --root-cause development` 或 `bug-rework`）

  当前 `is_valid_task_transition(verified, code-revising)` 返回 `True`，但事实源 (`command-reference.md` 状态机表 line 646-648 + plan §6.2) 严格要求 active Bug Flow + classification-specific 前置；并且 owner 仅能是 `bug-start` / `bug-rework`，不能通过普通 `update --task Tn --status code-revising` 触发。
- **Impact**:
  - 当前 Phase 2 没有运行时使用 `is_valid_task_transition`（progress.py 还未实现），所以不影响 Phase 3 changelog.py / validate.py file。
  - Phase 5 实现 `progress.py update --task` 时，若 implementer 把 `is_valid_task_transition()` 当成 single source of truth 做合法性判断，会**让普通 caller 通过 `update --task verifying-T1 --status code-revising`（无 active Bug Flow 上下文）合法地把 task 从 `verified` 拉回 `code-revising`**，绕过 Gap-4 protected owner gate。这是 spec violation（`command-reference.md` line 646: "Gap-4 protected rollback：...；owner=`bug-start` or `bug-rework`"）。
  - Phase 6 实现 `bug-start` / `bug-rework` 的 development auto-rollback（plan §6.2）也需要正确区分"普通 caller 不能用"vs"protected owner 可以用"。
- **Recommendation**: 三选一：
  - 选项 A（推荐，最小）：保留 `TASK_TRANSITIONS` 不变，在 `is_valid_task_transition` 函数 docstring 顶部加显眼警告：
    ```python
    def is_valid_task_transition(old, new):
        """Returns True iff (old, new) is a transition listed in command-reference.md.

        WARNING: this checks state-machine legality only. Gap-3 (verifying→code-revising)
        and Gap-4 (verified→test-revising / verified→code-revising / code-review-passed
        →code-revising) require additional caller-side preconditions (verification_result
        status, active Bug Flow + root_cause==development + BUG Affected Task(s) match,
        owner in {bug-start, bug-rework}). progress.py update --task must enforce these
        explicitly before calling this helper. See command-reference.md state machine
        table line 645-648 and task6_plan §6.1 / §6.2.
        """
    ```
  - 选项 B：拆 `TASK_TRANSITIONS` → `NORMAL_TASK_TRANSITIONS` + `PROTECTED_TASK_TRANSITIONS`，并提供 `is_valid_task_transition(old, new, *, allow_protected: bool = False)` 默认拒绝 protected，明确语义。
  - 选项 C：移除 `is_valid_task_transition` 直接暴露，让 `progress.py update --task` / `bug-start` / `bug-rework` 各自维护转移表（不复用 helper）；最严格但代码重复。

  推荐选项 A 或 B。若选 B，加测试：`is_valid_task_transition('verified', 'code-revising')` 默认 False；`allow_protected=True` 时 True。

### Low: `artifacts.REQUIRED_ARTIFACTS["workflow_incident_analysis"]` 是 empty list，缺 docstring 解释 design 选择

- **Location**: `skills/_shared/dev_workflow/artifacts.py:132-135`
- **Issue**: required-artifacts.md §9 写：
  ```yaml
  workflow_incident_analysis:
    required:
      - type: workflow-incident
        path_pattern: docs/incident/INCIDENT-*.md
        # 由 progress.md incident_report_path 字段指定具体路径
  ```
  spec 还注明"不走 P6 矩阵；workflow-evolution skill 接管，由 incident-resolve 退出"。当前实现把 `required` / `conditional` 都设为空 list，与 spec §9 表面冲突（spec 列了 workflow-incident artifact，实现却 empty）。
- **Impact**: 不阻塞——`progress.py update --advance` 永远不会进入 `workflow_incident_analysis` 阶段（incident-resolve 才是退出 incident 的命令），所以 `get_required_artifacts(progress)` 在 incident state 不会被调用。empty 是合理 design choice，因为 `incident_report_path` 是 progress.md 字段而非按 stage 模板渲染的 path。但 reader 不读 §9 全文（只看 §1-§8 stage 表）会困惑：为什么 `workflow_incident_analysis` 字段在 mapping 里但是空？
- **Recommendation**: 在 `REQUIRED_ARTIFACTS` 上方或 `workflow_incident_analysis` 条目内 inline comment 说明：
  ```python
  # workflow-incident-analysis is a special pseudo-stage that bypasses the P6 matrix.
  # The incident artifact path is recorded in progress.md `incident_report_path` and
  # validated by incident-start / incident-resolve directly (see required-artifacts.md §9
  # and command-reference.md §11-§12). get_required_artifacts must not be called here
  # via update --advance; this empty entry exists only to keep STAGE_KEY_BY_STAGE mapping
  # consistent for diagnostic queries.
  "workflow_incident_analysis": {
      "required": [],
      "conditional": [],
  },
  ```
  或者给 `get_required_artifacts` 加一行：进入 `workflow_incident_analysis` 时显式 raise `ArtifactError("incident state has no required artifacts; use progress.md incident_report_path")` — 二选一即可。

### Low: `atomic_write_text` 没有 fsync 父目录，crash-after-replace 极小概率丢失目录条目

- **Location**: `skills/_shared/dev_workflow/atomic.py:18-33`
- **Issue**: 当前流程：mkstemp → fdopen + write + flush + `os.fsync(handle.fileno())` → `os.replace(temp_name, target)`。在 Linux ext4 / xfs 等文件系统上，rename 操作的"目录条目变更"在 metadata journal 中，但**未对父目录执行 fsync**；如果系统在 replace 后立刻 crash 并 reboot，理论上 rename 可能丢失（rare，但 POSIX `rename(2)` 与 fsync 最佳实践要求父目录 fsync）。
- **Impact**: 本项目 personal Linux/bash 单机使用，crash 概率与影响都极小。但 release-start 长尾路径 + status_transition.py multi-doc 跨多个目录写时，父目录 fsync 缺失会让 atomic 保证比"完美 atomic"略弱。
- **Recommendation**: 在 `os.replace` 之后加：
  ```python
  parent_fd = os.open(target.parent, os.O_DIRECTORY)
  try:
      os.fsync(parent_fd)
  finally:
      os.close(parent_fd)
  ```
  对于 transaction 多文件场景，可在 transaction 提交时统一 fsync 所有受影响 parent dirs。Linux-only 实现 OK（task6 plan §4.7 已声明 current target environment 是 Linux/bash）。Low 优先级，可在 Phase 4 / Phase 7 polish 时补。

### Low: `AtomicTransaction.rollback()` 用 `shutil.copy2` 而非 atomic write，rollback 过程 crash 留下部分恢复文件

- **Location**: `skills/_shared/dev_workflow/atomic.py:73-75`
- **Issue**: rollback 的恢复路径用 `shutil.copy2(backup_path, target)`（非原子）。如果 rollback 过程中本身 crash（如电源中断、kill -9），target 处于"部分恢复"状态。
- **Impact**: 本项目 single-process personal use 概率低。但如果与 M2 一起改成 "rollback 容错继续"，那任何中间 crash 都会让多个 target 处于不一致状态。
- **Recommendation**: 把 `shutil.copy2(backup_path, target)` 改为：
  ```python
  with backup_path.open("rb") as src:
      atomic_write_text(target, src.read().decode("utf-8"))
  ```
  或者直接 `atomic_write_text(target, backup_path.read_text(encoding="utf-8"))`（如果 backup 的格式保证是 UTF-8 文本），享受 atomic_write_text 的 temp + rename 保证。Low 优先级，可与 M2 一起修。

### Low: `markdown.non_comment_lines` 不识别多行 HTML comment，会把多行 comment 各行误判为非空内容

- **Location**: `skills/_shared/dev_workflow/markdown.py:86-95`
- **Issue**: 当前实现仅识别一行内的 `<!-- ... -->`：
  ```python
  if stripped.startswith("<!--") and stripped.endswith("-->"):
      continue
  ```
  实证测试（多行 comment）：
  ```
  input: "<!--\nmultiline\ncomment\n-->\n"
  output: ['<!--', 'multiline', 'comment', '-->']  # 4 行被当成非 comment
  ```
- **Impact**:
  - change-log-format.md §2.3 spec 仅给出单行 comment 示例，未明确支持多行；当前实现严格匹配 spec 字面。
  - 但 Phase 3 `changelog.py validate` 类 6 (Change Log Discipline) 调 `non_comment_lines` 检查 Pending Changes 是否为空（除空白和注释）；若用户/AI 写多行 comment（自然 markdown 写法），会被 false positive 判为"未 promote 的 entries"，导致 validate 反复 reject 合法文档。
  - 对 Phase 3 影响不可忽视（changelog.py promote 后用户可能加多行说明）。
- **Recommendation**: 二选一：
  - 选项 A（与 spec 字面一致）：在 `non_comment_lines` docstring 注明 "single-line HTML comments only (per change-log-format.md §2.3)"，并在 spec §2.3 加一行 "多行 HTML comment 不被支持"。
  - 选项 B（更 robust）：扩展实现支持多行 comment block（用 buffered state machine 跨行），并在 spec §2.3 加合法多行示例。

  推荐选项 B，因为多行 comment 是普遍 markdown 实践，spec 字面限制单行没有强 motivation。Low 优先级，建议在 Phase 3 实现 changelog.py validate 时一并处理。

### Low: 缺 5-6 个 high-value boundary tests，影响 Phase 3 confidence

- **Location**: `tests/test_conditions_artifacts.py` / `tests/test_frontmatter_markdown_atomic.py`
- **Issue**: 当前 18 tests 覆盖了所有 `task6 plan §10.2` 6 个 spec required parser cases + happy paths，但缺以下 boundary tests：

  1. **DSL chain length > 2 reject**（required-artifacts.md grammar `<variable> = <identifier> ('.' <identifier>)?`）：`srs.detail.is_multi_module == true` 应 raise ConditionError。本 review 实证已验证实现行为正确，但缺测试 → 任何未来重构有可能引入回归。
  2. **DSL hyphenated LHS reject**：`scenario-fake == S3` 应 raise ConditionError。实证已验证行为正确。
  3. **DSL bool/enum 类型不匹配 reject**：`scenario == true`（enum 变量比 bool）和 `srs.is_multi_module == S3`（bool 变量比 enum）。实证已验证行为正确。
  4. **DSL precedence**：`scenario == S1 || scenario == S2 && current_stage == testing` 应解析为 `S1 || (S2 && testing)` 而非 `(S1 || S2) && testing`。当前 parser 行为正确（实证验证），但未单独测试，将来重构 parse_or/parse_and 时易引入回归。
  5. **artifacts Stage 3 `architecture_change == false` 不含 architecture-delta 路径**（complement of test_srs_conditionals_read_srs_frontmatter `True` case）。
  6. **artifacts S1 / S2 Stage 1 / Stage 2 不含 source-system-analysis 路径**（complement of test_s3_prd_requires_source_analysis）。
  7. **markdown 嵌套 heading cutoff**：`## A\n### A1\n### A2\n## B` 中 `## A` body 应包含 `### A1\n### A2\n` 但不含 `## B`。实证已验证正确。
  8. **AtomicTransaction 第二次 atomic_write_text 失败时 rollback 第一次的写入 + 删除任何已创建的新文件**（这正是 M2 finding 的 reproduction 测试）。

  优先级排序：
  - **8 优先级最高**（直接关联 M2，没有它无法 catch M2 这种类型 bug）
  - **5、6 中等**（验证 condition false 路径，5 行 test 即可）
  - **1-4、7 较低**（已被实证验证；spec 已写）
- **Impact**: Phase 2 acceptance "focused unit tests pass for shared modules" 已满足，不阻塞 Phase 3。但 Phase 4 status_transition.py 之前 8 必须有，否则 M2 类 bug 难以捕捉。
- **Recommendation**: Phase 3 起骨架时优先补 5、6、8；其余 1-4、7 在 Phase 3 收尾或 Phase 7 polish 时补齐。

### Low: `split_frontmatter` 不接受 `---\n---\n`（紧贴的空 frontmatter），与 YAML 字面合法但 spec 不支持

- **Location**: `skills/_shared/dev_workflow/frontmatter.py:40-57`
- **Issue**: 实证：
  - `"---\n---\n"`（closing `---` 紧跟 opening `---\n`） → raise FrontmatterError("missing closing delimiter")
  - `"---\n\n---\n"`（中间一空 line） → 接受，yaml_text = `""`, body = `""`

  原因：`find("\n---", 4)` 从 index 4 开始找 `\n---`，`---\n---\n` 的 yaml 段内没有 `\n` 前导 → 找不到 closing delimiter。
- **Impact**: 不阻塞——doc-guardian 管辖的所有 doc type 都必须含 universal 6 字段（frontmatter-schema.md §1），空 frontmatter 不合法，validate.py 类 3 会先 reject。但若 implementer 在 Phase 5 progress.py recover 中遇到极端 corrupt 文件，pre-validate 行为可能不一致。
- **Recommendation**: 在 `split_frontmatter` docstring 注明"empty frontmatter must include at least one newline between delimiters; truly empty `---\n---\n` is rejected as missing closing delimiter (acceptable: doc-guardian schema requires universal fields anyway)"。或者把 `find("\n---", 4)` 改为 `find("\n---", 3)` 让紧贴的空 frontmatter 被识别。Low 优先级，可在 Phase 7 polish 时考虑。

---

## Checklist Results

| Area | Status | Notes |
|------|--------|-------|
| frontmatter.py | ✅ | YAML timestamp resolver 正确移除（保 string）；release `"0.1"` 保字符串；CRLF normalize；missing/closing delimiter 检测；render round trip 正确。仅 Low 6 边界（`---\n---\n` 不被识别为空 frontmatter，但 spec 也不允许空 frontmatter） |
| markdown.py | ✅⚠️ | find_section 同/高级 heading cutoff 正确（实证验证嵌套 cutoff）；replace_section_body 保留前后内容；non_comment_lines 仅识别 single-line HTML comment（Low 4） |
| atomic.py | ⚠️ | atomic_write_text 实现正确（mkstemp + fsync + os.replace）但缺父目录 fsync (Low 2)；AtomicTransaction backup/rollback 正常路径正确（直接 rollback 测试通过）；**实证发现 rollback 在 mid-rollback OSError 时中断 → all-or-nothing 违背 (Medium 2)**；rollback 用 non-atomic copy2 (Low 3) |
| conditions.py DSL | ✅ | 6 个 spec parser test cases 全过；ALLOWED_VARIABLES 与 references 一致；&& 高于 || 优先级正确；chain > 2、hyphenated LHS、unknown variable / function / enum、quoted enum、assignment 全部 reject（实证验证）；无 eval/exec/ast.literal_eval；ENUM_LITERALS / ENUM_VALUES_BY_VARIABLE 与 required-artifacts.md 一致 |
| artifacts.py required artifacts | ✅⚠️ | REQUIRED_ARTIFACTS 与 required-artifacts.md §2-§8 一致；S3 Stage 1/2 必备清单正确；Stage 4 advance 无条件 4 个 per-task；is_multi_module / architecture_change 触发条件路径正确；read_srs_condition_fields 在 SRS missing 或 FrontmatterError 时 default false（与 spec 一致）。仅 workflow_incident_analysis empty list 缺 docstring (Low 1) |
| progress_state.py constants | ⚠️ | EVENTS / SUB_STATES / STAGES / NEXT_STAGE / ROOT_CAUSE_TO_STAGE 全部正确；TASK_TRANSITIONS 含全部 18 条转移（含 Gap-3 + Gap-4 三条）。但 **is_valid_task_transition 不区分 normal vs protected (Medium 1)** → Phase 5/6 implementer 风险 |
| schema.py constants | ✅ | INCREMENTAL/SNAPSHOT 分类与 change-log-format.md §1 完全一致（13 + 16 个）；UNIVERSAL_FIELDS / STATUSES / GATED_APPROVED_TYPES / PER_TYPE_REQUIRED_FIELDS（22 类）与 frontmatter-schema.md §5 一致；TYPE_PATHS（26 类）与 directory-layout.md §2 一致；SOURCE_ANALYSIS_PATHS（6 个 analysis_kind）与 directory-layout.md §2.3 一致；VERIFICATION_STATUSES / REVIEW_STATUSES / ROOT_CAUSES 完整 |
| unit tests | ✅⚠️ | 18 tests pass；`compileall` exit=0；覆盖 6 个 spec parser cases + happy paths + 2-task development scenario + Gap-3/4 transitions + key task6 schema fields。**缺 8 个 high-value boundary tests (Low 5)**，最关键的是 transaction 第二次写失败 rollback 测试（如有，会 catch Medium 2） |

---

## Open Questions / Assumptions

1. **Phase 3 的修复时机**: M2（AtomicTransaction.rollback fragility）严格说不阻塞 Phase 3 changelog.py + validate.py file，因为 changelog.py promote 用单文件 atomic_write_text，validate.py file 是只读。但 M2 必须在 Phase 4 status_transition.py + Phase 6 release-start 之前修。**建议：Phase 3 起骨架时同 round 顺手修 M2**（< 10 行 patch + 1 个新测试），而不是拖到 Phase 4。

2. **artifacts.py 保留 condition 字段在渲染后 ArtifactSpec 中**: `_render_specs` 把 `condition` 透传到结果 ArtifactSpec.condition。当前没有 caller 读这个字段（validate.py file 不需要 re-evaluate condition），但保留 audit info 不构成 confusion。**判断：可接受，不作为 finding。**

3. **render_markdown body trailing newline**: 如果 caller 传入的 body 末尾不是 `\n`，渲染输出末尾也无 `\n`。当前测试用 `"\n# Body\n"` 总有 trailing newline；spec 没强制 body 必须 trailing newline。**判断：行为合理但建议 Phase 3 changelog.py promote 自检渲染输出末尾是否为 `\n`，避免后续 append 时出现 `xxxx## Pending Changes` 拼接问题。** 不作为 finding，留作 Phase 3 实现注意事项。

4. **PRD supporting docs (competitor / market / non-goals 等) 在 schema.py 列为 SNAPSHOT_DOC_TYPES**: change-log-format.md §1 表没有显式列 PRD supporting，schema.py 把它们归入 SNAPSHOT。这是合理 inference（frontmatter-schema §3.5 说"按需创建"），但 spec 字面留有 ambiguity。**判断：可接受 inference，不作为 finding；建议在 change-log-format.md §1 加一行"PRD supporting docs (competitor-research, market-research, non-goals 等) 是 snapshot，不需 Change Log"。** 这是 spec doc clarity 改进，不阻塞 Phase 3。

5. **render_progress 的 default body** 是 placeholder `"\n# Current Stage Summary\n\n# Recent Activity\n"`。Phase 5 实现 progress.py 时会渲染真实 summary，default body 仅用于 unit testing convenience。**判断：可接受，不作为 finding；Phase 5 实现 init/recover 时会写真实 body。**

6. **TYPE_PATHS 里 source-system-analysis 没有 entry**：因为它按 analysis_kind 分路径（SOURCE_ANALYSIS_PATHS 单独 mapping）。validate.py 类 1 (Path) 必须先看 frontmatter `type==source-system-analysis` 时跳到 SOURCE_ANALYSIS_PATHS lookup（而非 TYPE_PATHS）。**判断：合理 design；建议 Phase 3 实现 validate.py 类 1 时在 docstring 加这条特例。** 不作为 finding。

---

## Recommendation

**(A) accept and proceed to Phase 3 changelog.py + validate.py file implementation**.

**Phase 3 之前可选清理**（不阻塞，但强烈建议）：

1. **修 M2**（atomic.py rollback 容错）+ 加回归测试（transaction 第二次 atomic_write_text 失败模拟）。约 10 行 patch + 15 行新测试。理由：M2 是真实 bug，越早修风险越小；Phase 4 status_transition.py 实现时已经能立刻复用 robust transaction，不会冒重写风险。

**Phase 4 (status_transition.py) 之前必须修**：

- M2（如未在 Phase 3 顺手修）

**Phase 5/6 (progress.py update --task / bug-start / bug-rework) 之前必须处理**：

- M1（is_valid_task_transition + Gap protected transitions）：选择选项 A（加 docstring 警告）或选项 B（拆 NORMAL/PROTECTED set 并加 allow_protected 参数）。推荐选项 B，因为它让 caller-side gate 显式可测试。

**可在 Phase 7 docs polish 阶段补齐的 Low**：

- Low 1（artifacts.py workflow_incident_analysis docstring）
- Low 2（atomic_write_text 父目录 fsync）
- Low 3（rollback 用 atomic_write_text 而非 shutil.copy2）
- Low 4（markdown.py 多行 HTML comment 支持，建议在 Phase 3 changelog.py validate 实现时一并处理）
- Low 5（5-6 个 boundary tests，建议 Phase 3 起骨架时补）
- Low 6（split_frontmatter 空 frontmatter docstring）

**Phase 3 实现入口点**（按 task6 plan §13 Phase 3）：

1. `skills/doc-guardian/scripts/changelog.py promote / validate`：复用 markdown.py find_section + replace_section_body + non_comment_lines；用 atomic.py atomic_write_text 单文件；按 change-log-format.md §4-§5 算法实现。
2. `skills/doc-guardian/scripts/validate.py file <path>`：Class 1 (Path) 用 schema.TYPE_PATHS / SOURCE_ANALYSIS_PATHS；Class 2 (Naming) 文件名 regex；Class 3 (Frontmatter Schema) 用 schema.UNIVERSAL_FIELDS + PER_TYPE_REQUIRED_FIELDS；Class 4 (Format) timestamp / release / owner / ID regex；Class 5 (Cross-Reference) path refs + ID refs；Class 6 (Change Log Discipline) delegate to `changelog.py validate`；Class 7 (ID Uniqueness)。
3. `skills/doc-guardian/scripts/validate.py ids`：仅 Class 7。
4. 测试：`tests/test_changelog.py` + `tests/test_validate_file.py`，覆盖 task6 plan §12.2 第 3-4 行点（promote happy path / 空 pending no-op / invalid timestamp / invalid section ref / 各 frontmatter schema 失败）。

**不推荐 (B) fix before Phase 3 的判据**：M1 仅在 Phase 5/6 暴露；M2 仅在 Phase 4 暴露；6 条 Low 都是 robustness / spec ambiguity / test coverage 类。Phase 3 实现 changelog.py + validate.py file 不直接依赖 transaction.rollback() 容错和 task transition protected gate。

**不推荐 (C) revisit design 的判据**：本批共享模块的 API 形态（FrontmatterDocument / Section / AtomicTransaction / ArtifactSpec / ProgressLike / ProgressDocument）与 task6 plan §3.2 设计意图严格一致；所有 spec mismatch 都是 implementation 层面 robustness 修补，不需要 design level 重做。
