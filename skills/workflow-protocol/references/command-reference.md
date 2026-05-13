# progress.py Command Reference

**物理路径**：`skills/workflow-protocol/scripts/progress.py`

**Path Normalization Note**（v0.6 F13）：本 reference 内代码块为简洁起见使用 `progress.py` 简写，**实际调用必须用完整路径** `skills/workflow-protocol/scripts/progress.py`。SKILL.md 主文档与 cross-skill prose 一律使用完整路径；本 reference 的代码块仅作 display-only 简写。

本 reference 提供 12 个子命令的精确前置条件 + 字段 mutation。Task 6 实现脚本时严格按此规范。

---

## 1. `init`

**用途**：新项目首次初始化 progress.md 和 progress-history.md。

**前置条件**：

- 项目根**不存在** `progress.md`
- 提供 `--project <name>`、`--scenario <S1|S3>`、`--release <x.y>` 参数

**Mutation**：

```yaml
# 创建 progress.md，写入初始 frontmatter：
project_name: <name>
workflow_version: v0.6
project_state: active
release: "<x.y>"
release_state: active
release_close_reason: null
previous_releases: []
scenario: <S1|S3>
scenario_subtype: null
current_stage: prd-inception
sub_state: write
review_iteration: 0
artifacts:                   # 初始化空路径（待各 stage 填）
  prd: docs/prd/prd.md
  architecture: docs/architecture/architecture.md
  srs: docs/release<x.y>/srs/srs.md
  acceptance_plan: docs/release<x.y>/srs/acceptance_plan.md
  integration_plan: null
  architecture_delta: null
bug_flow:
  active: false
  bug_report_path: null
  root_cause: null
workflow_incident_active: false
incident_report_path: null
unresolved_bugs: []
created: <now>
updated: <now>
```

同时创建空 `progress-history.md`，append 第一条 entry：`init — project created — scenario=<S1|S3>, release=<x.y>`。

---

## 2. `update`（v0.6 F8: --field 替换为 --event 白名单）

**用途**：状态机事件触发的入口。仅修改 sub_state / review_iteration / development_state.task_states 等"事件驱动字段"；受保护字段必须经 dedicated subcommand。

**调用模式**：

```bash
progress.py update --event <event-name> [--params ...]
progress.py update --advance                    # 推进到下一 stage（按状态机）
progress.py update --task <Tn> --status <new>   # Stage 4 task state 改动
```

**`--event` 白名单**（仅允许以下事件名）：

| Event | 触发时机 | 影响字段 |
|-------|---------|---------|
| `write-complete` | `*-write` 完成 draft + self-validate pass | `sub_state: write → in-review` |
| `review-issues` | `*-review` 输出 issues-found | `sub_state: in-review → revising`，`review_iteration += 1` |
| `review-passed` | `*-review` 输出 review-passed | `sub_state: → review-passed`，`review_iteration → 0` |
| `human-confirmed` | 人 gate 通过 | `sub_state: review-passed → approved`（仅 PRD/SRS/Architecture/CR）|

**前置条件**：

- progress.md 存在
- `project_state == active`（aborted/reconstructing 终态拒绝）
- `<event-name>` 在白名单内
- 当前 (current_stage, sub_state) 允许目标 event（按状态机转移表）

**禁止通过 `update` 修改的受保护字段**（必须经 dedicated subcommand）：

- `release_state` / `release` / `release_close_reason` / `previous_releases` → `release-close` / `release-start`
- `current_stage` → `release-start` / `bug-start` / `bug-rework` / `bug-close` / `incident-start` / `incident-resolve` / `--advance`
- `bug_flow.*` → `bug-start` / `bug-rework` / `bug-close` / `incident-start` / `incident-resolve`
- `workflow_incident_active` / `incident_report_path` → `incident-start` / `incident-resolve`
- `project_state` → `incident-resolve`
- `unresolved_bugs` → `bug-intake` / `release-start`

**通用流程**（所有 update 共用）：

```
1. 计算 new_progress + new_history_entry
2. flock on .progress.lock
3. 备份 progress.md + progress-history.md
4. 校验状态机合法性（见状态转移表）
5. append progress-history.md
6. overwrite progress.md
7. 一致性校验
8. 失败 → rollback；成功 → 解锁退出
```

### 2.1 主要 sub_state 转换（review 循环）

| from | trigger | to | review_iteration |
|------|---------|-----|------------------|
| `write` | write 完成 + self-validate pass | `in-review` | 不变 |
| `in-review` | review 输出 `issues-found` | `revising` | +1 |
| `in-review` | review 输出 `review-passed` | `review-passed` | 归零 |
| `revising` | revise 完成 | `in-review` | 不变 |
| `review-passed` | 非 gated stage 自动 → 触发 advance | next stage write | 归零 |
| `review-passed` | gated stage（PRD/SRS/Arch）等人确认 | `approved` | 归零 |
| `approved` | gated stage human-confirmed | next stage write | 归零 |
| 任意 | `review_iteration > 7` | reject + 报错升级人 | — |

### 2.2 `--advance` 子选项（v0.6 F4 修正 artifact 来源）

`--advance` 显式推进到下一 stage。前置：当前 stage 满足 P6 矩阵 A/B/C/D/E 全部维度。

合法 stage 序列：
```
prd-inception → srs-specification → architecture-design → development → testing → delivery → project-retrospective
```

**Artifact 必备清单事实源**：`skills/doc-guardian/references/required-artifacts.md`（scenario-aware YAML map）。`progress.md artifacts:` 仅存项目级 + release 级 mutable 入口路径；其他 stage artifact 路径由 doc-guardian 按 `(scenario, scenario_subtype, current_stage, release, task_id?, srs.is_multi_module?, srs.architecture_change?)` 推导。

`--advance` 流程：

1. 调用 doc-guardian 推导当前 stage 的 required artifacts list（按 required-artifacts.md 解析 + 条件求值）
2. 对每个 artifact path 调 `skills/doc-guardian/scripts/validate.py file <path>`，全部 exit 0（B 维度）+ 文件存在（A 维度）
3. 检查对应 `*-review` 最近一轮 `review-passed`（C 维度，从 progress-history.md 读最新 review event）
4. 若 gated stage（PRD/SRS/Architecture）：D 维度的实际入口是 `apply_update_advance` 校验 `progress.md.sub_state == "approved"`（即 `human-confirmed` 事件已被 apply 过、history 已记录该条目）；P6 B 维度的 `validate.py file` 已对 doc frontmatter 做 schema/format 复检，所以 advance 不在 D 维度独立重读 doc frontmatter `status` 字段。如果某 *-write skill 想要"sub_state=approved ↔ doc.status=approved"硬绑定，应在自评步骤里完成，advance 不重做这一比对。
5. 若 Stage 4/5/6：检查 verification artifact `verification_status: pass`（E 维度）
   - Stage 4：每个 task 的 `verification_result.md`
   - Stage 5：`test-report` 整体
   - Stage 6：`installation_result`
6. 全部通过 → `current_stage` 推进到下一 stage；`sub_state: write`；`review_iteration: 0`

任一维度失败 → reject + 报错列出失败维度（含具体哪个 artifact）。

**Bug Flow 与 advance 的非对称约束**（v0.6 round 2 / Phase 6.4 实装一致）：

- **development → testing 允许 `bug_flow.active == true`**：dev root_cause Bug Flow 完成 task 修复后，调 `update --advance` 推回 testing 进行 retest 是合法路径（apply_update_advance 在 development 分支不 check bug_flow），否则 dev Bug Flow 无法返回 testing。
- **testing → delivery 禁止 `bug_flow.active == true`**：apply_update_advance 在 testing 分支显式 forbid，必须先 `bug-close`（retest pass）或 `bug-rework`（retest fail/partial）后再 advance。
- 其它非 gated stage 与上述同：apply_update_advance 仅对 testing 一处 forbid bug_flow.active；development 是这条非对称的另一端。

**注**：`update --event` 单纯做状态机事件转换，**不**自动跑 validate.py（v0.6 F14 修正：删除 v0.5 中"默认调 validate"的说法）。validate 只在 `--advance` 时统一执行，或由 `*-write` skill 自评步骤显式调用。

---

## 3. `query`

**用途**：只读读取当前 state，不需锁，可并发。

**调用**：

```bash
progress.py query                       # 输出全部 state（YAML）
progress.py query --field <name>        # 输出指定字段
progress.py query --json                # JSON 输出
```

**Mutation**：无（只读）

---

## 4. `recover`（v0.6 round 3 M3 加 terminal 语义）

**用途**：异常恢复——progress.md 损坏 / 手工误编辑 / 一致性校验失败时使用。从 progress-history.md 重放重建 progress.md。

**前置条件**：

- progress-history.md 存在且 entry 完整（每条符合严格模板）
- 用户确认确实需要 recover（带 `--confirm` 标志）

**Terminal state 语义（v0.6 round 3 M3）**：

- `recover` 是 terminal state（`project_state ∈ {aborted, reconstructing}`）下**唯一允许的 repair mutation**
- recover 重放 history 必须保持 history 中的最终 `project_state`：如果 history 显示 project 已 abort/reconstruct，重建后的 progress.md 必须保持终态
- **禁止**用 recover 把 aborted/reconstructing project "复活"为 active（即使 history 显示原本曾是 active，replay 必须按 history 全程，不可截断到中间状态）

**Mutation**：

```yaml
# 从 history 第一条 entry 开始，按时间顺序 replay
# 每应用一条 entry，跑同一状态机 validator（与 update 用的同一份）
# 重建 progress.md（覆盖原文件）
# 不改 progress-history.md
# 重建后的 project_state / release_state / current_stage / sub_state 与 history 最末状态一致
```

**Replay validator 规则（v0.6 round 4 M3 新加）**：

recover 在 replay history 时必须按状态机校验每条 entry 的合法性。特别处理 terminal event：

```
algorithm replay(history_entries):
    state = empty_progress
    seen_terminal = false
    for entry in history_entries (按时间顺序):
        if seen_terminal:
            # terminal 后任何 mutating entry 都视为 history corruption
            if entry is mutating (非 query/recover 类):
                exit 1 with stderr: "History corruption detected at <timestamp>: 
                                     mutating entry after terminal event"
            else:
                continue   # 允许 query/recover 类 entry（无 state 变化）
        else:
            # 应用状态机校验
            if not state_machine.validate(state, entry):
                exit 1 with stderr: "Invalid state transition at <timestamp>: <entry>"
            state = state_machine.apply(state, entry)
            if entry is incident-resolve --action abort/reconstruct:
                seen_terminal = true
    return state
```

**关键约束**：

- 一旦 replay 遇到 `incident-resolve --action abort` 或 `--action reconstruct`，后续任何 mutating entry 都触发 fatal error（exit 1）
- **禁止** silently truncate 到 terminal 然后继续（避免静默掩盖 history corruption）
- **禁止** replay terminal 之后的非法 mutating entry（避免把 aborted/reconstructing project 错误"复活"）
- 如未来需要 force truncate 能力，需走 design review 单独添加 `recover --force-truncate-after-terminal` 子选项；当前版本不支持

**注意**：recover 只能恢复 progress.md 到 history 反映的 state。若 history 也损坏（如格式错、状态机校验全 fail），recover 拒绝执行，需人工介入。

---

## 5. `release-close`

**用途**：当前 release Stage 7 完成时，标记 release closed，准备启动下个 release。

**前置条件**：

- `release_state == active`
- `current_stage == project-retrospective`
- `sub_state == review-passed`
- Stage 7 retrospective 文档 review-passed

**Mutation**：

```yaml
release_state: active → closed
release_close_reason: null → "stage-7-completed"
previous_releases: [...] → [..., <current release>]
# 其他字段保留不变（current_stage 留在 project-retrospective）
```

**Append history**：

```markdown
## <now> — release-close — release <x.y> closed
- agent: <id>
- result: previous_releases now [..., "<x.y>"]
- next: release-start or bug-intake
```

---

## 6. `release-start --version <x.y> --scenario <S2-1|S2-2|S2-3>`

**用途**：启动新 active release。

**前置条件**：

- `release_state == closed`（首次 init 用 `init` 不用此命令）
- `<x.y>` 解析合法（regex `^(\d+)\.(\d+)$`）
- `<x.y>` 严格大于所有 `previous_releases` 版本（按 (major, minor) 数字对比较）
- `<scenario>` ∈ {S2-1, S2-2, S2-3}（S2-4 必须转 S3，不走此命令）

**Mutation**（v0.6 F10 修正 BUG consume 语义）：

```yaml
release: <previous> → <x.y>
release_state: closed → active
release_close_reason: <previous_reason> → null
scenario: → S2
scenario_subtype: → <S2-x>
current_stage: → 按 scenario:
  S2-1 → prd-inception
  S2-2 → srs-specification (Full Mode for new sections)
  S2-3 → srs-specification (Change Mode)
sub_state: → write
review_iteration: → 0
artifacts.srs: → docs/release<x.y>/srs/srs.md
artifacts.acceptance_plan: → docs/release<x.y>/srs/acceptance_plan.md
artifacts.integration_plan: → null（多模块时由 srs-write 填）
artifacts.architecture_delta: → null（如有架构变更由 architecture-write 填）
artifacts.prd: 不变（项目级）
artifacts.architecture: 不变（项目级）
unresolved_bugs: [...] → []  # 全部消费

# 同时为每个原 unresolved_bug 在对应 BUG-NNN.md frontmatter 原子设置（v0.6 F10）：
#   target_release: "<x.y>"          # 标明 bug fix 目标 release
#   consumed_in_release: "<x.y>"     # 标明被本 release 消费
# 两个字段同步设置；validate.py 类 5 校验 unique consumption（同一 BUG 不能被多个 release 消费）
```

**srs-write skill 下游处理**：在 SRS write 阶段，扫描 `docs/bug/BUG-*.md` 中 `consumed_in_release == <current release>` 的 bug 列表，把修复需求合并到新 SRS（生成 acceptance criteria for fixes 等）。

**Append history**：

```markdown
## <now> — release-start — new release <x.y> started
- agent: <id>
- result: scenario=<S2-x>, consumed N unresolved bugs
- next: <stage>-write Full Mode
```

由 srs-write skill 在 SRS write 阶段读取 `consumed_in_release == <current release>` 的 bug 列表，把修复需求合并到新 SRS。

---

## 7. `bug-intake --bug <bug-report-path>`（v0.6 F10 加 duplicate guard）

**用途**：post-close 期间记录 bug，加入 `unresolved_bugs` 等下次 S2 消费。

**前置条件**：

- `release_state == closed`（active 期间应走 `bug-start` 流程）
- `<bug-report-path>` 文件存在且通过 doc-guardian validate
- 对应 BUG-NNN.md frontmatter：
  - `target_release: null`
  - `consumed_in_release: null`
- BUG-NNN.md 路径**未在** `progress.md unresolved_bugs` 列表中（防止 duplicate intake）

**Mutation**：

```yaml
unresolved_bugs: [...] → [..., <bug-report-path>]
```

**Append history**：

```markdown
## <now> — bug-intake — BUG-NNN registered (post-close)
- agent: <id>
- result: unresolved_bugs count = <new count>
- next: wait for next release-start
```

---

## 8. `bug-start --bug <bug-report-path> --root-cause <enum>`（v0.5 F1）

**用途**：active Bug Flow 入口。bug-triage active mode 在判定 root_cause 后调用。

**前置条件**：

- `bug_flow.active == false`
- `release_state == active`
- `current_stage == testing` AND `sub_state == review-passed`（即 testing 刚完成发现 bug）
- `<bug-report-path>` 文件存在
- BUG-NNN.md frontmatter `root_cause == <root-cause>`（命令参数与 doc 事实一致）
- `<root-cause>` ∈ {srs, architecture, development}（prd-exception 走 `incident-start`）

**Mutation**：

```yaml
bug_flow.active: false → true
bug_flow.bug_report_path: null → <bug-report-path>
bug_flow.root_cause: null → <root-cause>
current_stage: testing → <root-cause stage>
  # srs → srs-specification
  # architecture → architecture-design
  # development → development（具体 task 由 BUG body `## Triage Analysis` 的 `Affected Task(s)` 标注）
sub_state: review-passed → write    # Change Mode 重走 write 循环
review_iteration: <N> → 0
```

**Development auto-rollback（Gap-4 / Task 6）**：

当 `<root-cause> == development` 时，`bug-start` 在进入 Development Change Mode 的同一原子 transaction 内解析 BUG body 的 `## Triage Analysis` 章节：

- 从 `**Affected Task(s)**: ...` 读取 `T<n>` 列表；当前 schema 不把 task IDs 放 frontmatter。
- 如果值为 `unable to localize` 或该字段缺失，命令不得猜测具体 task；应拒绝或进入 development planning route，并在 history 中要求 `development-planning-write` replan/route。
- 对每个 affected task，仅在分类明确时执行以下回退：
  - `verified -> test-revising`：fix 明确为 test-only / test-first / regression-test 缺失。
  - `verified -> code-revising`：fix 明确需要 source-code change。
  - `code-review-passed -> code-revising`：source fix needed before verification。
- 分类不明确时保持 task state 不变，并在 history 中写明需 planning route；不得把 `verified` task 手工改回旧状态。

**Append history**：

```markdown
## <now> — bug-start — Bug Flow entered (root_cause=<enum>)
- agent: <id>
- result: current_stage → <new stage> Change Mode; development rollback=<affected task summary if any>
- next: <stage>-write Change Mode
```

---

## 9. `bug-rework --bug <bug-report-path>`（Task 6 Gap-5）

**用途**：active Bug Flow 已经回到 Stage 5 Testing 重测，但 retest 仍 fail/partial 时，回到同一个 root-cause stage 继续 Change Mode。此命令专用于 retest fail/partial；不得 overload `bug-start`。

**前置条件**：

- `bug_flow.active == true`
- `current_stage == testing`
- `sub_state == review-passed`
- 最新 `docs/release<release>/testing/report.md` frontmatter `verification_status ∈ {fail, partial}`
- `<bug-report-path> == bug_flow.bug_report_path`
- `<bug-report-path>` 文件存在且 BUG frontmatter `root_cause == bug_flow.root_cause`
- `bug_flow.root_cause ∈ {srs, architecture, development}`

**Mutation**：

```yaml
bug_flow.active: true → true
bug_flow.bug_report_path: <path> → <same path>
bug_flow.root_cause: <enum> → <same enum>
current_stage: testing → <root_cause stage>
  # srs → srs-specification
  # architecture → architecture-design
  # development → development
sub_state: review-passed → write
review_iteration: <N> → 0
```

**Development auto-rollback**：

若 `bug_flow.root_cause == development`，复用 `bug-start` 的 Gap-4 逻辑：解析 BUG body `Affected Task(s)`，按当前 task state + 明确分类回退到 `test-revising` / `code-revising`。如果 affected task 缺失或分类不明确，要求 `development-planning-write` replan/route；不得猜测。

**Append history**（Phase 6.2 canonical-token contract，与 bug-start 镜像；replay 通过 `bug=` / `root_cause=` / 可选 `rollback=` 三个 token 反解状态机转换）：

```markdown
## <now> — bug-rework — bug=<bug-report-path> root_cause=<srs|architecture|development> Bug Flow rerouted [rollback=Tn:old->new;Tm:old->new]
- agent: <id>
- result: current_stage=<root_cause stage>[ (Tn: <reason>; Tm: <reason>)] | route=development-planning-write (no auto-rollback applied)
- next: <stage>-write Change Mode | development-planning-write replan/route
```

说明：

- summary 必含 `bug=` 与 `root_cause=`（缺任一 replay reject）；含 dev rollback 时再加 `rollback=Tn:old->new;...`（分号分隔，无空格）；字面词 `Bug Flow rerouted` 用于与 `bug-start` 的 `Bug Flow entered` / `bug-close` 的 `Bug Flow exited` 区分便于 grep。
- result 在含 rollback 时罗列 `(Tn: <reason>;...)`；dev root cause + 空 rollback 时改写 `route=development-planning-write (no auto-rollback applied)` 持久化 planning route 要求；其它 root cause 单写 `current_stage=<stage>`。
- next 在 dev 空 rollback 时为 `development-planning-write replan/route`；其它情形为 `<stage>-write Change Mode`。
- **test-report 路径不进 history**：retest fail/partial 校验是 forward CLI 责任（读 `docs/release<x.y>/testing/report.md` 校 `verification_status`），replay 不重读测试报告，与 `update --task` / `bug-start` / `bug-close` 一致。

**Rejected alternatives**：

- 不得为同一个 active issue 再次调用 `bug-start`。
- 不得为 active retest fail/partial 创建第二个 BUG。
- 不得在 retest fail/partial 时调用 `bug-close`。
- 不得手工编辑 `current_stage` / `bug_flow.*`。

---

## 10. `bug-close`（v0.5 F1）

**用途**：active Bug Flow 出口。testing-write 在 retest pass 后调用。

**前置条件**：

- `bug_flow.active == true`
- `current_stage == testing`
- testing 重测通过（最新 test-report `verification_status: pass`）

**Mutation**：

```yaml
bug_flow.active: true → false
bug_flow.bug_report_path: <path> → null
bug_flow.root_cause: <enum> → null
current_stage: testing → testing  # 保持，进入正常 Stage 5 done 判定
# sub_state 由 update --advance 后续转换处理
```

**Append history**：

```markdown
## <now> — bug-close — Bug Flow exited (retest passed)
- agent: <id>
- result: bug_flow.active → false
- next: progress.py update --advance to delivery
```

bug-close 后 caller 通常立即调 `update --advance` 推进 Stage 6。

### 10.1 完整 Bug Flow 时序（srs / architecture / development root_cause）

`bug-start` 与 `bug-close` 在 spec 上是 Bug Flow 的入口/出口，但中间的 stage 推进、retest、review 步骤散落在 §2 / §8 / §10。完整 happy-path 时序（retest pass）：

1. **bug-start** （from testing/review-passed）：`current_stage` 切到 `<root-cause stage>`、`sub_state=write`；dev root_cause 触发 Gap-4 task 回滚（`verified → test-revising` / `verified → code-revising` / `code-review-passed → code-revising`）。
2. **修复**：在 `<root-cause stage>` Change Mode 完成 write+review 循环；dev 还要把回滚的 task 重新走完 task state machine 到 `verified`。
3. **`update --advance`**：从 `<root-cause stage>` 推回 `testing/write`。dev 的非对称（见 §2.2 "Bug Flow 与 advance 的非对称约束"）允许 `bug_flow.active==true` 通过此 advance；srs / architecture 同理。
4. **重写 testing artifacts**：刷新 `testing/report.md` 至 `verification_status: pass`（`preparation.md` / `procedure.md` 通常无需重写）。
5. **`update --event write-complete` → `update --event review-passed`**：把 `testing` 走到 `review-passed`。
6. **bug-close**：要求 `current_stage==testing` + 最新 test-report `verification_status==pass`；清 `bug_flow`；保持 `sub_state=review-passed`。
7. **`update --advance`**：testing → delivery；此时 `bug_flow.active==false`，satisfies §2.2 testing → delivery 的非对称约束。

retest fail/partial 分支：第 5 步后**不**调 bug-close，改调 `bug-rework --bug ...`（§9）回到同一 root-cause stage 再走 §10.1 第 2-7 步；不得为同一 active issue 再次 `bug-start`。

---

## 11. `incident-start --bug <bug-path> --report <incident-report-path>`（v0.6 F2 修正）

**用途**：bug-triage 判定 `root_cause: prd-exception` 时调用，进入 workflow-incident-analysis 特殊 stage。

**v0.6 F2 关键变化**：不再要求 `bug_flow.active == true` 作为前置（之前不可达）。`incident-start` 自己一次性设置 bug_flow + incident state。

**前置条件**：

- `bug_flow.active == false`（如果已有 active bug flow，必须先 bug-close）
- `<bug-path>` 文件存在且 `skills/doc-guardian/scripts/validate.py file <bug-path>` exit 0
- `<bug-path>` BUG-NNN.md frontmatter `root_cause == prd-exception`
- `<incident-report-path>` 文件存在且为合法 `workflow-incident` type 的 skeleton（最少 frontmatter 完整）
- **`skills/doc-guardian/scripts/validate.py file <incident-report-path>` exit 0**（v0.6 round 3 M6：double-safety 二次 validate；caller 已 promote/validate 一次，此处再校验一次以保证 incident state 的输入合法）
- `<incident-path>` INCIDENT-NNN.md frontmatter `triggered_by_bug` ID 必须等于 `<bug-path>` 的 `bug_id`

任一前置不满足 → progress.py 拒绝并 exit 非 0；caller（bug-triage）必须修后重试。

**Mutation**：

```yaml
bug_flow.active: false → true                # incident-start 同时启动 bug_flow
bug_flow.bug_report_path: null → <bug-path>
bug_flow.root_cause: null → prd-exception
workflow_incident_active: false → true
incident_report_path: null → <incident-report-path>
current_stage: <previous, usually testing> → workflow-incident-analysis
# sub_state 保留（incident 期间不变）
```

**Append history**（Phase 6.3 canonical-token contract；replay 通过 `bug=` / `incident=` 两个 token 反解状态机转换；`root_cause=prd-exception` 是 forward CLI canonical-form token，replay 当前**不消费**此 token——既不校验是否存在也不校验值，因为 `apply_incident_start` mutation 总是写字面 `prd-exception` 到 `bug_flow.root_cause`。如未来需 hardening 让 replay 也强制 `root_cause=prd-exception` 作为 token 完整性检查，可在 `_apply_incident_start_handler` 加显式相等校验+regression test）：

```markdown
## <now> — incident-start — bug=<bug-report-path> incident=<incident-report-path> root_cause=prd-exception PRD exception triggered
- agent: <id>
- result: current_stage=workflow-incident-analysis; bug_flow.active=true root_cause=prd-exception
- next: workflow-evolution fills INCIDENT body
```

说明：

- summary 必含 `bug=` 与 `incident=`（缺任一 replay reject）；字面词 `PRD exception triggered` 用于与其它 incident-* 事件区分便于 grep。
- result 用 `current_stage=workflow-incident-analysis` + `bug_flow.active=true root_cause=prd-exception` 持久化关键状态供操作者 grep；replay 通过 state-machine mutation 重建，不依赖 result prose。
- next 默认指 `workflow-evolution fills INCIDENT body`（区分于 frontmatter 维护，body 是 incident analysis 真正写作目标）。
- **BUG / INCIDENT 文件本身不进 history**：path 是 forward CLI 的 ``validate.py file`` double-safety 校验目标，replay 不重读这些文件。

**INCIDENT-NNN.md 创建责任**：bug-triage 创建 skeleton（仅 frontmatter）；workflow-evolution 在 incident state 下填充 body（分析 / 改进建议 / resolution_action 字段）。

---

## 12. `incident-resolve --action <continue|abort|reconstruct>`

**用途**：用户决策后退出 incident state。

**前置条件**：

- `workflow_incident_active == true`
- 已存在 INCIDENT-NNN.md 且其 frontmatter `resolution_action ∈ {continue, abort, reconstruct}`（与命令参数 `--action` 一致；workflow-evolution 已标注）
- INCIDENT.frontmatter `status == review-passed`（workflow-evolution finalization 已完成）
- **`skills/doc-guardian/scripts/validate.py file <incident-report-path>` exit 0**（v0.6 round 3 M6：double-safety 二次 validate；caller 已 promote/validate 一次，此处再校验一次以保证 finalization 完整性 + Pending Changes 已空 + frontmatter 全合法；防 caller silent skip Step 6.f/g）

任一前置不满足 → progress.py 拒绝并 exit 非 0；caller（workflow-evolution）必须按 §3.1 Step 6.e-g 重做 finalization 后重试。

### 12.1 `--action continue`（v0.6 round 2 H3 简化：单一行为，无子参数）

适用：用户决定调整 workflow 后继续当前 release。

**v0.6 round 2 简化**：放弃 `--bug-flow keep|clear` 双行为；continue **只允许一种 mutation**——清空 bug_flow，回到 testing review-passed 状态重测。如果用户判定原 bug 仍需修复，需创建**新的 BUG report** 触发 bug-triage active mode（不复用原 BUG，避免 reclassification 状态污染）。

理由：避免引入 `workflow-incident.resolution_detail` / `bug-report.resolved_by_workflow_change` / `bug-report.final_status` 等额外 schema 字段。简单一致优于灵活。

**Mutation**：

```yaml
workflow_incident_active: true → false
incident_report_path: <path> → null
current_stage: workflow-incident-analysis → testing
sub_state: → review-passed              # 回到 testing review-passed 重测
review_iteration: <N> → 0
bug_flow.active: true → false
bug_flow.bug_report_path: <path> → null
bug_flow.root_cause: prd-exception → null
# 对应 BUG-NNN.md frontmatter 不变（保留 root_cause: prd-exception 作历史记录）
# INCIDENT-NNN.md 由 workflow-evolution 写入 resolution_action: continue
```

后续如果原 bug 仍需修复：用户/AI 创建新 `BUG-MMM.md`（new ID）触发新一轮 bug-triage active mode；新 BUG 的 root_cause 由 bug-triage 重新判定（不必是 prd-exception）。

### 12.2 `--action abort`（v0.6 F11 加 cleanup）

适用：用户判定 project 不可继续，终止开发。

**Mutation**：

```yaml
workflow_incident_active: true → false
incident_report_path: <path> → null
project_state: active → aborted
release_state: active → closed
release_close_reason: null → "incident-abort"
current_stage: workflow-incident-analysis → null   # 终态
sub_state: <any> → null                            # v0.6 F11：允许 null
review_iteration: <N> → 0                          # v0.6 F11
bug_flow.active: <any> → false                     # v0.6 F11
bug_flow.bug_report_path: <any> → null             # v0.6 F11
bug_flow.root_cause: <any> → null                  # v0.6 F11
```

abort 后 progress.md 进入终态，`update` 类命令全部拒绝。

### 12.3 `--action reconstruct`（v0.6 F11 加 cleanup）

适用：用户判定从外部源系统重构（即转 S3 新 project）。

**Mutation**：

```yaml
workflow_incident_active: true → false
incident_report_path: <path> → null
project_state: active → reconstructing
release_state: active → closed
release_close_reason: null → "incident-reconstruct"
current_stage: workflow-incident-analysis → null   # 终态
sub_state: <any> → null                            # v0.6 F11
review_iteration: <N> → 0                          # v0.6 F11
bug_flow.active: <any> → false                     # v0.6 F11
bug_flow.bug_report_path: <any> → null             # v0.6 F11
bug_flow.root_cause: <any> → null                  # v0.6 F11
```

reconstruct 后该 project 进入终态。用户启动新 S3 project（独立目录、独立 progress.md），可在新 PRD 引用本 project 作为 source system。

**Append history**（3 个 action 共用；Phase 6.3 canonical-token contract）：

```markdown
## <now> — incident-resolve — action=<continue|abort|reconstruct> incident=<incident-report-path> Incident resolved
- agent: <id>
- result: <see per-action prose below>
- next: <see per-action prose below>
```

说明：

- summary 必含 `action=` 与 `incident=`（缺任一 replay reject）；字面词 `Incident resolved` 与 `incident-start` 的 `PRD exception triggered` 配对便于 grep。
- replay dispatch loop 解析 `action=` token 决定是否将该 entry 标为终态（`abort` / `reconstruct` 终态；`continue` 非终态）。
- result / next 由 action 驱动：
  - `continue`：result `current_stage=testing sub_state=review-passed; bug_flow cleared (BUG report root_cause=prd-exception preserved on disk)`；next `testing-write retest (or new BUG via bug-triage)`。
  - `abort`：result `project_state=aborted release_state=closed close_reason=incident-abort; current_stage cleared (terminal)`；next `no further progress.py mutation accepted`。
  - `reconstruct`：result `project_state=reconstructing release_state=closed close_reason=incident-reconstruct; current_stage cleared (terminal)`；next `no further progress.py mutation accepted; start fresh project / release in a new directory`。
- replay 不重读 INCIDENT 文件；`resolution_action` / `status==review-passed` 是 forward CLI 的 ``validate.py file`` double-safety 校验目标。

---

## 状态机转移合法性表（v0.6 含 --event 白名单）

`update --event <name>` 校验的核心转移规则。任何不在此表的转换 → reject。

### 通用 sub_state 转换（适用所有 gated 与 non-gated stage 的 sub_state）

| From | Event | To | review_iteration |
|------|-------|------|------|
| `sub_state=write` | `write-complete` | `sub_state=in-review` | 不变 |
| `sub_state=in-review` | `review-issues` | `sub_state=revising` | +1（若 +1 后 > 7 → reject 升级人）|
| `sub_state=in-review` | `review-passed` | `sub_state=review-passed` | 归零 |
| `sub_state=revising` | `write-complete` | `sub_state=in-review` | 不变（Change Mode 完成）|
| `sub_state=review-passed`（gated stage）| `human-confirmed` | `sub_state=approved` | 归零 |
| `sub_state=review-passed`（非 gated stage）| `--advance` | next stage `sub_state=write` | 归零 |
| `sub_state=approved`（gated stage）| `--advance` | next stage `sub_state=write` | 归零 |

### Stage 4 task state 转换（通过 `update --task <Tn> --status <new>`）

| From | To | Required artifact / event |
|------|------|---------------------------|
| 任意（首次设值）| `planning-done` | `breakdown.md` declares `Tn` + `detailed_design.md` exists + frontmatter `task_id == Tn` + doc-guardian + review-passed |
| `planning-done` | `planning-done` | idempotent retry：重复注册同一 task 不 fatal；可 no-op 或 append idempotent history |
| `planning-done` | `test-writing` | development-test-write 开始 |
| `test-writing` | `test-review` | development-test-write 完成 + 写 test_review_report skeleton |
| `test-review` | `test-revising` | development-test-review 输出 issues-found |
| `test-review` | `test-done` | test_review_report `review_status: pass` 且 `blocking_findings_count: 0` |
| `test-revising` | `test-review` | test 修订完成（test-write Change Mode）|
| `test-done` | `code-writing` | development-code-write 开始 |
| `code-writing` | `code-review` | development-code-write 完成 + 写 code_review_report skeleton |
| `code-review` | `code-revising` | development-code-review 输出 issues-found |
| `code-review` | `code-review-passed` | code_review_report `review_status: pass` 且 `blocking_findings_count: 0` |
| `code-revising` | `code-review` | code 修订完成 |
| `code-review-passed` | `verifying` | development-code-write 启动测试执行 |
| `verifying` | `verified` | verification_result `verification_status: pass` |
| `verifying` | `code-revising` | Gap-3：verification_result `verification_status ∈ {fail, partial}`；verification retry，不走 bug-triage |
| `verified` | `test-revising` | Gap-4 protected rollback：active Bug Flow `root_cause==development`，BUG body `Affected Task(s)` includes `Tn`，fix 明确需要 test change；owner=`bug-start` or `bug-rework` |
| `verified` | `code-revising` | Gap-4 protected rollback：active Bug Flow `root_cause==development`，BUG body `Affected Task(s)` includes `Tn`，fix 明确需要 source change；owner=`bug-start` or `bug-rework` |
| `code-review-passed` | `code-revising` | Gap-4 protected rollback：active Bug Flow `root_cause==development`，BUG body `Affected Task(s)` includes `Tn`，source fix needed before verification；owner=`bug-start` or `bug-rework` |

### 受保护字段转换（必须经 dedicated subcommand）

| From state | To state | 命令 |
|------------|----------|------|
| `release_state=active, current_stage=project-retrospective, sub_state=review-passed` | `release_state=closed` | `release-close` |
| `release_state=closed` | `release_state=active, new release` | `release-start` |
| `release_state=active, current_stage=testing, sub_state=review-passed` | `bug_flow.active=true, current_stage=<root_cause stage>` | `bug-start`（root_cause ∈ {srs, architecture, development}）|
| `release_state=closed`（任意 sub_state）| `unresolved_bugs` 增加 | `bug-intake` |
| `bug_flow.active=true, current_stage=testing, sub_state=review-passed, latest test-report fail/partial` | `bug_flow.active=true, current_stage=<same root_cause stage>` | `bug-rework`（root_cause ∈ {srs, architecture, development}）|
| `current_stage=testing, bug_flow.active=true, retest pass` | `bug_flow.active=false, current_stage=testing` | `bug-close` |
| `project_state=active`, `bug_flow.active=false`, `workflow_incident_active=false`, BUG `root_cause=prd-exception`（**Phase 6.3 起：不 gate `current_stage`**——PRD 异常 escalation 可在 Stage 5、6、7 任一 stage 触发；前序 phase 描述的 testing-only 已废止）| `bug_flow.active=true, workflow_incident_active=true, current_stage=workflow-incident-analysis` | `incident-start` |
| `current_stage=workflow-incident-analysis` | terminal（aborted/reconstructing）或 testing（continue）| `incident-resolve` |
| `project_state=aborted/reconstructing` | （任何）| reject all mutation 类命令 |
