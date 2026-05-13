---
name: bug-triage
description: dev-workflow-skills2 bug 分类与路由 orchestration skill。双模式：(a) Active mode：仅在 release_state==active AND current_stage==testing AND sub_state==review-passed 时由 testing-write 自动调用（Stage 5 发现 bug）或 scenario-dispatcher 在 testing 阶段路由用户主动报 bug；判定 4 类根因（srs / architecture / development / prd-exception），写 BUG-NNN.md frontmatter root_cause，调 progress.py bug-start（前 3 类）或创建 INCIDENT skeleton + incident-start（prd-exception）；非 testing 阶段用户报 bug 由 dispatcher 在那一层 reject，bug-triage 不会被 invoke。(b) Post-close mode：closed release 期间用户报 bug 时由 scenario-dispatcher 调用，创建 BUG-NNN.md skeleton (target_release: null) 并调 progress.py bug-intake 加入 unresolved_bugs。本 skill 不写 INCIDENT body（workflow-evolution 负责），不修 SRS/Architecture/Development 内容（由对应 stage skill 处理），不直接 mutation progress.md。
authority: 4
references:
  - references/root-cause-rubric.md
  - references/triage-decision-tree.md
---

# bug-triage

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；**实际 invocation 必须用完整路径** `skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py`。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4（与 stage skill / orchestration skill 同级；位于 `workflow-protocol` / `AGENTS.md` / `doc-guardian` 之后）。

**职责（5 项）**：

1. **Active mode**：判定 active release 中 bug 的根因（srs / architecture / development / prd-exception），写入 BUG-NNN.md frontmatter
2. **Active mode**：分支调 `progress.py bug-start`（前 3 类）或创建 INCIDENT skeleton + 调 `progress.py incident-start`（prd-exception）
3. **Post-close mode**：在 closed release 期间为用户报告的 bug 创建 `docs/bug/BUG-NNN.md` skeleton（`target_release: null`、`root_cause: null`、`consumed_in_release: null`）
4. **Post-close mode**：调 `progress.py bug-intake --bug <path>` 加入 `unresolved_bugs` 队列
5. 维护 BUG report ID 唯一性（依赖 `doc-guardian validate.py ids` 校验）

**不属于本 skill**：

- 写 INCIDENT-NNN.md body（仅创建 skeleton 含 frontmatter）→ `workflow-evolution`
- 修 SRS / Architecture / Development 内容 → 对应 stage skill 在 Change Mode 完成
- 直接 mutation `progress.md` → `workflow-protocol` 的 `progress.py`
- 测试代码 / 测试报告 → `testing-write` / `testing-review`
- 决定 scenario / scenario_subtype → `scenario-dispatcher`
- 评审 BUG report 内容质量 → 不强制（v0.5 设计未为 BUG report 配独立 review skill）
- active Bug Flow retest fail/partial 回退 → `testing-write` / Bootstrap 调 `skills/workflow-protocol/scripts/progress.py bug-rework`；本 skill 不重 triage 同一 active BUG

## 2. When to Invoke

### 2.1 Active Mode 触发

| 时机 | 由谁调用 | 输入 |
|------|---------|------|
| Stage 5 testing 发现 bug → testing-write 写 BUG report 后 | `testing-write` skill | BUG-NNN.md 路径（frontmatter `bug_id` / `found_in_release` 已填、`root_cause: null`）|
| `release_state==active` 且 `current_stage==testing` 且 `sub_state==review-passed` 时用户主动报 bug | `scenario-dispatcher` | 用户 bug 描述（dispatcher 提示先创建 BUG-NNN.md skeleton）|
| Bootstrap 检测到 `bug_flow.active==true` 但 `BUG-NNN.md root_cause==null`（即上次 active mode 未完成）| AGENTS.md Bootstrap | BUG-NNN.md 路径（从 `bug_flow.bug_report_path` 取） |

**前置条件**（active mode；v0.6 round 2 batch2-F2 收敛后严格按 `progress.py bug-start` gate）：

- `release_state == active`
- **`current_stage == testing` AND `sub_state == review-passed`**（与 `progress.py bug-start` 前置一致；非 testing 阶段不允许 active triage，dispatcher 在那一层就 reject）
- BUG-NNN.md 已存在（由 testing-write 自动创建或 dispatcher 提示用户先与 testing-write 创建）
- BUG-NNN.md frontmatter：`type: bug-report`、`bug_id: BUG-\d{3}`、`found_in_release: <current release>`、`root_cause: null`

**v0.6 round 2 batch2-F2 收敛说明**：早期版本允许 active release 期间任何 stage 用户主动报 bug 进入 active mode，但实际 `progress.py bug-start` 内部要求 `current_stage==testing AND sub_state==review-passed`，二者会发生不一致；旧版本试图通过创建 "known-issue BUG with target_release/root_cause null" 绕过，但该 BUG 不进 `bug_flow`、不进 `unresolved_bugs`、无 schema 字段表达，不可实现。本轮统一收敛：active mode 入口前置 = `bug-start` 前置；非 testing 阶段一律拒绝。

### 2.2 Post-Close Mode 触发

| 时机 | 由谁调用 | 输入 |
|------|---------|------|
| `release_state==closed` 期间用户报 bug | `scenario-dispatcher`（closed_release_dispatch 路径）| 用户 bug 描述 |

**前置条件**（post-close mode）：

- `release_state == closed`
- `project_state == active`（aborted/reconstructing 终态拒绝）
- `bug_flow.active == false`
- `workflow_incident_active == false`

### 2.3 不会被 invoke 的时机

- `release_state==active` 且 `bug_flow.active==true` 且 BUG-NNN.md 已有 `root_cause`（已经分流过）→ 由对应 stage skill 在 Change Mode 处理修复
- `workflow_incident_active==true` → 由 `workflow-evolution` 接管（含 `incident-resolve`）
- `project_state ∈ {aborted, reconstructing}` → 终态，禁止任何 triage

## 3. Mode A: Active Bug Triage

### 3.1 Active Mode 流程（7 步）

```
1. 读 BUG-NNN.md（frontmatter + body）
2. 读相关上下文 doc 帮助分类：
   - SRS（docs/release<x.y>/srs/srs.md）
   - Architecture（docs/architecture/architecture.md + architecture_delta.md）
   - 相关 Detailed Design（docs/release<x.y>/development/tasks/Tn/detailed_design.md）
   - 相关 verification_result（如有）
   - PRD（仅在怀疑 prd-exception 时读）
3. 应用 root-cause rubric（见 §6 + references/root-cause-rubric.md）判定 4 类
4. 写入 BUG-NNN.md frontmatter root_cause: <enum>
   - 同时在 ## Pending Changes 加 entry 描述本次分类
5. 调 changelog.py promote 把 Pending → Change Log
6. 调 validate.py file 校验 BUG report
7. 分支：
   ├ root_cause ∈ {srs, architecture, development}:
   │   → 调 progress.py bug-start --bug <path> --root-cause <enum>
   │
   └ root_cause == prd-exception:
       a. 创建 docs/incident/INCIDENT-MMM.md skeleton（含 frontmatter + 占位 body
          + 一条 ## Pending Changes entry "skeleton 创建"）
       b. 调 changelog.py promote <incident-path>（把首条 Pending entry 移入 Change Log，
          满足 doc-guardian validate.py 类 6 Change Log Discipline 要求）
       c. 调 validate.py file <incident-path>（必须 exit 0；类 6 要求 Pending 为空、
          Change Log 已含创建 entry）
       d. 调 progress.py incident-start --bug <bug-path> --report <incident-path>
```

**关键约束（v0.6 round 2 batch2-F1）**：INCIDENT skeleton 是增量类 doc，必须经 `changelog.py promote` 让 Pending Changes 为空、Change Log 含创建 entry，才能通过 `validate.py file`；validate pass 是 `incident-start` 前置（progress.py 内部 validate INCIDENT 文件）。bug-triage 不允许跳过 promote 直接 validate。

### 3.2 4 类根因路由表

| Root Cause | 触发后 stage 切换 | 命令 | 后续接管 skill |
|-----------|-----------------|------|---------------|
| `srs` | `testing` → `srs-specification` (Change Mode) | `progress.py bug-start --root-cause srs` | `srs-write` Change Mode |
| `architecture` | `testing` → `architecture-design` (Change Mode) | `progress.py bug-start --root-cause architecture` | `architecture-write` Change Mode |
| `development` | `testing` → `development` (Change Mode) | `progress.py bug-start --root-cause development` | `development-planning-write` / `development-code-write` Change Mode |
| `prd-exception` | `testing` → `workflow-incident-analysis` | `progress.py incident-start` | `workflow-evolution` |

### 3.3 BUG-NNN.md frontmatter 写入示例

bug-triage 写完 root_cause 后的 frontmatter：

```yaml
---
title: BUG-007 登录在 IE11 崩溃
type: bug-report
status: review-passed
bug_id: BUG-007
found_in_release: "0.3"
target_release: "0.3"            # active mode：与 found_in_release 相同
root_cause: development          # ← bug-triage 写入
consumed_in_release: null        # active mode 不填
created: 2026-05-15T10:00:00Z
updated: 2026-05-15T11:00:00Z
owner: claude-opus-4-7/bug-triage
---
```

**关键约定**：

- `target_release == found_in_release`（active mode）
- `consumed_in_release: null`（active mode bug 不进 unresolved_bugs 队列）
- `root_cause` 必须是合法 enum：`srs | architecture | development | prd-exception`

### 3.4 Stage 4 Development 根因的 Task 标注

如果 `root_cause: development`，bug-triage 应在 BUG-NNN.md body 标注**具体 task** ID（如 `T3`），帮助下游 development-* Change Mode skill 定位：

```markdown
## Triage Analysis

**Root Cause**: development
**Affected Task(s)**: T3 (登录页面前端组件)
**Likely Affected Files**: src/pages/login.tsx
**Rationale**: bug 重现步骤定位到 IE11 兼容性，对应 T3 的 detailed_design.md
            未要求 IE11 polyfill；属于实现层缺失，PRD/SRS/Architecture 不变。
```

`progress.py bug-start --root-cause development` 切回 Stage 4 后，development-planning-write 读 BUG report 决定是否需重新 plan/breakdown 还是直接修代码。

## 4. Mode B: Post-Close Bug Intake

### 4.1 Post-Close Mode 流程（6 步）

```
1. 与用户对话获取 bug 详情：
   - 重现步骤 / 触发条件
   - 期望 vs 实际行为
   - found_in_release（默认当前 closed release）
   - 影响范围（功能性 / 性能 / UI / 数据等）
2. 计算下一个 BUG ID（扫描 docs/bug/BUG-*.md，取 max + 1，3 位 zero-padded）
3. 创建 docs/bug/BUG-NNN.md：
   - frontmatter（target_release: null, root_cause: null, consumed_in_release: null）
   - body 含 user 报告内容
   - ## Pending Changes 章节（首条 entry "BUG report 创建"）
   - ## Change Log 空章节
4. 调 changelog.py promote 处理 Pending Changes
5. 调 validate.py file 校验 BUG report
6. 调 progress.py bug-intake --bug docs/bug/BUG-NNN.md
   → unresolved_bugs.append(<path>)
```

### 4.2 Post-close BUG-NNN.md frontmatter 模板

```yaml
---
title: BUG-008 注册流程邮箱重复时不报错
type: bug-report
status: review-passed
bug_id: BUG-008
found_in_release: "0.3"          # 当前 closed release（用户提 bug 时所在 release）
target_release: null             # 下次 release-start 时由 progress.py 自动填新 release
root_cause: null                 # post-close 不分类；下次 release 内 active triage 时再判
consumed_in_release: null        # release-start 时由 progress.py 自动填
created: 2026-05-20T14:00:00Z
updated: 2026-05-20T14:00:00Z
owner: claude-opus-4-7/bug-triage
---
```

### 4.3 Post-close 不分类 root_cause 的理由

post-close 期间不存在 active scenario / Stage Change Mode；分类后无路径走。等下次 `release-start` 时：

- `progress.py release-start` 自动 consume `unresolved_bugs`，写入 `target_release` / `consumed_in_release`
- srs-write 在 SRS write 阶段读 `consumed_in_release == <new release>` 的 BUG 列表，把修复需求合并到新 SRS
- 新 SRS 进入 testing 阶段 → 若 retest 仍 fail → 触发 active triage → 此时才判 root_cause

简而言之：**post-close BUG 是"等待下个 release 处理"的占位记录，不需要立刻分类**。

### 4.4 用户提供的信息不足时

如果用户描述过于模糊（如"登录有问题"），bug-triage 应先**与用户对话补充**：

- 具体重现步骤
- 期望 vs 实际行为
- 浏览器 / 环境
- 频率（每次 / 偶发）

信息不足时**不要创建** BUG-NNN.md（避免低质量 doc 进 unresolved_bugs 队列）。

## 5. PRD Exception Special Path

仅适用 active mode + `root_cause: prd-exception`。

### 5.1 INCIDENT skeleton 创建（4 步）

bug-triage 创建 `docs/incident/INCIDENT-MMM.md`：

**Step 1**：写文件（含 frontmatter + 占位 body + 一条 Pending Changes entry）

```yaml
---
title: INCIDENT-001 PRD 异常引发的 testing 失败
type: workflow-incident
status: draft
incident_id: INCIDENT-001
triggered_by_bug: BUG-007                # ← 关联触发 incident 的 BUG ID（不是路径，是 ID）
triggered_in_release: "0.3"
resolution_action: null                  # ← workflow-evolution 后续填 continue/abort/reconstruct
created: 2026-05-15T11:30:00Z
updated: 2026-05-15T11:30:00Z
owner: claude-opus-4-7/bug-triage
---

# INCIDENT-001 PRD 异常引发的 testing 失败

> 本 incident skeleton 由 bug-triage 创建。Body 章节由 workflow-evolution 在
> incident analysis 阶段填充：
> - 根因分析（PRD 哪部分错 / 工作流哪段没拦住）
> - 工作流改进建议
> - 3 个 action 的评估（continue / abort / reconstruct）
> - Recommendation
> - Resolution（用户决策记录）

## Pending Changes
- 2026-05-15T11:30:00Z [frontmatter+body]: skeleton 创建（bug-triage 仅写 frontmatter + 占位 body；§3-§7 待 workflow-evolution）

## Change Log
```

**Step 2**：调 `skills/doc-guardian/scripts/changelog.py promote <incident-path>`

→ 把 Pending Changes 首条 entry 移入 Change Log（按日期分组）；写回文件。
→ 执行后 doc 状态变为：`## Pending Changes`（空）+ `## Change Log` 含 `### 2026-05-15` 块下的创建 entry。

**Step 3**：调 `skills/doc-guardian/scripts/validate.py file <incident-path>`

→ 必须 exit 0；类 6 (Change Log Discipline) 要求 Pending Changes 为空，类 3/4 校验 frontmatter 合法。
→ 失败则修 frontmatter / Pending（重 promote）后重试。

**Step 4**：调 `skills/workflow-protocol/scripts/progress.py incident-start`（见 §5.3）

**Promote 后的 doc 状态示例**：

```markdown
[frontmatter 同 Step 1]

# INCIDENT-001 PRD 异常引发的 testing 失败

[占位说明同 Step 1]

## Pending Changes

## Change Log

### 2026-05-15
- 2026-05-15T11:30:00Z [frontmatter+body]: skeleton 创建（bug-triage 仅写 frontmatter + 占位 body；§3-§7 待 workflow-evolution）
```

### 5.2 INCIDENT skeleton 严格约束

- bug-triage **只**填 frontmatter + 占位说明 body；**不**写 §3-§7 分析内容
- frontmatter `triggered_by_bug` 必须是 BUG-NNN ID（不是路径）；workflow-protocol incident-start 校验 BUG-NNN.md frontmatter `bug_id` 与本字段相等
- `resolution_action: null`（workflow-evolution 与用户决策后填）
- `status: draft`（直到 workflow-evolution 完成 body 后改 review-passed，详见 workflow-evolution SKILL §3）
- **Step 2 promote 不可省**：incident skeleton 是增量类 doc，validate.py 类 6 要求 Pending Changes 为空；省 promote 会让 Step 3 validate 失败、Step 4 incident-start 前置不满足，整条 PRD-exception 路径不可达（v0.6 round 2 batch2-F1）

### 5.3 调 incident-start

```
skills/workflow-protocol/scripts/progress.py incident-start \
    --bug docs/bug/BUG-NNN.md \
    --report docs/incident/INCIDENT-MMM.md
```

progress.py 校验：

- `bug_flow.active == false`（incident-start 自身会设 true）
- `<bug-path>` BUG-NNN.md frontmatter `root_cause == prd-exception`
- `<incident-path>` 文件存在且 `type: workflow-incident`、frontmatter 完整
- INCIDENT-MMM.md frontmatter `triggered_by_bug == <bug-path 的 bug_id>`

校验通过后一次性设：

- `bug_flow.active = true`
- `bug_flow.bug_report_path = <bug-path>`
- `bug_flow.root_cause = prd-exception`
- `workflow_incident_active = true`
- `incident_report_path = <incident-path>`
- `current_stage = workflow-incident-analysis`

### 5.4 后续 workflow-evolution 接管

bug-triage 调 `incident-start` 成功后**退出**，不再持续介入。后续：

- `workflow-evolution` skill 在 incident state 下读 INCIDENT skeleton + BUG report，填 body + 与用户决策
- 用户选择 `continue` / `abort` / `reconstruct` 后，由 workflow-evolution 调 `progress.py incident-resolve`

## 6. Root Cause Classification (4 类)

完整 rubric 见 `references/root-cause-rubric.md`。本节为决策树概要。

### 6.1 顶层决策树

```
观察 bug 现象 + 重现步骤
  ↓
Q1: bug 是否表明产品方向 / 用户故事 / 关键功能集本身有问题？
  ├ Yes → root_cause = prd-exception
  └ No  → 进 Q2

Q2: bug 是否表明 SRS 中的功能描述 / NFR / 接口契约错误或缺失？
  ├ Yes → root_cause = srs
  └ No  → 进 Q3

Q3: bug 是否表明架构层有缺陷（组件划分错 / 数据流错 / 跨服务契约错）？
  ├ Yes → root_cause = architecture
  └ No  → root_cause = development（默认兜底）
```

### 6.2 4 类的典型例子

| Root Cause | 典型例子 |
|-----------|---------|
| `srs` | SRS 漏掉 IE11 兼容性需求；NFR 性能指标设定不合理；接口字段定义不一致 |
| `architecture` | 服务划分把强耦合数据放两个服务；缓存层设计导致一致性问题；消息队列拓扑错 |
| `development` | 实现 bug（空指针 / 边界 / 拼写）；代码不符合 detailed_design；测试遗漏 case |
| `prd-exception` | 整个产品方向走错（用户根本不需要这功能）；产品边界冲突无法调和；技术栈选错无法实现 |

### 6.3 prd-exception 的高警惕性

`prd-exception` 是**异常路径**，触发 incident analysis + 项目可能 abort/reconstruct。bug-triage 判定此类时应**特别保守**：

- 优先考虑前 3 类是否能解释 bug
- 只有当 bug 表明"PRD 描述的产品在 SRS / Architecture / Development 任一层都无法合理实现"时才判 prd-exception
- 不确定时**与用户对话二次确认**：「这看起来可能是 PRD 层的问题（产品方向 / 边界），需要进入 incident 分析。确认吗？」

### 6.4 模糊情况：多根因

```
现象：登录在 IE11 崩溃
分析：
  - SRS 没要求 IE11 兼容（root=srs?）
  - 实现没加 polyfill（root=development?）
```

判定原则：**取最上层的根因**（srs > architecture > development）。

理由：修最上层（SRS 加 IE11 兼容性需求）后，再修下层（development 加 polyfill）才正确；只修下层而不修 SRS，下次需求来 IE11 兼容时还会重复 bug。

bug-triage 判此例为 `srs`（要求修 SRS 加 IE11 需求 + 验收准则），SRS Change Mode 完成后回 Stage 5 retest，可能触发 development Change Mode（这是正常 Bug Flow 子环节）。

## 7. Output Contract

bug-triage 的"输出"分两类：

### 7.1 Type A: 写 BUG-NNN.md frontmatter（active mode 唯一 mutation 责任）

| 字段 | active mode 写入 | post-close mode 写入 |
|------|-----------------|---------------------|
| `bug_id` | testing-write 已写 / dispatcher 提供 | bug-triage 计算并写入 |
| `type` | testing-write 已写 | bug-triage 写入 `bug-report` |
| `status` | testing-write 已写 | bug-triage 写入 `review-passed`（无独立 review skill，直接终态） |
| `found_in_release` | testing-write 已写 | bug-triage 写入（默认当前 closed release）|
| `target_release` | bug-triage 写入（与 found_in_release 相同）| `null`（由 release-start 自动填）|
| `root_cause` | **bug-triage 写入** | `null`（active triage 时才判）|
| `consumed_in_release` | `null` | `null`（由 release-start 自动填）|

### 7.2 Type B: 调 progress.py / 创建 doc

| 决策结果 | 命令 |
|---------|------|
| Active mode + root_cause ∈ {srs, architecture, development} | `skills/workflow-protocol/scripts/progress.py bug-start --bug <path> --root-cause <enum>` |
| Active mode + root_cause == prd-exception | (a) 创建 `docs/incident/INCIDENT-MMM.md` skeleton；(b) `skills/workflow-protocol/scripts/progress.py incident-start --bug <bug-path> --report <incident-path>` |
| Post-close mode | (a) 创建 `docs/bug/BUG-NNN.md` skeleton；(b) `skills/workflow-protocol/scripts/progress.py bug-intake --bug <path>` |

### 7.3 Type C: 路由到其他 skill（隐含）

bug-triage 调完 progress.py 后，**workflow-protocol 自动切 current_stage**，下游 skill 由 workflow 状态机决定：

- `bug-start --root-cause srs` → 切 `srs-specification` → 由 `srs-write` Change Mode 接管
- `bug-start --root-cause architecture` → 切 `architecture-design` → `architecture-write` Change Mode
- `bug-start --root-cause development` → 切 `development` → `development-planning-write` / `development-code-write` Change Mode（具体哪个由 user/Bootstrap 决定）
- `incident-start` → 切 `workflow-incident-analysis` → `workflow-evolution`

bug-triage 本身**不**显式 invoke 下游 skill。

## 8. Concurrency & Idempotency

- bug-triage 是**多步骤 + 持有外部 doc 修改责任**的 skill
- 写 BUG-NNN.md 时不持有 `.progress.lock`（doc 编辑不加锁；progress.md mutation 才加）
- 调 `progress.py bug-start` / `incident-start` / `bug-intake` 内部 flock 保证 progress.md 原子
- **重复 invoke 防护**：active mode 进入时若检测到 BUG-NNN.md frontmatter `root_cause` 已设非 null，**跳过分类**；直接调对应 progress.py 子命令（如果 bug_flow.active 还是 false 表明上次 progress.py 调用失败，重试是安全的；若 bug_flow.active 已 true 则报错——已经分流过）

### 8.1 Idempotency 边界（v0.6 round 4 隐含）

| 状态 | 重复 invoke active mode 行为 |
|------|---------------------------|
| BUG.root_cause==null, bug_flow.active==false | 正常 triage 流程（写 root_cause + 调 bug-start/incident-start）|
| BUG.root_cause==<enum>, bug_flow.active==false | 跳过分类；直接调 bug-start/incident-start（重试场景）|
| BUG.root_cause==<enum>, bug_flow.active==true（已分流）| reject + 报错"已经分流，下游 stage Change Mode 在进行中" |

**Active retest fail/partial 边界**：若 `bug_flow.active==true` 且同一 active BUG 在 Stage 5 retest 后仍 fail/partial，不重新 invoke bug-triage、不改 root_cause、不创建第二个 BUG；由 `testing-write` / Bootstrap 调 `skills/workflow-protocol/scripts/progress.py bug-rework --bug <bug_flow.bug_report_path>`。

## 9. Forbidden Actions

- ❌ 直接编辑 `progress.md`（mutation 必须经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 修 SRS / Architecture / Detailed Design / 源代码 / Test 文件（属于下游 stage skill 在 Change Mode 完成）
- ❌ 写 INCIDENT-NNN.md body（仅创建 skeleton；body 是 `workflow-evolution` 责任）
- ❌ post-close mode 中判定 `root_cause`（必须留 null；下次 release 内 active triage 时再判）
- ❌ post-close mode 中调 `progress.py bug-start`（必须用 `bug-intake`）
- ❌ active mode 中调 `progress.py bug-intake`（必须用 `bug-start` 或 `incident-start`）
- ❌ active Bug Flow retest fail/partial 时重新 triage 同一 active BUG（必须由 testing-write/Bootstrap 调 `bug-rework`）
- ❌ 在 `release_state==closed` 期间走 active mode（dispatcher 应路由到 post-close mode）
- ❌ 在 `release_state==active` 期间走 post-close mode（dispatcher 应路由到 active mode）
- ❌ **在 `current_stage != testing` 或 `sub_state != review-passed` 时进入 active mode**（v0.6 round 2 batch2-F2）：与 `progress.py bug-start` 前置不一致；应由 dispatcher 在那一层 reject。已经被 invoke 时立即 reject 并提示用户走"等 testing 阶段"路径
- ❌ **创建 "known-issue BUG"（target_release/root_cause 为 null 但不调 progress.py）**（v0.6 round 2 batch2-F2）：该状态无 schema/progress 承载，会成为 orphan doc；正确做法是把现象记入当前 stage doc（如 detailed_design known-issue 段），不创建 BUG-NNN.md
- ❌ 在 `bug_flow.active==true` 时重新 triage（已分流过；若需重 triage，由 incident-resolve continue 后用户创建新 BUG report 触发新一轮 triage）
- ❌ 跳过 `validate.py file <BUG path>` 校验直接调 progress.py
- ❌ 自创 `BUG-NNN.md` ID（必须扫描 `docs/bug/BUG-*.md` 取 max + 1，3 位 zero-padded；冲突时由 doc-guardian validate ids 拒绝）
- ❌ INCIDENT-MMM.md 与 BUG-NNN.md 的 ID 关联错位（`triggered_by_bug` 字段必须等于 BUG 的 `bug_id` ID 字符串）

## 10. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| `validate.py file <BUG-path>` 失败 | 修 BUG report frontmatter / body / 章节，重跑校验 |
| `progress.py bug-start` 拒绝（前置不满足，如 current_stage != testing）| 检查 progress.md state；若状态机不允许，提示用户走正确路径 |
| `progress.py incident-start` 拒绝（BUG.root_cause 与命令参数不一致）| 检查 BUG-NNN.md frontmatter root_cause 是否真的等于 prd-exception |
| Active mode 判定后 progress.py 调用失败，BUG.root_cause 已写但 bug_flow.active 仍 false | 重 invoke active mode：检测到 root_cause 已设 → 跳过分类 → 重试 bug-start/incident-start |
| Post-close mode 创建 BUG-NNN.md 后 `bug-intake` 拒绝（duplicate intake：路径已在 unresolved_bugs）| 检查 progress.md unresolved_bugs；若确实重复，删除新创建的 BUG report 或要求用户用不同 ID |
| 用户报告内容模糊无法分类（active mode）| 与用户对话补充重现步骤 / 影响范围；不要凭直觉猜分类 |
| BUG ID 冲突（`docs/bug/` 已有同 ID）| `validate.py ids` 会报；rename 新 BUG report 到下一个 free ID |
| INCIDENT ID 冲突 | 同上，扫描 `docs/incident/INCIDENT-*.md` 取 max + 1 |

## 11. References

- `references/root-cause-rubric.md` — 4 类根因详细 heuristic + 关键问句 + 例子表 + 边界处理
- `references/triage-decision-tree.md` — 双模式入口决策树 + INCIDENT skeleton 模板 + active/post-close 端到端流程
- `skills/workflow-protocol/SKILL.md` — workflow-protocol 主协议
- `skills/workflow-protocol/references/command-reference.md` — `bug-start` / `bug-close` / `bug-intake` / `incident-start` 完整 mutation
- `skills/doc-guardian/references/frontmatter-schema.md` — `bug-report` 与 `workflow-incident` doc type schema
- `docs/workflow/workflow_specification_claude.md`（项目级）— Bug Flow 4 类根因路由
- `docs/design/skill_set_design_proposal_v0.5.md`（项目级）— 完整设计方案
