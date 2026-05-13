# Task 6 Phase 2 Shared Foundation Review — Round 2 (post-fix regression)

**Review Target**: `skills/_shared/dev_workflow/*.py` + `tests/test_*.py` (after Round 1 fixes were applied by the reviewer per `docs/review/task6_phase2_shared_foundation_review_20260507.md`)
**Review Date**: 2026-05-07
**Reviewer**: Claude (claude-opus-4-7[1m])
**Baseline**: Task 6 Phase 1 accepted docs + Task 6 implementation plan Phase 2 + Round 1 review report
**Round 1 Review**: `docs/review/task6_phase2_shared_foundation_review_20260507.md`
**Recommendation**: **(A) accept regression and proceed to Phase 3** — Round 1 全部 2 Medium / 6 Low 已修；新引入 0 High / 0 Medium / 2 Low（trivial）；不阻塞 Phase 3
**Status**: regression: 0 remaining; new findings: 0 High / 0 Medium / 2 Low; blockers: no

---

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|----------|------|
| **M1 — `is_valid_task_transition` 把 Gap-3/Gap-4 protected transitions 与 normal transitions 混入同一 set** | ✅ 已修 (选项 B) | `progress_state.py:60-102` 拆 `NORMAL_TASK_TRANSITIONS` (14 条) + `PROTECTED_TASK_TRANSITIONS` (4 条) + `TASK_TRANSITIONS` 保留为 union 兼容；`is_valid_task_transition(old, new, *, allow_protected=False)` 签名为 keyword-only，默认拒绝 protected。`PROTECTED_TASK_TRANSITIONS` 上方 docstring 引用 command-reference state-machine table line 645-648 + plan §6.1/§6.2，说明每条的 caller-side 前置（verification_status / active Bug Flow / BUG body Affected Task(s) / owner=`bug-start`/`bug-rework`）。新增 5 个针对 M1 的 tests 覆盖：normal default allowed / protected require flag / protected set 完全等于 spec gap set / NORMAL ∩ PROTECTED = ∅ / NORMAL ∪ PROTECTED = TASK_TRANSITIONS / illegal transition 即使 allow_protected=True 仍 reject。 |
| **M2 — `AtomicTransaction.rollback()` 仅 catch FileNotFoundError，遇到 NotADirectoryError / PermissionError 等会中断 rollback** | ✅ 已修 | `atomic.py:105-130` 把 rollback 改为 per-target `try/except OSError`，aggregate errors 到 `errors` 列表，最后 raise `AtomicWriteError("Rollback partially failed: ...")`；`transaction()` context manager 在 rollback 自身 raise 时把 rollback exception chain 到原异常 (`raise rollback_exc from primary`)。新增 `test_transaction_rolls_back_when_a_later_write_fails` 复现 Round 1 实证场景（`a.txt/subfile` 父目录是 file，`tempfile.mkstemp` 抛 NotADirectoryError），验证 a 回滚到 'A0'、b 被删除、外层收到 OSError。Round 2 实证再次复现：a='A0'、b 不存在、`AtomicWriteError.__cause__` chain 到 NotADirectoryError → 行为完全符合 fix 目标。 |
| **L1 — `artifacts.REQUIRED_ARTIFACTS["workflow_incident_analysis"]` 是 empty list，缺 docstring** | ✅ 已修 | `artifacts.py:132-144` 在 `workflow_incident_analysis` 上方加 7 行 inline comment 引用 required-artifacts.md §9 + 说明为什么保留 empty entry（保持 STAGE_KEY_BY_STAGE 一致性 + 让 `get_required_artifacts` 显式 raise 而非 silent return `[]`）。`get_required_artifacts` 在 stage_key=="workflow_incident_analysis" 时显式 raise `ArtifactError("workflow-incident-analysis bypasses P6 advance; use progress.md incident_report_path with progress.py incident-start / incident-resolve instead of get_required_artifacts")`。新增 `test_workflow_incident_analysis_raises_explicit_error`。 |
| **L2 — `atomic_write_text` 没有 fsync 父目录** | ✅ 已修 | `atomic.py:17-27` 新增 `_fsync_parent(path)` helper（`os.open(parent, O_DIRECTORY) + os.fsync + os.close`，OSError silent return 兼容非 Linux 文件系统）；`atomic_write_text` 与 `atomic_replace_from` 在 `os.replace` 之后都调用 `_fsync_parent(target)`，rollback 在 unlink 成功后也调用。 |
| **L3 — `AtomicTransaction.rollback()` 用 `shutil.copy2` 而非 atomic write** | ✅ 已修 | 新增 `atomic.py:49-72` `atomic_replace_from(path, source)` 函数：mkstemp + binary chunked read/write (65536 bytes) + fsync + os.replace + parent fsync。`backup` 与 `rollback` 都改用此函数取代 shutil.copy2。同时移除 `import shutil` 依赖；`cleanup` 改为手动 iterdir + unlink + rmdir（backup_dir 只含平铺文件，无需 recursive）。 |
| **L4 — `markdown.non_comment_lines` 不识别多行 HTML comment** | ✅ 已修 | `markdown.py:86-113` 改为 buffered state machine：维护 `in_block_comment` 状态，遇 `<!--` 但无 `-->` 时进入 block 模式跳过后续行直到 `-->`。新增 docstring 显式声明支持 single-line + multi-line。新增 `test_non_comment_lines_handles_multi_line_html_comment` 与 `test_non_comment_lines_treats_only_comments_as_empty` tests。Round 2 实证：3-line `<!--\nfirst\nsecond\n-->\n` 被正确识别为单个 comment block 并 skip。 |
| **L5 — 缺 5-6 个 high-value boundary tests** | ✅ 已修 (12 个) | 新增 12 tests + 把原 1 个 `test_task_transitions_include_task6_gaps` 拆为 5 个更精细的 tests，总数 22 → 34。覆盖 Round 1 列出的所有高价值场景：transaction 第二次写失败 rollback (M2 regression)、DSL chain > 2 / hyphenated LHS / 类型不匹配 / precedence、artifacts S1 Stage 1/2 / Stage 3 false / incident raise、markdown 嵌套 heading cutoff / 多行 HTML comment / only-comments、progress_state normal-default / protected-require-flag / disjoint+union / illegal-with-flag / spec-gap-set。 |
| **L6 — `split_frontmatter` 不接受紧贴的空 frontmatter `---\n---\n`** | ✅ 已修 | `frontmatter.py:41-51` 在 `split_frontmatter` 加 docstring 显式说明：opening 必须 `---\n`、closing 必须前导 `\n` 的独立行；紧贴的 `---\n---\n` 被 reject 是预期行为（doc-guardian 的所有 doc type 都要求 universal 6 字段，空 frontmatter 不合法）；要表达"空 mapping"用 `---\n\n---\n`。无行为变化。 |

**回归结论**：8/8 项全部 ✅ 已修，0 项 ⚠️ 部分残留，0 项 ❌ 未修。

---

## New Findings (Round 2)

### Low: `test_and_has_higher_precedence_than_or` 的两个 valuation 都不能区分 `&&` vs `||` 优先级

- **Location**: `tests/test_conditions_artifacts.py:59-71`
- **Issue**: 当前测试用两组 valuation 验证 precedence：
  - `(scenario=S1, current_stage=testing)` → 表达式 `S1 || (S2 && testing)` = `True || (False && True)` = True；如果 precedence 错误解读为 `(S1 || S2) && testing` = `(True || False) && True` = True。**两种解读结果相同**。
  - `(scenario=S1, current_stage=delivery)` → 表达式 `(S1 && testing) || S2` = `(True && False) || False` = False；错误解读 `S1 && (testing || S2)` = `True && (False || False)` = False。**两种解读结果相同**。

  Round 2 实证：用一组能区分 precedence 的 valuation `(scenario=S1, current_stage=delivery)` 测试 `scenario == S1 || scenario == S2 && current_stage == testing`：
  - 正确解读（&& 高）：`True || (False && False)` = True
  - 错误解读（|| 高）：`(True || False) && False` = False

  当前实现返回 True（实现层面 precedence **正确**），但 **测试本身无法 catch 实现 regression**——把 parser 改为 `||` 优先于 `&&`，这两个 case 仍 pass。
- **Impact**: 不阻塞 Phase 3。conditions.py 当前 implementation 已经把 `parse_or` 包 `parse_and`，结构上正确。但作为 regression test，未来如果 implementer 重构 parser 把 precedence 弄反，这个测试不会 catch，需要其他 tests 兜底。
- **Recommendation**: 至少加一个能区分两种 precedence 的 case：
  ```python
  v_disc = {**self.variables, "scenario": "S1", "current_stage": "delivery"}
  # Discriminating case: True if && higher, False if || higher.
  self.assertTrue(
      evaluate("scenario == S1 || scenario == S2 && current_stage == testing", v_disc)
  )
  ```
  原本的两个 case 可以保留作为 "happy/不变" sanity，但至少有一个 case 必须能区分。Phase 3 起骨架时顺手补即可。

### Low: `markdown.non_comment_lines` 的多行 HTML comment 关闭行 inline content 被吞

- **Location**: `skills/_shared/dev_workflow/markdown.py:99-102`
- **Issue**: state machine 在 closing 行只看到 `-->` in stripped 就 set `in_block_comment = False` 并 `continue`（整行跳过）。如果 closing 行是 `--> after the close`，"after the close" 也被一起跳过。Round 2 实证：
  ```python
  body = 'first\n<!--\nstuff\n--> after the close\nlast\n'
  # Expected (most permissive): ['first', 'after the close', 'last']
  # Actual:                       ['first', 'last']
  ```
- **Impact**: 极小。change-log-format.md §2.3 不要求支持 inline content after `-->`；Pending Changes 的合法 entry 是 `- {timestamp} [{section_ref}]: {summary}`，绝不会与 comment closing tag 在同一行。Phase 3 changelog.py validate 不会因此 false negative。
- **Recommendation**: 二选一：
  - 选项 A（最小）：加 docstring "Inline content after the closing `-->` of a multi-line comment block is treated as part of the comment and skipped; this is acceptable because change-log-format.md §2.3 does not allow content sharing a line with a comment closing tag."
  - 选项 B：把 closing 行 `-->` 之后的内容截出来当作普通 line append。需要 split on `-->` 取 right part。

  推荐选项 A（spec 不要求），实现 cost 低。Phase 7 polish 时考虑选项 B。

---

## Cross-Finding Consistency Check

横向一致性逐条核对：

| 检查点 | 状态 | 评论 |
|--------|------|------|
| 1. **Event whitelist** ∈ {`write-complete`, `review-issues`, `review-passed`, `human-confirmed`} | ✓ | progress_state.py:28 仍精确为 4 个 event；`test_event_whitelist` 仍验证 `issues-found` not in EVENTS。无回归。 |
| 2. **TASK_TRANSITIONS 完整覆盖 command-reference state-machine table** | ✓ | NORMAL (14) + PROTECTED (4) = 18 条，与 command-reference state-machine table line 631-648 严格一致；`test_protected_set_matches_command_reference_gaps` 直接断言 PROTECTED set 等于 spec 列出的 4 条 Gap-3/4 transitions；`test_normal_and_protected_are_disjoint_and_union_is_full_table` 强制 disjoint + union 等价。 |
| 3. **DSL ALLOWED_VARIABLES + ENUM_LITERALS 与 required-artifacts.md 一致** | ✓ | 无改动，仍 6 变量 + 16 enum literal 白名单。新增 4 个 boundary tests 验证 chain > 2 / hyphenated LHS / type mismatch / precedence；其中 precedence test 见 New Finding L1。 |
| 4. **REQUIRED_ARTIFACTS 与 required-artifacts.md §2-§9 一致** | ✓ | 无改动；新增 `workflow_incident_analysis` inline docstring + 显式 raise，不改变 P6 advance 行为；新增 `test_s1_prd_inception_has_no_source_system_analysis` / `test_s1_srs_specification_has_no_source_system_analysis` / `test_architecture_design_without_change_omits_delta` 验证 conditional false 路径。 |
| 5. **change-log-format.md §1 incremental/snapshot 分类** | ✓ | schema.py 无改动；INCREMENTAL (13) + SNAPSHOT (16) = 29 doc types 与 spec §1 表完全一致。 |
| 6. **No direct state editing / Doc status owner = status_transition.py** | ✓ | atomic / progress_state / artifacts 改动都没暴露绕过 status_transition.py 的 path；transaction context manager + rollback 容错改造让 multi-doc all-or-nothing 保证更稳健，反而强化 Phase 4 的 owner boundary。 |
| 7. **No Python eval / exec / ast.literal_eval** | ✓ | conditions.py 无改动，仍是 whitelist tokenizer + recursive descent parser；rollback aggregate errors 用 string format 不涉及 eval。 |
| 8. **Atomic writes — backup + temp + rename + parent fsync** | ✓ | atomic.py 现在 atomic_write_text + atomic_replace_from 都 fsync 父目录；rollback 也 fsync；transaction context 在 rollback 失败时 chain 原异常。task6 plan §4.4 atomic 硬约束完全满足。 |

---

## Round 2 Implementation Quality Spot-checks

针对每个 fix 的实现细节做严格 code review:

### atomic.py
- `_fsync_parent` 用 `os.O_DIRECTORY` flag 在非 Linux 系统可能 raise OSError → silent return；可接受（Linux/bash target 已声明）。
- `atomic_replace_from` chunked binary read 65536 bytes，对 plain text backup 文件 always sufficient；UTF-8 / 二进制 mixed 无歧义。
- `cleanup` 不再 `import shutil`，手动 iterdir + unlink + rmdir。一个 trivial 观察：line 140 `except (OSError, FileNotFoundError)` 中 `FileNotFoundError` 是 `OSError` 子类，列表冗余（写 `except OSError` 即可）。**Trivial nit**，不作为 finding。
- transaction context manager 在 rollback raise 时用 `raise rollback_exc from primary`，Python 3 chained-exception 行为正确：caller 看到 `AtomicWriteError(...)` + "during handling of ... the above exception, another exception occurred"。

### progress_state.py
- M1 拆分采用选项 B（更显式），是 Round 1 推荐的选项；keyword-only 参数让 caller 必须 explicitly opt-in，安全 default。
- docstring 引用具体 spec 行号（command-reference state-machine table line 645-648 + plan §6.1/§6.2），implementer 可直接对照 spec 验证 caller-side 前置。
- `is_valid_task_transition` API 仍是粗粒度（不区分 Gap-3 vs Gap-4 的 caller owner），但 docstring 已经把 owner 列出来，依赖 caller 自检。这是合理的 design choice，进一步细分会引入 caller-specific API。**不作为 finding**。

### markdown.py
- state machine 处理 single-line `<!-- ... -->` / multi-line block / 未闭合块（unclosed → 整个文件剩余视为 comment，可接受 spec edge case）。
- closing 行 inline content 被吞 — 见 New Finding L2。

### artifacts.py
- workflow_incident_analysis raise ArtifactError 让 caller 显式知道这个 stage 不走 P6；信息密度高。
- `get_required_artifacts` 在 stage_key="workflow_incident_analysis" 的 raise 是 fail-fast 而非 silent default `[]`，避免 silent bug（implementer 误以为该 stage "no required artifacts" 然后让 `update --advance` pass）。

### frontmatter.py
- Low 6 fix 仅加 docstring，无行为变化；docstring 给出 workaround (`---\n\n---\n`)。

### tests
- M2 regression test (`test_transaction_rolls_back_when_a_later_write_fails`) 用合成 path `a.txt/subfile` 触发 NotADirectoryError；依赖 Linux/bash mkstemp 的特定行为（`tempfile.mkstemp(dir=parent)` 在 parent 是 file 时 raise NotADirectoryError）。task6 plan §4.7 已声明 Linux/bash target，所以这个 reproduce path 在 target 环境下稳定。
- precedence test 见 New Finding L1。
- 其他 11 个新 tests 都是 spec-source-of-truth correct 且独立验证。

---

## Checklist Results

| Area | Status | Notes |
|------|--------|-------|
| frontmatter.py | ✅ | Low 6 docstring 加正确；行为不变；timestamp/release/CRLF/closing delimiter 仍正确 |
| markdown.py | ✅⚠️ | Low 4 multi-line HTML comment state machine 实现正确；新加 3 tests；唯一新 Low 是 closing-line inline content 被吞（spec 不要求支持） |
| atomic.py | ✅ | M2 fix 实证可重现并通过；Low 2 父目录 fsync ✓；Low 3 atomic_replace_from ✓；transaction context manager chain rollback failure 到 primary；trivial `except (OSError, FileNotFoundError)` 列表冗余但无害 |
| conditions.py DSL | ✅⚠️ | conditions.py 本身未改；4 个新 boundary tests 中 precedence test 不能区分 && vs \|\| 优先级（New Finding L1） |
| artifacts.py required artifacts | ✅ | Low 1 workflow_incident_analysis 显式 raise + inline comment 引用 spec §9；4 个新 boundary tests 覆盖 S1 / Stage 3 false / incident raise |
| progress_state.py constants | ✅ | M1 拆分 NORMAL/PROTECTED + keyword-only allow_protected 安全 default；docstring 引用 spec 行号；5 个新 tests 验证默认拒绝/显式允许/spec 一致/disjoint+union/illegal-with-flag |
| schema.py constants | ✅ | 无改动；与 references 一致性维持 |
| unit tests | ✅⚠️ | 22 → 34 tests，涵盖 Round 1 列出的 5/6/8 高价值 boundary 与 M1/M2 regression；唯一缺陷是 precedence test 区分能力（New Finding L1） |

---

## Open Questions / Assumptions

1. **rollback 失败的 backup 是否应保留**：当前 transaction context manager 在 `finally: tx.cleanup()` 中无条件删除 backup_dir。如果 rollback 自身 raise，意味着部分文件未恢复，但 cleanup 仍会删除 backup → 后续手动恢复无 backup 可用。**判断**：对于 single-process personal use，rollback partial failure 已经是 catastrophic state corruption，应该让人手动介入（git checkout / 备份）；保留 backup 反而让用户看到 stale backup files 困惑。当前行为 acceptable；不作为 finding。

2. **precedence test 准确性 vs implementation correctness**：实现层面 parse_or wraps parse_and，precedence 正确；但 test 覆盖度不足以 catch implementation regression。建议 Phase 3 起骨架时补一个能区分的 case（5 行 patch）。**不阻塞 Phase 3**。

3. **multi-line comment closing-line tail content**：spec 没要求支持；如果未来 changelog.py validate 遇到这种合法的 markdown 文档（e.g. user 在 Pending Changes section 注释里写 `--> note about timestamp format`），可能 silent skip 而非 error；用户行为驱动改进，不作为 Phase 3 阻塞。

4. **trivial `except (OSError, FileNotFoundError)` 冗余**：`atomic.py:140`。FileNotFoundError 是 OSError 子类，写 `except OSError` 即可。零行为影响。可在 Phase 3 起骨架时顺手清理。

---

## Recommendation

**(A) accept regression and proceed to Phase 3 changelog.py + validate.py file implementation**.

**Round 1 全部 8 个 findings (2 Medium + 6 Low) 已 100% 闭环修复**：
- M1 拆分采用 Round 1 推荐的选项 B（NORMAL/PROTECTED + keyword-only flag）
- M2 实证可重现，rollback 容错 + transaction context chain
- L1-L6 全部按 Round 1 推荐方向实施

**Round 2 新发现 0 High / 0 Medium / 2 Low（trivial）**：
- L1 precedence test 不能区分两种 precedence 解读（implementation 层面 precedence 正确）
- L2 multi-line comment closing-line inline content 被吞（spec 不要求支持）

**Phase 3 之前可选清理**（不阻塞，但建议 Phase 3 起骨架时 inline 修）：
- 加一个能区分 && vs || precedence 的 test case（5 行）
- 清理 `atomic.py cleanup` 的 `except (OSError, FileNotFoundError)` 冗余（1 行）

**Phase 5/6 (progress.py update --task / bug-start / bug-rework) 之前需要的 caller-side 工作**：
- 在 caller 内部检查 verification_status / active Bug Flow / BUG body Affected Task(s) / owner，确认前置满足后才传 `allow_protected=True` 给 `is_valid_task_transition`。docstring 已明确这个 contract，implementer 可直接对照实施。

**Phase 7 docs polish 阶段可选清理**：
- markdown.py 多行 comment closing 行 inline content 处理（选项 B 实现）

**不推荐 (B) fix before Phase 3 的判据**：当前 finding 含 0 High / 0 Medium / 2 Low（trivial）；2 条 Low 都不会让 Phase 3 changelog.py + validate.py file 行为错误。

**不推荐 (C) revisit design 的判据**：所有 Round 1 fixes 都按推荐方向实施，未触及任何已闭环架构决策；M1 拆分 + M2 容错改造让共享模块比 Round 1 baseline 更稳健，没有引入新设计决策。

**Phase 3 实现入口点**（按 task6 plan §13 Phase 3）：

1. `skills/doc-guardian/scripts/changelog.py promote / validate`：复用 `markdown.find_section` + `replace_section_body` + `non_comment_lines` (now multi-line comment safe)；用 `atomic_write_text` 单文件 atomic + parent fsync。
2. `skills/doc-guardian/scripts/validate.py file <path>`：Class 1 用 `schema.TYPE_PATHS` / `SOURCE_ANALYSIS_PATHS`；Class 2 文件名 regex；Class 3 用 `schema.UNIVERSAL_FIELDS` + `PER_TYPE_REQUIRED_FIELDS`；Class 4 timestamp / release / owner / ID regex；Class 5 path refs + ID refs；Class 6 delegate to `changelog.py validate`；Class 7 ID Uniqueness。
3. 测试：`tests/test_changelog.py` + `tests/test_validate_file.py` (task6 plan §12.2 §3-4)；建议同 PR 加上 Round 2 New Finding L1 的 precedence discriminator 与 atomic.py cleanup 冗余清理。
