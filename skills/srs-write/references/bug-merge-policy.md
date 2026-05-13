# Consumed Unresolved Bugs Merge Policy

**配套**：`skills/srs-write/SKILL.md` §5 consumed_unresolved_bugs Merge Procedure。

本 reference 详细规定 srs-write 在本 release 首次进入 SRS 时（覆盖 S2-1/S2-2/S2-3，S1/S3 也跑保持一致性）如何把 release-start 已消费的 unresolved bugs 合并到 SRS。流程总览见 SKILL.md §5；本文给出按 root_cause 的逐类规则、边界处理、典型例子、recovery。

---

## 1. 触发时机（再确认）

**仅在以下条件**：

- `progress.md.current_stage == srs-specification`
- `progress.md.sub_state == write`
- 本 release 首次进入 SRS write（同一 release 二次进入时幂等跳过 §3 的写入步骤）

**不触发的场景**：

- Bug Flow re-entry (`bug_flow.active==true AND bug_flow.root_cause==srs`) — 这是 active bug 修复，独立路径
- revise 循环 — 不是新 release 起点

---

## 2. 数据源（事实源）

**唯一事实源**：扫描 `docs/bug/BUG-*.md` frontmatter，筛选 `consumed_in_release == <progress.md.release>` 的列表。

**禁止使用的事实源**：

- `progress.md.unresolved_bugs`（release-start 已清空）
- `progress-history.md release-start entry` 的 result 字段（仅记 count，不记 list）

**一致性约束**：

- 同一 BUG `consumed_in_release` 字段在 release-start 后被设置一次，之后只读
- doc-guardian validate.py 类 5 unique consumption 校验确保同一 BUG 不被多个 release 消费

---

## 3. 按 `root_cause` 分类合并

### 3.1 决策表

| `root_cause` | 是否进 SRS body | Pending Changes | 是否触发 Architecture / Development | srs-review 维度 7 校验 |
|--------------|----------------|-----------------|-----------------------------------|-----------------------|
| `null`（post-close intake 默认）| ✓ 视为"未分类修复需求" | ✓ 加 `Merged BUG-NNN: <title> — root_cause=null/awaiting-classification` | 否（修 SRS 即可让下游 Stage 3/4 看到需求）| ✓ blocking 检查 |
| `srs` | ✓ 修订 functional req / acceptance criterion | ✓ 加 `Merged BUG-NNN: <title> — root_cause=srs` | 否（同上）| ✓ blocking 检查 |
| `architecture` | ✗（仅可加跨 stage 责任注记，非强制）| ✗（避免在 SRS 虚假记录"改动"）| ✓ 触发 Stage 3 architecture-write 处理 | 不强制；过度合并 → medium |
| `development` | ✗（同上）| ✗（同上）| ✓ 触发 Stage 4 development-* 处理 | 不强制；过度合并 → medium |
| `prd-exception` | ✗ **拒绝 + 输出 issue** | ✗ | — | blocking 脏数据 |

### 3.2 各类详细处理

#### 3.2.1 `root_cause: null`（post-close intake 默认）

**含义**：post-close 期间用户用 `progress.py bug-intake` 把 bug 加入 unresolved_bugs，那时不做 active triage（command-reference §7），所以 root_cause 默认 null。release-start 消费后仍保持 null。

**处理**：

- 视为"未分类修复需求"，与 `srs` 同等合并到 SRS body
- **不**要求 srs-write 自行做 active triage（active triage 仅在 testing 阶段由 bug-triage 做）
- Pending Changes entry 显式标注 `root_cause=null/awaiting-classification` 让 srs-review 知道这是 post-close intake 默认，不是 SRS 漏标
- SRS body 修订形式：把 BUG body 描述的故障 / 缺陷转为 §2 functional req 的修订 + §<acceptance_plan> 加对应 AC
- 后续 stage 如果发现该 bug 实际上不属 SRS 范畴（e.g., 其实是 architecture 问题），再走标准 issues-found / re-triage 路径，不在本 skill 解决

#### 3.2.2 `root_cause: srs`

**含义**：bug-triage 在 active mode 已判定该 bug 属 SRS 层（功能描述 / NFR / 接口契约错误或缺失）。

**处理**：

- 同 §3.2.1 合并到 SRS body
- Pending Changes 显式标 `root_cause=srs`
- 修订形式：直接在 §2 functional req / §3 NFR / §4 interface contract 里改对应章节

#### 3.2.3 `root_cause: architecture`

**含义**：bug-triage 已判定该 bug 属架构层（组件划分 / 数据流 / 跨服务契约 / 模块边界）。

**处理**：

- **不**进 SRS body §2-§4
- 可加 §6 Consumed Bug Fixes 表中的"责任注记"行，标注 "（architecture 影响；SRS 仅加责任注记，详见 BUG-NNN.md）"
- 不在 Pending Changes 加 entry（避免 SRS Change Log 虚假记录"改动"）
- 实际修复在 Stage 3 architecture-write 进行

**为什么 SRS 仍可选注记**：让 srs-review 通读时能看到本 release 有哪些 architecture-class bug 在并行处理；但这是 **optional**，不强制。

#### 3.2.4 `root_cause: development`

**含义**：bug-triage 已判定该 bug 属实现层（detailed_design 已正确指定但实现 deviate）。

**处理**：

- 同 §3.2.3 不进 SRS body
- 可加 §6 表"责任注记"行
- 实际修复在 Stage 4 development-* 进行

#### 3.2.5 `root_cause: prd-exception`（脏数据）

**含义**：理论上不应在 consumed 列表出现——`prd-exception` 在原 release testing 阶段已通过 incident-resolve 处理（continue / abort / reconstruct 终态）。如果出现，说明数据脏（罕见，但需要 fail-safe）。

**处理**：

- **拒绝合并**
- 输出 issue 让用户人工 audit
- 修复路径：从 git 历史恢复 BUG-NNN.md 正确 frontmatter（或人工修正 `root_cause` / `consumed_in_release` 字段）→ 重跑 `validate.py file <BUG-NNN.md>` → 重新触发 srs-write 扫描
- **不要**期待 `progress.py recover` 修该脏数据——`recover` 仅从 progress-history.md 重建 progress.md，**不**改 BUG report frontmatter（事实源 progress.py recover §4 + v0.6 round 2 M4）

---

## 4. SRS body 修订形式

### 4.1 root_cause ∈ {null, srs} 的合并模式

**Pattern 1: 修订既有 capability**

如果 BUG 暴露既有 §2 capability 描述错误：

```markdown
### 2.1.1 Capability A1 — Cart checkout

- **Source**: PRD §3 (P0 story 1) + BUG-007 fix
- **Description**: 修订自 v0.1 — 原描述未覆盖 ZIP code 5 位 vs 9 位差异；本 release 加：
  - Inputs: payment + shipping address + ZIP (5 or 9 digits)
  - Validation: ZIP 必须匹配 ^\d{5}(-\d{4})?$
- **Acceptance Criteria**: → acceptance_plan.md §2.1 (含 BUG-007 regression AC)
```

**Pattern 2: 新增 capability**（如 BUG 暴露 SRS 漏功能）

```markdown
### 2.3.1 Capability C1 — Email confirmation (added in v0.2 to address BUG-009)

...
```

**Pattern 3: 修订 NFR**（如 BUG 是性能问题）

```markdown
| Performance | API p95 latency | ≤ 100ms (revised from 200ms in v0.1; see BUG-012) | Stage 5 load test |
```

### 4.2 §6 Consumed Bug Fixes 表

无论 §2-§4 怎么修，§6 表必须列每个 root_cause ∈ {null, srs} 的 bug：

```markdown
## 6. Consumed Bug Fixes

| BUG ID | root_cause | 本 SRS 中的修复需求 | 关联 Acceptance Criteria |
|--------|-----------|--------------------|------------------------|
| BUG-007 | srs | §2.1.1 Capability A1 修订 ZIP validation | acceptance_plan.md §2.1 AC-005 |
| BUG-009 | null | §2.3.1 新增 Capability C1 | acceptance_plan.md §2.3 AC-012 |
| BUG-012 | architecture | (architecture 影响；SRS 加责任注记，详见 BUG-012.md) | — |
```

### 4.3 Pending Changes 条目格式

```markdown
## Pending Changes

- 2026-05-15T10:30:00Z [Section 2.1.1]: Merged BUG-007: ZIP code 5/9 digit support — root_cause=srs
- 2026-05-15T10:32:00Z [Section 2.3.1]: Merged BUG-009: Email confirmation capability — root_cause=null/awaiting-classification
- 2026-05-15T10:33:00Z [Section 6]: Add architecture-class BUG-012 responsibility note
```

每条 entry 必须能映射回 body 实际改动；Change Log 与 body 漂移会被 srs-review 维度 5 拒绝。

---

## 5. Edge Cases

### 5.1 BUG-NNN.md frontmatter 缺失或 unparseable

**处理**：拒绝合并；输出 issue 让用户从 git 恢复或修正；不静默跳过。validate.py 类 5 cross-ref 也会拒绝 advance。

### 5.2 BUG body `## Triage Analysis` 缺失（root_cause==development 时）

**处理**：development 类 bug 不进 SRS，所以 srs-write 不需读 Triage Analysis；缺失不影响本 skill。development 阶段 bug-triage 已处理；本 skill 仅依赖 frontmatter `root_cause` 字段。

### 5.3 同 release 多次进入 SRS write（advance 失败回退 / Bug Flow re-entry 后 advance 回 SRS）

**处理**：扫描结果应已无新增"未被 SRS 引用的 consumed bug"。如果发现新 bug（通常因为用户在中间 manually 加了 BUG-NNN.md `consumed_in_release` 字段），按 §3 流程合并；幂等条件是看 SRS Change Log 是否已有对应 `Merged BUG-NNN` entry。

### 5.4 用户改主意：取消某条 consumed bug

**处理**（与 SKILL.md §10 Recovery 表一致）：

- 改 BUG-NNN.md frontmatter `target_release: null` + `consumed_in_release: null`（视为撤回）
- 不改 progress.md
- srs-review 维度 7 扫描不到该 BUG，自然不要求 SRS 合并
- 如果 SRS 已加了 §2 / §6 行，srs-write 在下一轮 revise 时移除（Pending Changes 加 "Removed BUG-NNN: <reason>"）
- **推荐**：在 release-start 之前从 progress.md `unresolved_bugs` 列表移除（避免事后撤回）

### 5.5 BUG-NNN.md `consumed_in_release` 与 `target_release` 不一致

**处理**：拒绝合并；这是脏数据；提示用户 audit。release-start 应该把两字段同步设为同一 release 值。

### 5.6 跨 release reuse 同一 BUG

**处理**：validate.py 类 5 unique consumption 已拦下；srs-write 不会看到这种状态。

---

## 6. srs-review 维度 7 校验对照

srs-review §3 维度 7（consumed_unresolved_bugs 合并完整性）应按本 policy 校验：

| Check | severity if 失败 |
|-------|----------------|
| 每条 root_cause ∈ {null, srs} 的 consumed bug 在 SRS §2-§4 有对应改动 + §6 行 + Change Log entry | blocking |
| 每条 root_cause ∈ {architecture, development} 的 consumed bug 不在 SRS body §2-§4（仅 §6 注记 OK，强加 → 维度 7 medium）| medium 或 blocking（视过度合并程度）|
| 任意 consumed bug `root_cause==prd-exception` 出现 | blocking（脏数据）|
| §6 表行数 ≥ scan 出的 root_cause ∈ {null, srs, architecture, development} consumed bug 总数 | blocking |
| 每条 §6 行的 BUG ID 与 frontmatter `consumed_in_release` 字段对应 | blocking |

详见 `skills/srs-review/references/review-rubric.md` 维度 7 完整 checklist。

---

## 7. 演化

- 修改本 policy 必须在 SKILL.md §5 + §10 References 节同步说明
- 改变 root_cause → 是否进 SRS 的决策需走 design proposal review cycle
- 当前对应 design proposal 版本：v0.5（2026-05-06）+ Phase 7 polish
