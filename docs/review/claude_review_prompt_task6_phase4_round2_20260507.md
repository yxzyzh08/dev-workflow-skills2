# Claude Review Prompt — Task 6 Phase 4 Round 2 (post-fix regression review)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase4_status_transition_round2_review_20260507.md`。Round 2 通过后才能进入 Phase 5/6（`progress.py` 工作流状态机、Bug Flow、`update --advance`、`validate.py consistency`）。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 4 Round 2 fixes** 做一次回归 review。Round 1 评审（Codex 出具）给出 **(B) fix before Phase 5/6** 结论，列出 0 High / 2 Medium / 0 Low；本轮请确认两个 Medium 全部已修，并扫一眼新引入的代码 / 测试是否埋下新问题。

本轮是回归 review。范围：

- Round 1 review report：`docs/review/task6_phase4_status_transition_review_20260507.md`
- Round 1 实施代码：`skills/doc-guardian/scripts/status_transition.py` + `tests/test_status_transition.py`
- Round 2 fixes 的所有 diff（同两个文件，内容增量；未引入新文件、未改任何 shared module / Phase 3 脚本 / references）

**不要**要求 `progress.py` / `validate.py consistency` / `update --advance` / `bug-rework` / Gap-3/4/5 / event 白名单以外的事件已实现；这些仍是 Phase 5/6 范围。

## Round 1 baseline

- Phase 4 Round 1 review report: `docs/review/task6_phase4_status_transition_review_20260507.md`
- Recommendation: **(B) fix before Phase 5/6**
- Findings: 0 High / **2 Medium (M1, M2)** / 0 Low
  - **M1** — `compute_plan` 不拒绝未知 `type` 字符串；当 `current==target` 时会被错误判为 no-op，apply 直接成功无落盘也无校验
  - **M2** — `apply_plan` 信任 stale `PlanItem`：`compute_plan` 与 `apply_plan` 之间若 doc 在磁盘上被改动，会用旧的 target 覆盖新的状态（potentially illegal backward transition），且 `validate_file` 不会抓到（它只校 schema，不校 transition legality）

当前 Round 2 后测试 / compile：

```bash
python3 -m unittest discover -s tests
# Ran 160 tests in 0.370s
# OK
#  - baseline before round 1:  153 (Phase 1-3 + Phase 4 round 1 36 tests)
#  - new in round 2:             7 (M1 ×3 + M2 ×4)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK

python3 skills/doc-guardian/scripts/status_transition.py --help
python3 skills/doc-guardian/scripts/status_transition.py plan --help
python3 skills/doc-guardian/scripts/status_transition.py apply --help
# 三个 help 均正常
```

## Round 2 修复摘要（请逐条核对是否到位）

### M1 — Unknown `type` 在 `compute_plan` 阶段就 reject（必修）

- 修改：`skills/doc-guardian/scripts/status_transition.py`
  - 从 `skills._shared.dev_workflow.schema` 加 import `DOC_TYPES`
  - 在 `compute_plan` 的 errors 收集块里，紧跟 `if doc_type is None` 后加 `elif doc_type not in DOC_TYPES: errors.append("unknown doc type ...: not registered in schema DOC_TYPES")`
  - 该检查位于 gated_only 检查之前、no-op 短路之前，确保未知 type 永远走 reject 分支，不会因 `current==target` 偶然 no-op
- 新增 3 个 regression tests（`Round2RegressionTests` 类）：
  - `test_m1_unknown_type_at_target_status_rejected` — 即使 status==target 也必须 reject
  - `test_m1_unknown_type_in_mutating_status_rejected` — mutating 路径也 reject
  - `test_m1_unknown_type_blocks_mixed_batch` — 多 doc 批次中任一未知 type 阻止整批写入

### M2 — `apply_plan` 增加 freshness gate，避免 stale plan 落盘（必修）

- 修改：`skills/doc-guardian/scripts/status_transition.py`
  - 新增 private `_verify_plan_freshness(plan)`：对每个非 `op="reject"` item 重读文件 + parse_frontmatter，比较 on-disk `type` / `status` 与 `PlanItem.doc_type` / `PlanItem.current_status`；任一不一致则把所有 discrepancies 拼成消息后 raise `StatusTransitionError`
  - `apply_plan` 在 reject preflight 之后、`now=...` / mutate 内存构建之前调 `_verify_plan_freshness(plan)`
  - 覆盖 mutate **与** no-op 两种路径（no-op stale 也必须 reject，避免给 caller 假成功信号）
  - 错误消息含 `rel_path` + `(plan=..., on-disk=...)`，符合 reviewer 推荐的 stale-plan detail 要求
- 新增 4 个 regression tests：
  - `test_m2_apply_rejects_stale_status_change_for_mutate` — plan=draft→in-review，外部把 doc 改成 review-passed；apply 抛错，文件保留外部内容
  - `test_m2_apply_rejects_stale_status_change_for_no_op` — plan=no-op (already in-review)，外部把 doc 改成 draft；apply 抛错（no-op 也走 freshness gate）
  - `test_m2_apply_rejects_stale_type_change` — plan 的 type=srs，外部把 doc 改写成 development-plan；apply 抛错
  - `test_m2_apply_rejects_stale_in_multi_doc_batch` — 多 doc 中只有一个 stale，整批 abort、所有 doc 字节级不动

## 重点 review 项

请按以下维度逐条核对，不要跳过：

### A. M1 fix 是否到位

- `compute_plan` 是否在 errors 收集阶段就 reject 未知 type？
- 检查顺序：unknown-type check 是否位于 gated/no-op 短路之前？
- 错误消息是否带 `type` 实际值，便于 caller 排错？
- 是否引入对 `STATUSES` / `GATED_APPROVED_TYPES` 等其它 enum 的额外校验（不应有；本轮只补 `DOC_TYPES`）？
- 是否破坏了 Phase 4 round 1 既有的 `op="no-op"` 行为（已知合法 type、status==target、`is_incremental` 一致 → 仍应 no-op）？
- 是否破坏了 `_build_new_content` / `apply_plan` 既有逻辑（M1 是 compute_plan 内的局部修改）？

### B. M2 fix 是否到位

- `_verify_plan_freshness` 是否对所有非 reject item 都做检查（含 mutate 与 no-op）？
- 是否仅比较 `type` 与 `current_status`，不比 `is_incremental`（is_incremental 由 type 推导，type 一致 ⇒ is_incremental 一致；额外比对会 redundant）？
- 重读时遇到 OSError / FrontmatterError 是否作为 discrepancy 收集而非中断遍历，最终一次性 raise？
- 错误消息是否区分 "type changed" 与 "status changed" 两种 case，便于诊断？
- 是否在 reject preflight 之后、now / `_build_new_content` / transaction 之前调用？换言之 stale plan 不会浪费内存 promote，也绝对不进入 transaction？
- Phase 4 round 1 已有的 36 个测试是否仍全部通过（freshness gate 不能误伤 happy path）？

### C. 既有 invariant 是否保持

- `compute_plan` 仍是 read-only？`_verify_plan_freshness` 是 read-only？两者都不写文件、不进 transaction？
- `apply_plan` 仍遵循"reject preflight → freshness gate → 内存构建 finals → transaction.write_text → post-write self-validate"的固定顺序？
- post-write self-validate 仍调 `validate_module.validate_file`（in-process，不 subprocess）？
- 多 doc all-or-nothing rollback 仍由 `atomic.transaction()` 提供，未引入自定义回滚？
- 增量 doc 的 `[frontmatter]` Pending entry 仍通过 `changelog.promote_text` 在内存内 promote → 写盘前已 canonical？
- snapshot doc 仍只改 frontmatter status + updated，不引入 Change Log 章节？
- 幂等 no-op 仍 byte-for-byte 不动？（注意：M2 fix 让 no-op 经过 freshness 检查，但只读，不写；既有 byte-equality 测试仍应通过）

### D. 测试质量

- M1 的 3 个 regression test：
  - 是否覆盖未知 type 在 target / mutating / 多 doc 批次三种语境？
  - 是否同时检查 `op="reject"`、`errors` 含 "unknown doc type"、`apply_plan` 抛错、文件 byte-for-byte 不动？
- M2 的 4 个 regression test：
  - 是否覆盖 mutate stale / no-op stale / type stale / multi-doc stale 四种语境？
  - 是否使用"compute → 外部覆写文件 → apply"三段式时序？
  - 是否同时检查抛 `StatusTransitionError`、消息含 "stale plan" 与 "status changed" / "type changed"、文件保留外部内容（即 stale apply 不写）？
- 是否所有 round 2 新测都用 `tempfile.TemporaryDirectory` + temp fixtures？是否触碰真实 repo 的 `docs/` / `skills/`？（不应触碰）
- Round 1 的 36 个测试是否全部仍通过？（已在 above 测试统计中确认 153→160 全通）

### E. Cross-doc 一致性

- `task6_plan_20260507.md §9` 描述的 plan / apply / 幂等 / 多 doc atomicity 是否仍符合（M1/M2 是 strictness 提升，不是行为改设）？
- `doc-guardian/SKILL.md §6.7` 的 4 events / 调用顺序 / Change Log 原子性 / 幂等是否仍符合？
- `change-log-format.md §7.1` 的 `[frontmatter]` Pending entry 模式是否仍符合？
- `frontmatter-schema.md §1` universal fields 中 `type` 必属 enum 的原始要求，本次 M1 fix 是否更准确地兑现？

### F. 设计 / 可维护性

- M1 fix 的 import diff（多一个 `DOC_TYPES`）是否是最小侵入？
- M2 的 `_verify_plan_freshness` 是 module-level 函数还是嵌入 apply_plan？现在是 module-level 私有函数，便于未来 Phase 5 callers 在不同时机复用。是否合理？
- M2 是否需要把 `_verify_plan_freshness` 抽到 shared helper？(本 Round 2 不必；status_transition.py 唯一调用。Phase 5 progress.py 若需要可以再抽。)
- 错误消息格式是否一致（`rel_path: ...`），便于 caller 与 stderr 输出统一？
- import 顺序与 `noqa: E402` 是否仍合理？

### G. 已知 Phase 5/6 后续工作（不在本 review 评判范围）

- Phase 5 `progress.py` 工作流状态机（init / query / recover / update --event / update --task / release-close / release-start / bug-intake）
- Phase 5 `validate.py consistency`（Class 8 进度↔doc 一致性）
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` + Gap-3/4/5
- Phase 6 `progress.py update --advance` P6 矩阵
- Phase 7 full smoke + AGENTS/CLAUDE/plugin metadata polish

这些不应作为 Round 2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase4_status_transition_round2_review_20260507.md
```

评审报告需要包含以下章节（参考 Phase 3 round 2 review 的结构）：

1. **Executive Summary** — Round 2 总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5/6
2. **Round 1 Findings 回归状态** — M1 / M2 各自 ✅ Fixed / ⚠️ Partially Fixed / ❌ Not Fixed，附简短理由
3. **New Findings (Round 2)** — Round 2 修复或测试若引入了新的 H/M/L finding，列出 location + issue + impact + recommendation；没有则注明 "No new findings"
4. **Cross-Finding Consistency Check** — 各 reference / plan / SKILL.md 与新代码行为一致性
5. **Round 2 Implementation Quality Spot-checks** — `compute_plan` unknown-type 路径、`_verify_plan_freshness` 实现、新增 7 个 regression test 的覆盖度
6. **Checklist Results** — 按本 prompt §A-§F 各维度逐项 ✓ / ⚠️ / ❌
7. **Open Questions / Assumptions**（如有）
8. **Recommendation** — 三选一：
   - **(A) accept regression and proceed to Phase 5/6**（可附 Phase 5 之前可选清理 list）
   - **(B) fix before Phase 5/6**（必修 list；为何 Phase 5 不能在不修这些 finding 下推进）
   - **(C) revisit design**（哪些已闭环架构层决策被本批 implementation 触发了再设计需求）

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 5 前修
- 哪些可以推迟到 Phase 5/6/7
- 修复路径估计（行数级粗估）

## Boundaries

- 不要重写 `status_transition.py` / `tests/test_status_transition.py` / 其它脚本 / references / SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 5/6 设计讨论；如发现 Phase 5/6 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
