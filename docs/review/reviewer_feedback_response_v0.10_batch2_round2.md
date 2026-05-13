# Reviewer Feedback Response — Batch 2 Round 2 Review

**Source Review**: `docs/review/skill_set_batch2_round2_review.md`
**Adopted In**: `skills/scenario-dispatcher/*` + `skills/bug-triage/*` + `skills/workflow-evolution/*` + `skills/workflow-protocol/references/command-reference.md`
**Date**: 2026-05-06
**Reviewed By**: User + Claude
**Review Cycle**: Task 5 Batch 2 第二轮（review status: 0 New High + 6 Medium + 1 Low；Round 1 全部 ✅ 已修主路径，⚠️ 部分文档残留）

---

## Findings 处置一览（7 项全部采纳）

### Round 1 Finding 残留补丁（4 项 ⚠️ → ✅）

| Round 1 # | 残留点 | Round 2 处置 |
|-----------|-------|-------------|
| F1 PRD-exception INCIDENT changelog | root-cause-rubric Example E 缺 `changelog.py promote → validate.py file` 步；triage-decision-tree §4.3 validate checklist 不完整 | M2 修：Example E 加 promote/validate 步骤；§4.3 改为完整 1-7 类 + 引用 doc-guardian §5.1 |
| F2 active 非 testing reject | bug-triage frontmatter description 仍写"其他 stage 主动报"；triage-decision-tree §1 顶层伪代码缺 testing/review-passed early gate | M1 修：description 收紧为"仅 testing AND review-passed"；§1 顶层决策树拆 active 子分支为 testing-pass / non-testing-reject 两路；§2.1 active_mode_triage() 加 Step 0 early gate |
| F4 advisory vs patch | retrospective consumption 模板没按每条 advisory 标 Action Item；examples §4 没示范 | M4 修：SKILL §4.3 + incident-analysis-template §5 加 Action Item 列；retrospective 模板顶部加 Advisory Notice；examples §4 全部加 per-item Action Item |
| F5 finalization 序列 | 幂等性"直接重试 incident-resolve"未确认 Pending 已空 / validate 已 pass | M5 修：拆"finalization complete"vs"body-only 已写"两态；后者必须重 promote/validate；加 reentrant_finalization_check 伪代码 |

### Round 2 New Findings（6 Medium + 1 Low）

| # | Finding | 处置 | 关键决策 |
|---|---------|------|---------|
| M1 | active mode 入口描述与伪代码 early gate | **同步三层 gate** | bug-triage description / §2.1 / triage-decision-tree §1 顶层 + §2.1 active_mode_triage() 全部前置 = `progress.py bug-start` 前置 (current_stage==testing AND sub_state==review-passed)；不读 BUG / 不写 frontmatter / 不调 progress.py |
| M2 | PRD-exception Example E + §4.3 validate checklist | **加 promote 步骤 + 完整 7 类清单** | Example E 加 `changelog.py promote → validate.py file → progress.py incident-start`；§4.3 改为完整 1-7 类（事实源 doc-guardian §5.1）+ 注明 class 8 (consistency) 不在本时点 |
| M3 | post-close BUG 模板 Pending 仍非空 | **改为 HTML comment** | 模板 `## Pending Changes` 下改成 `<!-- empty after changelog.py promote -->`，符合 change-log-format.md §2.3 空章节规则 |
| M4 | retrospective Action Item 标注 + advisory notice | **加表列 + 顶部 notice + examples 同步** | SKILL §4.3 / incident-analysis-template §5 retrospective output 模板：5 个 suggestions table 加 Action Item 列、顶部加 Advisory Notice；incident examples §4.1/§4.2/§4.3 的 §4 全部加 per-item Action Item + 末尾加 advisory only 提示 |
| M5 | workflow-evolution 幂等性 6.e-g 完成性确认 | **拆两态 + reentrant_finalization_check** | SKILL §7.1 严格 6 条规则（含 Pending 为空 + validate 重新 pass）；§7.2 表拆 `finalization complete` vs `body/frontmatter complete but finalization unknown` 两行；§10 Recovery 改写不允许"直接重试"；incident-analysis-template §1.6.1 加伪代码示范 reentrant 检查 |
| M6 | progress.py 二次 validate 契约不一致 | **command-reference 加 validate 前置（Option A）** | command-reference §10 incident-start + §11 incident-resolve 前置加 `validate.py file <incident-path> exit 0`；保持 batch 2 double-safety 设计，caller validate 一次 + progress.py 二次 |
| L1 | examples 跳过 finalization block | **3 个 examples 加 Finalization sequence 说明** | Example A/B/C §7 Resolution 与 incident-resolve 之间加 6 行 6.b-g 序列说明，强化 §1.6 记忆点 |

## 关键决策详解

### M1 三层 gate 一致性

bug-triage 早期 description 写"active release 其他 stage 主动报 bug 时由 dispatcher 调用"——这与 round 1 F2 收敛后的"严格 testing-only" 不一致。triage-decision-tree §1 顶层伪代码也只写 `release_state == active → Active Mode`，缺 stage 检查。

修复后三层 gate 完全一致：

```
1. scenario-dispatcher（已对）：
   - current_stage == testing AND sub_state == review-passed → invoke bug-triage active
   - 其他 → reject + 提示

2. bug-triage SKILL §2.1（已对）：
   - 前置严格要求 (testing, review-passed)
   - description 收紧为"仅 testing AND review-passed"

3. bug-triage triage-decision-tree §1 + §2.1（本轮修）：
   - 顶层决策树 active 分支拆 testing-pass / non-testing-reject
   - active_mode_triage() Step 0 early gate；缺即 reject 不读 BUG
```

实现时三层任一前置失败都能在最早阶段拦截，不会写出 root_cause 已设但 bug_flow 未启动的半成品状态。

### M2 INCIDENT validate 7 类完整清单

triage-decision-tree §4.3 原写"覆盖 single-file check 1-7"，但实际只列 frontmatter / ID / cross-ref / change-log 4 类相关项。修复后改为完整 7 类清单 + 事实源引用：

| 类 | 检查 | INCIDENT skeleton 必满足 |
|----|------|------|
| 1 Path | `docs/incident/INCIDENT-<NNN>.md` | ✓ |
| 2 Naming | `INCIDENT-\d{3}.md` 大写连字符 + 3 位 zero-padded | ✓ |
| 3 Frontmatter Schema | universal 6 + 扩展 4 字段 + status/type/resolution_action enum | ✓ |
| 4 Frontmatter Format | timestamp / incident_id / owner / resolution_action 格式 | ✓ |
| 5 Cross-Reference | triggered_by_bug 解析 → docs/bug/<id>.md 文件存在 | ✓ |
| 6 Change Log Discipline | Pending 已空 + Change Log 格式 | ✓ |
| 7 ID Uniqueness | INCIDENT-NNN 不与既有冲突 | ✓ |
| 8 Consistency | progress.md 一致性 | 不在本时点（incident-start 才会改 progress.md）|

不重复维护一份 partial checklist，事实源指向 `skills/doc-guardian/SKILL.md` §5.1。

### M3 Pending Changes 空章节合法形式

doc-guardian `change-log-format.md` §2.3 明确：

- ✓ `## Pending Changes\n\n## Change Log` （纯空）
- ✓ `## Pending Changes\n<!-- comments allowed -->\n\n## Change Log` （仅 HTML comment）
- ✗ 任何非注释、非空白行（包括 list item `- (空，已 promote)`）

post-close BUG 模板早期写 `- (空，已 promote)` 实际上是非空行，validate.py 类 6 会拒绝。修复后改为 HTML comment：`<!-- empty after changelog.py promote -->`，既人类可读又符合规范。

### M4 retrospective Action Item 全文一致性

retrospective consumption mode 与 incident analysis mode 在 advisory/patch 边界上必须一致。修复 4 处：

1. workflow-evolution SKILL §4.3 retrospective output 模板：5 个 suggestions table 全部加 Action Item 列
2. incident-analysis-template §5 同上 + 顶部加 Advisory Notice
3. incident examples §4.1/§4.2/§4.3 的 §4 改为 per-item Action Item 表（不再是只列建议+优先级）
4. 末尾加 "advisory only；禁止 patch/diff" 提示

实现者读 incident mode 与 retrospective mode 都得到同样的 advisory/patch 边界，不再分叉。

### M5 finalization 完成性二次确认

原 idempotency 表写"如已写 body 但 incident-resolve 调用失败，重 invoke 检测到 INCIDENT body §3-§7 已填、frontmatter resolution_action 已设 → 跳过 body 编辑，直接重试 incident-resolve"。这是 silent skip——会绕过 Step 6.e-g 的 Pending entry / promote / validate。

修复：拆为两态严格规则。

```python
def reentrant_finalization_check(incident_path):
    if status == review-passed AND resolution_action ∈ enum AND body §3-§7 done:
        # 必须再跑一次 validate
        validate_pass = run_validate_py_file(incident_path).exit_code == 0
        pending_empty = pending_changes_section_is_empty(incident)
        
        if validate_pass and pending_empty:
            return retry(incident_resolve)  # finalization complete，幂等重试
        else:
            return resume_step_6_e_through_g(...)  # body-only 已写，必须重 promote/validate
```

不允许"silent skip 到 incident-resolve"。

### M6 progress.py 二次 validate 契约（Option A）

batch 2 文档（bug-triage SKILL §5.2 / workflow-evolution SKILL §3.1 Step 7）声称 "progress.py 内部再次 validate INCIDENT 文件（双重保险）"。但 batch 1 command-reference §10 incident-start / §11 incident-resolve 前置只列 doc-guardian validate（implicit through "通过 doc-guardian validate"）/ frontmatter fields，没有显式 `validate.py file <incident-path> exit 0`。

修复（Option A，与 batch 2 double-safety 一致）：command-reference §10 / §11 前置显式加：

```
- skills/doc-guardian/scripts/validate.py file <incident-report-path> exit 0
```

incident-start 加：double-safety 二次 validate skeleton。
incident-resolve 加：double-safety 二次 validate finalization 完整性 + Pending 已空（防 caller silent skip Step 6.f/g）+ frontmatter status==review-passed + resolution_action ∈ enum 与命令参数一致。

caller validate 一次（bug-triage / workflow-evolution Step 6.g）+ progress.py 再次 validate = double-safety；任一漏 promote / silent skip 都被拦下。

### L1 examples Finalization 序列展示

incident-analysis-template Example A/B/C 末尾原直接从 §7 Resolution 跳到 incident-resolve 效果展示，跳过了 §1.6 严格 6.b-g 序列。修复后每个 example 加 "Finalization sequence" 段：

```
Finalization sequence:
  6.b 改 frontmatter resolution_action: null → <enum>
  6.c 改 frontmatter status: draft → review-passed
  6.d 改 frontmatter updated: <now>
  6.e 加 Pending entry "incident analysis 完成"
  6.f changelog.py promote
  6.g validate.py file → exit 0
仅在 6.g pass 后调 progress.py incident-resolve
```

主模板已强制；examples 同步示范让实现者复制时不漏序列。

## 影响的物理文件清单（7 份 + 1）

| 文件 | M1 | M2 | M3 | M4 | M5 | M6 | L1 |
|------|----|----|----|----|----|----|----|
| `skills/scenario-dispatcher/SKILL.md` | — | — | — | — | — | — | — |
| `skills/scenario-dispatcher/references/scenario-decision-tree.md` | — | — | — | — | — | — | — |
| `skills/bug-triage/SKILL.md` | ✓ frontmatter | — | — | — | — | — | — |
| `skills/bug-triage/references/root-cause-rubric.md` | — | ✓ §7.5 Example E | — | — | — | — | — |
| `skills/bug-triage/references/triage-decision-tree.md` | ✓ §1 顶层 / §2.1 Step 0 | ✓ §4.3 完整清单 | ✓ §3.2 模板 | — | — | — | — |
| `skills/workflow-evolution/SKILL.md` | — | — | — | ✓ §4.3 模板 | ✓ §7.1 / §7.2 / §10 | — | — |
| `skills/workflow-evolution/references/incident-analysis-template.md` | — | — | — | ✓ §5 / §4.1-§4.3 | ✓ §1.6.1 新增 | — | ✓ Example A/B/C |
| `skills/workflow-protocol/references/command-reference.md`（**batch 1 reference 同步**）| — | — | — | — | — | ✓ §10 + §11 前置 | — |

scenario-dispatcher 在本轮**无修改**——其 active non-testing reject 路径在 round 1 F2 已正确落实。

## 没有采纳/弱采纳的项

无。7 项 Finding 全部采纳：6 Medium 全部修；1 Low 也修（虽不阻塞，但 examples 是实现者最易复制的路径，加 finalization 序列展示有低成本高收益）。M6 涉及修改 batch 1 已闭环的 command-reference.md，但属于**前置缺失补全**（不改 mutation 语义），与 batch 2 double-safety 设计一致，是合理小补丁。

## 评审循环统计

| 版本 | Finding 总数 | High | Medium | Low | Recommendation |
|------|-------------|------|--------|-----|---------------|
| design v0.1 | 9 | 5 | 4 | 0 | fix |
| design v0.2 | 8 | 5 | 3 | 0 | fix |
| design v0.3 | 6 | 3 | 2 | 1 | fix |
| design v0.4 | 4 | 0 | 2 | 2 | fix |
| batch 1 round 1 | 16 | 8 | 5 | 3 | fix |
| batch 1 round 2 | 9 | 4 | 4 | 1 | fix |
| batch 1 round 3 | 5 | 2 | 2 | 1 | fix |
| batch 1 round 4 | 5 | 1 | 3 | 1 | fix |
| batch 1 round 5 | 2 | 0 | 1 | 1 | (A) 闭环 |
| batch 2 round 1 | 5 | 3 | 2 | 0 | fix |
| **batch 2 round 2** | **7** | **0** | **6** | **1** | **(B) 小 patch + 复评** |

收敛特征：

- High 已清零（与 design v0.4 → batch 1 round 5 模式一致）
- Medium 数量 6 偏多但全部是文档同步残留（不涉及设计层）
- 5 项 Round 1 残留全部 ✅ → ✅；2 项纯 Round 2 新发现（M3 post-close 模板 / M6 progress.py 契约）
- 预期 round 3 finding 数会大幅下降（< 3）；如全部 ✅ + 0 New High 即可进 batch 3

---

**End of Feedback Response v0.10 (batch 2 round 2)**
