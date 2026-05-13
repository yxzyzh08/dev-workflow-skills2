# Architecture Review Rubric

**配套**：`skills/architecture-review/SKILL.md` §3 Review Rubric Overview + §4 Output Contract + §5 Review Procedure。

本 reference 是 Architecture review 的 7 个维度的**详细 checklist + severity 决断 + 典型 finding 例子**。`architecture-review` 在 §5 Step 3 逐维度评审时按本文逐项检查。维度 6 与 architecture-write 的 `delta-policy.md` 配套；维度 7 与 SKILL.md §7.1 Bug Flow 性质表配套。

---

## 0. Severity 决断公共标准

- **blocking**：阻断 review-passed
- **medium**：建议修但不阻断
- **low**：风格 / 可读性提示

**review-passed 判定**：7 维度合计**无 blocking finding**。
**issues-found 判定**：任一维度产出 ≥ 1 blocking finding。

`review_iteration` 上限 7；第 8 次 issues-found 拒绝。

---

## 1. 维度 1：完整性 (Per-Doc Completeness)

### 1.1 关键问题

每个改动 doc（architecture.md 主文档 + 本 release architecture_delta.md，若存在）的核心章节是否齐全？

### 1.2 architecture.md Checklist（按 `architecture-template.md` §1.1）

| # | Check | severity if 缺 |
|---|-------|---------------|
| 1.1 | §1 Overview（含 Purpose & Scope + Architecture Style + Glossary）| blocking |
| 1.2 | §2 System Context（External Actors + Context Diagram）| blocking |
| 1.3 | §3 Component Catalog（≥ 1 component）| blocking |
| 1.4 | §3 每个 component 含 7 子项（Responsibility / Technology / Inputs / Outputs / Persistence / Scaling / Failure mode）| blocking |
| 1.5 | §4 Interfaces & Contracts（4.1 External APIs + 4.3 Cross-Cutting Concerns；多 component 时 4.2 必备）| blocking |
| 1.6 | §5 Data Flows（≥ 1 use case flow，对应 SRS P0 stories）| blocking |
| 1.7 | §6 Data Model（Primary Entities + Storage Decisions）| blocking |
| 1.8 | §7 Deployment Topology（哪怕单进程也要写 §7.1）| blocking |
| 1.9 | §8 Operational Characteristics（Availability + Observability + Security 至少各 1 段）| blocking |
| 1.10 | §9 ADR ≥ 3 条 | medium |
| 1.11 | `## Pending Changes` + `## Change Log` 节存在 | blocking（validate.py 类 6 也拦）|

### 1.3 architecture_delta.md Checklist（按 `architecture-template.md` §2.1）

仅 delta 存在时启用：

| # | Check | severity if 缺 |
|---|-------|---------------|
| 1.12 | §1 Release Context（Triggered by + Decision summary）| blocking |
| 1.13 | §2 Inventory of Changes（按 §2.1-§2.5 至少覆盖 component / interface / data flow / data model / deployment 中的相关项）| blocking |
| 1.14 | §3 Long-Term Fact Sync 表存在 + 每条改动一行 + Long-term/Synced 列填写 | blocking（事实源 `delta-policy.md` §5）|
| 1.15 | §4 Migration & Rollback（S2-x 必填；S1/S3 首 release 可写 N/A）| medium |
| 1.16 | §5 Bug Flow Linkage（仅 root_cause==architecture 时启用）| blocking 当 trigger 条件满足 |

### 1.4 Finding 例子

```markdown
### Finding 1 [blocking, 维度 1: 完整性]
- **Where**: architecture.md §3 Component Catalog
- **Issue**: §3.2 component "API Server" 缺 Failure mode 子项；评审无法判断该组件宕机 / 慢响应时上下游应如何处理
- **Recommendation**: 加 Failure mode 子项，至少描述 (a) 完全宕机时 web 客户端表现；(b) 慢响应（>5s）时 fallback 路径
```

---

## 2. 维度 2：跨 Doc 一致性（主 doc ↔ delta）

### 2.1 关键问题

architecture_delta 中描述的"基础架构"假设与 architecture.md 一致；delta 不破坏主 doc 长期事实（除非 §3 决策长期事实路径已说明并同步更新主 doc）。

### 2.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 2.1 | delta `parent_architecture` 字段指向 `docs/architecture/architecture.md`（已校；validate.py 类 5）| blocking |
| 2.2 | delta §2 引用的 component 名 / interface 名与主 doc 一致（不是新造同义词）| blocking |
| 2.3 | delta §3 Long-Term Fact Sync 表中标 yes synced 的条目，主 doc 对应章节确实有改动 | blocking |
| 2.4 | delta §3 表中标 no synced 的条目，主 doc 对应章节确实**未**改动（避免误把 local 写进主 doc）| medium |
| 2.5 | 主 doc Change Log 含全部 delta §3 yes synced 条目 | blocking |
| 2.6 | 主 doc Change Log **不含** delta §3 no synced 条目（避免污染主 doc）| medium |
| 2.7 | 跨 release 一致性：上一 release 的 architecture_delta 标 yes synced 的条目应已在本 release 主 doc 中存在 | blocking（漏同步会让本 release 起点错误）|

### 2.3 Finding 例子

```markdown
### Finding 2 [blocking, 维度 2: 跨 doc 一致性]
- **Where**: architecture_delta.md §2.1 "Add component search-service" / architecture.md §3 缺该 component
- **Issue**: delta 标该改动为 long-term fact + Synced=yes，但 architecture.md §3 Component Catalog 没加 search-service 章节
- **Recommendation**: architecture.md §3.<n> 加 search-service 完整 7 子项；同步 Pending Changes + promote → 重 submit
```

---

## 3. 维度 3：与上游 SRS 一致性

### 3.1 关键问题

SRS 的功能性 / 非功能性需求 → 架构组件 / 接口 / 数据流的映射完整？多模块时 SRS module list 与架构组件切分对应？S3 时 reuse-replace 决策在架构中体现？

### 3.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 3.1 | SRS §2 每个 capability 在架构中至少有 1 component 承担 | blocking |
| 3.2 | SRS §3 每条 NFR 在架构中有兑现路径（component scaling / observability / security 章节响应）| blocking |
| 3.3 | SRS §4.1 External APIs 在 architecture §4.1 有对应（contract → impl）| blocking |
| 3.4 | 多模块时 SRS §2 module list ↔ architecture §3 component catalog 切分对应（不一定 1:1，但必须有合理映射）| blocking |
| 3.5 | S3 时 source-system-analysis `reuse_replace_capability.md` 决策在 architecture §1.2 / §3 / §9 ADR 体现 | blocking |
| 3.6 | architecture 引入的 component / interface 不超出 SRS 范围（不写 SRS 没要求的功能）| medium |

### 3.3 Finding 例子

```markdown
### Finding 3 [blocking, 维度 3: SRS 一致性]
- **Where**: SRS §3 NFR "API p95 latency ≤ 200ms" / architecture.md §3 缺对应 scaling / cache 描述
- **Issue**: SRS NFR 要求 200ms p95 但架构无 cache 或多实例描述；现有架构无法兑现该 NFR
- **Recommendation**: §3 加 cache component + scaling characteristics；或 §8.2 加 latency monitoring + alert；让 NFR 兑现路径明确
```

---

## 4. 维度 4：可决策性 (Down-Stream Decidability)

### 4.1 关键问题

架构描述是否够具体让 Stage 4 Development 下展开？接口签名 / 数据 schema / 关键算法 / 部署假设可决策？

### 4.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 4.1 | §3 component 之间调用关系明确（哪个 component 调哪个；同步还是异步）| blocking |
| 4.2 | §4.2 inter-component contract 含 interface kind（REST / gRPC / event / shared DB）| blocking |
| 4.3 | §4.2 含关键 schema 或链接到 SRS §4.3 / 主 doc §6 | blocking |
| 4.4 | §6 Data Model 关键 entity 含 fields / types / relationships | blocking |
| 4.5 | §7.1 runtime topology 含数量 / sizing 假设（哪怕 "1 process"）| blocking |
| 4.6 | §7.3 environment strategy 标 dev/staging/prod 差异 | medium |
| 4.7 | §9 ADR 选项有清晰 rationale + alternatives | medium |

### 4.3 Finding 例子

```markdown
### Finding 4 [blocking, 维度 4: 可决策性]
- **Where**: architecture.md §4.2 "auth service → API server"
- **Issue**: 仅写 "auth service authenticates requests"；缺 interface kind / schema / failure mode
- **Recommendation**: 至少给 (a) interface kind: REST POST /auth/verify；(b) request schema (token field) / response schema (user_id, scopes)；(c) failure mode: auth service 不可用时 API 返回 503 / 客户端 retry 1 次
```

---

## 5. 维度 5：Change Log 与 Frontmatter 业务合理

### 5.1 关键问题

Pending Changes 已 promote；Change Log 与 doc body 改动一致；delta `parent_architecture` 指向主 doc；frontmatter `release` / `updated` 合理。

### 5.2 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 5.1 | 主 doc + delta（若存在）的 `## Pending Changes` 节均为空（已 promote）| blocking |
| 5.2 | 主 doc Change Log 每条 entry section_ref 与 body 改动章节匹配 | blocking |
| 5.3 | delta Change Log 每条 entry 与 §3 Long-Term Fact Sync 表对应 | blocking |
| 5.4 | delta frontmatter `parent_architecture: docs/architecture/architecture.md`（路径精确）| blocking |
| 5.5 | delta frontmatter `release` 字段 == progress.md.release | blocking |
| 5.6 | 主 doc frontmatter **不**含 `release` 字段（项目级 doc）| blocking |
| 5.7 | 主 doc + delta frontmatter `owner` 第二段是 `architecture-write` | medium |
| 5.8 | 主 doc + delta frontmatter `updated` ≥ `created` | medium |

### 5.3 Finding 例子

```markdown
### Finding 5 [blocking, 维度 5: Change Log + frontmatter]
- **Where**: architecture_delta.md frontmatter `release: 0.2` / progress.md.release == 0.3
- **Issue**: delta 字段 release 与当前 release 不一致；可能复制了上一 release 的 delta 模板
- **Recommendation**: 改 frontmatter `release: "0.3"` + 重跑 validate.py file
```

---

## 6. 维度 6：主 Doc vs Delta 决策合理性（仅 S2 / Bug Flow + delta 存在时）

### 6.1 关键问题

architecture-write `delta-policy.md` 决策是否被合理应用？长期事实是否回写主 doc？仅本 release 局部变化是否仅写 delta？

### 6.2 Checklist

按 `delta-policy.md` §7 配套：

| # | Check | severity if 失败 |
|---|-------|----------------|
| 6.1 | delta §3 Long-Term Fact Sync 表存在且每条改动一行 | blocking（事实源 `delta-policy.md` §5）|
| 6.2 | 表中每行 Long-term fact? 列有 yes / no 决策（不留空）| blocking |
| 6.3 | 表中每行 Synced 列与 Long-term fact? 一致（yes→yes / no→no）| blocking |
| 6.4 | 主 doc Change Log 含全部 yes synced 条目 | blocking |
| 6.5 | 主 doc Change Log 不含 no synced 条目（避免污染主 doc）| medium |
| 6.6 | 长期事实判别合理（按 `delta-policy.md` §3.1 信号）| blocking 若误判 |
| 6.7 | 模糊场景按"长期事实"保守处理（同步 + 标 "may consolidate" 注记）| medium 若激进只写 delta |

### 6.3 Finding 例子

```markdown
### Finding 6 [blocking, 维度 6: 主 doc vs delta 决策]
- **Where**: architecture_delta.md §2.4 "Add new column 'tenant_id' to users table; migration script attached" / architecture.md §6 Data Model 未同步
- **Issue**: 数据 schema 改变是 long-term fact（按 `delta-policy.md` §3.1 第 3 行）；但 §3 Long-Term Fact Sync 表标 no synced + 主 doc §6 未改
- **Recommendation**: 二选一：(a) 改 §3 表为 yes synced + architecture.md §6 同步加 tenant_id；(b) 如果是临时 column（下 release 删除），加显式注记说明 schema 临时性 + 标 no synced。默认按 (a) 保守处理
```

---

## 7. 维度 7：Bug Flow 实质覆盖（仅 root_cause==architecture）

### 7.1 关键问题

BUG-NNN 涉及的架构层（组件 / 接口 / 数据流）是否被实质修改（不是单加 Change Log entry 不动 body）？SKILL.md §7.1 改 doc 决策（主 vs delta）是否符合 architecture-write 表？

### 7.2 触发场景

仅在 `bug_flow.active==true AND bug_flow.root_cause==architecture` 时启用本维度。

### 7.3 Checklist

| # | Check | severity if 失败 |
|---|-------|----------------|
| 7.1 | architecture_delta.md §5 Bug Flow Linkage 节存在 + 标 BUG-NNN | blocking |
| 7.2 | BUG-NNN 涉及的具体 architecture 章节（组件 / 接口 / 数据流 / 部署）有 body 实质修改（不是 typo / 注释）| blocking |
| 7.3 | 改动按 SKILL.md §7.1 表分类（如运行时架构 bug → 长期事实候选 → 主 doc + delta 同步）| blocking |
| 7.4 | 长期事实候选时主 doc 已同步（不能仅写 delta）| blocking |
| 7.5 | Pending Changes 关联 BUG-NNN | blocking |

### 7.4 Finding 例子

```markdown
### Finding 7 [blocking, 维度 7: Bug Flow 覆盖]
- **Where**: BUG-007 描述 "API rate limiting design 在多实例部署下不生效" / architecture_delta.md §2.4 仅加 "noted limitation" 注记 / architecture.md 未改
- **Issue**: bug 暴露的是运行时架构缺陷（rate limit 不能仅靠单实例 in-memory counter），按 SKILL.md §7.1 第 3 行属长期事实候选；但 delta 仅加注记，主 doc 未改
- **Recommendation**: §3 加 distributed rate limiter component（typically Redis-backed）+ §4.3 改 cross-cutting concern "rate limiting" 描述 + architecture.md §3 同步加 component；§3 Long-Term Fact Sync 表加 yes synced 行
```

---

## 8. 跨维度组合决断

### 8.1 多 finding 同一处

同一处文本被多个维度命中（如 §3 component 缺章节 + 与 SRS 不一致）按**最高 severity** 输出 1 条 finding，body 列全部维度。

### 8.2 跨 doc finding

任一 finding 涉及 ≥ 2 doc（典型：架构 ↔ SRS 不一致）时，`Where` 字段必须显式给所有相关 doc path。

### 8.3 review_iteration 升级阈值

- iteration 1-3：blocking findings 出全 + 给 fix 方向
- iteration 4-6：聚焦核心矛盾；不再加新 finding
- iteration 7：finding 必含 "**升级人介入**" 提示

### 8.4 替 architecture-write 做决策（禁忌）

architecture-review **仅评审 architecture-write 已做的决策**；不替它决策（如不替它判断长期事实路径）。给 finding + recommendation，不直接给 "应该这样改架构" 命令。

---

## 9. Anti-Patterns（review skill 自身的禁忌）

| Anti-pattern | 后果 | 替代 |
|--------------|------|------|
| 输出 `approved` / `pending` / `pass` / `fail` / `LGTM` | 越权 / 模糊 | 仅 `review-passed` / `issues-found` |
| 直接修架构 doc body | 越界 architecture-write 职责 | finding 形式 |
| 直接改 doc frontmatter `status` | 越界 status_transition.py 职责 | 由 progress.py update --event 后 caller 调 |
| 单 finding 跨多 severity | 内部矛盾 | 拆 |
| 未读 SRS 就 review-passed | 维度 3 漏检 | §5 Step 2 必读上游 SRS 关键章节 |
| 维度 6 在 scenario==S1 / S3 首 release 触发 | 误判（S1/S3 首 release 通常无 delta） | 仅 S2-x / Bug Flow + delta 存在时启用 |
| 维度 7 在 root_cause != architecture 时触发 | 误判 | 仅 bug_flow.active==true AND root_cause==architecture 时启用 |
| 自行决定主 doc vs delta 决策路径 | 越权 architecture-write | 仅评审 architecture-write 是否合理；不替它决策 |
| 跨 release 修历史 release 的 delta finding | 历史目录只读 | 接受 + 提示 architecture-write 在新 release 主 doc 中补救（事实源 `delta-policy.md` §8.5）|

---

## 10. 输出 finding 标准格式

```markdown
## architecture-review iteration <N> — issues-found

**Summary**: <B> blocking / <M> medium / <L> low
**Coverage**: architecture.md<? + delta release-x.y>

### Finding 1 [blocking, 维度 6: 主 doc vs delta 决策]
- **Where**: architecture_delta.md §<n> + architecture.md §<m>
- **Issue**: ...
- **Recommendation**: ...

### Finding 2 [medium, 维度 4: 可决策性]
...
```

review-passed 时若有 non-blocking 建议同样输出，Summary 行写 "review-passed (X non-blocking suggestions)"。

---

## 11. 演化

- 修改本 rubric 必须在 SKILL.md §10 References 节同步说明
- 增加新维度 / 改变 severity 决断需走 design proposal review cycle
- 当前对应 design proposal 版本：v0.5（2026-05-06）+ v0.6 round 1 H3 + v0.6 round 2 M2 + Phase 7 polish
