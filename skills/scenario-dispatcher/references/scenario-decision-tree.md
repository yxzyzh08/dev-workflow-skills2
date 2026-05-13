# scenario-dispatcher Decision Tree

**配套**：`skills/scenario-dispatcher/SKILL.md`

本 reference 提供完整决策树、S1 vs S3 首次入口判定、S2 4 子场景 heuristic、S4 触发约束、edge cases 与端到端示例。Task 6 实现 dispatcher 时必须严格按本 reference。

---

## 1. Top-Level Decision Tree

dispatcher 的 invoke 入口走以下决策树（伪代码）：

```python
def dispatch():
    state = progress_query()  # skills/workflow-protocol/scripts/progress.py query

    # ---- 分支 A: progress.md 不存在 ----
    if state is None or progress_md_missing:
        return route_first_time(user_input)

    # ---- 分支 B: progress.md 损坏 ----
    if state.schema_invalid or state.scenario is None:
        return reject(
            reason="progress.md 损坏或 scenario 字段缺失",
            recovery="调 skills/workflow-protocol/scripts/progress.py recover --confirm"
        )

    # ---- 分支 C: 终态 ----
    if state.project_state in {"aborted", "reconstructing"}:
        return reject(
            reason=f"project_state={state.project_state}（终态）",
            recovery="起新 project（独立目录、独立 progress.md）"
        )

    # ---- 分支 D: incident 接管 ----
    if state.workflow_incident_active:
        return route_to("workflow-evolution")

    # ---- 分支 E: bug flow 接管 ----
    if state.bug_flow.active:
        return route_to("bug-triage", mode="active")

    # ---- 分支 F: 按 release_state 分流 ----
    if state.release_state == "active":
        return dispatch_active_release(state, user_input)
    elif state.release_state == "closed":
        return dispatch_closed_release(state, user_input)
```

---

## 2. S1 vs S3 First-Time Routing

适用：`progress.md` 不存在，dispatcher 决定走 S1 还是 S3 init。

### 2.1 关键问句

dispatcher 必须**与用户对话确认**，不要从用户输入语义猜。直接问：

```
问句 A：「你是从 0 打造一个全新产品，还是要基于一个已有的外部系统重构？」
  - 选项 1: 从 0 打造新产品 → S1
  - 选项 2: 重构 / 重写 / 替换已有的外部系统 → S3
```

### 2.2 S1 触发条件清单

满足**全部**：

- 用户明确说"新产品"、"全新项目"、"从 0 开始"
- **没有**外部源系统作为基准
- PRD 将由用户与 prd-write skill 共同从头编写
- 没有源系统 PRD/SRS 可读

→ 调 `skills/workflow-protocol/scripts/progress.py init --project <name> --scenario S1 --release <x.y>`

### 2.3 S3 触发条件清单

满足**任一**：

- 用户明确提及"重构"、"重写"、"重建"、"替换"已有系统
- 用户提供了**源系统的 PRD 或 SRS** 文档（路径或内容）
- 用户描述目标是"用新技术栈实现已有产品功能"

→ dispatcher **必须先确认用户提供了源系统 PRD/SRS 路径或内容**，缺失则不允许 init。
→ 调 `skills/workflow-protocol/scripts/progress.py init --project <name> --scenario S3 --release <x.y>`

### 2.4 S3 初始化后必须告知用户的硬约束

dispatcher 在 init 完成后**必须**给用户以下提示（事实源 `skills/doc-guardian/references/required-artifacts.md`）：

```
S3 后续阶段强制要求：
- Stage 1 (PRD Inception) 必备 2 份源系统分析:
  * docs/prd/supporting/source_product_prd_analysis.md (analysis_kind: prd-level)
  * docs/prd/supporting/feature_matrix.md (analysis_kind: feature-matrix)
- Stage 2 (SRS Specification) 必备 3 份 + 1 推荐:
  * docs/release<x.y>/srs/source_product_srs_analysis.md (analysis_kind: srs-level) - 必备
  * docs/release<x.y>/srs/source_module_analysis.md (analysis_kind: module-level) - 必备
  * docs/release<x.y>/srs/reuse_replace_capability.md (analysis_kind: reuse-replace) - 必备
  * docs/release<x.y>/srs/technical_debt_analysis.md (analysis_kind: technical-debt) - 推荐非必备
缺失任一必备 artifact 时，progress.py update --advance 会被 doc-guardian validate 拒绝。
```

dispatcher **不**创建这些 doc（由 prd-write / srs-write 负责），只是**通知用户**。

### 2.5 边界情况

| 情况 | 处理 |
|------|------|
| 用户说"借鉴竞品 X 的设计"但不重写 X 的代码 | **S1**（竞品分析放 `docs/prd/supporting/competitor_research.md`，不需要源系统 PRD）|
| 用户说"我们已经有个老系统但只想加个新功能" | **不是 S3**；先问"老系统是否已用本工作流（有 progress.md）"——若有，则是 S2；若无，则需先把老系统纳入工作流（独立讨论）|
| 用户说"重写老项目的某一个模块" | **S3**（哪怕只重写一部分，源系统 SRS 必备）|
| 用户对"全新"/"重构"边界不清楚 | dispatcher 列两个选项的具体差异（必备 artifacts 不同 / Stage 1-2 流程不同）让用户选 |

---

## 3. S2 Sub-scenario Decision Tree

适用：`release_state==closed` 且用户提"非 bug 类"新需求。

### 3.1 三层 Heuristic 问句序列

dispatcher 必须按**严格顺序**问下面 3 个问句（不要跳跃 / 不要合并）：

```
Q1：「这次需求是否需要改写 PRD（产品定位 / 用户故事 / 关键功能集）？」
  - Yes → 进 Q2
  - No  → 进 Q3

Q2：「PRD 改动是否影响现有架构骨架（技术栈替换 / 重大架构重写 / 产品形态根本改变）？」
  - Yes → S2-4（**不在本 project 继续**，起新 S3 project）
  - No  → S2-1（PRD Inception Change Mode）

Q3：「现有 SRS 是否需要修改（已存在的 SRS section 改写）？」
  - Yes → S2-3（SRS Specification Change Mode）
  - No  → S2-2（SRS Specification Full Mode for new SRS sections）
```

### 3.2 例子表（Q1 = Yes）

| 用户描述 | Q2 答案 | 子场景 | 入口 |
|---------|--------|-------|------|
| "再加个会员积分系统，要在 PRD 加这个功能模块" | No | S2-1 | `progress.py release-start --version <x.y> --scenario S2-1` |
| "把产品从 To-B 转 To-C，重新定义用户群" | Yes | S2-4 | 起新 S3 project |
| "PRD 加一节关键 KPI 指标，但不变核心定位" | No | S2-1 | `release-start --scenario S2-1` |
| "把单体架构换成微服务，PRD 也要重写" | Yes | S2-4 | 起新 S3 project |
| "产品类型从 SaaS 改成本地部署 enterprise edition" | Yes | S2-4 | 起新 S3 project |

### 3.3 例子表（Q1 = No, Q3 = Yes）

| 用户描述 | 子场景 | 入口 | 备注 |
|---------|-------|------|------|
| "登录模块的 SRS 加多因素认证需求" | S2-3 | `release-start --scenario S2-3` | SRS Change Mode |
| "支付模块改用第三方网关，更新 SRS" | S2-3 | `release-start --scenario S2-3` | SRS Change Mode |
| "API 性能要求从 200ms 改 100ms" | S2-3 | `release-start --scenario S2-3` | SRS Change Mode（NFR 修改）|

### 3.4 例子表（Q1 = No, Q3 = No）

| 用户描述 | 子场景 | 入口 | 备注 |
|---------|-------|------|------|
| "新增报表模块（之前 SRS 完全不涉及）" | S2-2 | `release-start --scenario S2-2` | SRS Full Mode for new sections |
| "再加一个客服工单子系统" | S2-2 | `release-start --scenario S2-2` | 全新模块 SRS |
| "增加一组管理后台功能（新模块）" | S2-2 | `release-start --scenario S2-2` | 全新 SRS sections |

### 3.5 S2-1 vs S2-3 边界（高频混淆）

两者都涉及"修改"，区别在**修改的 doc**：

- **S2-1**：PRD（项目级，`docs/prd/prd.md`）需要改 → 入口 `prd-inception` Change Mode → 之后通常也要改 SRS（但 dispatcher 不预判，由 prd-write 决定）
- **S2-3**：仅 SRS（release 级，`docs/release<x.y>/srs/srs.md`）需要改，PRD 完全不动 → 入口 `srs-specification` Change Mode

判定原则：若用户描述能不动 PRD 就实现需求（仅在 SRS 层）→ S2-3；若用户描述需要改 PRD（产品定位/功能集变化）→ S2-1。

**不确定时不要猜**，问用户：「这次 PRD 是否需要修改？」

### 3.6 S2-4 vs S2-1 边界（最难判定）

两者都改 PRD，区别在**改动深度**：

- **S2-1**：PRD 微调（加新功能模块，但产品形态、技术栈、整体架构骨架不变）→ 在本 project 内继续
- **S2-4**：PRD 大改（产品形态变 / 技术栈变 / 架构重写级）→ 起新 S3 project，本 project 走 release-close（如未完）后视为 source system

判定 rubric（满足**任一**就是 S2-4）：

| 信号 | 例子 |
|------|------|
| 技术栈替换 | 单体→微服务 / 同步→事件驱动 / SQL→NoSQL 主存储替换 |
| 产品形态变化 | SaaS→on-premise / B2C→B2B / Web→Mobile-first |
| 用户群根本变化 | 内部工具→公开产品 / 单租户→多租户 |
| 大部分既有代码无法复用 | dispatcher 应主动问用户："新方案下既有代码大概能复用多少？"低于 30% → S2-4 |

**关键警示**：S2-4 一旦起新 S3 project，**回滚成本极高**（独立目录、独立 progress.md、原 project 进 closed 状态作 source system）。dispatcher 必须在调 `progress.py init`（新 S3）**前**与用户**二次确认**；若用户犹豫，建议先走 S2-1 试做（万一不行再 abort/reconstruct）。

### 3.7 S2-4 路径细节

S2-4 的两条物理路径（dispatcher 与用户共同确认）：

**路径 1：当前 project 已 closed**（正常路径）

```
release_state == closed
  ↓
dispatcher 判定 S2-4 → 拒绝 release-start
  ↓
告知用户：本 project 进入归档，启动新 S3 project（独立目录、独立 progress.md）
  ↓
用户 cd 到新目录 → dispatcher 重新 invoke → S3 init（指引用户用本 project 作 source system）
```

**路径 2：当前 project active 但触发 PRD 重构需要**（异常路径）

```
release_state == active
  ↓
正常情况这不应该是 dispatcher 入口（dispatcher 不会在 active 期间被 invoke 重新决定 scenario）
  ↓
若用户硬要起 S2-4：dispatcher 拒绝，提示走以下任一路径：
  (a) 完成当前 release（Stage 7 → release-close）后再走路径 1
  (b) 若是 PRD 异常（即"做错方向"），等 testing 阶段触发 → bug-triage → incident-start →
      workflow-evolution → incident-resolve --action reconstruct → 自动转 S3
```

---

## 4. S4 Trigger Constraint

S4 (Bug Fix) 触发条件 + 错误路径处理：

### 4.1 S4 合法触发条件

**全部**满足：

- `release_state == active`
- 已存在或可创建合法 BUG-NNN.md（type=`bug-report`，frontmatter 含 `bug_id`、`found_in_release`）

### 4.2 S4 入口路径（v0.6 round 2 batch2-F2 收敛）

| 触发源 | dispatcher 介入？ | 流程 |
|--------|-----------------|------|
| Stage 5 testing 自动发现 bug | **否**（直接 testing-write → bug-triage active mode）| dispatcher 不参与；这个路径是工作流内部 |
| 用户在 active release 的 testing 阶段主动报 bug（`current_stage==testing` AND `sub_state==review-passed`）| **是** | dispatcher 检测到用户输入是 bug 描述 → 提示创建 BUG report skeleton → invoke bug-triage active mode |
| 用户在 active release 的**非 testing 阶段**（或 sub_state ≠ review-passed）主动报 bug | **是（拒绝）** | dispatcher 拒绝；解释 `progress.py bug-start` 前置约束；提示路径：(a) 等本 release 推进到 testing 阶段；(b) 把现象记入当前 stage doc 的 known-issue 段；**不**创建 orphan BUG、**不**调任何 progress.py 子命令 |
| 用户在 closed release 期间报 bug | **是** | dispatcher → invoke bug-triage **post-close mode**（**不**走 S4） |

### 4.3 dispatcher 区分 "新需求" vs "bug" 的 heuristic

| 用户描述特征 | 判定 |
|------------|------|
| "登录失败 / 报错 / 行为不符合 SRS / 测试失败" | **bug**（S4 active 或 post-close）|
| "增加 / 新功能 / 改产品" | **新需求**（S2 子场景判定）|
| "性能慢 / 体验差，但功能正常" | **dispatcher 无法直接判定**：问用户「这是 SRS 已规定的性能/体验指标未达标（→ bug），还是想提升超出原 SRS 的新指标（→ S2-3）？」|
| "之前的 X 功能现在不工作了"（regression）| **bug** |

模糊时**不要猜**，列两个选项让用户选。

### 4.4 closed release 期间禁止 `progress.py bug-start`

dispatcher 必须 reject 任何 closed release 期间的 S4 / `bug-start` 请求，并解释正确路径：

```
拒绝消息模板：
"当前 release_state==closed，S4 (Bug Fix) 仅在 active release 期间允许。
 此 bug 应通过 post-close 路径处理：
   1. 创建 docs/bug/BUG-NNN.md（target_release: null）
   2. 调 skills/workflow-protocol/scripts/progress.py bug-intake --bug <path>
 该 bug 进 unresolved_bugs 队列，下次 release-start 时由 srs-write 合并到新 SRS。
 
 我（scenario-dispatcher）将 invoke bug-triage post-close mode 完成上述步骤。"
```

---

## 5. Active Release Dispatch Sub-tree

适用：`release_state == active` 且 dispatcher 被 invoke（一般是异常路径，正常 active 期间 dispatcher 不会被 invoke）。

```python
def dispatch_active_release(state, user_input):
    intent = classify_user_input(user_input)

    if intent == "continue_current_stage":
        # 不是 dispatcher 的活；dispatcher 应该不会被 invoke 到这里
        return passthrough(target=state.current_stage + "-write/-review")

    if intent == "report_bug":
        # v0.6 round 2 batch2-F2: 严格按 bug-start 前置 gate
        if state.current_stage == "testing" and state.sub_state == "review-passed":
            return route_to("bug-triage", mode="active",
                            prep="先与用户确认 bug 描述，提示创建 BUG report skeleton")
        else:
            return reject(
                reason=(
                    f"progress.py bug-start 前置要求 current_stage==testing AND "
                    f"sub_state==review-passed；当前 ({state.current_stage}, "
                    f"{state.sub_state}) 不满足"
                ),
                recovery=(
                    "(a) 等本 release 推进到 testing 阶段，由 testing-write 自动发现并 triage；"
                    "(b) 把当前现象写到当前 stage doc 的 known-issue 段（detailed_design / "
                    "test_preparation 等）作笔记；不创建 orphan BUG report、不调 progress.py"
                )
            )

    if intent == "new_feature":
        return reject(
            reason="active release 期间不允许引入新 scenario / 新 feature 范围",
            recovery="完成当前 release（→ release-close）后再起新 S2 release"
        )

    if intent == "product_reconstruct":
        return reject(
            reason="active release 期间不允许整体重构 dispatch",
            recovery=(
                "(a) 完成当前 release（Stage 7 → release-close）后再起新 S2-4/S3；"
                "(b) 若是 PRD 异常路径，等 testing 触发 → bug-triage → incident-start → "
                "workflow-evolution → incident-resolve --action reconstruct"
            )
        )

    return ask_user_to_clarify_intent()
```

### 5.1 用户意图分类 heuristic

| 用户输入特征 | 分类 |
|------------|------|
| "继续 / 下一步 / 接着做" | continue_current_stage |
| "X 出错了 / 测试失败 / 行为不符" | report_bug |
| "再加个 Y / 新增 Z 功能" | new_feature（active 期间拒绝）|
| "改产品方向 / 技术栈换 / 整体重构" | product_reconstruct（拒绝 + 提示路径）|
| 模糊 | ask_user_to_clarify_intent |

---

## 6. Closed Release Dispatch Sub-tree

适用：`release_state == closed` 且用户提新输入。

```python
def dispatch_closed_release(state, user_input):
    intent = classify_user_input(user_input)

    if intent == "report_bug":
        return route_to("bug-triage", mode="post-close")

    if intent == "new_feature":
        # 走 S2 4 子场景判定（§3）
        s2_subtype = run_s2_decision_tree(user_input)
        if s2_subtype == "S2-4":
            return reject(
                reason="S2-4 (PRD 重构级) 不在本 project 继续",
                recovery="起新 S3 project（独立目录），可在新 PRD 引用本 project 作 source system"
            )
        return invoke_command(
            f"skills/workflow-protocol/scripts/progress.py release-start "
            f"--version {next_version} --scenario {s2_subtype}"
        )

    if intent == "product_reconstruct":
        # 直接转 S3（与 S2-4 同路径）
        return reject(
            reason="整体重构需起新 S3 project",
            recovery="新建独立目录，dispatcher 在新目录中重新 invoke 后走 S3 init"
        )

    return ask_user_to_clarify_intent()
```

### 6.1 next_version 计算

dispatcher 计算 `next_version` 时：

- 读 `progress.md previous_releases` + 当前 `release`（最近 closed 的 release）
- 默认建议 minor +1（如 `0.3` → `0.4`）
- 若用户明确说"大版本"，建议 major +1, minor 0（如 `0.3` → `1.0`）
- **必须**让用户确认 version；不要静默选定

校验规则：新 version 必须严格大于 `previous_releases` 中所有版本（按 (major, minor) 数字对比较）。

---

## 7. Edge Cases

### 7.1 `progress.md` 损坏

| 损坏类型 | dispatcher 处理 |
|---------|----------------|
| YAML parse 失败 | 拒绝；提示用户用 editor 检查 / 调 `progress.py recover` |
| 关键字段缺失（`scenario` / `release_state` / `project_state`）| 拒绝；提示 `progress.py recover` |
| `scenario` 值非 enum（如 `"S5"`）| 拒绝；要求修复或 recover |
| `previous_releases` 含非法 version 字符串 | 拒绝；要求修复 |

dispatcher **不**自行修复 progress.md（会破坏 history 一致性）；统一走 `recover`。

### 7.2 用户在错误时机调 dispatcher

| 时机 | dispatcher 反应 |
|------|---------------|
| `release_state==active` 且 `bug_flow.active==true` 时调 dispatcher | 检测到 → invoke bug-triage active mode 接管，不走 dispatch 逻辑 |
| `workflow_incident_active==true` 时调 dispatcher | 检测到 → invoke workflow-evolution 接管，不走 dispatch 逻辑 |
| `project_state==aborted` 时调 dispatcher | reject + 提示起新 project |
| `release_state==active` 且 scenario 已设、用户提"继续" | 不走 dispatch 逻辑；让 caller 直接路由当前 stage skill |

### 7.3 多个新需求同时提

```
用户："这次 release 既要加会员系统，还要改支付模块，再修一个老 bug。"
```

dispatcher 处理：

1. **拒绝混合 dispatch**；分解 3 项并按优先级处理
2. 推荐顺序（dispatcher 主动建议）：
   - 修 bug 优先（如果是 active release 中或 closed-post 的 bug，先走 bug 路径）
   - 然后选**一个**主导 scenario（通常用户明示哪个最优先）
   - 同 release 内可以同时含 S2-2（新模块）+ S2-3（改既有）的混合改动，但 dispatcher 决策 release-start 时只能选**一个** scenario_subtype。混合改动选择规则：
     - 主导改动是新增 → S2-2，改动现有的 srs section 当作"附带变更"
     - 主导改动是修改 → S2-3，新增 section 当作"附带新增"
     - 含 PRD 改动 → S2-1（覆盖前两者）
3. **不要替用户决定主导 scenario**；用 AskUserQuestion 让用户选

### 7.4 跨 release 残留 unresolved_bugs

dispatcher 在 `release_state==closed` 期间检测到 `unresolved_bugs` 非空时：

- **不**自动消费这些 bug
- 在与用户对话决定下个 release scenario 时，**主动告知** unresolved_bugs 列表，让用户考虑这些 bug 是否需要纳入下个 release 的 SRS（这是 srs-write 的工作，但用户应知情）
- `release-start` 命令会自动消费 unresolved_bugs 并标 `consumed_in_release`，dispatcher 只是路由 + 提示

### 7.5 用户提供错误的 version

```
用户："起 release 0.2"，但 previous_releases = ["0.1", "0.5"]
```

dispatcher 调 `progress.py release-start --version 0.2` 会被 progress.py 校验拒绝（0.2 < 0.5）。dispatcher 应**预先校验**：

- 计算 `max(previous_releases ∪ {current_release})`
- 若 `next_version <= max`，提示用户选更大 version
- 不要尝试改 progress.md 让 0.2 通过

### 7.6 S3 内嵌 S2 的特殊情况

S3 项目第一次走完 7 阶段产生 release 0.1 后，**第 2 个 release 起**走 S2 流程（不再是 S3）：

- progress.md `scenario` 字段在 release-start 时由 dispatcher 改写为 S2（基于用户输入的 S2 子场景）
- 不需要每个 release 重复源系统分析（已在 release 0.1 完成）
- 但 dispatcher 应在 release-start 时**告知用户**："本 release 起转入 S2 流程，源系统分析不再必备"

---

## 8. End-to-End Examples

### 8.1 Example A：S1 全新项目首次启动

```
用户：「我要开始一个全新的 todo 应用项目」

dispatcher:
1. progress.py query → progress.md 不存在
2. 与用户确认：「从 0 打造新产品 vs 重构外部系统？」→ 用户选 S1
3. 与用户确认：「项目名 / 首个 release version」→ todo-app / 0.1
4. 调：skills/workflow-protocol/scripts/progress.py init \
        --project todo-app --scenario S1 --release 0.1
5. 路由：prd-write 进入 Stage 1
```

### 8.2 Example B：S3 重构外部系统

```
用户：「我要把老的 PHP 论坛系统重构成 Node.js + React」

dispatcher:
1. progress.py query → progress.md 不存在
2. 确认：S3（明确"重构"+提及具体源系统）
3. 与用户确认：源系统 PRD/SRS 路径
4. 用户提供 docs/source-system/legacy_forum_prd.md + legacy_forum_srs.md
5. 与用户确认：项目名 / 首个 release / 默认 release 0.1
6. 调：progress.py init --project new-forum --scenario S3 --release 0.1
7. 告知用户：Stage 1 必备 source-system-analysis (prd-level + feature-matrix)
            Stage 2 必备 (srs-level + module-level + reuse-replace)
8. 路由：prd-write 进入 Stage 1
```

### 8.3 Example C：S2-1 PRD 加新功能模块

```
当前：release 0.2 closed，previous_releases = ["0.1", "0.2"]
用户：「加一个会员积分系统作为新功能」

dispatcher:
1. progress.py query → release_state==closed, previous_releases=["0.1","0.2"], release="0.2"
2. 用户输入 → new_feature 类
3. 走 S2 decision tree:
   Q1 (PRD 改？) → 用户答 Yes（积分是新模块要进 PRD）
   Q2 (架构骨架变？) → 用户答 No（架构层面不变）
   → S2-1
4. 计算 next_version: max(0.1, 0.2) = 0.2 → 建议 0.3 → 用户确认
5. 调：progress.py release-start --version 0.3 --scenario S2-1
6. 路由：prd-write Change Mode 进入 Stage 1
```

### 8.4 Example D：S2-3 仅改既有 SRS

```
当前：release 0.5 closed
用户：「登录模块要加多因素认证，PRD 不动」

dispatcher:
1. progress.py query → release_state==closed
2. 用户输入 → new_feature
3. S2 decision tree:
   Q1 (PRD 改？) → 用户答 No
   Q3 (SRS 改？) → 用户答 Yes（登录模块 SRS 要加 MFA 章节）
   → S2-3
4. 计算 next_version: 0.5 → 0.6
5. 调：progress.py release-start --version 0.6 --scenario S2-3
6. 路由：srs-write Change Mode 进入 Stage 2
```

### 8.5 Example E：S2-2 加新模块

```
当前：release 0.3 closed
用户：「再加个全新的客服工单子系统」

dispatcher:
1. progress.py query → release_state==closed
2. 用户输入 → new_feature
3. S2 decision tree:
   Q1 (PRD 改？) → 用户答 No（客服工单是 PRD 早提到的待开发模块）
   Q3 (SRS 改？) → 用户答 No（之前 SRS 没涉及）
   → S2-2
4. next_version: 0.3 → 0.4
5. 调：progress.py release-start --version 0.4 --scenario S2-2
6. 路由：srs-write Full Mode for new SRS sections 进入 Stage 2
```

### 8.6 Example F：S2-4 PRD 重构级变更

```
当前：release 0.4 closed
用户：「我要把产品从 SaaS 改成本地部署 enterprise edition，整体重新规划」

dispatcher:
1. progress.py query → release_state==closed
2. 用户输入 → 包含"整体重新规划"信号
3. S2 decision tree:
   Q1 (PRD 改？) → Yes
   Q2 (架构骨架变？) → Yes（部署形态完全改变 = 产品形态变化）
   → S2-4
4. **二次确认**：
   "S2-4 意味着不在本 project 内继续，需要起新 S3 project（独立目录），
    本 project 的 release 0.4 作为 source system。回滚成本高，确定吗？"
   → 用户确认
5. 拒绝在本 project release-start
6. 提示用户：
   - cd 到新目录创建 new-enterprise-edition/
   - 在新目录中 dispatcher 重新 invoke
   - 走 S3 init，引用本 project 作 source system PRD/SRS
```

### 8.7 Example G：closed-post bug

```
当前：release 0.5 closed
用户：「线上发现登录页面在 IE11 里崩溃」

dispatcher:
1. progress.py query → release_state==closed
2. 用户输入 → report_bug
3. 不走 S2 / S4，走 post-close path
4. 路由：bug-triage post-close mode
5. bug-triage 创建 docs/bug/BUG-007.md (target_release: null)
6. bug-triage 调：progress.py bug-intake --bug docs/bug/BUG-007.md
7. unresolved_bugs.append("docs/bug/BUG-007.md")
8. 提示用户：bug 已加入待处理队列，下次 release-start 时由 srs-write 合并入新 SRS
```

### 8.8 Example H：active release 中拒绝重构 dispatch

```
当前：release 0.3 active，current_stage=development，bug_flow.active=false
用户："我想把架构改成微服务"

dispatcher:
1. progress.py query → release_state==active, scenario already set
2. 这种情况 dispatcher 一般不被 invoke（normal 路径不会走到 dispatcher）
3. 若 Bootstrap 检测到与 active scenario 矛盾的输入并 invoke dispatcher：
   classify_user_input → product_reconstruct
4. 拒绝；提示路径:
   (a) 完成当前 release（推进到 Stage 7 → release-close）后起新 S2-4 / S3；
   (b) 若用户判定当前 release 方向已错，等 testing 触发或主动 abort：
       走 bug-triage → incident-start → workflow-evolution →
       incident-resolve --action reconstruct
```

### 8.9 Example I：active release 非 testing 阶段用户主动报 bug → 拒绝（v0.6 round 2 batch2-F2）

```
当前：release 0.4 active，current_stage=development，sub_state=write，bug_flow.active=false
用户："我刚发现登录在某些情况下会偶发 500"

dispatcher:
1. progress.py query → release_state=active, current_stage=development, sub_state=write
2. classify_user_input → report_bug
3. 检查 bug-start 前置 (current_stage==testing AND sub_state==review-passed) → 不满足
4. 拒绝；提示路径:
   (a) 等本 release 推进到 testing 阶段，testing-write 跑测试时如果重现该现象会自动
       创建 BUG report 并 invoke bug-triage active mode；
   (b) 当前现象记到 development 阶段的 detailed_design.md known-issue 段
       （或 plan.md / breakdown.md，取决于现象指向哪个 task），方便 testing 阶段重点验证；
5. 不创建 docs/bug/BUG-NNN.md；不调 progress.py 子命令；dispatcher 退出
```

注：这是 batch2-F2 收敛后的标准路径。dispatcher 严格按 `bug-start` 前置 gate，不创建 orphan BUG。

---

## 9. Dispatch 决策日志

dispatcher 每次决策应输出**人类可读的 decision summary**给用户（不写入 progress-history.md，那是 progress.py 的职责）：

```
模板：
"scenario-dispatcher decision summary:
 - Detected state: progress.md=<exists|missing>, release_state=<...>, ..."
 - User intent classification: <continue_current_stage|report_bug|new_feature|product_reconstruct|ambiguous>"
 - Decision: <S1|S2-1|S2-2|S2-3|S2-4|S3|S4-active|S4-postclose|reject>"
 - Rationale: <one-line>"
 - Next action: <invoke command | route to skill | reject reason>"
```

如果用户对决策有异议，dispatcher 应允许重新对话；不要把"已经 dispatch 过"作为不容反悔的理由（除非已经成功调 `progress.py init` / `release-start`，那时 progress.md 已 mutation，回滚需要 recover）。

---

## 10. 与其他 skill 的协作边界

| skill | dispatcher 与之关系 |
|-------|-------------------|
| `workflow-protocol` | dispatcher 是 progress.py 的 caller；不直接 mutation state |
| `doc-guardian` | dispatcher 不调 validate.py（doc 校验在 stage skill 内）；只在 §2.4 提示 S3 必备 artifacts |
| `bug-triage` | dispatcher 路由 bug 类输入到此 skill；不自行分类根因 |
| `workflow-evolution` | dispatcher 在 `workflow_incident_active==true` 时路由到此；不自行分析 incident |
| stage skill (`prd-write` 等) | dispatcher 在 init/release-start 后路由到入口 stage skill；不直接调 stage skill 内部子命令 |

---

**End of Decision Tree Reference**
