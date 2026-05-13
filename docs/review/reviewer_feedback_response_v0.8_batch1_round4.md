# Reviewer Feedback Response — Batch 1 Round 4 SKILL.md Review

**Source Review**: `docs/review/skill_set_batch1_round4_review.md`
**Adopted In**: `skills/workflow-protocol/*` + `skills/doc-guardian/*` (round 4 修订)
**Date**: 2026-05-06
**Reviewed By**: User + Claude
**Review Cycle**: Task 5 Batch 1 第 4 轮

---

## Findings 处置一览（5 项新 finding）

| # | Severity | Finding 摘要 | 处置 | 关键决策 |
|---|----------|---------------|------|---------|
| H1 | High | `pending` 与 "pass iff blocking=0" invariant 冲突 | **采纳** | 改为三态规则：pending 豁免、pass 强制 blocking=0、fail 任意；同步 SKILL §4.4 row 与"关键不变量" |
| M2 | Medium | DSL grammar 缺括号产生式 + enum literal 白名单未定义 | **采纳** | 补完整 grammar：`<primary>` 含括号；定义 enum literal 白名单 3 类；hyphenated 仅 RHS 接受；加 6 个 parser test cases |
| M3 | Medium | terminal recover 未定义 post-terminal 非法 history | **采纳** | recover replay 时跑状态机 validator；遇 terminal event 后再有 mutating entry → exit 1（fatal）；不允许 silent truncate |
| M4 | Medium | doc-guardian §7 与 required-artifacts 不一致 | **采纳** | §7.1 重写为对齐表：Stage 4 4 个 per-task 无条件；Stage 7 单文件 + 内部章节澄清 |
| L5 | Low | SRS 示例缺 round 3 新 2 bool 字段 | **采纳** | 示例补 `is_multi_module: false` + `architecture_change: false` + 注释 |

5 项全采纳，无反驳。

## 关键决策详解

### H1：三态不变量替换原 "pass iff blocking=0"

原规则：`review_status == "pass" iff blocking_findings_count == 0`（全局适用）

新三态规则：

| review_status | blocking_findings_count 约束 | doc status | 适用阶段 |
|---------------|------------------------------|------------|---------|
| `pending` | **豁免**（可为 0，不强制关系）| `draft` | skeleton |
| `pass` | **必须为 0** | `review-passed` | review skill 填，无 issue |
| `fail` | 可任意 ≥ 0 | `in-review` 或 `revising` | review skill 填，有 issue |

skeleton（`development-test-write` / `development-code-write` 创建）的 `pending + 0 + low` 在新规则下合法。validate.py 类 3/4 按 review_status 值分支校验。

`关键不变量` 段也同步更新，避免冲突。`doc-guardian/SKILL.md` §4.3 字段快查 row 加 pending。

### M2：DSL grammar 完整化

补 4 个 production：

```
<expr>       = <or-expr>
<or-expr>    = <and-expr> ( '||' <and-expr> )*
<and-expr>   = <primary> ( '&&' <primary> )*
<primary>    = <comparison> | '(' <expr> ')'
```

其余 `<comparison>` / `<variable>` / `<literal>` / `<bool>` / `<enum-literal>` / `<quoted-string>` / `<identifier>` 也明确定义。

**Enum literal 白名单**（unquoted token 仅以下 3 类 16 个值视为 enum literal，其他报错）：

- scenario：`S1` / `S2` / `S3` / `S4`（4 个）
- scenario_subtype：`S2-1` / `S2-2` / `S2-3` / `S2-4`（4 个）
- current_stage：`prd-inception` / `srs-specification` / `architecture-design` / `development` / `testing` / `delivery` / `project-retrospective` / `workflow-incident-analysis`（8 个）

**Hyphenated literal 处理**：tokenizer 识别 `[A-Za-z0-9-]+` 序列；仅当出现在 `<comparison>` RHS 位置才视为 enum literal；其他位置（如变量名）报错。`<identifier>` 严格 `[a-z][a-z0-9_]*`，不含 hyphen 或大写。

加 6 个 parser test case 实现者必须覆盖。

### M3：recover replay validator

terminal event（`incident-resolve --action abort` / `--action reconstruct`）之后任何 mutating history entry → fatal error（exit 1）。规则明文：

- ✗ silent truncate（掩盖 history corruption）
- ✗ replay 后续非法 entry（"复活"风险）
- ✓ replay 到 terminal 后剩下只允许 query/recover 类 entry（无 state 变化）
- ✓ 如未来需要 force truncate，单独走 design review 加 `--force-truncate-after-terminal` 选项

避免实现者私自决定行为分叉。

### M4：doc-guardian §7 重写为对齐表

§7.1 改为表格形式，明示每 stage 必备清单与 required-artifacts.md 完全同源：

- Stage 4 加 "**每个 task 无条件 4 个 per-task artifacts**"，删除 v0.5/v0.6 round 3 残留的 "复杂任务必有 Detailed Design" 条件描述
- Stage 7 澄清单文件 + 内部章节：Issue Analysis / Improvement Proposals 是 retrospective.md 的章节，不是独立 doc

§7.2 条件必备改为引用 condition DSL：`is_multi_module == true` / `architecture_change == true`。

### L5：SRS 示例补字段 + 注释

```yaml
release: "0.1"
is_multi_module: false                       # 必含；srs-write 决定；required-artifacts.md DSL 判定 Integration Plan 必备性
architecture_change: false                   # 必含；srs-write 决定；DSL 判定 Architecture Delta 必备性
```

注释说明字段来源责任。

## v0.7 → v0.8 主要修改清单

| 文件 | 变化 |
|------|------|
| `skills/doc-guardian/references/frontmatter-schema.md` | H1: code-review-report / test-review-report 加三态约束块 + 关键不变量改写；L5: SRS 示例补 2 bool 字段 |
| `skills/doc-guardian/SKILL.md` | H1: §4.3 review_status row 加 pending；M4: §7.1 重写表格对齐 required-artifacts |
| `skills/doc-guardian/references/required-artifacts.md` | M2: DSL 加完整 grammar + enum literal 白名单 + 6 个 parser test cases |
| `skills/workflow-protocol/references/command-reference.md` | M3: recover 加 replay validator 规则；terminal 后非法 entry → fatal |

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
| batch 1 round 3 | 5 | 2 | 2 | 1 | fix |
| **batch 1 round 4** | **5** | **1** | **3** | **1** | fix |

收敛持续：High 8 → 4 → 2 → 1。Round 5 预期 High = 0，可推进 batch 2。

## 验证 Round 3 partial-resolved 是否在 Round 4 全部覆盖

| Round 3 残留 | Round 4 覆盖 |
|-------------|--------------|
| H1 round 3（DSL 残留 substate_matches）→ M2 round 4 grammar 不全 | ✅ M2 round 4 |
| H2 round 3（pending invariant 冲突）| ✅ H1 round 4 |
| M3 round 3（init/recover）→ recover edge case | ✅ M3 round 4 |
| M4 round 3（SRS bool cheat sheet）→ 示例残留 | ✅ L5 round 4 |
| L5 round 3（ID 文案）| ✅ 已 round 3 fully resolved |

5 项 round 3 残留全覆盖。

## 进 batch 2 评估

Round 4 仅 1 High（H1 invariant），已修。如果 round 5 验证：
- High = 0 + finding ≤ 3 → **进 batch 2**
- High = 1 → 再 round 6
- High ≥ 2 → 考虑暂停 review，进 Task 6 实际实现获信号
