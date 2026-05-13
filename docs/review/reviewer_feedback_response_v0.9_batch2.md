# Reviewer Feedback Response — Batch 2 Round 1 Review

**Source Review**: `docs/review/skill_set_batch2_review.md`
**Adopted In**: `skills/scenario-dispatcher/*` + `skills/bug-triage/*` + `skills/workflow-evolution/*`
**Date**: 2026-05-06
**Reviewed By**: User + Claude
**Review Cycle**: Task 5 Batch 2 第一轮（review status: 3 High + 2 Medium）

---

## Findings 处置一览（5 项全部采纳）

### High（3 项）

| # | Finding | 处置 | 关键设计决策 |
|---|---------|------|--------------|
| F1 | PRD-exception INCIDENT skeleton 因 Pending Changes 未 promote 而无法通过 doc-guardian validate | **加 changelog.py promote 步骤** | bug-triage 创建 INCIDENT skeleton 后必须按序：写文件含一条 Pending entry → `changelog.py promote <incident-path>` → `validate.py file <incident-path>` → `progress.py incident-start`；不允许跳过 promote |
| F2 | active 非 testing 阶段用户报 bug 的路由与 `bug-start` 前置冲突，known-issue 路径无 schema 承载 | **统一收敛为 reject**（Option A） | scenario-dispatcher 在 `current_stage != testing` OR `sub_state != review-passed` 时一律拒绝 bug-triage active mode；提示用户 (a) 等本 release 推进到 testing 阶段；(b) 把现象记入当前 stage doc 的 known-issue 段；不创建 orphan BUG report、不调 progress.py |
| F3 | root-cause-rubric 引入"非真 bug / out-of-scope" 第五路径，但 schema 无承载 | **删除第五路径，强制 4 类输出**（Option A） | bug-triage active mode 必须从 {srs, architecture, development, prd-exception} 中选 1；不允许第五状态 / 不允许 silent close BUG；用户判定 BUG 应撤销时必须**手动删除** BUG-NNN.md 文件，bug-triage 退出不调 progress.py |

### Medium（2 项）

| # | Finding | 处置 | 关键决策 |
|---|---------|------|---------|
| F4 | workflow-evolution 递归约束与 §4 Workflow Improvement Suggestions / 自评 #13 互相矛盾 | **严格区分 patch vs advisory** | 允许并鼓励 §4 输出**精确的 advisory 建议**（引用具体 skill / 章节 / rubric 项）；禁止输出 patch / diff / unified diff 直接编辑本 skill 集文件；每条 advisory 必须标注 "Action Item: 提交 dev-workflow-skills2 design proposal review cycle"；自评 #13 改为"是否输出 patch/diff（不是 advisory 建议）"，新增 #14 强化约束 |
| F5 | INCIDENT finalization promote/validate 顺序模糊，可能让最终 frontmatter 逃过 validate | **明确单一原子序列** | Step 6.a-g 严格序列：§7 body → frontmatter (resolution_action + status + updated) → Pending entry → `changelog.py promote` → `validate.py file` → `progress.py incident-resolve`；validate 后到 incident-resolve 之间禁止 doc 编辑；后续如需补充必须重走 6.a-g |

## 关键决策详解

### F1 PRD-exception INCIDENT 必经 changelog.py promote

**问题**：`workflow-incident` 是增量类 doc，`validate.py` 类 6 (Change Log Discipline) 要求 `## Pending Changes` 为空；但 bug-triage 创建 skeleton 时模板含未 promote 的 Pending entry，且 §3.1 Step 7 未列 promote。导致 validate fail → incident-start 前置不满足 → 整条 PRD-exception 路径不可达。

**修复后流程**（bug-triage SKILL.md §3.1 Step 7d / §5.1 Step 1-4 / triage-decision-tree.md §2.1 / §4.1 / §4.3 / §7.4）：

```
prd-exception 分支：
1. bug-triage 写 INCIDENT-NNN.md 文件（含 frontmatter + 占位 body + 一条 Pending Changes entry "skeleton 创建"）
2. bug-triage 调 changelog.py promote <incident-path>
   → Pending Changes 清空，Change Log 含创建 entry（按日期分组）
3. bug-triage 调 validate.py file <incident-path>
   → 必须 exit 0（类 6 + 类 3/4 + 类 5 全 pass）
4. bug-triage 调 progress.py incident-start --bug <bug-path> --report <incident-path>
   → progress.py 内部再次 validate INCIDENT 文件（双重保险）
```

模板更新展示 "promote 前" 与 "promote 后" 两种状态，避免实现者混淆。

### F2 active 非 testing 阶段报 bug 统一 reject

**问题**：早期版本允许 active release 任何 stage 用户主动报 bug 进入 bug-triage active mode；但 batch 1 `progress.py bug-start` 前置：`current_stage==testing AND sub_state==review-passed`。三份文档给实现者三种不兼容选择：
- 直接 triage 并调用会失败的 bug-start
- 创建 "known-issue BUG"（target_release/root_cause null 不调 progress.py）→ orphan doc，无 schema 字段，无 Bootstrap 重 triage 触发器
- 拒绝到 testing 再处理

**修复**（scenario-dispatcher SKILL.md §2/§3/§5/§6/§9 + scenario-decision-tree.md §4.2/§5/§8.9 + bug-triage SKILL.md §2.1/§9 + triage-decision-tree.md Example B）：

收敛为 Option A（"reject + 提示路径"）：

| 触发条件 | dispatcher 反应 |
|---------|---------------|
| `release_state==active` AND `current_stage==testing` AND `sub_state==review-passed` 用户主动报 bug | route to bug-triage active mode（与 testing-write 自动触发同路径）|
| `release_state==active` 但 stage/sub_state 不满足 `bug-start` 前置时用户主动报 bug | **reject**；解释 bug-start 前置；提示 (a) 等 testing 阶段；(b) 记入当前 stage doc 的 known-issue 段；**不**创建 BUG report、**不**调 progress.py |

理由：保持 dispatcher / bug-triage / progress.py 三层前置一致；不引入 schema 扩展（Option B）。

### F3 强制 active mode 4 类输出（删除 out-of-scope 第五路径）

**问题**：root-cause-rubric Example D 让 bug-triage 在某些"非 SRS 范围"反馈中"关闭 BUG"、"不调 progress.py"、"保留 documented limitation"。但 `bug-report` schema 没有 `triage_status / final_status / out_of_scope` 字段，progress.py 没有"关闭未进入 bug_flow 的 BUG"子命令。

**修复**（root-cause-rubric.md §4.4a 新增 + §7.4 Example D 重写）：

bug-triage active mode **强制**从 {srs, architecture, development, prd-exception} 选 1：

- 留 root_cause: null 调 bug-start → progress.py 拒绝（参数与 frontmatter 一致校验）
- 写第五种值（out-of-scope / rejected / documented） → doc-guardian validate.py 拒绝
- silently 关闭 BUG report → bug-triage 没有该子命令

如 bug-triage 判定 BUG 不在 SRS 范围 / 非目标用户群反馈，**升级用户决策**：

1. 用户希望扩 SRS 接收该需求 → root_cause = `srs`
2. 用户判定 BUG 应撤销 → 用户**手动删除** docs/bug/BUG-NNN.md（bug-triage 无权撤销）；删除后 bug-triage 退出，不调 progress.py
3. 用户判定触及产品方向问题 → root_cause = `prd-exception`

不引入 schema 扩展（Option B 留待 batch 1 design 层独立 review）。

### F4 区分 advisory 建议（允许）vs patch/diff（禁止）

**问题**：递归悖论应禁止 workflow-evolution 直接 patch dev-workflow-skills2 自身文件，但不应禁止合法 advisory 改进建议。原 SKILL §8.2 + 自评 #13 表述把"具体建议"也判为违规，会让 §4 模板变空泛。

**修复**（workflow-evolution SKILL.md §8.2 重写 + §3.5 自评清单加 #10/#11/#12 + incident-analysis-template.md §1.2 §4 模板加注 + §3 自评清单加 #13/#14）：

| 行为 | 允许 | 例子 |
|------|------|------|
| 输出 advisory 改进建议（自然语言）+ 引用具体 skill/章节/rubric | ✓ | "建议 prd-review SKILL.md §6.3 加'NFR feasibility check'子项" |
| 引用具体 skill/章节做精确建议 | ✓ | "建议在 workflow-protocol §5.1 P6 矩阵 D 维度加..." |
| 标注 "Action Item: 提交 dev-workflow-skills2 design proposal review cycle" | ✓ | 每条 advisory 必标 |
| 输出 patch / diff / unified diff | ✗ | `--- a/skills/...` |
| 直接编辑 dev-workflow-skills2 文件 | ✗ | Edit / Write 任何文件 |
| 自行声明 "本建议已采纳" / "本 incident 自动改 spec" | ✗ | patch 类语义 |

自评清单从 9 项扩到 12 项（SKILL.md）/ 13 项扩到 16 项（incident-analysis-template.md），新增项分别覆盖 advisory 精确性、Action Item 标注、patch 禁止、finalization 顺序、Pending entry 完整性。

### F5 INCIDENT Finalization 单一原子序列

**问题**：原 §3.1 Step 6 模糊（"先 promote → validate → 全 pass，再设 status: review-passed"），让最终 frontmatter mutation 在 validate 之后，绕开 doc-guardian change-log discipline。

**修复**（workflow-evolution SKILL.md §3.1 Step 6.a-g + §3.4 + §9 加 2 条 Forbidden + incident-analysis-template.md §1.6 新增 + §3 自评 #15/#16）：

```
Step 6 严格序列（按字母顺序，缺一则失败）：
  a. 填 INCIDENT body §7 Resolution
  b. 改 frontmatter resolution_action: null → <enum>
  c. 改 frontmatter status: draft → review-passed
  d. 改 frontmatter updated: <now>
  e. 加 ## Pending Changes entry（覆盖 §3-§7 body 编辑 + frontmatter mutation）
  f. changelog.py promote <incident-path>
  g. validate.py file <incident-path> → 必须 exit 0
Step 7: 仅在 6.g pass 后调 progress.py incident-resolve --action <enum>
```

新增 Forbidden Actions 2 条：

- ❌ validate.py pass 后再改 INCIDENT frontmatter / body（必须重走 6.a-g 含再 promote + 再 validate）
- ❌ 跳过 changelog.py promote 直接 validate（每次编辑必须有 Pending entry）

## 影响的物理文件清单

| 文件 | F1 | F2 | F3 | F4 | F5 |
|------|----|----|----|----|----|
| `skills/scenario-dispatcher/SKILL.md` | — | ✓ §3 / §5.1 / §6.2 / §6.3 / §9 | — | — | — |
| `skills/scenario-dispatcher/references/scenario-decision-tree.md` | — | ✓ §4.2 / §5 / §8.9 新增 | — | — | — |
| `skills/bug-triage/SKILL.md` | ✓ §3.1 / §5.1 / §5.2 | ✓ §2.1 / §9 | — | — | — |
| `skills/bug-triage/references/root-cause-rubric.md` | — | — | ✓ §4.4a 新增 / §7.4 重写 | — | — |
| `skills/bug-triage/references/triage-decision-tree.md` | ✓ §2.1 / §4.1 / §4.3 / §7.4 | ✓ §7.2 Example B 重写 | — | — | — |
| `skills/workflow-evolution/SKILL.md` | — | — | — | ✓ §3.5 / §8.2 重写 / §9 | ✓ §3.1 / §3.4 / §9 加 2 条 |
| `skills/workflow-evolution/references/incident-analysis-template.md` | — | — | — | ✓ §1.2 / §3 自评 #13/#14 | ✓ §1.6 新增 / §3 自评 #15/#16 |

7 份文件全部更新。

## 没有采纳/弱采纳的项

无强反驳。5 项 Finding 全部采纳，且都选了 codex 标记为推荐的 Option A（不引入 schema 扩展）。这与 handoff §11 "spec-level 推演收益递减" 一致：batch 2 不引入 batch 1 design 层改动，复杂扩展（如 known-issue queue / triage_status 字段）留待独立 design proposal review cycle。

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
| **batch 2 round 1** | **5** | **3** | **2** | **0** | **(B) fix + 复评** |

收敛特征：

- batch 2 round 1 finding 数明显低于 batch 1 round 1（5 vs 16），说明从 batch 1 闭环模式中受益（路径设计、Forbidden Actions、术语等已成熟）
- 3 项 High 全部围绕"跨 skill 协作 / 状态前置一致性"——这是 batch 2 三个 skill 互相协作引入的新风险面（batch 1 是单一 skill 内）
- 0 Low 表明文档质量层面已稳定

预期 round 2 主要风险：F2 / F5 涉及多文件同步修改，可能引入新的引用一致性问题；F4 advisory vs patch 边界在 retrospective consumption mode 输出模板中是否完整覆盖。

---

**End of Feedback Response v0.9 (batch 2 round 1)**
