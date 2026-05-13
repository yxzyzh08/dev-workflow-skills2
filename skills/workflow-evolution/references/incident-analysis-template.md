# workflow-evolution Incident Analysis Template & 3 Action Decision Matrix

**配套**：`skills/workflow-evolution/SKILL.md`

本 reference 提供：

- INCIDENT-NNN.md body §3-§7 详细模板与每章节填写指南
- Three Action Decision Matrix（continue / abort / reconstruct 评估框架）
- 自评清单（workflow-evolution 写完 body 后必跑）
- 端到端 examples（3 个典型 incident scenario）
- Retrospective consumption mode 的 conversation 输出格式

仅适用 workflow-evolution skill。`bug-triage` 创建 skeleton 后**不**进本 reference。

---

## 1. Incident Body Section Templates

INCIDENT-NNN.md body 由 7 个章节组成。§1-§2 由 `bug-triage` 在 skeleton 阶段填客观信息；§3-§7 由 `workflow-evolution` 在 incident analysis mode 填充。

### 1.1 §3 Root Cause Analysis 模板

```markdown
## 3. Root Cause Analysis

### 3.1 PRD Defect Pinpoint

**Affected PRD Section(s)**: <PRD 哪节哪段；引用 docs/prd/prd.md 章节号>
**Defect Nature**:
  - [ ] PRD 描述与实际用户需求不符
  - [ ] PRD 关键功能集存在内部逻辑冲突
  - [ ] PRD 设定的 NFR / 性能指标 / 准确率在任何技术栈都不可达
  - [ ] PRD 假设的用户群与实际使用场景错配
  - [ ] 其他：<具体描述>

**Evidence**:
  - <从 BUG report / SRS / Architecture / 测试结果引用具体证据>
  - <例：BUG-009 重复测试 50 次平均准确率 50%，远低于 PRD 80% 要求>

### 3.2 Workflow Stage Where Defect Should Have Been Caught

**Should Have Been Caught At**:
  - [ ] Stage 1 PRD Inception（人 gate 阶段是否漏审？）
  - [ ] Stage 2 SRS Specification（细化时是否暴露但未升级？）
  - [ ] Stage 3 Architecture Design（架构方案评估时是否预警？）
  - [ ] Stage 4 Development（实现 / 测试编写时是否有信号被忽视？）
  - [ ] 工作流当前**无机制**能拦截此类 PRD 异常

**Why It Wasn't Caught**:
  <2-5 句自然语言：解释为何 Stage X review / 人 gate 没拦下。例：
   "Stage 1 PRD review 阶段评估了功能完整性但未对 NFR 80% 准确率做技术可行性分析；
    工作流当前的 prd-review skill 没有 NFR feasibility 这一项 rubric。">

### 3.3 Is This a Known Pattern?

**Cross-Reference Check**:
  - 检查 `docs/incident/INCIDENT-*.md`：本类 incident 是否第二次以上出现？
  - 若否：**新模式**
  - 若是：列出 prior INCIDENT IDs + 上次 resolution_action

**If Recurring**: 工作流改进的紧迫性显著上升；§4 应优先推荐 spec / rubric 修订
```

**填写指南**：

- §3.1 必须**具体引用** PRD 章节，不接受泛泛而谈
- §3.2 至少选 1 项（含"无机制能拦截"的诚实选项）
- §3.3 是 cross-release 信号：重复出现的 pattern 比单点 incident 更值得 workflow 改进

### 1.2 §4 Workflow Improvement Suggestions 模板

```markdown
## 4. Workflow Improvement Suggestions

> **Scope Notice**：本节建议**针对 dev-workflow-skills2 工作流自身的改进**，而非用户当前
> project 的代码。改进建议落地需在 dev-workflow-skills2 仓库走独立 design proposal
> review cycle。本节仅产出 **advisory 自然语言建议**（允许且鼓励引用具体 skill / 章节）；
> **禁止**输出 patch / diff / unified diff 或直接编辑 dev-workflow-skills2 文件
> （v0.6 round 2 batch2-F4：严格区分 advisory 与 patch；递归悖论防的是 patch，不是建议）。
>
> 每条建议尾部必须标注 `**Action Item**: 提交到 dev-workflow-skills2 仓库走独立
> design proposal review cycle`，让用户清楚 advisory 不会自动落地。

### 4.1 Workflow Spec Suggestions

针对 `docs/workflow/workflow_specification_claude.md`：

| 改进点 | 当前状态 | 建议改动 | 优先级 |
|--------|---------|---------|--------|
| <例：Stage 1 prd-review rubric 加 NFR feasibility 项> | 当前 prd-review 不评 NFR 可行性 | 加 §X.Y 描述 NFR feasibility check | High / Med / Low |
| ... | ... | ... | ... |

### 4.2 Skill Suggestions

针对 `skills/<name>/SKILL.md`：

| 改进点 | 目标 skill | 建议改动 | 优先级 |
|--------|-----------|---------|--------|
| <例：prd-review 加 NFR rubric> | prd-review | §X. Review Rubric 加 NFR feasibility 子项 | High / Med / Low |

### 4.3 Template Suggestions

针对 stage skill 的 doc 模板（如果有）：

| 改进点 | 目标 doc type | 建议改动 |
|--------|-------------|---------|
| ... | ... | ... |

### 4.4 Review Rubric Suggestions

针对各 *-review skill 的评审标准：

| 改进点 | 目标 review skill | 建议加 / 改 rubric |
|--------|----------------|-----------------|
| ... | ... | ... |

### 4.5 Action Item Owner

| Action | 落地路径 | Owner |
|--------|---------|-------|
| 上述 §4.1-§4.4 全部建议 | dev-workflow-skills2 仓库 design proposal review cycle | 用户 / dev-workflow-skills2 维护者 |
| **不**在本 incident 中直接修 dev-workflow-skills2 文件 | — | — |
```

**填写指南**：

- 严格区分"本 skill 集改进"（本节）vs"用户项目改进"（§3-§5 不涉及，由 retrospective-write 处理）
- 每条改进必须**具体可行**（不是"加强 review"这种泛泛建议；而是"加 X rubric 项检查 Y"）
- 优先级标注帮助用户决定是否值得投入 design proposal 流程

### 1.3 §5 Three Action Evaluation 模板

```markdown
## 5. Three Action Evaluation

### 5.1 Continue

**适用条件**（满足任一）:
  - [ ] §3 分析揭示 bug 实际可在 srs / architecture / development 任一层修复（即 bug-triage 误判 prd-exception）
  - [ ] §4 提议的 workflow 改进已足以避免此类异常未来再发生，PRD 与 release 内容仍有效
  - [ ] 用户判定 incident 属于"特殊单点"，整体方向不变

**预期后续工作**:
  - 调 `progress.py incident-resolve --action continue`
  - 退出 incident state，回到 testing review-passed
  - 如原 bug 仍需修复：用户创建**新 BUG-MMM.md**（new ID）触发 bug-triage active mode；新 BUG 的 root_cause 由新一轮 triage 重新判定（不应再判 prd-exception）
  - §4 的 workflow 改进建议提交到 dev-workflow-skills2 design proposal cycle

**风险**:
  - 若 PRD 实际有问题但选 continue → bug 可能在后续 release 反复出现
  - workflow 改进若未跟进 → 下次还会卡在同一类异常

### 5.2 Abort

**适用条件**（满足任一）:
  - [ ] §3 分析揭示 PRD 描述的产品**根本不可行**（任何技术栈都达不到目标，且产品定位无法妥协）
  - [ ] 用户判定投资回报率不足以继续投入
  - [ ] 项目方向与组织战略变化（外部因素，非工作流问题）

**预期后续工作**:
  - 调 `progress.py incident-resolve --action abort`
  - `project_state: aborted`、`release_state: closed`、`release_close_reason: "incident-abort"`、`current_stage: null`
  - 终态：progress.py 拒绝任何后续 mutation（仅 query / recover 允许）
  - 用户起新 project（独立目录 / 独立 progress.md）

**风险**:
  - 已投入的 release 1...N 沉没成本
  - terminal state 不可逆（除非起新 project）

### 5.3 Reconstruct

**适用条件**（必须**全部**满足）:
  - [ ] PRD 描述的产品方向有效（用户群 / 核心价值不变）
  - [ ] 当前实现路径（架构 / 技术栈 / 数据模型）已根本走错
  - [ ] 需要从外部源系统重建：本 project 作 source system，新 S3 project 用新方案重做

**预期后续工作**:
  - 调 `progress.py incident-resolve --action reconstruct`
  - `project_state: reconstructing`、`release_state: closed`、`release_close_reason: "incident-reconstruct"`
  - 终态；用户起新 S3 project，引用本 project 作 source system
  - 新 project 走 S3 入口（scenario-dispatcher）
  - Stage 1/2 强制源系统分析（含本 project 的 source-system-analysis 套件）

**风险**:
  - 新 S3 project 需重新走完整 7 阶段
  - 旧 project 代码 / 测试基本不可复用
  - 时间成本与 abort 相当甚至更高
```

**填写指南**：

- 3 个 action 都必须填，不能省（即使明显某 action 不适用，也要写出"为何不适用"的 rationale）
- 适用条件用 checkbox 形式让用户与 workflow-evolution 共同评估
- "预期后续工作"明确 progress.py 命令与下游 stage state，避免用户对实际后果不清楚

### 1.4 §6 Recommendation 模板

```markdown
## 6. Recommendation

**Recommended Action**: <continue | abort | reconstruct>

**Rationale**:
  <2-5 句话：基于 §3 Root Cause + §5 评估，为何推荐此 action>
  <例："基于 §3.1 的 PRD NFR 80% 准确率分析，当前技术栈上限约 60%（详见 BUG-009 重复测试），
       且产品定位'AI 替代人写纪要'高度依赖该 NFR，下调到 50% 会让产品价值显著缩水。
       但产品方向（AI 辅助会议记录）仍有效，可考虑用混合策略（AI 起草 + 人工校对）实现 PRD 价值。
       Recommend: reconstruct（用新 S3 project 重做混合策略架构）。">

**Confidence**: <high | medium | low>

**Alternative Action**:
  <如 confidence != high，列次优 action + 触发条件>
  <例："若用户判定混合策略也不符合产品定位（必须纯 AI），则推荐 abort。">

**Decision Authority**:
  本 recommendation 仅 advisory；最终决策由用户在 §7 做出。
```

**填写指南**：

- recommendation **必须**与 §3 Root Cause + §5 评估一致；不能凭直觉
- confidence 反映分析质量，不是 recommendation 强度（high confidence 不等于必须按推荐做）
- alternative 帮助用户在边界情况选择
- 永远强调"用户最终决定"

### 1.5 §7 Resolution 模板

```markdown
## 7. Resolution

**Decision Made**: <continue | abort | reconstruct>
**Decision By**: <user / 用户名>
**Decision Date**: <ISO8601 UTC timestamp>

**User Rationale**:
  <用户给出的决策理由；可与 §6 recommendation 一致也可不同；中立记录>

**Resolution Command**:
  ```
  skills/workflow-protocol/scripts/progress.py incident-resolve --action <enum>
  ```

**Post-Resolution Path**:
  <根据 action 描述后续路径>
  - continue: 回到 testing review-passed 重测；如原 bug 仍需修，创建新 BUG-MMM.md
  - abort: project terminal；起新 project
  - reconstruct: project terminal；起新 S3 project 引用本 project

**Workflow Improvement Items Submitted**:
  - <列出 §4 中决定提交的改进项 + 提交去向（dev-workflow-skills2 design proposal）>
  - <如未决定提交：写"无 / 用户后续评估"，不要漏不写>
```

**填写指南**：

- §7 在用户做出 3 action 决策**后**填，不能 placeholder
- Decision By / Date 客观字段，不要写"AI" / "claude"（决策权在用户）
- Resolution Command 必须与 frontmatter `resolution_action` 一致
- Post-Resolution Path 给用户**明确知情**接下来发生什么

### 1.6 INCIDENT Finalization 严格序列（v0.6 round 2 batch2-F5）

§7 填完后，workflow-evolution **必须**按以下严格序列执行（与 SKILL.md §3.1 Step 6.a-g 一致；缺步则 incident-resolve 失败或 doc-guardian validate 拒绝）：

```bash
# Step 6.a: 填 §7 Resolution body
# Step 6.b: 改 INCIDENT frontmatter resolution_action: null → <enum>
# Step 6.c: 改 INCIDENT frontmatter status: draft → review-passed
# Step 6.d: 改 INCIDENT frontmatter updated: <now ISO8601 UTC>
# Step 6.e: 加 ## Pending Changes entry（覆盖 §3-§7 + frontmatter mutation 所有改动）

# Step 6.f: changelog promote
skills/doc-guardian/scripts/changelog.py promote <incident-path>

# Step 6.g: validate
skills/doc-guardian/scripts/validate.py file <incident-path>
# → 必须 exit 0；类 6 (Pending 已空) + 类 3/4 (frontmatter 合法) + 类 5 (cross-ref triggered_by_bug)
# → fail 则修后重 promote / validate；不允许 silent skip

# Step 7: 仅在 6.g pass 后才能调 incident-resolve
skills/workflow-protocol/scripts/progress.py incident-resolve --action <enum>
```

**禁止**：

- validate 后再改 frontmatter / body（任何后续改动必须重走 6.a-g 含再 promote + 再 validate）
- 跳过 promote 直接 validate（Pending 不为空时 validate 类 6 拒绝）
- frontmatter mutation 不写 Pending entry（changelog discipline 破坏）

### 1.6.1 重 invoke 与幂等性（v0.6 round 3 M5 防 silent skip）

session 中断后重 invoke workflow-evolution 时，**不能仅凭 `status=review-passed` 推断 finalization 已完成**。必须按以下规则判定下一步：

```python
def reentrant_finalization_check(incident_path):
    state = progress_query()
    if state.workflow_incident_active is False:
        return exit("已 resolved；本 skill 不应被 invoke")
    
    incident = read(incident_path)
    body_done = bodies_3_to_7_filled(incident)
    fm_set = (
        incident.frontmatter.resolution_action in {"continue", "abort", "reconstruct"}
        and incident.frontmatter.status == "review-passed"
    )
    
    # 关键：只有 status=review-passed 不够，必须再跑一次 validate
    validate_pass = run_validate_py_file(incident_path).exit_code == 0
    pending_empty = pending_changes_section_is_empty(incident)
    
    if body_done and fm_set and validate_pass and pending_empty:
        # finalization 完整，可直接重试 incident-resolve（幂等）
        return retry("progress.py incident-resolve --action " + incident.frontmatter.resolution_action)
    elif body_done and fm_set and (not validate_pass or not pending_empty):
        # body/frontmatter 已写，但 finalization 未跑完
        return resume_step_6_e_through_g(
            "补 Pending entry 描述 'finalization 重做' → changelog.py promote → "
            "validate.py file → exit 0 后 incident-resolve"
        )
    elif body_done and not fm_set:
        # 漏写 frontmatter
        return resume_step_6_b_through_g
    else:
        return resume_full_step_5_and_6
```

不允许"silent skip 到 incident-resolve"。这是 v0.6 round 3 M5 修正的 round 1 F5 残留。

---

## 2. Three Action Decision Matrix

详细判定矩阵，帮 workflow-evolution 形成 §6 recommendation。

### 2.1 关键评估维度

| 维度 | 描述 | 影响哪个 action |
|------|------|----------------|
| D1. PRD 方向是否仍有效 | 产品对用户价值是否成立 | 否 → abort；是 → continue/reconstruct |
| D2. PRD 描述是否可在某种技术下实现 | 不只是当前路径，而是任何已知方案 | 否 → abort；是 → continue/reconstruct |
| D3. 当前实现路径与重构成本 | 修当前 release 还是从 0 重建？ | 修可行 → continue；从 0 → reconstruct |
| D4. Workflow 改进能否避免再发生 | 是单点还是系统性问题 | 是 → continue；否 → reconstruct/abort |
| D5. 沉没成本与剩余预算 | 用户经济决策（外部因素） | 影响 abort vs continue |
| D6. 错误是否 PRD 之外（被误判 prd-exception）| bug-triage 是否实际错判 | 是 → continue（重新分类）|

### 2.2 决策矩阵

| 场景 | D1 | D2 | D3 | D4 | D5 | 推荐 |
|------|----|----|----|----|----|----|
| bug-triage 误判（实际是 srs/arch/dev）| ✓ | ✓ | 修可行 | 是（单点）| 充足 | **continue** |
| 单点 PRD 微调（边角 NFR 设错）| ✓ | ✓ | 微调可行 | 是 | 充足 | **continue** |
| PRD 实现路径错（架构需重做）但方向有效 | ✓ | ✓ | 从 0 | 否 | 充足 | **reconstruct** |
| PRD 描述的功能技术上不可实现 | ✓（方向）| ✗ | — | 否 | 不足 | **abort** |
| PRD 方向错（用户不需要此产品）| ✗ | — | — | — | — | **abort** |
| 投资回报率不足（外部因素）| ✓ | ✓ | — | — | 不足 | **abort** |

### 2.3 用 D1-D6 形成 recommendation

workflow-evolution 在 §6 应**显式**列出每个维度的判断：

```markdown
**Dimensional Evaluation**:
  - D1 (PRD direction valid): <Yes/No + evidence>
  - D2 (Implementable in some tech): <Yes/No + evidence>
  - D3 (Current path fixable vs from-scratch): <fix / scratch + evidence>
  - D4 (Workflow improvement avoids recurrence): <Yes/No + evidence>
  - D5 (Sunk cost vs remaining budget): <user input>
  - D6 (PRD-exception misclassified): <Yes/No + evidence>

**Mapping to Action**:
  D1=Yes, D2=Yes, D3=fix, D4=Yes, D5=adequate, D6=No → continue
  D1=Yes, D2=Yes, D3=scratch, D4=No → reconstruct
  D1=No 或 D2=No → abort
```

### 2.4 边界情况

#### 2.4.1 D2 不确定（"可能可以但风险高"）

例：PRD 要求 80% 准确率；当前技术上限 60-70%，未来或可能达到 80%。

判定原则：

- 如果 6 个月内无明确技术突破 → 视为 D2=No → abort
- 如果用户愿意等技术成熟（且 D5 允许）→ 视为 D2=Yes（暂搁）→ workflow-evolution 不应推荐该路径，建议用户走 abort

不要让 workflow-evolution"乐观主义"地把 D2 判 Yes。

#### 2.4.2 D4 不确定（不知道改进会不会有效）

判定原则：

- §4 改进必须**具体可执行**才算 D4=Yes（如"加 NFR feasibility rubric 项"）
- 模糊建议（"加强评审"）算 D4=No
- 跨多个 incident 的反复模式（§3.3 是 known pattern）算 D4=No（说明改进未落地或无效）

#### 2.4.3 用户与 recommendation 不一致

如用户选 reconstruct，但 workflow-evolution 推荐 continue：

- 在 §6 保留原 recommendation 不改
- §7 Resolution 记录用户决定与用户 rationale
- 不要在 §6 暗中把 recommendation 改成与用户一致（保持中立的 advisory 角色）

---

## 3. Self-Evaluation Checklist

workflow-evolution 写完 §3-§7 后必跑（详见 SKILL.md §3.5）。

| # | 自评项 | 通过标准 | 失败处理 |
|---|--------|---------|---------|
| 1 | §3.1 是否引用具体 PRD 章节 | 至少 1 处具体引用 | 补具体章节号 |
| 2 | §3.2 是否选至少 1 项（含"无机制"诚实选项）| 是 | 补选 |
| 3 | §3.3 是否检查 cross-reference INCIDENT history | 是 | 扫描 docs/incident/ 后补 |
| 4 | §4 是否区分本 skill 集改进 vs 用户项目改进 | 区分清晰 | 重写：本节仅本 skill 集 |
| 5 | §4 每条改进是否具体可行（advisory 仍要精确）| 是；引用具体 skill / 章节 / rubric 项 | 重写为具体 advisory 描述（自然语言；**禁止** patch/diff）|
| 6 | §5 是否填 3 个 action 全部 | 是 | 补 |
| 7 | §5 每个 action 是否含适用条件 + 后续工作 + 风险 | 是 | 补 |
| 8 | §6 recommendation 是否与 §3 + §5 一致 | 一致 | 修 §6 或重审 §3 |
| 9 | §6 是否含 Dimensional Evaluation D1-D6 | 是 | 补 |
| 10 | §7 是否在用户决策后填（含 timestamp + rationale）| 是 | 用户决策后补 |
| 11 | INCIDENT frontmatter resolution_action 是否与 §7 一致 | 一致 | 修 frontmatter 或 §7 |
| 12 | INCIDENT frontmatter triggered_by_bug 是否指向真实 BUG | doc-guardian validate cross-ref 校验 | 修 frontmatter |
| 13 | §4 是否每条改进都标注 "Action Item: 提交 dev-workflow-skills2 design proposal review cycle"？（v0.6 round 2 batch2-F4）| 是 | 补标注 |
| 14 | **本 INCIDENT 是否输出可直接应用的 patch / diff / unified diff 给 dev-workflow-skills2 自身文件？**（v0.6 round 2 batch2-F4 严格区分 advisory vs patch）| **否**（advisory 自然语言建议允许；patch/diff 严禁）| 删 patch；改写为 advisory 描述 |
| 15 | finalization 顺序（§1.6）：§7 → frontmatter (resolution_action + status + updated) → Pending entry → changelog.py promote → validate.py file → incident-resolve；validate 后是否还有 frontmatter / body 改动？（v0.6 round 2 batch2-F5）| **否**（validate pass 后到 incident-resolve 之间不允许编辑 doc）| 重走 6.a-g：再加 Pending entry + 再 promote + 再 validate |
| 16 | 每次 frontmatter / body 改动是否都有对应 ## Pending Changes entry？（v0.6 round 2 batch2-F5）| 是 | 补 Pending entry + 重 promote |

任一未通过 → 修复后重跑 validate.py file <incident path>。

---

## 4. End-to-End Examples

### 4.1 Example A：误判 prd-exception → continue

```
背景：BUG-009（API 性能 200ms 偶发超时），bug-triage 判 root_cause=prd-exception
incident-start 触发，workflow-evolution 接管

§3 Root Cause Analysis:
  3.1 Affected PRD Section: §4.2 NFR "API 响应 ≤ 200ms 99% 请求"
       Defect Nature: 看起来 PRD NFR 不可达
       Evidence: BUG-009 显示 5% 请求超 200ms
  3.2 Should Have Been Caught At: 看似 Stage 1 PRD review，但深入分析…
       Why It Wasn't Caught: 测试发现的超时实际只在某个 endpoint（user-export）发生；
                            其他 endpoint 都达标。
  3.3 Is Recurring? No.

深入分析揭示：bug 实际不是 PRD 错，是 user-export endpoint 实现层 N+1 查询问题
              （architecture 已规划好缓存层，development 实现没接缓存）
  → bug-triage 误判 prd-exception；实际是 development 类

§4 Workflow Improvement Suggestions（v0.6 round 3 M4：每条加 Action Item）:
  4.1 Workflow Spec: bug-triage rubric 加"在判 prd-exception 前必须排查 N+1 / cache miss 类
                     单点性能问题"
       优先级：Med
       Action Item: 提交 dev-workflow-skills2 design proposal review cycle
  4.2 Skill: bug-triage SKILL.md root-cause-rubric.md 加 §4.x 例子
       优先级：Med
       Action Item: 提交 dev-workflow-skills2 design proposal review cycle
  （advisory only；禁止 patch/diff/直接编辑 dev-workflow-skills2 文件）

§5 Three Action Evaluation:
  5.1 Continue: 适用（误判修正 + workflow 改进足以避免再发生）；后续创建 BUG-010
              (root_cause=development) 触发新 bug-triage active mode
  5.2 Abort: 不适用（PRD 没问题）
  5.3 Reconstruct: 不适用（不需要从 0 重建）

§6 Recommendation: continue
  Dimensional Evaluation:
    D1 (PRD valid): Yes（NFR 设计合理，实际只在 1 个 endpoint 失败）
    D2 (Implementable): Yes（其他 endpoint 已达 200ms，user-export 接缓存即可）
    D3 (Fixable in current path): Yes（development Change Mode 修 N+1）
    D4 (Workflow improvement effective): Yes（rubric 修订）
    D5 (Sunk cost): N/A
    D6 (Misclassified): **Yes**
  Confidence: high

§7 Resolution（用户决策后填）:
  Decision: continue
  Decision By: user
  Decision Date: 2026-05-16T10:00:00Z
  User Rationale: 同意误判修正
  Resolution Command: progress.py incident-resolve --action continue
  Post-Resolution: 创建 BUG-010 (root_cause=development) 触发新 triage
                  Workflow Improvement: 提交到 dev-workflow-skills2 design proposal cycle

Finalization sequence（v0.6 round 3 L1：示例展示 §1.6 严格序列）:
  6.b 改 frontmatter resolution_action: null → continue
  6.c 改 frontmatter status: draft → review-passed
  6.d 改 frontmatter updated: 2026-05-16T10:00:00Z
  6.e 加 ## Pending Changes entry "incident analysis 完成 + resolution_action=continue"
  6.f changelog.py promote docs/incident/INCIDENT-001.md
  6.g validate.py file docs/incident/INCIDENT-001.md → exit 0
仅在 6.g pass 后才能调 progress.py incident-resolve --action continue：

incident-resolve --action continue:
  → workflow_incident_active=false
  → bug_flow.active=false（清空 bug_flow，原 BUG-009 保留作历史）
  → current_stage=testing, sub_state=review-passed, review_iteration=0
```

### 4.2 Example B：真 prd-exception → reconstruct

```
背景：BUG-009（AI 会议纪要准确率始终 50%，PRD 要求 80%），bug-triage 判 prd-exception
incident-start 触发，workflow-evolution 接管

§3 Root Cause Analysis:
  3.1 Affected PRD Section: §3.1 Core Function "AI 自动生成会议纪要"
       §4.1 NFR "准确率 ≥ 80%"
       Defect Nature: PRD NFR 在任何技术栈都不可达
       Evidence:
         - BUG-009 报告 50 次测试平均准确率 50%
         - 行业 SOTA（GPT-4 + fine-tune）在自然语言任务上限约 60-65%
         - 6 个月内无明确技术突破预测达到 80%
  3.2 Should Have Been Caught At: Stage 1 PRD review
       Why It Wasn't Caught: prd-review 当前 rubric 不含 NFR feasibility 项；
                            review skill 仅评功能完整性 / 一致性，不评技术可行性
  3.3 Is Recurring? No（首次）

§4 Workflow Improvement Suggestions（v0.6 round 3 M4：每条加 Action Item）:
  4.1 Workflow Spec: prd-review §X.Y rubric 加 NFR feasibility check
       优先级：High
       Action Item: 提交 dev-workflow-skills2 design proposal review cycle
  4.2 Skill: prd-review SKILL.md 加 NFR rubric subsection
       优先级：High
       Action Item: 提交 dev-workflow-skills2 design proposal review cycle
  4.4 Review Rubric: 加"列出每个 NFR 的当前技术上限 + 投资估算"checklist
       优先级：High
       Action Item: 提交 dev-workflow-skills2 design proposal review cycle
  （advisory only；禁止 patch/diff/直接编辑 dev-workflow-skills2 文件）

§5 Three Action Evaluation:
  5.1 Continue: 适用条件不满足（修 SRS 把 80% 降到 50% 会让产品价值消失，PRD 仍 invalid）
       不推荐
  5.2 Abort: 部分适用
       - PRD 描述的产品（"AI 替代人写纪要"）在当前技术不可达
       - 但产品方向（AI 辅助会议记录）仍有用户价值
       不是 D1=No；不推荐 abort
  5.3 Reconstruct: 适用
       - D1=Yes（"AI 辅助会议记录"方向有效）
       - D2=Yes（混合策略 "AI 起草 + 人工校对" 可达 80%）
       - D3=scratch（架构改混合策略，需要新 review/edit workflow，几乎重建）
       推荐

§6 Recommendation: reconstruct
  Dimensional Evaluation:
    D1: Yes（产品方向有效）
    D2: Yes（混合策略可实现）
    D3: scratch（混合策略架构与单纯 AI 完全不同）
    D4: Yes（workflow 改进会避免再判 prd-exception 但根因是 PRD 设计错，不是工作流错）
    D5: 用户判断
    D6: No（bug-triage 判定正确，确实是 PRD 异常）
  Confidence: high
  Alternative: 若用户判定混合策略不符产品定位（必须纯 AI）→ abort

§7 Resolution（用户决策后填）:
  Decision: reconstruct
  Decision By: user
  Decision Date: 2026-05-16T10:00:00Z
  User Rationale: 接受混合策略；准备起新 S3 project
  Resolution Command: progress.py incident-resolve --action reconstruct
  Post-Resolution:
    - 本 project 进 reconstructing 终态
    - 用户起新 S3 project (new-meeting-notes-hybrid)，引用本 project 作 source system
    - 新 project Stage 1/2 强制源系统分析

Finalization sequence（v0.6 round 3 L1）:
  6.b 改 frontmatter resolution_action: null → reconstruct
  6.c 改 frontmatter status: draft → review-passed
  6.d 改 frontmatter updated: 2026-05-16T10:00:00Z
  6.e 加 Pending entry "incident analysis 完成 + resolution_action=reconstruct"
  6.f changelog.py promote docs/incident/INCIDENT-001.md
  6.g validate.py file docs/incident/INCIDENT-001.md → exit 0
仅在 6.g pass 后调 progress.py incident-resolve --action reconstruct：

incident-resolve --action reconstruct:
  → project_state=reconstructing, release_state=closed
  → release_close_reason="incident-reconstruct"
  → current_stage=null（终态）
```

### 4.3 Example C：抽离失败 → abort

```
背景：BUG-015（产品定位为"独立创业者管理工具"，但所有 beta 用户反馈"完全用不上"），
     bug-triage 判 prd-exception
incident-start 触发，workflow-evolution 接管

§3 Root Cause Analysis:
  3.1 Affected PRD Section: §1 Product Definition / §2 Target Users
       Defect Nature: PRD 假设的目标用户群（独立创业者）与实际反馈错配
       Evidence:
         - 30 位 beta 用户反馈：22 位"功能不需要"、8 位"操作复杂"
         - 假设场景"每天记录 OKR" → 实际用户每周记 1 次
  3.2 Should Have Been Caught At: Stage 1 PRD review（用户研究阶段）
       Why It Wasn't Caught: PRD 假设基于创始人个人经验，未做用户访谈；
                            人 gate 当时也未提出此 risk
  3.3 Is Recurring? Check: 本 release 第 2 次此类反馈（之前 release 也有但未升级）
       → Yes，是 known pattern

§4 Workflow Improvement Suggestions（v0.6 round 3 M4：每条加 Action Item）:
  4.1 Workflow Spec: Stage 1 PRD Inception 加 "用户访谈 / beta validation" 必备 artifact
       优先级：High
       Action Item: 提交 dev-workflow-skills2 design proposal review cycle
  4.4 Review Rubric: prd-review 加"PRD 假设是否有真实用户数据支撑"check
       优先级：High
       Action Item: 提交 dev-workflow-skills2 design proposal review cycle
  （advisory only；禁止 patch/diff/直接编辑 dev-workflow-skills2 文件）

§5 Three Action Evaluation:
  5.1 Continue: 不适用（修 PRD 描述无法解决"用户根本不需要"）
  5.2 Abort: 适用
       - D1=No（产品方向无效，目标用户根本不需要）
       - 修 PRD 改用户群本质上是 D1=No → reconstruct？
       但用户反馈表明：连"独立创业者管理工具"这个 category 是否有市场都不确定
       推荐 abort
  5.3 Reconstruct: 部分适用
       - 如果用户判定换目标用户群（如"中小团队管理工具"）有价值 → reconstruct
       - 如果用户判定整个 category 无价值 → abort

§6 Recommendation: abort
  Dimensional Evaluation:
    D1: No（目标用户群与产品错配，且不知道哪个用户群可行）
    D2: N/A
    D3: N/A
    D4: Yes（workflow 改进可避免下次再做用户群假设错的 PRD）
    D5: 用户判断
  Confidence: medium（依赖用户对市场判断）
  Alternative: 若用户判定换目标用户群可行（基于额外用户研究）→ reconstruct

§7 Resolution（用户决策后填）:
  Decision: abort
  Decision By: user
  Decision Date: 2026-05-20T10:00:00Z
  User Rationale: 30 用户反馈足够说明定位错；不再投入；先做用户研究再考虑新 project
  Resolution Command: progress.py incident-resolve --action abort
  Post-Resolution:
    - 本 project terminal (aborted)
    - 用户做用户研究后可能起新 project（独立流程，不在本 incident scope）
  Workflow Improvement Items: §4 提交 dev-workflow-skills2 design proposal cycle

Finalization sequence（v0.6 round 3 L1）:
  6.b 改 frontmatter resolution_action: null → abort
  6.c 改 frontmatter status: draft → review-passed
  6.d 改 frontmatter updated: 2026-05-20T10:00:00Z
  6.e 加 Pending entry "incident analysis 完成 + resolution_action=abort"
  6.f changelog.py promote docs/incident/INCIDENT-002.md
  6.g validate.py file docs/incident/INCIDENT-002.md → exit 0
仅在 6.g pass 后调 progress.py incident-resolve --action abort：

incident-resolve --action abort:
  → project_state=aborted, release_state=closed
  → release_close_reason="incident-abort"
  → current_stage=null（终态）
```

---

## 5. Retrospective Consumption Mode Output Format

retrospective consumption mode 不写 doc，只输出 conversation。模板：

```markdown
# Workflow Evolution Analysis (Release X.Y / Cross-Release)

> **Advisory Notice**（v0.6 round 3 M4：与 incident mode advisory/patch 边界一致）：
> 本输出由 workflow-evolution skill 在 retrospective consumption mode 下产出。
> 仅 advisory 自然语言建议；**禁止**输出 patch / diff / unified diff，**禁止**直接编辑
> dev-workflow-skills2 自身文件（递归悖论防的是 patch，不是建议）。
> 每条建议尾部必须含 Action Item 列，标 "提交 dev-workflow-skills2 design proposal review cycle"。
>
> **No-Suggestion Legitimacy**（v0.6 round 3 L2）：如某类（spec / skill / template / rubric）
> 经分析后**无 actionable 建议**，对应 table 必须填一行 `None — no actionable suggestion found`，
> **不要为了凑表格而编造低价值或假阳性建议**。质量 > 数量。

## 1. Context

- Analysis scope: <release X.Y / 跨 release [...] / 跨 incident [...]>
- Input docs:
  - retrospective.md (chapters: ...)
  - progress-history.md (range: ... to ...)
  - INCIDENT-* (count: N)
  - BUG-* (count: M, root_cause distribution: ...)

## 2. Patterns Observed

### 2.1 Recurring Patterns (跨多次出现)

| Pattern | 出现次数 | 涉及 release / stage |
|---------|---------|--------------------|
| <例：review iteration 反复达 5+ 次> | 3 | release 0.2 SRS, release 0.3 Architecture, release 0.4 SRS |
| ... | ... | ... |

### 2.2 Single-Occurrence Notable Patterns

- <例：Stage 4 development 中 T3 反复 fail，最终发现是测试环境问题而非代码问题>
- ...

## 3. Workflow Spec Suggestions

| 改进点 | 目标章节 | 建议改动 | 优先级 | Action Item |
|--------|---------|---------|--------|-------------|
| <例：review iteration 接近上限时 workflow-protocol 自动 trigger 升级提醒（不只是 reject）> | workflow-protocol §8 Review Loop | 加 review_iteration ≥ 6 时输出升级 hint | High | 提交 dev-workflow-skills2 design proposal review cycle |
| ... | ... | ... | ... | 提交 dev-workflow-skills2 design proposal review cycle |

## 4. Skill Suggestions

| 改进点 | 目标 skill | 建议改动 | 优先级 | Action Item |
|--------|-----------|---------|--------|-------------|
| <例：srs-review 加 NFR feasibility rubric> | srs-review | §X. Review Rubric 加 NFR feasibility 子项 | High | 提交 dev-workflow-skills2 design proposal review cycle |
| ... | ... | ... | ... | 提交 dev-workflow-skills2 design proposal review cycle |

## 5. Template Suggestions

| 改进点 | 目标 doc type | 建议改动 | 优先级 | Action Item |
|--------|-------------|---------|--------|-------------|
| <例：detailed-design 加测试环境依赖必备章节> | detailed-design | 加 §X "测试环境依赖" 必备章节 | Med | 提交 dev-workflow-skills2 design proposal review cycle |
| ... | ... | ... | ... | 提交 dev-workflow-skills2 design proposal review cycle |

## 6. Review Rubric Suggestions

| 改进点 | 目标 review skill | 加 / 改 rubric | 优先级 | Action Item |
|--------|----------------|---------------|--------|-------------|
| ... | ... | ... | ... | 提交 dev-workflow-skills2 design proposal review cycle |

## 7. Caveat

- 本输出仅 advisory；不会自动改 workflow / skill / template
- 改进建议落地路径：
  (a) 在下次 retrospective.md 加"Workflow Improvements"章节（由 retrospective-write 在 Stage 7 Change Mode 处理）
  (b) 跨 project 复盘后，去 dev-workflow-skills2 仓库走 **独立 design proposal review cycle**
- workflow-evolution **不**直接修改 dev-workflow-skills2 自身文件（递归悖论）
- 不输出 patch / diff / unified diff；只输出自然语言 advisory 建议
```

输出后 workflow-evolution 退出，不调任何 progress.py 命令（retrospective consumption 是只读）。

---

## 6. 与 root-cause-rubric.md 的对比

| 视角 | bug-triage root-cause-rubric.md | workflow-evolution incident-analysis-template.md |
|------|--------------------------------|------------------------------------------------|
| 时机 | 进 Bug Flow 之前（active mode 4 类分类）| 进 incident state 之后（仅 prd-exception 类）|
| 输出 | 4 类根因 enum | 3 action 决策 + INCIDENT body |
| 数据来源 | BUG report + SRS + Architecture + Detailed Design | 上述 + PRD + 历史 INCIDENT + retrospective |
| 决策权 | bug-triage 判定 + 用户二次确认 prd-exception | 用户最终决策 3 action |
| 影响 | 切 current_stage（bug-start）或进 incident state（incident-start）| 退出 incident state（continue）或 project terminal（abort/reconstruct）|
| 修改 doc | 写 BUG.frontmatter.root_cause | 写 INCIDENT.body §3-§7 + frontmatter resolution_action |

---

## 7. ID 计算（INCIDENT-NNN）

INCIDENT ID 由 `bug-triage` 创建 skeleton 时计算（不在本 reference 范围）。workflow-evolution 仅引用既有 ID，不再计算。

如果 bug-triage 计算 ID 失败（如 docs/incident/ 不存在），workflow-evolution 不应自创 ID，而是退出并提示 bug-triage 重试。

---

**End of Incident Analysis Template**
