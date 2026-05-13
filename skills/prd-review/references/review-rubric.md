# PRD Review Rubric

**配套**：`skills/prd-review/SKILL.md` §3 Review Rubric Overview + §4 Output Contract + §5 Review Procedure。

本 reference 是 PRD review 的 6 个维度的**详细 checklist + severity 决断 + 典型 finding 例子**，扩展 SKILL.md §3 概览表。`prd-review` 在 §5 Step 3 逐维度评审时按本文逐项检查，每项产出 0+ finding。完整术语 / 输出态 / progress event 接口见 SKILL.md §4。

---

## 0. Severity 决断公共标准

- **blocking**：阻断 review-passed；必须在 prd-write Change Mode 修后再次提交
- **medium**：建议修但不阻断 review-passed（review-passed 也照样列在对话）
- **low**：风格 / 可读性提示；不修也行

**review-passed 判定**：6 维度合计**无 blocking finding**。任意 medium / low 数量都不阻断。
**issues-found 判定**：任一维度产出 ≥ 1 blocking finding。

`review_iteration` 上限 7（事实源 `progress_state.py REVIEW_ITERATION_LIMIT`）；第 8 次 issues-found 时 `progress.py update --event review-issues` 拒绝，须升级人介入。

---

## 1. 维度 1：完整性 (Per-Section Completeness)

### 1.1 关键问题

PRD 主文档的核心章节（§1 Vision / §2 Personas / §3 Stories / §4 Capabilities / §5 NFR Posture / §6 Boundary / §7 Assumptions）是否齐全？

### 1.2 Checklist

| # | Check | severity if 缺 |
|---|-------|---------------|
| 1.1 | §1 Vision 含一句话 pitch + 立项理由 | blocking |
| 1.2 | §2 Personas 至少 1 primary persona | blocking |
| 1.3 | §3 Stories 至少 1 P0 story | blocking |
| 1.4 | §4 Capabilities 至少 1 capability，且每条 → §3 Story 有 traceability | blocking |
| 1.5 | §5 NFR posture 给方向（即使 "best-effort"）| medium |
| 1.6 | §6 Non-Goals 至少 1 条（产品边界明确）| blocking |
| 1.7 | §7 Assumptions / Constraints 至少 1 条 | medium |
| 1.8 | §8 Open Questions（如有未解问题）| low |
| 1.9 | §3 Stories 用业务动词（不是 API spec）| medium |
| 1.10 | §4 Capabilities P0 数量 ≤ 10 | medium（warn）|

### 1.3 Finding 例子

```markdown
### Finding 1 [blocking, 维度 1: 完整性]
- **Where**: §6 Boundary / Scope / Non-Goals 缺失
- **Issue**: PRD 仅 1100 行但完全没有 Non-Goals 章节；SRS 阶段无法定位产品边界
- **Recommendation**: 补 §6，至少列 3 条明确不做的方向 + 与 §2 Anti-personas 互校
```

---

## 2. 维度 2：业务一致性 (Internal Consistency)

### 2.1 关键问题

PRD 内部章节是否互相支撑？是否有矛盾？

### 2.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 2.1 | §3 P0 Stories 全部映射到 §4 Capabilities（traceability 表 / 段落明示）| blocking |
| 2.2 | §6 Non-Goals 的拒绝项 与 §2 Anti-personas 一致 | blocking |
| 2.3 | §4 Capabilities 之间逻辑无矛盾（A 章要求 X，B 章要求 not X）| blocking |
| 2.4 | §5 NFR posture 与 §4 Capabilities 可行性不冲突（如 PRD 说 "interactive" 但 capability 全是 batch）| blocking |
| 2.5 | §7 Assumptions 与 §4 Capabilities 可行性不冲突 | medium |
| 2.6 | §1 Vision 与 §4 Capabilities P0 集 → 一句话 pitch 应能涵盖全部 P0 | medium |

### 2.3 Finding 例子

```markdown
### Finding 2 [blocking, 维度 2: 业务一致性]
- **Where**: §4.A "real-time alerts" / §5 NFR "best-effort latency"
- **Issue**: §4 P0 capability 要求实时告警但 §5 NFR posture 标 best-effort；二者不可同时成立
- **Recommendation**: 选其一：(a) §4 改为 "near-real-time within 5 min" 让 NFR 仍可 best-effort；(b) §5 NFR 升级为 "interactive (sub-second)" 并接受相应实现成本
```

---

## 3. 维度 3：可决策性 (Down-Stream Decidability)

### 3.1 关键问题

PRD 是否足够具体让 SRS 阶段能展开？

### 3.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 3.1 | 每个 §4 Capability 描述能让 SRS 拆出 ≥ 1 functional requirement | blocking |
| 3.2 | §5 NFR posture 给 "方向 + 大类"（足以让 SRS NFR 章量化）| blocking |
| 3.3 | §3 Stories 写法允许 SRS 推导 acceptance criteria（不是纯感受式描述）| blocking |
| 3.4 | §4 Capabilities 之间依赖 / 顺序明确（哪条 P0 先做）| medium |
| 3.5 | §7 Constraints 可被转成 SRS 可验证 acceptance criteria | medium |

### 3.3 Finding 例子

```markdown
### Finding 3 [blocking, 维度 3: 可决策性]
- **Where**: §4.B "smart recommendations"
- **Issue**: capability 仅一句 "system suggests relevant items"；SRS 无法推导推荐算法 / 数据源 / 评估指标
- **Recommendation**: 至少给方向（content-based / collaborative）+ 数据源大类 + 1 条评估口径（CTR / dwell time），SRS 再展开成 NFR + acceptance criteria
```

---

## 4. 维度 4：业务术语清晰 (Terminology Stability)

### 4.1 关键问题

关键术语在文中首现处定义；不混用同义词；专有名词稳定。

### 4.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 4.1 | 每个产品专有名词在首现处给 1 句定义（或链接到 glossary）| medium |
| 4.2 | 同一概念全篇用同一称呼（不混用 "user" / "customer" / "client"）| medium |
| 4.3 | persona 名称在 §2 之后保持一致 | medium |
| 4.4 | 行业术语未广泛接受时给定义（避免读者误解）| low |

### 4.3 Finding 例子

```markdown
### Finding 4 [medium, 维度 4: 业务术语清晰]
- **Where**: §2 用 "buyer", §3 / §4 改用 "customer" / "user"
- **Issue**: 三个词指同一 persona，下游 SRS 不知道是否同义
- **Recommendation**: 统一为 "buyer"；§3 / §4 / §6 全文 search-replace
```

---

## 5. 维度 5：Change Log 与 Frontmatter 业务合理

### 5.1 关键问题

Pending Changes 已 promote；Change Log 各 entry 描述与 doc body 改动一致；frontmatter `title` / `status` / `updated` 合理。

### 5.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 5.1 | `## Pending Changes` 节为空（已 changelog.py promote）| blocking |
| 5.2 | `## Change Log` 每条 entry 的 section_ref 与 body 改动章节匹配 | blocking |
| 5.3 | Change Log entry summary 描述能映射到 body 实际改动（不是空话）| blocking |
| 5.4 | frontmatter `title` 与 doc 第一行 `# <Title>` 一致或语义一致 | medium |
| 5.5 | frontmatter `updated` ≥ `created` | medium |
| 5.6 | frontmatter `status` 在 enum 内（draft / in-review / revising / review-passed / approved）| blocking（多由 validate.py 拦下，但 review 仍校）|
| 5.7 | frontmatter `owner` 第二段是 `prd-write`（不是 `prd-review` 或别的）| medium |

注：`validate.py` 类 6 已自动检 `## Pending Changes` 是否有未 promote entries（见 SKILL.md §5 Step 1）；本维度复检 + 增加业务级一致性。

### 5.3 Finding 例子

```markdown
### Finding 5 [blocking, 维度 5: Change Log 业务合理]
- **Where**: Change Log §2026-05-12 entry "Added §4.B smart recommendations"
- **Issue**: PRD body §4 不存在 B 项 capability，仅 §4.A；entry 描述与 body 不一致
- **Recommendation**: 二选一：(a) 实际加 §4.B 内容；(b) 修 Change Log entry 描述与 body 实际改动一致；不要让 Change Log 与 body 漂移
```

---

## 6. 维度 6：S3 源系统分析深度（仅 S3）

### 6.1 关键问题

S3 场景下 `source_product_prd_analysis.md` + `feature_matrix.md` 是否实质回答源系统现状 + 重构动因 + 复用 / 替换决策？

仅在 `progress.md.scenario == S3` 时启用本维度。

### 6.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 6.1 | `source_product_prd_analysis.md` §3 Capability Inventory 至少列 3 条源系统已交付能力 | blocking |
| 6.2 | `source_product_prd_analysis.md` §5 Reconstruction Drivers 至少 1 条（且不是空话）| blocking |
| 6.3 | `feature_matrix.md` 行数 ≥ §source-system-analysis §3 Inventory 行数（每条源能力都有 reuse / rewrite / replace / drop 决策）| blocking |
| 6.4 | `feature_matrix.md` Decision 列每行只取 enum（reuse / rewrite / replace / drop）| blocking |
| 6.5 | `feature_matrix.md` Rationale 列每行 1-2 句决策依据（不是空白）| medium |
| 6.6 | `feature_matrix.md` drop 行 ↔ PRD §6 Non-Goals 互校（drop 项必须在 Non-Goals 出现）| blocking |
| 6.7 | `source_product_prd_analysis.md` §1 Source Identity 写明 source_system_name（与 frontmatter 一致）| blocking |

### 6.3 Finding 例子

```markdown
### Finding 6 [blocking, 维度 6: S3 源系统分析深度]
- **Where**: feature_matrix.md row "<capC>: drop" / PRD §6 Non-Goals 缺对应条目
- **Issue**: feature matrix 决定 drop 一条源能力但 PRD §6 没有把它列入 Non-Goals；下游 stakeholder 不知道这条能力被砍
- **Recommendation**: PRD §6 加 "<capC>: 本 release 不实现，详见 feature_matrix.md drop 决策" + Pending Changes 加对应条目 → promote
```

---

## 7. 跨维度组合决断

### 7.1 多 finding 同一处

同一处文本被多个维度命中时（如 §3 一条 story 同时缺定义 + 与 §6 Non-Goals 矛盾），按**最高 severity** 输出 1 条 finding，body 列全部维度命中（避免 review iteration 中重复 noise）。

### 7.2 跨 doc finding (S3)

S3 时 `source_product_prd_analysis.md` 和 `feature_matrix.md` 也是 review 范围；finding 的 `Where` 字段必须显式给出 doc path（不仅是 §section），让 prd-write 不歧义定位。

### 7.3 review_iteration 升级阈值

- iteration 1-3：blocking findings 出全 + 给 fix 方向；尽量让 prd-write 1 轮消化
- iteration 4-6：blocking findings 应聚焦尚未解决的核心矛盾；不再加新 finding，避免 prd-write 不收敛
- iteration 7：最终 issues-found 后 progress.py 第 8 次 update --event review-issues 会拒绝；本 skill 在 iteration 7 issues-found 时 finding 必须包含 "**升级人介入**" 提示

---

## 8. Anti-Patterns（review skill 自身的禁忌）

| Anti-pattern | 后果 | 替代 |
|--------------|------|------|
| 输出 `approved` / `pending` / `pass` / `fail` / `LGTM` | 越权 / 模糊 | 仅 `review-passed` / `issues-found` |
| 直接修 PRD doc body | 越界 prd-write 职责 | 以 finding 形式输出 recommendation |
| 直接改 PRD frontmatter `status` | 越界 doc-guardian/status_transition.py 职责 | 由 `progress.py update --event review-passed` 后 caller 调 status_transition.py 同步 |
| 单 finding 跨多 severity（"blocking 但建议忽略"）| 内部矛盾 | 拆成两条；一条 blocking，一条 low/medium |
| 因 §1 一句话定义不全就直接 issues-found | severity 过激 | 维度 4 多为 medium；不轻易 blocking |
| 没读 §6 / §7 直接 issues-found | 评审不充分 | §5 Step 2 必读 PRD 全文 |

---

## 9. 输出 finding 的标准格式

最终 finding 列表回到对话由 prd-write 消化；不写独立 review-report doc（PRD review **不产** review-report，事实源 `frontmatter-schema.md` 未注册 `prd-review-report` type）。

```markdown
## prd-review iteration <N> — issues-found

**Summary**: <B> blocking / <M> medium / <L> low

### Finding 1 [blocking, 维度 1: 完整性]
- **Where**: §<section>
- **Issue**: <问题一句话>
- **Recommendation**: <可执行修改建议>

### Finding 2 [medium, 维度 4: 业务术语清晰]
...
```

review-passed 时若有 non-blocking 建议（medium / low），同样输出此模板，仅 Summary 行写 "review-passed (X non-blocking suggestions)"。

---

## 10. 演化

本文件随 dev-workflow-skills2 spec 演化：

1. 修改本 rubric 必须在 SKILL.md §10 References 节同步说明
2. 增加新维度需走 design proposal review cycle（不可直接改本文）
3. 当前对应 design proposal 版本：v0.5（2026-05-06）+ Phase 7 polish
