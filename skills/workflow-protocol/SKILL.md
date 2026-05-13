---
name: workflow-protocol
description: dev-workflow-skills2 工作流协议核心。任何使用本工作流的项目里，agent 起手必读本 skill。负责状态机、转换规则、Hook 闭环硬约束、progress.md/progress-history.md 管理（含 progress.py 12 个子命令）、评审循环计数与超限升级。所有 stage skill 完成产物前必须 invoke 本 skill 提供的 progress.py 推进 state；无 progress.py 自由编辑 state 文件即违规。
authority: 1
references:
  - references/command-reference.md
---

# workflow-protocol

> **Path Convention Note**（v0.6 round 2 L9）：本 skill 文档为可读性使用 `progress.py` 等简写指代脚本；**实际 invocation 必须用完整路径** `skills/workflow-protocol/scripts/progress.py`。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：本 skill 在 `AGENTS.md` Authority Hierarchy 中位列第 1（高于 AGENTS.md 自身、doc-guardian、各 stage skill）。当本 skill 与其他 skill 规则冲突时，以本 skill 为准。

**职责边界**（精简后 5 项）：

1. **状态机定义**：Hybrid 形式（YAML schema + 转移表 + prose 解释）
2. **转换规则**：state X → state Y 的合法性校验
3. **Hook 闭环 / "MUST call X" 硬约束**：各阶段强制调用清单
4. **progress.md / progress-history.md 管理**：唯一通过 `scripts/progress.py` 子命令操作
5. **评审循环计数 + 超 7 升级人介入**：在 progress.md 记录 review_iteration

**不属于本 skill 的事**：

- Bootstrap 协议 → `AGENTS.md`
- Scenario 路由（S1/S2/S3/S4 判定）→ `scenario-dispatcher` skill
- Bug 根因分类 → `bug-triage` skill
- doc 合规校验 → `doc-guardian` skill

## 2. When to Invoke

**任何 stage skill / orchestration skill 在以下时机必须 invoke 本 skill 的 progress.py**：

| 时机 | 调用 |
|------|------|
| 新会话 / 新任务起手 | `progress.py query`（读 state） |
| stage 内 sub_state 转换（write → in-review → revising 等）| `skills/workflow-protocol/scripts/progress.py update --event <name>`（v0.6 F8 命名事件白名单）|
| 推进到下一 stage | `progress.py update --advance` |
| Stage 7 完成 close release | `progress.py release-close` |
| 启动新 release | `progress.py release-start --version <x.y> --scenario <S2-1\|S2-2\|S2-3>` |
| post-close 期间收到 bug | `progress.py bug-intake --bug <path>` |
| Stage 5 testing 发现 bug | `progress.py bug-start --bug <path> --root-cause <enum>` |
| active Bug Flow retest fail/partial | `skills/workflow-protocol/scripts/progress.py bug-rework --bug <BUG-NNN.md>` |
| Bug 修复完成 + retest pass | `progress.py bug-close` |
| bug-triage 判 prd-exception | `skills/workflow-protocol/scripts/progress.py incident-start --bug <bug-path> --report <incident-path>`（v0.6 round 2 H2 修签名）|
| 用户决定 incident 处置 | `skills/workflow-protocol/scripts/progress.py incident-resolve --action <continue\|abort\|reconstruct>` |

**禁止任何 agent 直接编辑 progress.md 或 progress-history.md**。所有写入必须经 progress.py（含原子性 + 回退 + 一致性校验）。

## 3. State Files

| 文件 | 路径 | 写入入口 | 编辑约束 |
|------|------|---------|---------|
| `progress.md` | 项目根 | `progress.py update` 等子命令 | overwrite mode；禁止手工编辑 |
| `progress-history.md` | 项目根 | `progress.py update` append | append-only；禁止修改历史 entry |
| `.progress.lock` | 项目根 | flock 自动管理 | 不要手工创建/删除 |

### 3.1 progress.md Schema

```yaml
---
project_name: <string>
workflow_version: v0.6
project_state: active | aborted | reconstructing
release: "<MAJOR.MINOR>"
release_state: active | closed
release_close_reason: null | "stage-7-completed" | "incident-abort" | "incident-reconstruct"
previous_releases: [<list of MAJOR.MINOR strings>]
scenario: S1 | S2 | S3 | S4
scenario_subtype: null | S2-1 | S2-2 | S2-3 | S2-4
current_stage: prd-inception | srs-specification | architecture-design | development | testing | delivery | project-retrospective | workflow-incident-analysis | null
sub_state: null | write | in-review | revising | review-passed | approved   # v0.6 round 2 M5: 允许 null（terminal state 用）
review_iteration: <int, 0-7>
development_state:                  # 仅 current_stage=development 时存在
  total_tasks: <int>
  task_states: { Tn: <state>, ... }
artifacts:
  prd: <path>
  architecture: <path>
  srs: <path>
  acceptance_plan: <path>
  integration_plan: <path>          # 多模块时
  architecture_delta: <path>        # 本 release 改架构时
bug_flow:
  active: <bool>
  bug_report_path: <path or null>
  root_cause: null | srs | architecture | development | prd-exception
workflow_incident_active: <bool>
incident_report_path: <path or null>
unresolved_bugs: [<list of bug report paths>]
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
---

# Current Stage Summary
[当前 stage / sub_state / 关键 doc 路径 / next action]

# Recent Activity
[自动从 progress-history.md 取最近 3 条 derive；不可手工编辑]
```

### 3.2 progress-history.md Schema

时间顺序追加（旧顶新底），每条 entry 严格模板（脚本生成）：

```markdown
## {ISO8601 UTC timestamp} — {action_type} — {one_line_result}
- agent: {agent_id}
- task: {task_id, 仅 Stage 4 时存在}
- result: {结构化结果}
- next: {next_action}
```

## 4. progress.py 子命令清单（12 个）

完整 mutation 详表见 `references/command-reference.md`。本节仅列概要。

| Subcommand | 用途 | 适用 state |
|-----------|------|-----------|
| `init` | 新项目首次初始化 progress.md（创建首个 release）| 项目根无 progress.md |
| `update --event <name>` / `--advance` / `--task <Tn> --status <new>` | 状态机事件触发（原子 + 回退）；event 白名单见 references/command-reference.md（v0.6 F8）| 任何活动 state |
| `query` | 读取当前 state（只读，可并发，无锁）| 任何 state |
| `recover` | 从 progress-history.md 重建 progress.md（异常恢复）| 任何 state |
| `release-close` | Stage 7 完成时 close 当前 release | `release_state==active` AND Stage 7 done |
| `release-start --version <x.y> --scenario <S2-x>` | 启动新 active release | `release_state==closed` |
| `bug-intake --bug <path>` | post-close 期间记录 bug | `release_state==closed` |
| `bug-start --bug <path> --root-cause <enum>` | active Bug Flow 入口 | `bug_flow.active==false` AND `current_stage==testing` |
| `bug-rework --bug <path>` | active Bug Flow retest fail/partial 后回同一 root-cause stage | `bug_flow.active==true` AND `current_stage==testing` AND latest test-report fail/partial |
| `bug-close` | active Bug Flow 出口（retest pass 后）| `bug_flow.active==true` AND retest pass |
| `incident-start --bug <bug-path> --report <incident-path>` | bug-triage 判 prd-exception 后调用（v0.6 round 2 H2 新签名）| `project_state==active AND bug_flow.active==false AND workflow_incident_active==false AND BUG.root_cause==prd-exception` —— Phase 6.3 不 gate `current_stage`，PRD-exception 可在 Stage 5 或更晚 stage 触发 |
| `incident-resolve --action <continue\|abort\|reconstruct>` | 退出 incident 状态（v0.6 round 2 H3：continue 已简化为只清空 bug_flow，无 --bug-flow 子参数）| `workflow_incident_active==true` |

### 4.1 `update` 原子流程（适用于所有改动）

任何改动 state 的子命令内部都走以下流程：

```
1. 计算 new_progress + new_history_entry
2. flock on `.progress.lock`（其他 agent 阻塞）
3. 备份当前 progress.md + progress-history.md
4. 校验状态机转换合法性
   - 不合法 → 解锁、报错（exit 1）、不动文件
5. append progress-history.md（原子 file write）
6. overwrite progress.md（原子 rename）
7. 一致性校验：从 history 重建 progress.md == 实际写入的 progress.md
   - 不一致 → rollback 两文件 → exit 1
8. 删备份、释放锁、exit 0
```

**任何 step 失败**：rollback + 报错 + 由 caller AI 修复触发原因后重新调用，禁止绕过脚本直接写。

## 5. Stage Done 判定矩阵（P6）

`progress.py update --advance` 的合法性由本矩阵决定。stage skill 调 `--advance` 时，本 skill 校验下列维度：

| 维度 | 检查方式 |
|------|---------|
| **A. 必需 artifacts 存在** | 由 `skills/doc-guardian/references/required-artifacts.md` 经 `skills/_shared/dev_workflow/artifacts.get_required_artifacts(progress, root)` 推导当前 stage 的必备 artifact 列表（scenario-aware + 条件 DSL 驱动），逐路径检查文件存在。事实源是 required-artifacts.md，**不是** progress.md `artifacts:` dict（后者只存项目级 + release 级 mutable 入口路径，不参与 P6 A 推导）。 |
| **B. doc-guardian 校验通过** | 对 A 推导出的每个路径调 `skills/doc-guardian/scripts/validate.py file <each artifact>` 全部 exit 0 |
| **C. Review 通过** | 对应 `*-review` skill 最近一轮返回 `review-passed`（无 issues-found）；由 `apply_update_advance` 通过 sub_state 前置间接 enforce |
| **D. 人确认（仅 PRD/SRS/Architecture/CR）** | `apply_update_advance` 校验 `progress.md.sub_state == approved`（即 `progress.py update --event human-confirmed` 已 fire；progress-history.md 自动有对应条目）即视为 D 维度通过；对应 doc frontmatter `status: approved` 由 `skills/doc-guardian/scripts/status_transition.py apply --event human-confirmed --doc <path>`（多 doc 重复 `--doc`）同步，由 P6 B 维度 `validate.py file` 复检。advance 不在 D 维度独立重读 doc.status；事实源 command-reference §2.2 + Phase 7 P4 polish。 |
| **E. 内部验证（Stage 4/5/6）** | Stage 4: `apply_update_advance` 检查 development_state.task_states 全 `verified`（per-task verification 已在 Stage 4 transition 时校验）；Stage 5: `progress.py update --advance` 读 test-report.verification_status==pass；Stage 6: 读 installation-result.verification_status==pass |

任一维度失败 → `--advance` 拒绝 → stage skill 须先修复。

### 5.1 7 个 Stage 的判定矩阵（v0.6）

**Artifact 必备清单的事实源是 `skills/doc-guardian/references/required-artifacts.md`**（scenario-aware），本表只列各 stage 的必备核心 artifact 概要。完整清单（含条件性、S3 必备、per-task）由 required-artifacts.md 提供，`update --advance` 时由 workflow-protocol 调用 doc-guardian 推导。

| Stage | A. 核心必备（详见 required-artifacts.md）| B | C | D | E |
|-------|---|---|---|---|---|
| 1 PRD | PRD（S3 时含 source-system-analysis prd-level + feature-matrix）| ✓ | review-passed | approved | — |
| 2 SRS | SRS + Acceptance Plan + Integration Plan（**多模块时**）+ S3 时含 source-system-analysis srs-level/module-level/reuse-replace（technical-debt 推荐）| ✓ | review-passed | approved | — |
| 3 Architecture | Architecture Document + Architecture Delta（**本 release 引入架构变更时**）| ✓ | review-passed | approved | — |
| 4 Development | 见 5.2 task-level 矩阵；含 development-plan + task-breakdown + 各 task per-task artifacts | ✓ | review-passed | — | per-task verification-result `verification_status: pass` |
| 5 Testing | Test Preparation + Test Procedure + Test Report | ✓ | review-passed | — | Test Report `verification_status: pass`（initial fail → bug-start；active retest fail/partial → bug-rework）|
| 6 Delivery | Deployment Doc + Operation Manual + Installation Result | ✓ | review-passed | — | Installation Result `verification_status: pass` |
| 7 Retrospective | Project Retrospective（项目级单文件，每 release 增量加节）| ✓ | review-passed | — | — |

### 5.2 Stage 4 task-level 判定（v0.6 含 test-review-report）

```
Stage 4 done ⇔ all task_states[Tn] == "verified"
```

每 task 子状态序列：

| 子状态 | 满足条件 |
|--------|---------|
| `planning-done` | `detailed_design.md` 通过 doc-guardian + 对应 review skill 输出 review-passed |
| `test-writing` → `test-review` → `test-revising` → `test-done` | `test_review_report.md` (per-task) 满足 **`review_status: pass`**（v0.6 round 3 H2：skeleton 默认 pending，必须由 development-test-review 填 pass 才允许）且 `blocking_findings_count: 0` |
| `code-writing` → `code-review` → `code-revising` → `code-review-passed` | `code_review_report.md` 满足 **`review_status: pass`**（v0.6 round 3 H2：skeleton 默认 pending，必须由 development-code-review 填 pass）且 `blocking_findings_count: 0` |
| `verifying` → `verified` | `verification_result.md` 满足 `verification_status: pass`（unit + integration tests 全部通过的执行报告）|

**测试代码本身**（`tests/unit/` / `tests/integration/`）不在 doc-guardian 管辖。`test_review_report.md` 是测试代码的 review 输出 doc，由 `development-test-review` skill 产出。

## 6. Bug Flow 完整闭环（v0.6 修正 PRD exception 路径）

Stage 5 E 失败 → 进入 Bug Flow：

```
1. testing-write 写 Bug Report (BUG-NNN.md，frontmatter root_cause 暂为 null)
2. invoke bug-triage active mode → 判断 root_cause，写入 BUG-NNN.md frontmatter
3. 分支：
   ├ root_cause ∈ {srs, architecture, development}:
   │   - bug-triage 调 skills/workflow-protocol/scripts/progress.py bug-start
   │     --bug docs/bug/BUG-NNN.md --root-cause <enum>
   │   - workflow-protocol 校验 BUG-NNN.md frontmatter root_cause 与命令参数一致
   │   - 切 current_stage 到对应 stage（Change Mode）
   │     · root_cause==development 时，progress.py 解析 BUG body `## Triage Analysis`
   │       `**Affected Task(s)**` + classification keyword（test-only / source-code 等）
   │       并按 PROTECTED_TASK_TRANSITIONS 自动回退 affected task（verified → test-revising
   │       / verified → code-revising / code-review-passed → code-revising）；缺失或
   │       分类不明确时要求 development-planning-write replan/route，不猜测；事实源
   │       skills/_shared/dev_workflow/progress_state.py 的 compute_dev_bug_rollback +
   │       PROTECTED_TASK_TRANSITIONS（Task 6 Phase 6.1 实装；原 Gap-4 已 closed）
   │   - 该 stage 重新过 A/B/C/D/E（写 → review → revise → ... → review-passed → human approved if gated）
   │   - 完成后回到 Stage 5 重测
   │   - retest pass → testing-write 调 progress.py bug-close
   │   - workflow-protocol 评估 Stage 5 done → 推进 Stage 6
   │   - retest fail/partial → testing-write / Bootstrap 调
   │     skills/workflow-protocol/scripts/progress.py bug-rework --bug docs/bug/BUG-NNN.md
   │     回到同一个 root-cause stage；不得再次 bug-start / 新建第二个 BUG
   │
   └ root_cause == prd-exception:
       - bug-triage 在 BUG-NNN.md frontmatter 标 root_cause: prd-exception
       - bug-triage 创建 INCIDENT-NNN.md skeleton（仅 frontmatter，body 待 workflow-evolution 填）
       - bug-triage 调 progress.py incident-start
         --bug docs/bug/BUG-NNN.md --report docs/incident/INCIDENT-NNN.md
       - progress.py 校验 BUG-NNN.md frontmatter root_cause==prd-exception
       - 校验通过 → 同时设 bug_flow.active=true + workflow_incident_active=true + current_stage=workflow-incident-analysis
       - workflow-evolution skill 接管，填充 INCIDENT-NNN.md 内容
       - 用户决策后调 progress.py incident-resolve --action <continue|abort|reconstruct>
         （v0.6 round 2 H3：continue 已简化为单一行为——清空 bug_flow + 回到 testing；无 --bug-flow 子参数；
          若需要重新分类原 bug，用户需在 continue 后创建新 BUG report 触发 bug-triage active mode）
```

**关键修正（v0.6 F2）**：`incident-start` 不再要求"先有 bug_flow.active"作为前置——它自身一次性设置 bug_flow + incident state。整条 PRD exception 路径自闭。

## 7. Release Lifecycle

### 7.1 Version Grammar

`<MAJOR>.<MINOR>` 两个非负整数（regex `^(\d+)\.(\d+)$`）。

按数字对比较：`(0, 10) > (0, 2)` 因为 minor 10 > 2，所以 `"0.10" > "0.2"`。

`progress.py release-start` 校验新 version 严格大于 `previous_releases` 中所有版本。

### 7.2 Lifecycle Rule

| 规则 | 内容 |
|------|------|
| 同时只 1 个 active release | `release_state` 字段约束 |
| Release 创建 | `progress.py release-start`（首次用 `init`）|
| Release close 条件 | Stage 7 retrospective 完成且 review-passed |
| 历史 release 只读 | release close 后，对应 `docs/release<x.y>/` 目录变只读 |
| S4 policy | 仅 active release 期间触发；post-close 走 `bug-intake` |
| Post-close bug 处理 | bug-triage post-close mode → `progress.py bug-intake` → 加入 `unresolved_bugs` → 下次 `release-start` 时由 srs-write 合并到新 SRS |
| S2 → release 映射 | S2-1/2/3 全部触发新 release；S2-4 转 S3（新 project）|

## 8. Review Loop

| 规则 | 内容 |
|------|------|
| 评审循环上限 | **7 次** |
| 计数位置 | progress.md `review_iteration` 字段 |
| 计数行为 | 每次 review 输出 `issues-found` 后 +1；review-passed 后归零（推进下一 sub_state）|
| 超限处理 | `review_iteration > 7` 时 `progress.py update` 拒绝写入；caller 必须升级人介入 |
| Revise owner | `*-write` skill 在 Change Mode 下完成；无独立 `*-revise` skill |
| 状态转换 | `in-review (issues-found)` → `revising` → `in-review (review-passed?)` |

## 9. Project Terminal State（v0.6 含字段清理）

`project_state ∈ {aborted, reconstructing}` 是终态。一旦进入：

- `progress.py update` / `update --advance` / `update --event` / `update --task` 全部拒绝
- 受保护字段相关 dedicated subcommand（`bug-start` / `bug-rework` / `bug-close` / `release-start` / `release-close` / `bug-intake` / `incident-start` / `incident-resolve`）也拒绝
- 仅允许 `progress.py query`（只读）和 `progress.py recover`（**唯一允许的 repair mutation**——v0.6 round 2 M5 澄清：recover 能从 history 重建 progress.md，但**不得改变 `project_state` 终态语义**——重建后的 progress.md 必须保持 `project_state: aborted/reconstructing`）
- 用户若要继续，必须新开 project（独立目录、独立 progress.md）

**Terminal mutation 必须清理字段**（v0.6 F11）：进入 `aborted` 或 `reconstructing` 时同时执行：

```yaml
sub_state: <any> → null            # schema 允许 null（v0.6 起）
review_iteration: <N> → 0
bug_flow.active: <any> → false
bug_flow.bug_report_path: <any> → null
bug_flow.root_cause: <any> → null
workflow_incident_active: true → false
incident_report_path: <any> → null
current_stage: <any> → null
```

进入终态的两个路径：

| 命令 | project_state |
|------|---------------|
| `incident-resolve --action abort` | `aborted` |
| `incident-resolve --action reconstruct` | `reconstructing`（用户随后启动新 S3 project，可在新 PRD 引用本 project 作为 source system）|

## 10. Concurrency Model

- **统一接口**：任何 agent（无论主协调还是子 agent）都通过 `progress.py update`
- **锁内部处理并发**：`.progress.lock` 串行化多 agent 请求
- **Stage 4 子 agent**：每个 task 子 agent 通过 `update --task <Tn> --status <new>` 报告进度；脚本内部 diff old vs new task state，决定是否更新 progress.md（变化时）或仅 append history（无变化时）

## 11. Forbidden Actions

- ❌ 直接编辑 `progress.md` 或 `progress-history.md`
- ❌ 跳过 `progress.py` 自创 `.progress.lock`
- ❌ 推进 stage 不调 `update --advance`
- ❌ 在 workflow-protocol 内部跑 unit/integration tests（只读 `verification_status` 字段）
- ❌ stage skill 自行判断 next stage（必须由本 skill 状态机决定）
- ❌ 评审循环超过 7 次仍尝试推进（必须升级人介入）
- ❌ 在 `release_state==closed` 期间调 `bug-start`（必须先 `release-start` 启动新 release）
- ❌ 在 active Bug Flow retest fail/partial 时再次调 `bug-start` 或创建第二个 BUG（必须调 `skills/workflow-protocol/scripts/progress.py bug-rework --bug <BUG-NNN.md>`）
- ❌ 在 `project_state ∈ {aborted, reconstructing}` 时调任何 mutation 类命令
- ❌ **使用 `update --event` 修改受保护字段**（v0.6 F8）：`release_state` / `release` / `release_close_reason` / `previous_releases` / `current_stage` / `bug_flow.*` / `workflow_incident_active` / `incident_report_path` / `project_state` / `unresolved_bugs` 必须经 dedicated subcommand
- ❌ **bug-triage 判定 `prd-exception` 后调 `bug-start`**（v0.6 F2）：必须调 `incident-start`
- ❌ **使用旧 `incident-start --report <path>` 单参数签名**（v0.6 round 2 H2）：必须用 `--bug <bug-path> --report <incident-path>` 两参数版本

## 12. Recovery on Failure

任何 `progress.py update` 失败：

1. 脚本自动 rollback 两文件到调用前状态
2. exit 非 0 + stderr 输出错误
3. caller AI 必须：
   - 读懂 stderr 报错
   - 修复触发原因（如补缺的 artifact、修复 doc-guardian 校验失败、人确认未完成 等）
   - 重新调用脚本

如果 progress.md 自身损坏（如手工编辑导致 schema 不合法），用 `progress.py recover` 从 progress-history.md 重建。

## 13. References

- `references/command-reference.md` — 12 个子命令的完整 mutation 详表
- `docs/workflow/workflow_specification_claude.md`（项目级）— Workflow spec 定义
- `docs/design/skill_set_design_proposal_v0.5.md`（项目级）— 完整设计方案
