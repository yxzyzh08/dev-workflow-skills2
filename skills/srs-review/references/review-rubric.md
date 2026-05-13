# SRS Review Rubric

**配套**：`skills/srs-review/SKILL.md` §3 Review Rubric Overview + §4 Output Contract + §5 Review Procedure。

本 reference 是 SRS review 的 7 个维度的**详细 checklist + severity 决断 + 典型 finding 例子**。`srs-review` 在 §5 Step 3 逐维度评审时按本文逐项检查。完整术语 / 输出态 / progress event 接口见 SKILL.md §4。

---

## 0. Severity 决断公共标准

- **blocking**：阻断 review-passed；必须在 srs-write Change Mode 修后再次提交
- **medium**：建议修但不阻断 review-passed
- **low**：风格 / 可读性提示

**review-passed 判定**：7 维度合计**无 blocking finding**。
**issues-found 判定**：任一维度产出 ≥ 1 blocking finding。

`review_iteration` 上限 7（事实源 `progress_state.py REVIEW_ITERATION_LIMIT`）；第 8 次 issues-found 拒绝。

---

## 1. 维度 1：完整性 (Per-Doc Completeness)

### 1.1 关键问题

每个改动 doc（SRS 主文档 + Acceptance Plan + 多模块时 Integration Plan + S3 时 source-system-analysis 4 doc）的核心章节是否齐全？

### 1.2 SRS 主文档 Checklist（按 `srs-template.md` §1.1）

| # | Check | severity if 缺 |
|---|-------|---------------|
| 1.1 | §1 Introduction（含 Release Scope）| blocking |
| 1.2 | §2 Functional Requirements（至少 1 capability）| blocking |
| 1.3 | §2 每个 capability 必含 7 子项（Source / Description / Inputs / Outputs / Pre / Post / Error）| blocking |
| 1.4 | §3 Non-Functional Requirements（至少 1 NFR + measurement + threshold）| blocking |
| 1.5 | §4 Interface Contracts | blocking（多模块 §4.2 必备）|
| 1.6 | §5 Constraints & Assumptions | medium |
| 1.7 | §6 Consumed Bug Fixes（S2-x 时；事实源 BUG-*.md `consumed_in_release` scan）| 见维度 7 |
| 1.8 | §7 Open Questions | low |
| 1.9 | `## Pending Changes` + `## Change Log` 节存在 | blocking（validate.py 类 6 也拦）|

### 1.3 Acceptance Plan Checklist

| # | Check | severity if 缺 |
|---|-------|---------------|
| 1.10 | §2 Acceptance Criteria 每个 SRS §2 capability 至少 1 条 AC | blocking |
| 1.11 | §3 NFR Acceptance 每条 SRS §3 NFR 一行 verification approach | blocking |
| 1.12 | frontmatter `related_srs` 指向同 release srs.md | blocking（validate.py 类 5 也拦）|

### 1.4 Integration Plan Checklist (`is_multi_module: true` 时)

| # | Check | severity if 缺 |
|---|-------|---------------|
| 1.13 | §1 Modules 列表与 SRS §2 module list 1:1 | blocking |
| 1.14 | §2 Integration Sequence 含依赖图（mermaid 或 prose）| medium |
| 1.15 | §3 Inter-Module Contracts 覆盖 §1 列出的所有 module-pair | blocking |

### 1.5 Finding 例子

```markdown
### Finding 1 [blocking, 维度 1: 完整性]
- **Where**: SRS §3 Non-Functional Requirements
- **Issue**: NFR 表只列了 4 项 NFR 但全部缺 Measurement 列；Stage 5 testing 无法验证
- **Recommendation**: 每条 NFR 补 Measurement + Pass criterion；至少 4 行（API latency / throughput / availability / security）
```

---

## 2. 维度 2：跨 Doc 一致性 (Cross-Doc Consistency)

### 2.1 关键问题

SRS / Acceptance Plan / Integration Plan / source-system-analysis 之间是否互相支撑、无矛盾？

### 2.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 2.1 | SRS §2 每个 capability 在 acceptance_plan.md §2 有对应 AC | blocking |
| 2.2 | SRS §3 每条 NFR 在 acceptance_plan.md §3 有对应 verification approach | blocking |
| 2.3 | 多模块时 SRS §2 module list 与 integration_plan.md §1 module list 一致 | blocking |
| 2.4 | 多模块时 integration_plan.md §3 contracts 覆盖 SRS §4.2 module boundaries | blocking |
| 2.5 | S3 时 source-system-analysis reuse-replace 决策与 SRS §2 capability 集对应（drop 类不在 SRS；reuse 类在 SRS 描述基于源系统）| blocking |
| 2.6 | 多 doc frontmatter `release` 字段一致（all == progress.md.release）| blocking |
| 2.7 | 多 doc frontmatter `updated` 时间合理（≤ now，≥ created）| medium |

### 2.3 Finding 例子

```markdown
### Finding 2 [blocking, 维度 2: 跨 doc 一致性]
- **Where**: SRS §2.1.3 Capability "scheduled email reports" / acceptance_plan.md §2 缺对应 AC
- **Issue**: SRS 已定义但 Acceptance Plan §2 没有对应章节；testing 阶段无法验收
- **Recommendation**: acceptance_plan.md §2 加 Capability 2.1.3 节，至少 2 条 AC（happy path + 至少 1 个 edge case）
```

---

## 3. 维度 3：可决策性 (Down-Stream Decidability)

### 3.1 关键问题

SRS 描述是否够具体让 Stage 3 Architecture 阶段下展开（接口 / 模块边界 / 数据流可决策）？NFR 是否可量化让 Stage 5 testing 验证？

### 3.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 3.1 | §2 每条 capability 描述足够 architecture-write 推导 ≥ 1 组件 | blocking |
| 3.2 | §3 每条 NFR 含数值 + measurement（不是 "good performance"）| blocking |
| 3.3 | §4.1 每个外部 API 含 endpoint / method / 错误码大类 | blocking |
| 3.4 | §4.3 关键 entity 含 schema 或链接到详细定义 | blocking |
| 3.5 | 多模块时 §4.2 module boundaries 含 interface kind（REST / gRPC / event / shared DB）| blocking |
| 3.6 | §5 Constraints 可被 Stage 4 测试验证 | medium |

### 3.3 Finding 例子

```markdown
### Finding 3 [blocking, 维度 3: 可决策性]
- **Where**: SRS §4.1 API "POST /search"
- **Issue**: 仅写 "search returns relevant items"；缺 input schema / output schema / 错误码
- **Recommendation**: 至少给 input fields (query / filters / pagination) + response schema (item type) + 错误码大类（400 invalid query / 401 unauthorized / 503 backend unavailable）
```

---

## 4. 维度 4：业务术语稳定 (Terminology Stability)

### 4.1 关键问题

术语在文中首现处定义；与 PRD 术语一致；不混用同义词。

### 4.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 4.1 | §1.3 Glossary 有定义关键术语 | medium |
| 4.2 | 同一概念全篇用同一称呼 | medium |
| 4.3 | 与 PRD glossary 互斥时显式标 "本 SRS 范围内 X 指 Y" | medium |
| 4.4 | API 路径 / event 名 / module 名 拼写一致 | medium |

### 4.3 Finding 例子

```markdown
### Finding 4 [medium, 维度 4: 术语稳定]
- **Where**: SRS §2.1 用 "User", §2.2 用 "Customer", §4.1 用 "Account holder"
- **Issue**: 三个词指同一 persona；下游 architecture / development 不知是否同义
- **Recommendation**: §1.3 Glossary 加定义 "User"，§2.2 / §4.1 全文 search-replace 统一为 "User"（与 PRD 一致）
```

---

## 5. 维度 5：Change Log 与 Frontmatter 业务合理（含 SRS 2 bool 一致性）

### 5.1 关键问题

Pending Changes 已 promote；Change Log 与 doc body 改动一致；SRS frontmatter `is_multi_module` / `architecture_change` 与 body 一致。

### 5.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 5.1 | `## Pending Changes` 节为空（已 changelog.py promote）| blocking |
| 5.2 | `## Change Log` 每条 entry 的 section_ref 与 body 改动章节匹配 | blocking |
| 5.3 | Change Log entry summary 描述与 body 实际改动一致 | blocking |
| 5.4 | SRS frontmatter `is_multi_module: bool` 必含 + 与 §2 module list 一致（true ⇔ ≥2 module + §4.2 非空 + integration_plan.md 存在）| blocking |
| 5.5 | SRS frontmatter `architecture_change: bool` 必含 + 与 SRS body 一致（true ⇔ §2/§4 蕴含组件 / 接口 / 数据流改变）| blocking |
| 5.6 | source-system-analysis 必含 `source_system_name` 字段 | medium |
| 5.7 | 多 doc frontmatter `owner` 第二段是 `srs-write`（不是 srs-review）| medium |
| 5.8 | 多 doc frontmatter `release` 字段 == progress.md.release | blocking（validate.py 也拦）|

### 5.3 Finding 例子

```markdown
### Finding 5 [blocking, 维度 5: Change Log + 2 bool 一致性]
- **Where**: SRS frontmatter `is_multi_module: false` / SRS §2 列出 2 个 module + §4.2 非空 / integration_plan.md 不存在
- **Issue**: SRS body 实际是多模块但 frontmatter 标 false，required-artifacts.md DSL 推导 integration_plan 非必备
- **Recommendation**: 二选一：(a) 改 frontmatter `is_multi_module: true` + 创 integration_plan.md；(b) 把 §2 合并为单 module + §4.2 内联到 §4.3 + frontmatter 保持 false
```

---

## 6. 维度 6：S3 源系统分析深度（仅 S3）

### 6.1 关键问题

S3 时 source-system-analysis 4 个 doc（3 必备 + 1 推荐）是否实质回答源系统现状 + 重构动因 + 复用 / 替换决策？

仅在 `progress.md.scenario == S3` 时启用。

### 6.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 6.1 | `source_product_srs_analysis.md` 描述源系统 SRS 章节级别分析（不是 prd-level 拷贝）| blocking |
| 6.2 | `source_module_analysis.md` 模块切分清晰（与本 release SRS §2 module list 对照）| blocking |
| 6.3 | `reuse_replace_capability.md` 每条源能力有 reuse / rewrite / replace / drop 决策（与 prd-level feature_matrix.md 兼容但更细）| blocking |
| 6.4 | `reuse_replace_capability.md` drop 决策 → 本 SRS §2 不含 + PRD §6 Non-Goals 已注 | blocking |
| 6.5 | `technical_debt_analysis.md`（推荐 optional）：识别可弃 / 可重写部分；存在则评审；不存在不阻断 | low/medium（推荐质量）|
| 6.6 | 4 个 source-system-analysis doc frontmatter `source_system_name` 一致 | medium |
| 6.7 | 4 个 doc frontmatter `release` 字段 == progress.md.release | blocking |

### 6.3 Finding 例子

```markdown
### Finding 6 [blocking, 维度 6: S3 源系统分析]
- **Where**: reuse_replace_capability.md row "<capX>: drop" / SRS §2 仍含 capX 对应 functional req
- **Issue**: 决策 drop 但 SRS 仍把它当本 release 功能；下游 architecture / development 会浪费工作
- **Recommendation**: SRS §2 移除 capX；PRD §6 Non-Goals 加注；reuse_replace_capability.md Rationale 列加 1 句决策依据
```

---

## 7. 维度 7：Consumed Unresolved Bugs 合并完整性

### 7.1 关键问题

本 release 通过 release-start 消费的 unresolved_bugs 是否在 SRS 实质合并？事实源是 `docs/bug/BUG-*.md` `consumed_in_release == <progress.md.release>` 的 scan 结果。

按 `bug-merge-policy.md` 校验。

### 7.2 触发场景

- 本 release 首次进入 SRS review（覆盖 S2-1/S2-2/S2-3；S1/S3 通常 scan 为空但仍跑保持一致性）
- Bug Flow re-entry 时 `bug_flow.active==true AND bug_flow.root_cause==srs`：维度 7 特化为 BUG-NNN 实质覆盖检查（不要求重新 scan 整个 consumed list）

### 7.3 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 7.1 | 每条 root_cause ∈ {null, srs} 的 consumed bug 在 SRS §2-§4 有对应改动 + §6 行 + Change Log entry | blocking |
| 7.2 | 每条 root_cause ∈ {architecture, development} 的 consumed bug 不在 SRS §2-§4（§6 注记 OK；过度合并 → medium）| medium 或 blocking |
| 7.3 | 任意 consumed bug `root_cause==prd-exception` 出现 | blocking（脏数据；要求 audit BUG-NNN.md）|
| 7.4 | §6 表行数 ≥ scan 出的 root_cause ∈ {null, srs, architecture, development} consumed bug 总数 | blocking |
| 7.5 | 每条 §6 行的 BUG ID 与 frontmatter `consumed_in_release` 字段对应 | blocking |
| 7.6 | Pending Changes 关联 root_cause ∈ {null, srs} bug 必含 `Merged BUG-NNN: <title> — root_cause=<value or null/awaiting-classification>` | blocking |
| 7.7 | Bug Flow re-entry 时 BUG-NNN 涉及的 SRS 章节有实质修改（不是单加 Change Log entry 不动 body）| blocking |

### 7.4 Finding 例子

```markdown
### Finding 7 [blocking, 维度 7: Bug 合并]
- **Where**: BUG-*.md scan: BUG-005 (consumed_in_release=0.3, root_cause=null) + BUG-007 (consumed_in_release=0.3, root_cause=srs) / SRS Change Log 仅有 BUG-005 / SRS §6 表无 BUG-007 行
- **Issue**: BUG-007（root_cause=srs）已 consumed 但 SRS body 无对应改动 + §6 表缺 BUG-007 行
- **Recommendation**: 在 SRS body 加 BUG-007 修复需求 / acceptance criteria + §6 表加 BUG-007 行 + Pending Changes 加 `Merged BUG-007: <title> — root_cause=srs` → promote → 重 submit
```

---

## 8. 跨维度组合决断

### 8.1 多 finding 同一处

同一处文本被多个维度命中（如 §3 NFR 缺量化 + 缺 measurement）按**最高 severity** 输出 1 条 finding，body 列全部维度命中。

### 8.2 跨 doc finding

任一 finding 涉及 ≥ 2 doc 时（典型：SRS ↔ Acceptance Plan 不一致），`Where` 字段必须显式给所有相关 doc path + section。

### 8.3 review_iteration 升级阈值

- iteration 1-3：blocking findings 出全 + 给 fix 方向
- iteration 4-6：blocking findings 应聚焦尚未解决的核心矛盾；不再加新 finding
- iteration 7：finding 必须含 "**升级人介入**" 提示

---

## 9. Anti-Patterns（review skill 自身的禁忌）

| Anti-pattern | 后果 | 替代 |
|--------------|------|------|
| 输出 `approved` / `pending` / `pass` / `fail` / `LGTM` | 越权 / 模糊 | 仅 `review-passed` / `issues-found` |
| 直接修 SRS / Acceptance Plan / Integration Plan doc body | 越界 srs-write 职责 | finding 形式 |
| 直接改 doc frontmatter `status` | 越界 status_transition.py 职责 | 由 progress.py update --event 后 caller 调 |
| 单 finding 跨多 severity | 内部矛盾 | 拆成两条 |
| 未读 Acceptance Plan 就 review-passed | 评审不充分 | §5 Step 2 必读全部改动 doc |
| 未做 BUG-*.md scan 就 review-passed | 维度 7 漏检 | §5 Step 2 包含 scan |
| 维度 6 在 scenario != S3 时仍触发 finding | 误判 | 仅 S3 启用 |
| 把 architecture/development 类 bug 强行写入 SRS body | 维度 7.2 medium/blocking | 仅 §6 注记，实际修复在 Stage 3/4 |

---

## 10. 输出 finding 标准格式

```markdown
## srs-review iteration <N> — issues-found

**Summary**: <B> blocking / <M> medium / <L> low
**Coverage**: SRS + Acceptance Plan + (Integration Plan?) + (S3 supporting?)

### Finding 1 [blocking, 维度 2: 跨 doc 一致性]
- **Where**: SRS §<n> + Acceptance Plan §<m>
- **Issue**: ...
- **Recommendation**: ...

### Finding 2 [medium, 维度 4: 术语稳定]
...
```

review-passed 时若有 non-blocking 建议同样输出此模板，Summary 行写 "review-passed (X non-blocking suggestions)"。

---

## 11. 演化

- 修改本 rubric 必须在 SKILL.md §10 References 节同步说明
- 增加新维度 / 改变 severity 决断需走 design proposal review cycle
- 当前对应 design proposal 版本：v0.5（2026-05-06）+ Phase 7 polish
