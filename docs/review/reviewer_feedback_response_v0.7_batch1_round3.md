# Reviewer Feedback Response — Batch 1 Round 3 SKILL.md Review

**Source Review**: `docs/review/skill_set_batch1_round3_review.md`
**Adopted In**: `skills/workflow-protocol/*` + `skills/doc-guardian/*` (round 3 修订)
**Date**: 2026-05-06
**Reviewed By**: User + Claude
**Review Cycle**: Task 5 Batch 1 第 3 轮

---

## Findings 处置一览（5 项新 finding）

| # | Severity | Finding 摘要 | 处置 | 关键决策 |
|---|----------|---------------|------|---------|
| H1 | High | required-artifacts §12 实现 Hint 仍含 substate_matches + eval | **采纳** | 重写 §12：删旧算法，加白名单 parser 完整伪码 + grammar；明确禁用 eval/exec |
| H2 | High | review-report skeleton 默认 pass 可绕过 review | **采纳 Option A** | enum 加 `pending`；skeleton 用 `pending`；transition 严格要求 `pass`（pending/fail 都 reject）|
| M3 | Medium | command-reference init/recover 未同步 v0.6 | **采纳** | init mutation `workflow_version: v0.5 → v0.6`；recover 加 terminal repair 语义 |
| M4 | Medium | SRS 新 bool 字段未同步 cheat sheet/SKILL summary | **采纳** | doc-guardian SKILL §4.4 + frontmatter cheat sheet 加 srs row：必含 release + is_multi_module + architecture_change |
| L5 | Low | ID 3 位文案不一致 + >999 模糊 | **采纳** | doc-guardian SKILL §4.3 改 `\d{3}`；frontmatter-schema 删"仍合法"措辞，明确"超 999 必须先 review cycle 升级" |

5 项全采纳，无反驳。

## 关键决策详解

### H2：选 reviewer Option A（加 `pending` enum）

reviewer 给两个选项：
- **A**：enum 加 `pending`，skeleton 用 `pending`，transition 严格要求 `pass`
- **B**：enum 保持 `pass|fail`，skeleton 用 `fail`，transition 同时检查 progress-history 中存在对应 review skill 的 `review-passed` event

选 A 理由：

1. **单一事实源**：`review_status` 字段本身充分决定 transition 合法性，不需要 cross-check progress-history
2. **schema 干净**：明确表达"未评审 / 评审通过 / 评审失败"三态语义；`pending` 直观
3. **实现简单**：transition guard 一行 `assert report.review_status == "pass"`；不需要 history scan
4. **bypass 难度**：要绕过必须直接编辑 report frontmatter 改 `review_status: pass` —— 这等同于篡改任意字段（现有 Forbidden 已禁），而不需要专门防护

代价：enum 多一个值；`severity_distribution` 在 pending 状态全 0 但 `review_status: pending`，schema 校验仍合法。

### H1：white-list parser 完整伪码

新 §12 加了：

- 完整 grammar：`<expr>` / `<comparison>` / `<variable>` / `<literal>` 4 个产生式
- 白名单 6 个变量、5 个运算符、3 类 literal
- `tokenize` / `parse` / `evaluate` 三个函数职责明示
- 显式禁止：`eval` / `exec` / `ast.literal_eval` / 变量逃逸 / 函数调用
- Stage 4 advance 改为无条件 append 全部 4 个 per-task entries（不再按 substate 匹配）

实现者读完伪码后能直接写 simple recursive descent parser。

### M4：SRS row 在两处都加

doc-guardian SKILL.md §4.4 cheat sheet 和 frontmatter-schema.md §5 cheat sheet 同步：把 srs 从泛化 row 单独拆出来，明示 `is_multi_module: bool` + `architecture_change: bool` 必含。validate.py 类 3 必须校验这两个字段存在且 YAML bool 类型合法。

### L5：>999 ID 扩展明文禁止

frontmatter-schema 加："当前 validate.py 只接受 3 位。若未来 ID 数量超过 999，必须先经 review cycle 升级 regex（改为 `\d{3,}`）和 directory-layout policy；在那之前 `BUG-1000` 等 4 位 ID 一律 reject。不允许以'未来扩展'为由当前接受 4 位 ID。"

避免实现者基于"将来可能扩展"做超前优化。

## v0.6 batch 1 round 2 → v0.7 batch 1 round 3 主要修改清单

| 文件 | 变化 |
|------|------|
| `skills/doc-guardian/references/required-artifacts.md` | H1: §12 重写完整白名单 parser 伪码 + grammar |
| `skills/doc-guardian/references/frontmatter-schema.md` | H2: code-review-report / test-review-report enum 加 pending；skeleton 用 pending；transition 改严格；M4: cheat sheet 加 srs row；L5: 删 ">999 仍合法" 措辞 |
| `skills/doc-guardian/SKILL.md` | M4: cheat sheet 加 srs row；L5: ID regex 改 \d{3}；class 4 加 pending enum 提及 |
| `skills/workflow-protocol/SKILL.md` | H2: Stage 4 task state 转移强调 review_status: pass（pending 不允许）|
| `skills/workflow-protocol/references/command-reference.md` | M3: init mutation v0.5→v0.6；recover 加 terminal 语义 |

## 没有采纳的项

无。5 项全部采纳。

## 评审循环统计

| 轮次 | Finding 总数 | High | Medium | Low | Recommendation |
|------|-------------|------|--------|-----|----------------|
| design v0.1 | 9 | 5 | 4 | 0 | fix |
| design v0.2 | 8 | 5 | 3 | 0 | fix |
| design v0.3 | 6 | 3 | 2 | 1 | fix |
| design v0.4 | 4 | 0 | 2 | 2 | fix |
| batch 1 round 1 | 16 | 8 | 5 | 3 | fix |
| batch 1 round 2 | 9 | 4 | 4 | 1 | fix |
| **batch 1 round 3** | **5** | **2** | **2** | **1** | fix |

收敛趋势：从 round 2 的 9 项降到 round 3 的 5 项；High 4 → 2。round 4 预期 High = 0 或 1，可推进 batch 2。

## 验证 Round 2 partial-resolved 是否在 Round 3 全部覆盖

Round 2 中 4 项 partial-resolved finding，对照 Round 3 处置：

| Round 2 残留 | Round 3 覆盖 |
|-------------|--------------|
| H1 round 2 partial（DSL Hint）| ✅ H1 round 3 重写 §12 |
| M5 round 2 partial（command-reference 未同步）| ✅ M3 round 3 |
| M6 round 2 partial（substate_matches 残留）| ✅ H1 round 3（合并修） |
| M7 round 2 partial（skeleton 默认值）| ✅ H2 round 3（升级到 High，因为是 bypass）|
| M8 round 2 partial（ID summary 不一致）| ✅ L5 round 3 |

5 项 round 2 残留全部被 round 3 处置。
