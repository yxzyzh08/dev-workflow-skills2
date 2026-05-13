# PRD Document Body Template

**配套**：`skills/prd-write/SKILL.md` §4 Doc Output Contract + §5 4-Step Standard Procedure。

本 reference 是 PRD 主文档（`docs/prd/prd.md`）以及 S3 场景下两份必备 supporting artifacts (`source_product_prd_analysis.md` + `feature_matrix.md`) 的章节级模板。`prd-write` 在 Full Mode 时按本文复制章节骨架后填内容；Change Mode 时仍以本文为对照检查既有 PRD 是否漏章节。完整 frontmatter schema 见 `skills/doc-guardian/references/frontmatter-schema.md`，本模板仅给 doc body。

---

## 1. PRD 主文档（`docs/prd/prd.md`）

### 1.1 章节顺序与必含内容

```markdown
---
<frontmatter, 见 skills/doc-guardian/references/frontmatter-schema.md §3.1>
---

# <Project Name> Product Requirements

## 1. Vision & Product Positioning

- **One-sentence pitch**: <一句话产品定位>
- **Why this product, why now**: <立项理由 + 时机>
- **Success measure (qualitative)**: <主观成功标准；量化 KPI 进 SRS NFR>

## 2. Target Users & Personas

- **Primary persona(s)**: <角色 + 痛点 + 现行替代方案>
- **Secondary persona(s)**: <次要角色，可选>
- **Anti-personas (out of scope)**: <明确不服务的用户群；与 §6 Non-Goals 互相印证>

## 3. User Stories / Key Scenarios

每条 user story 用 "As a <persona>, I want <capability>, so that <outcome>" 格式；
按 priority (P0 / P1 / P2) 分组。

- **P0 (must)**: <story>
- **P1 (should)**: <story>
- **P2 (nice-to-have)**: <story>

每条 story 可附 1-2 行 narrative 解释，但**不**展开 acceptance criteria（那是 SRS 层）。

## 4. Functional Capability Set

按 capability 分类（不必逐功能列详细 spec；细节由 SRS 处理）：

| Capability | Description | Linked Stories |
|-----------|-------------|----------------|
| <capability A> | <one-paragraph description> | P0-1, P1-2 |
| <capability B> | ... | ... |

每个 capability 的"具体 functional requirements / API / 数据模型"留给 SRS。

## 5. Non-Functional Goals (qualitative)

PRD 仅给方向；具体量化指标（latency ≤ Xms、throughput ≥ Y rps）由 SRS NFR 章。

- **Performance posture**: <e.g. interactive 工具 vs batch 服务>
- **Reliability / availability**: <e.g. business-critical vs best-effort>
- **Security & privacy**: <数据敏感度 + 合规需求大类，e.g. GDPR / HIPAA / SOX>
- **Accessibility / i18n**: <e.g. WCAG 2.1 AA、目标语言区域>

## 6. Boundary / Scope / Non-Goals

- **In scope (this product)**: <关键边界，3-5 条>
- **Out of scope (explicitly)**: <对应 §2 Anti-personas + 拒绝功能>
- **Future considerations (not committed)**: <已识别但本 release 不做的方向>

## 7. Assumptions & Constraints

- **External dependencies**: <第三方 / 上下游系统假设>
- **Resource constraints**: <团队 / 时间 / 预算大类>
- **Regulatory constraints**: <合规 / 行业要求>
- **Known unknowns**: <识别但未解决的不确定性>

## 8. Open Questions

- <悬而未决问题，会在后续 release / SRS 阶段消化>

## Pending Changes

<!--
本节存放本次 write/revise 周期的改动条目；changelog.py promote 后转入 Change Log。
单条格式：
- <YYYY-MM-DDTHH:MM:SSZ> [Section <n>]: <语义化摘要>
事实源 skills/doc-guardian/references/change-log-format.md §2.2。
-->

## Change Log

<!--
按日期分组（### YYYY-MM-DD），同日内 entry 时间升序，不同日期组按日期降序。
事实源 skills/doc-guardian/references/change-log-format.md §3.1。
-->
```

### 1.2 章节级写作准则

- **§1 Vision**：一段话能讲清楚；超过 3 段说明定位还没收敛，建议先与用户对话。
- **§2 Personas**：至少 1 primary；anti-persona 是边界利器，明确"我们不服务谁"避免功能漂移。
- **§3 Stories**：避免技术语言；用业务动词（"approve" / "submit" / "audit"），不用 "API call" / "POST"。
- **§4 Capabilities**：每条 1 段 narrative；不超过 10 个 P0 capability（超过 → 说明产品定位太宽，触发 prd-exception 风险）。
- **§5 NFR posture**：仅给"方向 + 大类"；具体数字进 SRS NFR + Acceptance Plan 量化。
- **§6 Non-Goals**：与 §2 Anti-personas 互校；一处改另一处必须同步。
- **§7 Assumptions**：每条假设都应可被 SRS 转成可验证 acceptance criterion；纯文学性 assumption 删掉。

### 1.3 长度建议

- 总长 600-1500 行（含 markdown 标记）通常够；超过 2000 行说明有内容应该下沉到 SRS。
- 短于 300 行说明信息密度太低；增加 personas / non-goals / assumptions。

---

## 2. S3 必备 supporting artifact: `source_product_prd_analysis.md`

S3（重构既有产品）必备。`type: source-system-analysis`, `analysis_kind: prd-level`, `release: null`, `source_system_name: <name>`。

### 2.1 章节模板

```markdown
---
<frontmatter, 见 skills/doc-guardian/references/frontmatter-schema.md §3.5>
---

# Source Product PRD Analysis (<source_system_name>)

## 1. Source Product Identity

- **Source system name**: <name>
- **Source product line / version**: <e.g. v3.2 LTS、legacy 2018 build>
- **Documentation entry points**: <github / wiki / pdf 链接>

## 2. Source Product Vision (重述源系统视角)

- **Original pitch**: <源系统当年立项的产品定位>
- **Original target users**: <源系统目标用户>
- **Drift over time**: <历经迭代后实际服务的用户群是否仍与原始定位一致>

## 3. Functional Capability Inventory

按 capability 列源系统当前已交付的功能，标注成熟度：

| Capability | Maturity | Adoption | Pain Points |
|-----------|----------|----------|-------------|
| <capA> | mature / partial / experimental | 高 / 中 / 低 | <bullet list> |

## 4. User Pain Points (聚焦驱动重构的痛点)

- <按 frequency × severity 优先级排>

## 5. Reconstruction Drivers (重构动因)

- <为什么要重构而非继续维护>
- <对应 PRD 的 §1 Vision 应该回应这些动因>

## 6. Constraints Inherited from Source

- <重构产品仍要保留的能力 / 兼容性 / 数据迁移要求>

## 7. References

- <源系统 spec / 调研 / 用户访谈 链接列表>
```

注：本 doc 是 **snapshot 类**（事实源 `skills/doc-guardian/references/change-log-format.md`）；**不**含 `## Pending Changes` / `## Change Log` 章节。

---

## 3. S3 必备 supporting artifact: `feature_matrix.md`

S3 必备。`type: source-system-analysis`, `analysis_kind: feature-matrix`, `release: null`, `source_system_name: <name>`。

### 3.1 章节模板

```markdown
---
<frontmatter, 见 skills/doc-guardian/references/frontmatter-schema.md §3.5>
---

# Feature Matrix: <source_system_name> vs <new product name>

## 1. Matrix Schema

每行一个 capability；以下 4 列严格出现：

| Column | Allowed values | Notes |
|--------|----------------|-------|
| `Capability` | <free text> | 必填，与 §source-system-analysis 用同一名词 |
| `Source maturity` | mature / partial / experimental / absent | 源系统当前状态 |
| `Decision` | reuse / rewrite / replace / drop | 见 §3.2 |
| `Rationale` | <free text> | 1-2 句决策依据 |

## 2. The Matrix

| Capability | Source maturity | Decision | Rationale |
|-----------|-----------------|----------|-----------|
| <capA> | mature | reuse | 复用源系统模块；无重写动因 |
| <capB> | partial | rewrite | 现有实现有性能问题；新栈重写 |
| <capC> | experimental | drop | 实验性功能采纳率低；本次不做 |
| <capD> | absent | replace | 源系统没有，直接新建（属新产品 net-new） |

## 3. Decision Rubric（§3.2）

- **reuse**：源系统已有且无 product-level 改进诉求；直接迁移代码 / 接口
- **rewrite**：源系统已有但实现 / 接口 / 性能不满足；保留 capability 重写
- **replace**：源系统能力被新方案完全取代（典型：换技术栈）
- **drop**：源系统已有但本次不做（必须在 PRD §6 Non-Goals 显式标 + 通知 stakeholder）

## 4. Coverage Statistics

- Total source capabilities surveyed: <N>
- reuse: <%>; rewrite: <%>; replace: <%>; drop: <%>
- 校验：百分比之和 = 100；若 absent capabilities 在新产品需要，统计在 §replace（不在 §source 行）
```

注：本 doc 同 §2 是 **snapshot 类**；**不**含 Pending Changes / Change Log 章节。

---

## 4. Optional supporting artifacts (非强制)

按需创建，非 S3 必备；frontmatter `type` 必须是已注册 doc-guardian type（`competitor-research` / `competitor-architecture` / `market-research` / `user-scenario-analysis` / `non-goals` / `risk-analysis`），不要伞名 `prd-supporting`。

每份 optional doc 推荐自然有的章节：

- `competitor_research.md`：竞品列表 + 各自定位 + 优劣势 + 借鉴 / 规避点
- `market_research.md`：目标市场规模 + 趋势 + 主要参与方
- `user_scenario_analysis.md`：典型场景 walk-through（可补充 PRD §3 Stories）
- `non_goals.md`：本次明确不做的方向 + 理由（与 PRD §6 Boundary 互校）
- `risk_analysis.md`：风险登记 + 严重度 + 缓解方案

这些 doc 同样是 **snapshot 类**：不含 Pending Changes / Change Log。

---

## 5. Common Pitfalls

| Pitfall | 后果 | 改正 |
|---------|------|------|
| §3 User Stories 写成 API spec | SRS 阶段无法基于 PRD 推导功能边界 | 用业务动词重写 |
| §4 Capabilities 列 > 10 P0 项 | 说明产品定位太宽，可能触发 prd-exception | 拆 release / 收敛定位 |
| §5 NFR 直接给量化指标 | 与 SRS NFR 重复且容易不一致 | PRD 仅给"方向"，量化进 SRS |
| Optional doc 用 `type: prd-supporting` 伞名 | validate.py 类 3 schema 拒绝 | 用 §4 列出的具体 type |
| S3 缺 feature_matrix 或 source_product_prd_analysis | P6 dim A reject `update --advance` | 同步补两份必备 supporting |
| Pending Changes 写完没跑 changelog.py promote | validate.py 类 6 拒绝（unpromoted entries）| 跑 `skills/doc-guardian/scripts/changelog.py promote docs/prd/prd.md` |

---

## 6. 演化

模板随 dev-workflow-skills2 spec 演化。修改本文必须：

1. 在 SKILL.md §10 References 节同步说明
2. 走 design proposal review cycle（不可直接改本文）
3. 当前对应 design proposal 版本：v0.5（2026-05-06）+ Phase 7 polish
