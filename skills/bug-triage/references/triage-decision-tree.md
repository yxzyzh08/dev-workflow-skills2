# bug-triage Decision Tree

**配套**：`skills/bug-triage/SKILL.md`

本 reference 提供 bug-triage 的双模式入口决策树、Active / Post-Close 端到端流程、INCIDENT skeleton 模板、BUG / INCIDENT ID 计算规则、并发控制约束。根因分类详细 rubric 见 `root-cause-rubric.md`。

---

## 1. 双模式入口决策树

```
invoke bug-triage
  ↓
读 progress.py query
  ↓
分支：
  ├ project_state ∈ {aborted, reconstructing}
  │     → reject + 提示终态
  │
  ├ workflow_incident_active == true
  │     → reject + 提示用 workflow-evolution（incident-resolve 后再 triage）
  │
  ├ release_state == active
  │     ├ current_stage != testing OR sub_state != review-passed
  │     │     → reject early（v0.6 round 2 batch2-F2 / round 3 M1）；
  │     │       与 progress.py bug-start 前置一致；不读 BUG / 不写 frontmatter / 不调 progress.py；
  │     │       提示用户：(a) 等 testing 阶段；(b) 把现象记入当前 stage doc 的 known-issue 段
  │     ├ current_stage == testing AND sub_state == review-passed
  │     │     → 走 Active Mode（§2）
  │     │     ├ bug_flow.active == false → 正常 active triage
  │     │     ├ bug_flow.active == true AND BUG.root_cause == null → 重试 active triage（上次失败）
  │     │     └ bug_flow.active == true AND BUG.root_cause != null → reject（已分流过；下游 stage Change Mode 进行中）
  │
  └ release_state == closed
        → 走 Post-Close Mode（§3）
        ├ bug_flow.active == false（应是；closed 期间不可能 true）→ 正常 post-close intake
        └ bug_flow.active == true → schema 异常；要求 progress.py recover
```

---

## 2. Active Mode 端到端流程

### 2.1 7 步流程

```python
def active_mode_triage(bug_path):
    # Step 0: Early gate (v0.6 round 2 batch2-F2 / round 3 M1)
    # 与 progress.py bug-start 前置完全一致；缺一项即 reject early。
    state = progress_query()
    if state.release_state != "active":
        return reject(reason="active mode 仅在 release_state==active 期间允许")
    if state.current_stage != "testing" or state.sub_state != "review-passed":
        return reject(
            reason=(
                f"progress.py bug-start 前置要求 current_stage==testing AND "
                f"sub_state==review-passed；当前 ({state.current_stage}, "
                f"{state.sub_state}) 不满足"
            ),
            recovery=(
                "(a) 等本 release 推进到 testing 阶段，testing-write 自动发现并 invoke bug-triage；"
                "(b) 把现象记入当前 stage doc 的 known-issue 段；不读/不写 BUG report"
            ),
        )

    # Step 1: 读 BUG report（仅在 Step 0 pass 后才允许）
    bug = read_yaml_frontmatter(bug_path) + read_body(bug_path)
    assert bug.frontmatter.type == "bug-report"
    assert bug.frontmatter.bug_id matches r"BUG-\d{3}"
    
    # Step 2: 读相关上下文 doc
    ctx = read_contextual_docs(
        srs="docs/release{release}/srs/srs.md",
        architecture="docs/architecture/architecture.md",
        architecture_delta="docs/release{release}/architecture_delta.md (if exists)",
        detailed_designs="docs/release{release}/development/tasks/T*/detailed_design.md",
        verification_results="docs/release{release}/development/tasks/T*/verification_result.md",
        prd="docs/prd/prd.md (仅在怀疑 prd-exception 时读)"
    )
    
    # Step 3: 应用 root-cause rubric 判定
    root_cause = classify(bug, ctx)  # 见 root-cause-rubric.md
    confidence = compute_confidence(bug, ctx, root_cause)
    
    if confidence == "low":
        # 与用户对话二次确认
        confirm = ask_user(
            f"我倾向判定 root_cause={root_cause}，但 confidence 不高。"
            f"Alternative: ...。确认吗？"
        )
        if not confirm:
            iterate_with_user(...)  # 重新分类
    
    if root_cause == "prd-exception":
        # 必须二次确认（高警惕性）
        confirm = ask_user(
            "判定为 prd-exception 会触发 incident analysis，可能 abort/reconstruct。确认吗？"
        )
        if not confirm:
            return iterate_with_user(...)
    
    # Step 4: 写 BUG report frontmatter root_cause + Triage Analysis 章节
    update_frontmatter(bug_path, root_cause=root_cause)
    add_triage_analysis_section(bug_path, root_cause, ctx, rationale)
    add_pending_changes_entry(bug_path,
        f"{now} [frontmatter+body]: triage 完成 root_cause={root_cause}")
    
    # Step 5: changelog promote
    run("skills/doc-guardian/scripts/changelog.py promote " + bug_path)
    
    # Step 6: validate.py 校验
    run("skills/doc-guardian/scripts/validate.py file " + bug_path)
    if exit_code != 0:
        return error("BUG report 校验失败，修复后重试")
    
    # Step 7: 分支调用 progress.py
    if root_cause in {"srs", "architecture", "development"}:
        run(
            "skills/workflow-protocol/scripts/progress.py bug-start "
            f"--bug {bug_path} --root-cause {root_cause}"
        )
    elif root_cause == "prd-exception":
        # Step 7a: 创建 INCIDENT skeleton（含 Pending Changes 首条 entry "skeleton 创建"）
        incident_path = create_incident_skeleton(
            triggered_by_bug=bug.frontmatter.bug_id,
            triggered_in_release=bug.frontmatter.found_in_release
        )
        # Step 7b: changelog promote（必做；INCIDENT 是增量类 doc，不 promote 则 validate 类 6 fail）
        run("skills/doc-guardian/scripts/changelog.py promote " + incident_path)
        # Step 7c: validate INCIDENT skeleton（必须 exit 0；progress.py incident-start 前置）
        run("skills/doc-guardian/scripts/validate.py file " + incident_path)
        # Step 7d: 调 incident-start
        run(
            "skills/workflow-protocol/scripts/progress.py incident-start "
            f"--bug {bug_path} --report {incident_path}"
        )
    
    return "active triage complete"
```

### 2.2 Step 4 — Triage Analysis 章节模板

bug-triage 在 BUG-NNN.md body 加（详细模板见 `root-cause-rubric.md` §6）：

```markdown
## Triage Analysis

**Root Cause**: <enum>
**Affected Doc/Module**:
  - SRS: <章节引用 if applicable>
  - Architecture: <组件名 if applicable>
  - Detailed Design: <task ID + 文件路径 if applicable>
  - Source Code: <文件路径 if applicable>
**Affected Task(s)**: <T1, T3 | "unable to localize" | N/A>
**Rationale**:
  <2-5 句自然语言>

**Confidence**: <high | medium | low>
**Alternative Hypothesis**: <如 confidence != high>

**Next Step**:
  - root_cause ∈ {srs, architecture, development}: progress.py bug-start
  - root_cause == prd-exception: 创建 INCIDENT skeleton + progress.py incident-start
```

### 2.3 Step 7 progress.py bug-start 校验

`progress.py bug-start` 内部校验（详见 `skills/workflow-protocol/references/command-reference.md` §8）：

- `bug_flow.active == false`
- `release_state == active`
- `current_stage == testing` AND `sub_state == review-passed`
- `<bug-path>` 文件存在
- BUG-NNN.md frontmatter `root_cause == <命令参数 root-cause>`（一致性校验）
- `<root-cause>` ∈ {srs, architecture, development}

校验通过后 progress.py 自动：

- 设 `bug_flow.active = true`
- 设 `bug_flow.bug_report_path = <bug-path>`
- 设 `bug_flow.root_cause = <enum>`
- 切 `current_stage` 到对应 stage（srs → srs-specification；architecture → architecture-design；development → development）
- 设 `sub_state = write`
- `review_iteration = 0`

下游 `*-write` skill 在 Change Mode 接管。

### 2.4 Step 7 progress.py incident-start 校验

`progress.py incident-start --bug <bug-path> --report <incident-path>` 内部校验：

- `bug_flow.active == false`
- `<bug-path>` 文件存在 + frontmatter `root_cause == prd-exception`
- `<incident-path>` 文件存在 + `type: workflow-incident`
- INCIDENT.frontmatter `triggered_by_bug == <bug-path 的 bug_id>`（ID 一致）

校验通过后一次性设：

- `bug_flow.active = true`
- `bug_flow.bug_report_path = <bug-path>`
- `bug_flow.root_cause = prd-exception`
- `workflow_incident_active = true`
- `incident_report_path = <incident-path>`
- `current_stage = workflow-incident-analysis`

`workflow-evolution` 接管。

### 2.5 Active Mode 错误恢复

| 失败步骤 | 修复 |
|---------|------|
| Step 1: BUG report 不存在 / 格式损坏 | 让 testing-write 重新创建 / 修复 BUG report |
| Step 2: 上下文 doc 缺失（如 SRS 路径错）| 调 `progress.py query` 确认 artifact 路径正确 |
| Step 3: 分类置信度低 | 与用户对话补充信息 / 重新分类 |
| Step 4-6: validate.py 失败 | 按 validate 错误修复 BUG report |
| Step 7 (bug-start): progress.py 拒绝 | 检查 progress.md state 是否真满足前置；若 root_cause 与 BUG frontmatter 不一致，rewrite frontmatter |
| Step 7 (incident-start): INCIDENT skeleton validate fail | 修 INCIDENT frontmatter（特别是 triggered_by_bug ID 必须等于 BUG.bug_id） |

---

## 3. Post-Close Mode 端到端流程

### 3.1 6 步流程

```python
def post_close_mode_intake(user_input):
    # Step 1: 与用户对话获取 bug 详情
    bug_details = ask_user(
        questions=[
            "重现步骤 / 触发条件",
            "期望行为 vs 实际行为",
            "影响范围（功能 / 性能 / UI / 数据 等）",
            "频率（每次 / 偶发）",
        ]
    )
    if any_missing(bug_details):
        return "信息不足，等用户补充"
    
    # Step 2: 计算 BUG ID
    bug_id = compute_next_bug_id()  # 见 §5
    bug_path = f"docs/bug/{bug_id}.md"
    
    # Step 3: 创建 BUG-NNN.md
    state = read_progress_query()
    bug_md_content = build_bug_md(
        bug_id=bug_id,
        type="bug-report",
        status="review-passed",  # post-close 直接终态
        found_in_release=state.release,  # 当前 closed release
        target_release=None,
        root_cause=None,
        consumed_in_release=None,
        owner="claude-opus-4-7/bug-triage",
        body=format_bug_body(bug_details)
    )
    write_file(bug_path, bug_md_content)
    
    # Step 4: changelog promote
    run("skills/doc-guardian/scripts/changelog.py promote " + bug_path)
    
    # Step 5: validate.py file
    run("skills/doc-guardian/scripts/validate.py file " + bug_path)
    if exit_code != 0:
        return error("BUG report 校验失败")
    
    # Step 6: bug-intake
    run(
        "skills/workflow-protocol/scripts/progress.py bug-intake "
        f"--bug {bug_path}"
    )
    
    return f"post-close intake complete: {bug_id} 已加入 unresolved_bugs"
```

### 3.2 Post-close BUG-NNN.md 完整模板

```markdown
---
title: BUG-008 注册流程邮箱重复时不报错
type: bug-report
status: review-passed
bug_id: BUG-008
found_in_release: "0.3"
target_release: null
root_cause: null
consumed_in_release: null
created: 2026-05-20T14:00:00Z
updated: 2026-05-20T14:00:00Z
owner: claude-opus-4-7/bug-triage
---

# BUG-008 注册流程邮箱重复时不报错

## 1. Symptom（现象）

用户用已注册的 email 再次注册时，系统返回 "Registration successful"，但实际不创建第二个账号（数据库唯一约束阻止）。用户预期看到错误提示。

## 2. Reproduction Steps（重现步骤）

1. 用 email `test@example.com` 注册账号 A
2. 用同一 email `test@example.com` 再次提交注册表单
3. 观察响应：返回 200 + "Registration successful"，无报错
4. 预期：返回 4xx + "Email already registered"

## 3. Environment（环境）

- Release: 0.3 (closed)
- 浏览器：Chrome 120
- 后端版本：v0.3.0

## 4. Impact（影响范围）

功能性 bug：用户认为账号已注册，但实际未创建，会导致后续登录失败的二次困扰。

## 5. Frequency

100% 复现（每次都失败）。

## 6. Triage Status

**Mode**: post-close intake
**Note**: 此 BUG 在 release 0.3 closed 后由用户报告，已通过 `progress.py bug-intake` 加入
        `unresolved_bugs` 队列。下次 `release-start` 时由 progress.py 自动设
        `target_release` 与 `consumed_in_release`，由 srs-write 在新 SRS 合并修复需求。
        `root_cause` 待下次 release 内 active triage 阶段判定。

## Pending Changes

<!-- empty after changelog.py promote -->

## Change Log

### 2026-05-20
- 2026-05-20T14:00:00Z [全文]: BUG report 创建（post-close intake）
```

注（v0.6 round 3 M3）：`## Pending Changes` 章节在 promote 后必须为**真正空章节**（仅允许空白行或 HTML comment，参 `skills/doc-guardian/references/change-log-format.md` §2.3）；任何非注释、非空白行（如 `- (空，已 promote)` 这种 list item）会被 validate.py 类 6 视为未 promote 的 entry 而拒绝。

### 3.3 与用户对话的最小信息集

bug-triage 创建 post-close BUG-NNN.md 前**必须**收集以下最小集：

| 字段 | 必需 | 来源 |
|------|------|------|
| Symptom | ✓ | 用户描述 |
| Reproduction Steps | ✓ | 用户描述 |
| Environment | ✓ | 用户描述 + dispatcher 提供 release |
| Impact | ✓ | 用户描述 |
| Frequency | ✓ | 用户描述 |
| Expected vs Actual | ✓ | 用户描述 |

任一缺失 → 与用户对话补充。**不要**用模糊描述创建 BUG report（垃圾进则垃圾出）。

### 3.4 Post-close 不分类 root_cause 的规则

post-close mode **绝不**判定 root_cause；BUG-NNN.md frontmatter `root_cause: null`。

理由：

- closed release 期间无 active scenario / Stage Change Mode；分类后无路径走
- 下次 release-start 时，BUG 进入新 release scope，由 srs-write 合并修复需求
- 新 SRS 走完 Stage 1-4 进入 testing；若 testing 重测 fail，触发新一轮 active mode triage（此时才判 root_cause）

post-close BUG report 是**等待下一 release 处理的占位记录**，不需要立刻分类。

### 3.5 Post-close 期间 BUG 不允许"立即修"

用户可能要求"立刻修这个 bug"。bug-triage 必须 reject + 解释：

```
拒绝消息模板：
"当前 release 0.3 已 closed，无法在本 release 直接修 bug（S4 仅 active release 期间允许）。
 此 bug 已加入 unresolved_bugs，下次启动新 release 时（progress.py release-start）
 会自动 consume 并合并到新 SRS。
 
 如果用户希望尽快处理：
 (a) 现在调 release-start 启动新 release 0.4（按 S2 子场景判定，scenario-dispatcher）
 (b) 该 bug 在新 release SRS 中作为 fix 需求处理"
```

### 3.6 Post-Close Mode 错误恢复

| 失败步骤 | 修复 |
|---------|------|
| Step 1: 用户描述太模糊 | 多轮对话补充；不要凭模糊创建 BUG |
| Step 2: BUG ID 冲突 | 重新扫描 docs/bug/，取 max+1 |
| Step 3-5: BUG 创建 / validate fail | 修 frontmatter / body |
| Step 6: bug-intake 拒绝（duplicate intake：bug_path 已在 unresolved_bugs）| 检查 progress.md unresolved_bugs；若确实重复，提示用户 / 删新创建的 BUG |

---

## 4. INCIDENT-MMM.md Skeleton Template

bug-triage 在 active mode + `root_cause: prd-exception` 时创建。

### 4.1 完整 skeleton

```markdown
---
title: INCIDENT-001 PRD 异常引发的 testing 失败
type: workflow-incident
status: draft
incident_id: INCIDENT-001
triggered_by_bug: BUG-007
triggered_in_release: "0.3"
resolution_action: null
created: 2026-05-15T11:30:00Z
updated: 2026-05-15T11:30:00Z
owner: claude-opus-4-7/bug-triage
---

# INCIDENT-001 PRD 异常引发的 testing 失败

> **Skeleton Notice**：本 incident skeleton 由 `bug-triage` 创建，仅含 frontmatter
> 与本 placeholder。Body 章节由 `workflow-evolution` 在 incident analysis 阶段填充。

## 1. Triggering Bug

详见 `docs/bug/BUG-007.md`。

## 2. Workflow State at Trigger

- Release: 0.3
- Stage at trigger: testing
- Scenario: <从 progress.py query 取>
- Project State: active

## 3. Root Cause Analysis

> 待 workflow-evolution 填充：
> - PRD 哪部分错（章节引用）
> - 工作流哪段没拦住（Stage 1/2/3 中是否本该被人确认拦截）
> - 是否属于已知 known-issue

## 4. Workflow Improvement Suggestions

> 待 workflow-evolution 填充：
> - workflow spec 修改建议
> - skill 改进建议
> - template 改进建议
> - 评审 rubric 改进建议

## 5. Three Action Evaluation

> 待 workflow-evolution 填充。3 个 action 评估：
>
> ### 5.1 Continue
> - 适用条件：<…>
> - 风险：<…>
> - 后续工作：<…>
>
> ### 5.2 Abort
> - 适用条件：<…>
> - 影响：<本 project 进 aborted 终态>
>
> ### 5.3 Reconstruct
> - 适用条件：<…>
> - 影响：<本 project 进 reconstructing 终态，转 S3 起新 project>

## 6. Recommendation

> 待 workflow-evolution 填充：基于上面分析，推荐的 action + rationale。

## 7. Resolution

> 待 workflow-evolution 填充：用户决策记录 + 调用 incident-resolve 命令。

## Pending Changes
- 2026-05-15T11:30:00Z [frontmatter+placeholder]: skeleton 由 bug-triage 创建（§3-§7 待 workflow-evolution）

## Change Log
```

> **关键**：上面是**写文件后、promote 前**的状态。bug-triage 必须接着调 `changelog.py promote`，
> 让 `## Pending Changes` 清空、`## Change Log` 含创建 entry 后，再调 validate.py file。

**Promote 后状态**（写完文件 + 跑 `changelog.py promote <incident-path>` 后）：

```markdown
[frontmatter 与上面相同]

# INCIDENT-001 PRD 异常引发的 testing 失败

[Skeleton Notice + §1-§7 placeholder 与上面相同]

## Pending Changes

## Change Log

### 2026-05-15
- 2026-05-15T11:30:00Z [frontmatter+placeholder]: skeleton 由 bug-triage 创建（§3-§7 待 workflow-evolution）
```

此时 `validate.py file` 才能 pass（类 6 Change Log Discipline 要求 Pending 为空 + Change Log 格式合法）。

### 4.2 Skeleton 严格约束

bug-triage 创建 skeleton 时**只**能写：

- frontmatter 全部字段（含 `resolution_action: null`）
- "Skeleton Notice" 段
- 章节标题（§1-§7）
- §1 引用 BUG report 的链接
- §2 客观状态信息（从 progress.py query 取）
- §3-§7 全部留 `> 待 workflow-evolution 填充：` placeholder
- 一条 ## Pending Changes entry "skeleton 创建"（promote 前）

**禁止**写：

- §3 根因分析内容
- §4 工作流改进建议
- §5 3 action 评估
- §6 recommendation
- §7 resolution

这些是 `workflow-evolution` 的 mutation 责任。

### 4.3 Skeleton 文件创建后必跑流程（v0.6 round 2 batch2-F1）

bug-triage 写完 skeleton 文件后**必须按序**调 3 个命令，缺一不可：

```bash
# 1. promote：把首条 Pending entry 移入 Change Log
skills/doc-guardian/scripts/changelog.py promote <incident-path>

# 2. validate：确认 class 1-7 single-file checks 通过（class 8 由 validate.py consistency 单独跑，详见后表）
skills/doc-guardian/scripts/validate.py file <incident-path>

# 3. （前两步全 pass 后）调 incident-start
skills/workflow-protocol/scripts/progress.py incident-start \
    --bug <bug-path> --report <incident-path>
```

validate.py 类 6 (Change Log Discipline) 要求 `## Pending Changes` 为空；省 promote 步骤会让 validate 失败、incident-start 前置不满足，整条 PRD-exception 路径不可达。

**validate 检查清单**（v0.6 round 3 M2 修正：完整覆盖 class 1-7 single-file checks，事实源 `skills/doc-guardian/SKILL.md` §5.1）：

| 类 | 名称 | INCIDENT skeleton 必须满足 |
|----|------|---------------------------|
| 1 | Path | `docs/incident/INCIDENT-<NNN>.md`（按 directory-layout）|
| 2 | Naming | `INCIDENT-\d{3}.md` 大写连字符 + 3 位 zero-padded |
| 3 | Frontmatter Schema | universal 6 字段（title/type/status/created/updated/owner）+ 扩展字段（incident_id / triggered_by_bug / triggered_in_release / resolution_action）全在；status ∈ {draft, in-review, revising, review-passed, approved}；type=`workflow-incident` |
| 4 | Frontmatter Format | timestamp ISO8601 UTC、incident_id `INCIDENT-\d{3}`、owner `agent/skill`、resolution_action ∈ {null, continue, abort, reconstruct}（skeleton 阶段必为 null） |
| 5 | Cross-Reference | `triggered_by_bug` 值为合法 BUG ID，按 `docs/bug/<value>.md` lookup 文件存在 |
| 6 | Change Log Discipline | `## Pending Changes` 已 promote 清空（仅允许空白行或 HTML comment）；`## Change Log` 含 `### YYYY-MM-DD` 分组 + 创建 entry 格式合法 |
| 7 | ID Uniqueness | `docs/incident/` 下 `INCIDENT-NNN` 不与既有冲突 |

class 8 (Consistency with progress.md) 由 `validate.py consistency` 单独跑，不在 single-file check 内；INCIDENT skeleton 创建时 progress.md 尚未更新（incident-start 才会改），因此 class 8 不在本时点检查。

完整 8 类校验定义见 `skills/doc-guardian/SKILL.md` §5.1。

### 4.4 路径

INCIDENT skeleton 必须放 `docs/incident/INCIDENT-<NNN>.md`（按 doc-guardian directory-layout 规定）。

---

## 5. ID 计算策略

### 5.1 BUG ID

```python
def compute_next_bug_id():
    existing_ids = []
    for path in glob("docs/bug/BUG-*.md"):
        match = re.match(r"docs/bug/BUG-(\d{3})\.md", path)
        if match:
            existing_ids.append(int(match.group(1)))
    next_id = max(existing_ids, default=0) + 1
    return f"BUG-{next_id:03d}"  # 强制 3 位 zero-padded
```

**约束**（v0.6 round 3 L5）：

- 强制 3 位 zero-padded（`BUG-001` 而非 `BUG-1`）
- 大写连字符（`BUG-` 而非 `bug-` / `Bug-`）
- 4 位以上 reject（`BUG-1000` 不允许；如果项目 bug 超过 999，需要 design review 决定 ID 升位）

### 5.2 INCIDENT ID

```python
def compute_next_incident_id():
    existing_ids = []
    for path in glob("docs/incident/INCIDENT-*.md"):
        match = re.match(r"docs/incident/INCIDENT-(\d{3})\.md", path)
        if match:
            existing_ids.append(int(match.group(1)))
    next_id = max(existing_ids, default=0) + 1
    return f"INCIDENT-{next_id:03d}"
```

约束同 §5.1。

### 5.3 ID 冲突处理

`validate.py ids` 会检测重复。如发生：

- bug-triage 检测到自己计算的 ID 与已有冲突 → 重新扫描取 max+1
- 极小概率 race condition（同时创建两个 BUG）→ 第二个 validate fail，bug-triage 重试

---

## 6. 与 root-cause-rubric.md 的协作

```
bug-triage 调用入口
  ↓
triage-decision-tree.md（本 reference）：
  - 判 active mode vs post-close mode
  - active mode 路径
  ↓
root-cause-rubric.md：
  - 判 4 类根因
  ↓
triage-decision-tree.md（本 reference）：
  - 根据 root_cause 决定 progress.py 命令
  - active srs/arch/dev → bug-start
  - active prd-exception → 创建 INCIDENT skeleton + incident-start
  - post-close 全程不进 root-cause-rubric.md，仅本 reference
```

---

## 7. 端到端 Decision Examples

### 7.1 Example A：Stage 5 testing 自动触发 active mode

```
背景：release 0.3 active，current_stage=testing，sub_state=review-passed
testing-write 跑测试发现 BUG-005（登录 IE11 崩溃），写 BUG report 后 invoke bug-triage

bug-triage active mode：
1. progress.py query → release_state=active, bug_flow.active=false
2. 走 Active Mode（§2）
3. 读 BUG-005.md + SRS + Architecture + relevant detailed_design
4. root-cause-rubric.md 分析 → root_cause=srs（SRS 漏 IE11 兼容性需求）
5. confidence=high，无需二次确认
6. 写 BUG-005.md frontmatter root_cause=srs
7. 加 Triage Analysis 章节
8. changelog.py promote → validate.py file → 全 pass
9. 调 progress.py bug-start --bug docs/bug/BUG-005.md --root-cause srs
10. progress.py 切 current_stage=srs-specification，sub_state=write
11. srs-write Change Mode 接管
```

### 7.2 Example B：用户在 active release 非 testing 阶段主动报 bug → dispatcher 拒绝（v0.6 round 2 batch2-F2）

```
背景：release 0.4 active，current_stage=development，sub_state=write
用户："我刚发现登录在某些情况下会偶发 500"

dispatcher 检测：
- release_state==active
- current_stage=development（非 testing）
- 用户输入是 bug 描述 → classify intent = report_bug
→ 检查 bug-start 前置（current_stage==testing AND sub_state==review-passed）→ 不满足
→ dispatcher 不路由到 bug-triage active mode；走 reject 路径

dispatcher 输出（拒绝 + 提示，不 invoke bug-triage）：
"progress.py bug-start 前置要求 current_stage==testing AND sub_state==review-passed；
 当前 (development, write) 不满足。建议路径：
 (a) 等本 release 推进到 testing 阶段；testing-write 跑测试时如果重现该现象，
     会自动创建 BUG report 并 invoke bug-triage active mode；
 (b) 现在把现象记到当前 stage doc 的 known-issue 段（development/plan.md /
     development/breakdown.md / development/tasks/Tn/detailed_design.md，
     由 development-planning-write 处理），方便 testing 阶段重点验证；
 (c) 如果是 release 0.3 closed 后才发现的 bug，应该等本 release（0.4）close 之后
     走 post-close mode（progress.py bug-intake）"

不创建 docs/bug/BUG-NNN.md；不调任何 progress.py 子命令；dispatcher 退出。
bug-triage 不会被 invoke（已经在 dispatcher 层 reject）。
```

注（v0.6 round 2 batch2-F2 收敛）：active mode 入口前置 = `progress.py bug-start` 前置 = `current_stage==testing AND sub_state==review-passed`。早期版本试图通过创建"known-issue BUG"绕过该约束，但该 BUG 不进 `bug_flow` / `unresolved_bugs`、frontmatter 字段无法描述其状态、Bootstrap 无法判断后续是否重 triage——属于 orphan doc，已废弃。非 testing 阶段报 bug 统一由 dispatcher reject + 提示用户记入当前 stage doc。

### 7.3 Example C：用户在 closed release 期间报 bug → post-close mode

```
背景：release 0.3 closed，previous_releases=["0.1","0.2","0.3"]
用户："注册时 email 重复不报错"

dispatcher：
1. progress.py query → release_state=closed
2. 用户输入是 bug 描述
3. 路由到 bug-triage post-close mode

bug-triage post-close mode：
1. 与用户对话补充信息：
   - Symptom: 注册返回 200 但实际不创建账号
   - Reproduction: 用同一 email 注册两次
   - Environment: release 0.3, Chrome 120
   - Impact: 功能性 bug
   - Frequency: 100%
   - Expected: 4xx + "email already registered"
2. 计算下一个 BUG ID：scan docs/bug/ → max=BUG-007 → 下一个 BUG-008
3. 创建 docs/bug/BUG-008.md（按 §3.2 模板）
4. changelog.py promote
5. validate.py file → pass
6. progress.py bug-intake --bug docs/bug/BUG-008.md
   → progress.md unresolved_bugs.append("docs/bug/BUG-008.md")
7. 通知用户："BUG-008 已加入待处理队列。下次 release-start 时
   会自动 consume，srs-write 会在新 SRS 合并此修复需求。"
```

### 7.4 Example D：active mode 判定 prd-exception

```
背景：release 0.5 active, current_stage=testing, sub_state=review-passed
testing-write 发现 BUG-009（自动会议纪要准确率始终 50%，SRS 要求 80%）

bug-triage active mode：
1. 走 Active Mode
2. 读 BUG-009 + PRD + SRS + Architecture + detailed_design
3. root-cause-rubric.md 分析：
   - 修 SRS 把 80% 改 50%? → PRD 关键功能"AI 替代人写纪要"不成立
   - 修 architecture? → 任何技术栈都达不到 80%（自然语言任务上限）
   - 修 development? → 实现已合理
   → 唯一可能是 prd-exception
4. confidence=medium（任何技术栈都达不到这个判断不易确定）
5. 与用户二次确认：
   "判定为 prd-exception 会触发 incident analysis，可能 abort/reconstruct。
    具体证据：现有技术下准确率上限约 60%，距离 SRS 要求 80% 有显著 gap。
    确认进入 incident？"
6. 用户确认
7. 写 BUG-009.md frontmatter root_cause=prd-exception + Triage Analysis
8. changelog.py promote → validate.py → pass
9. 计算下一个 INCIDENT ID：scan docs/incident/ → 第一次，INCIDENT-001
10. 创建 docs/incident/INCIDENT-001.md skeleton（§4.1 模板）
    - frontmatter triggered_by_bug=BUG-009
    - 一条 ## Pending Changes entry "skeleton 创建"
11. **changelog.py promote docs/incident/INCIDENT-001.md** → Pending → Change Log（§4.1 promote 后状态）
12. validate.py file <incident path> → pass（类 6 Change Log Discipline 要求 Pending 已空）
13. progress.py incident-start --bug docs/bug/BUG-009.md --report docs/incident/INCIDENT-001.md
    → 设 bug_flow.active=true, bug_flow.root_cause=prd-exception,
       workflow_incident_active=true, current_stage=workflow-incident-analysis
13. workflow-evolution 接管
```

### 7.5 Example E：active mode 重试场景

```
背景：上次 active triage 时
- 写完 BUG-005 frontmatter root_cause=srs ✓
- changelog promote ✓
- validate.py ✓
- progress.py bug-start 调用失败（如磁盘锁竞争异常）

新 session 重新进入：
1. AGENTS.md Bootstrap → progress.py query
2. 检测到 bug_flow.active=false，但 docs/bug/BUG-005.md 存在 + root_cause=srs
3. Bootstrap 判断这是上次 triage 完成但 bug-start 未成功的状态
4. invoke bug-triage active mode

bug-triage active mode：
1. 走 Active Mode
2. 读 BUG-005，发现 root_cause 已设为 srs
3. 跳过 Step 3-6（已完成）
4. 直接 Step 7：调 progress.py bug-start --bug docs/bug/BUG-005.md --root-cause srs
5. 成功 → bug_flow.active=true, current_stage=srs-specification
```

这个示例展示**幂等性**：重 invoke active mode 不会重复分类，只重试未成功的 progress.py 调用。

### 7.6 Example F：active mode 情况下用户提供模糊描述

```
背景：testing-write 写了 BUG-010 但 body 只有 "登录有问题"，没重现步骤

bug-triage active mode：
1. 读 BUG-010.md → body 信息严重不足
2. 拒绝立刻分类
3. 与用户对话：
   "BUG-010 信息不足无法分类。请补充：
   - 具体重现步骤（登录哪一步失败？）
   - 期望 vs 实际行为
   - 触发条件（特定账号 / 特定浏览器？）"
4. 用户补充
5. 由 testing-write 在 BUG-010 加 Pending Changes + changelog promote
6. 重 invoke bug-triage active mode → 此时 root_cause 仍 null，重新走分类
```

### 7.7 Example G：post-close 用户要求"立刻修"

```
背景：release 0.3 closed
用户："登录有 bug，赶紧修"

bug-triage post-close mode：
1. progress.py query → release_state=closed
2. 走 Post-Close Mode
3. 收集 bug 详情，创建 BUG-011，调 bug-intake
4. 用户："你怎么不直接修？"
5. bug-triage 解释（按 §3.5 拒绝模板）：
   "release 0.3 已 closed，本 release 不能再修代码（S4 仅 active release 期间允许）。
    选项 A：现在启动新 release 0.4 → invoke scenario-dispatcher 决定 S2 子场景
    选项 B：BUG-011 已加入队列，等下次 release-start 时合并到新 SRS"
6. 用户选 A
7. bug-triage 退出，路由回 scenario-dispatcher
```

---

## 8. Concurrency 约束

### 8.1 active mode

- 同一 BUG-NNN.md 不允许两个 bug-triage 实例并发分类（doc 编辑层无锁，由 doc-guardian validate id 防 ID 冲突）
- progress.py bug-start / incident-start 内部 flock 串行
- 重 invoke 是允许的（幂等性）

### 8.2 post-close mode

- 多个用户同时报 bug 创建多个 BUG-NNN.md：
  - ID 计算 `max+1` 可能 race（两个并发都拿到同一 next_id）
  - validate.py ids 会拒绝其中一个（重复 ID）
  - 失败的那个 bug-triage 重新计算 ID 重试

### 8.3 与 dispatcher 协作

- dispatcher 路由到 bug-triage 后退出；bug-triage 独立执行
- bug-triage 完成后 control 不返回 dispatcher（除非 dispatcher 链式调用，但当前设计不支持）
- 用户后续操作由 AGENTS.md Bootstrap 重新决定路由

---

**End of Triage Decision Tree Reference**
