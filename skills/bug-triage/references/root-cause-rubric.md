# bug-triage Root Cause Classification Rubric

**配套**：`skills/bug-triage/SKILL.md`

本 reference 提供 4 类根因（`srs` / `architecture` / `development` / `prd-exception`）的详细判定 heuristic、关键问句、典型例子、多根因优先级、边界处理。仅适用于 **active mode**（post-close mode 不分类 root_cause）。

---

## 1. 顶层决策树

```
观察 bug 现象 + 重现步骤 + 影响范围
  ↓
读 PRD（如怀疑 prd-exception）/ SRS / Architecture / 相关 detailed_design
  ↓
按以下 4 道问句**严格序列**判定（不跳跃 / 不合并 / 不并行）：

Q1（产品级判定）：bug 是否表明产品方向 / 用户故事 / 关键功能集**本身有问题**？
  ├ Yes → root_cause = prd-exception（异常路径）
  └ No  → 进 Q2

Q2（需求级判定）：bug 是否表明 SRS 中的功能描述 / NFR / 接口契约**错误或缺失**？
  ├ Yes → root_cause = srs
  └ No  → 进 Q3

Q3（架构级判定）：bug 是否表明架构层有缺陷（组件划分 / 数据流 / 跨服务契约 / 模块边界）？
  ├ Yes → root_cause = architecture
  └ No  → 进 Q4

Q4（实现级兜底）：bug 是否在 detailed_design 已正确指定的实现层 deviate？
  → root_cause = development
```

**严格顺序**的理由：取最上层根因。修上层（如 SRS 加 IE11 兼容性需求）会自动触发下层修复（development 加 polyfill）；只修下层不修上层会留下"再次踩坑"隐患。

---

## 2. 各类根因详细 Heuristic

### 2.1 `prd-exception`（异常路径，高警惕性）

**含义**：PRD 描述的产品本身存在不可调和的问题，无法通过修 SRS / Architecture / Development 解决。

**触发信号**（满足**任一** + 高确信度）：

- 产品定位与目标用户群根本错配（实际用户根本不需要此功能 / 此用户群不是产品对象）
- 关键功能集之间存在**逻辑冲突**（PRD A 章要求 X，B 章要求 not X，二者无法同时成立）
- 产品边界 / 范围在工作流推进过程中**反复振荡**（多次 release 都触及同一边界争议）
- 关键功能在任何技术栈选择下都**无法可行实现**（不是性能慢，是 fundamentally 做不到）
- 用户使用场景与 PRD 假设**完全不符**（如假设用户在 PC 但实际全是手机使用）

**关键问句**：

| 问句 | Yes 暗示 prd-exception |
|------|----------------------|
| 「修 SRS / Architecture / Development 任一层能让 bug 消失吗？」 | **No** 暗示 prd-exception |
| 「这个 bug 是否质疑 PRD 描述的产品方向 / 用户故事？」 | **Yes** 暗示 prd-exception |
| 「PRD 的关键功能集之间是否存在逻辑矛盾？」 | **Yes** 暗示 prd-exception |
| 「再过 1-2 个 release，这类 bug 是否还会以变种形式重现？」 | **Yes** 暗示 prd-exception |

**反例（不是 prd-exception）**：

| 现象 | 真实根因 | 理由 |
|------|---------|------|
| "PRD 漏掉某个功能（如 IE11 兼容）" | `srs` | PRD 不需要列举所有兼容性细节；属 SRS 层补充 |
| "PRD 与 SRS 不一致" | `srs` 或 `architecture` | 修一致即可，PRD 本身没错 |
| "PRD 选了错误技术栈" | 通常是 `architecture`；除非技术栈使产品**根本无法实现** | 多数情况换技术栈即可 |
| "PRD 写得不清楚" | `srs` | SRS 应展开细化；不清楚不等于错 |

**警告**：`prd-exception` 触发后会进入 incident analysis，可能导致 project abort/reconstruct。**绝不轻判**。bug-triage 在判定 prd-exception 前**必须与用户对话二次确认**。

### 2.2 `srs`（需求级）

**含义**：SRS 中的功能描述、非功能需求 (NFR)、验收准则、接口契约存在错误、缺失、不一致。修复需要 SRS Change Mode 重新定义需求。

**触发信号**（满足**任一**）：

- SRS 没有覆盖 bug 暴露的场景（功能描述缺失）
- SRS NFR 设定不合理（性能 / 兼容性 / 安全 等指标错误）
- SRS 中两段功能描述相互矛盾
- 接口契约（函数签名 / API endpoint / 数据 schema）描述错或不完整
- 验收准则不足以判定 bug 行为是否符合预期
- bug 暴露的需求层面缺失（如未提及边缘 case 处理 / error path / 输入校验规则）

**关键问句**：

| 问句 | Yes 暗示 srs |
|------|------------|
| 「SRS 是否覆盖了 bug 触发场景？」 | **No** 暗示 srs |
| 「SRS 是否对 bug 行为给出明确验收准则？」 | **No** 暗示 srs |
| 「SRS 中是否存在与 bug 行为冲突的两段描述？」 | **Yes** 暗示 srs |
| 「修 detailed_design / 代码能 silently 解决 bug，还是需要先在 SRS 加新需求？」 | 后者 → srs |

**典型例子**：

| 现象 | 为什么是 srs |
|------|-------------|
| 登录在 IE11 崩溃 | SRS 漏掉 IE11 兼容性需求 |
| 性能指标 200ms 但实际无法达到（硬件限制下）| SRS NFR 设定不合理 |
| 接口字段 `user_id` 在两段描述中类型不一致（int vs string）| SRS 接口契约不一致 |
| 注册流程对 email 不去重 | SRS 漏掉 unique constraint 描述 |
| 错误码集合在 SRS 不完整，导致 client 无法识别新错误 | SRS 错误码列表缺失 |
| 数据导出时格式不统一（CSV/JSON 选哪个）| SRS 未明确产物格式 |

### 2.3 `architecture`（架构级）

**含义**：架构层的组件划分、服务边界、数据流、消息拓扑、缓存策略等存在缺陷。SRS 没问题但架构无法支撑该需求。修复需要 Architecture Change Mode（产生 architecture_delta.md）。

**触发信号**（满足**任一**）：

- 服务划分把强耦合数据放在多个服务（导致跨服务一致性 bug）
- 数据流方向错（如 read-after-write 一致性问题、事件顺序问题）
- 缓存层导致一致性 bug（缓存失效策略错）
- 消息队列拓扑错（消息重复 / 顺序错 / 丢失）
- 模块边界划分使某需求无法在单模块内完成
- 依赖方向错（A 依赖 B，但 B 也依赖 A，导致循环 / 启动顺序问题）
- 共享资源策略错（数据库连接池 / 锁粒度等架构层决定）
- 部署拓扑导致网络分区下的可用性问题

**关键问句**：

| 问句 | Yes 暗示 architecture |
|------|---------------------|
| 「SRS 中需求清晰且正确，但当前架构无法满足？」 | **Yes** 暗示 architecture |
| 「修代码 / detailed_design 不够，需要重新规划组件边界？」 | **Yes** 暗示 architecture |
| 「bug 是否跨多个服务 / 模块的协作问题？」 | **Yes** 强烈暗示 architecture |
| 「修复需要新增 / 移除组件 or 改变数据流方向？」 | **Yes** 暗示 architecture |

**典型例子**：

| 现象 | 为什么是 architecture |
|------|---------------------|
| 用户资料服务和订单服务之间数据不一致 | 架构把强耦合数据划到两个服务 |
| Redis 缓存与 DB 之间偶发不一致 | 缓存失效策略架构层错 |
| 消息队列偶发重复消费导致重复扣款 | 消息拓扑没考虑 idempotent；架构层缺重试策略 |
| 服务启动时循环依赖导致 deadlock | 架构层依赖方向错 |
| 高并发下数据库连接池耗尽 | 架构层连接池规模 / 共享策略错 |
| 单点模块成为瓶颈，无法横向扩展 | 架构层 stateless / sharding 策略错 |

### 2.4 `development`（实现级，默认兜底）

**含义**：SRS 与 Architecture 都正确，bug 出在实现层（detailed_design 或 source code 或 unit/integration test）的 deviate。修复需要 development Change Mode（development-planning-write 或 development-test-write 或 development-code-write Change Mode）。

**触发信号**（满足**任一**）：

- 实现 bug：空指针 / 边界条件 / 拼写错 / 类型错 / 错误处理遗漏
- 代码不符合 detailed_design（design 正确，code 没按 design 写）
- 测试遗漏 case（test 没覆盖 bug 触发的输入）
- 单元测试 / 集成测试 fail 但 SRS / Architecture 正确
- 第三方库 API 用错
- 并发 bug（race condition / deadlock）但架构层没设计错
- 性能慢但 SRS / Architecture 都正确（实现可优化）

**关键问句**：

| 问句 | Yes 暗示 development |
|------|--------------------|
| 「SRS 描述的功能是否完整正确？」 | Yes 排除 srs |
| 「Architecture 是否能支撑此需求？」 | Yes 排除 architecture |
| 「detailed_design 是否描述了此实现细节？」 | Yes → 实现层 deviate（development）|
| 「修复是否只需改 source code / test，无需改 design / arch / SRS？」 | **Yes** 强烈暗示 development |

**典型例子**：

| 现象 | 为什么是 development |
|------|--------------------|
| 登录失败时返回 500 而不是 401 | 错误处理实现错（SRS 已规定返回 401）|
| 列表分页 offset 计算错 | 边界条件 bug |
| 字符串转换没考虑空字符串 | 实现层缺 null check |
| 测试 case 缺覆盖某 input | development-test 层遗漏 |
| 并发场景下计数器值偶尔错 | race condition（架构没强制 single-threaded，实现层用了非原子操作）|
| 内存泄漏 | 实现层资源管理 bug |
| 字段 lint warning 但功能正常 | 实现层代码质量问题 |

---

## 3. 多根因优先级（取最上层）

如 bug 同时具备多类信号，按 **prd-exception > srs > architecture > development** 取最上层。

### 3.1 优先级理由

修最上层根因后，下层会**自然要求**重新设计 / 实现：

```
修 SRS（加 IE11 需求）
  ↓ 触发
detailed_design 重新设计（加 polyfill 章节）
  ↓ 触发
source code 修改（加 polyfill 实现）
  ↓ 触发
test 加 IE11 用例
  ↓
回 Stage 5 retest
```

只修最下层（直接加 polyfill 而 SRS 不动）会留下两个问题：
- **可追溯性**：下次有人读 SRS 不知道有 IE11 需求
- **再现风险**：下次需求触及 IE11 时，SRS 仍然是错的，再次踩同一坑

### 3.2 多根因例子

| 现象 | 多类信号 | 取哪一层 | 理由 |
|------|---------|---------|------|
| 登录在 IE11 崩溃 | SRS 漏需求 + 实现没 polyfill | **srs** | 修 SRS 才能从根上解决 |
| 服务间数据不一致 + 实现层 race condition | architecture + development | **architecture** | 数据划分错才是根；race 是次生问题 |
| 性能 NFR 不合理 + 实现层未优化 | srs + development | **srs** | 先修 NFR，再决定是否需要优化 |
| 产品方向错 + 全栈 bug 一堆 | prd-exception + 多层 | **prd-exception** | 项目方向先定，再谈实现 |
| 接口契约 SRS 错 + 实现按错的契约写 | srs + development | **srs** | 修契约才能让 client/server 对齐 |

### 3.3 反例：不应取上层的情况

| 现象 | 看似上层但实际下层 | 真实根因 |
|------|------------------|---------|
| 登录 500 错误（SRS 已规定 401，实现错）| 不是 srs（SRS 已对）| **development** |
| 性能慢（SRS 200ms 合理，实现层 N+1 查询）| 不是 srs（NFR 合理）| **development** |
| 缓存没生效（架构已规定缓存层，实现没接缓存）| 不是 architecture（架构对）| **development** |

判定时**先确认上层是否真的错**，再决定是否取上层。如果上层正确，则下层的实现 deviate 才是根因。

---

## 4. 边界情况

### 4.1 PRD/SRS/Architecture 都在写但还没 review-passed

bug-triage 仅在 testing 阶段（Stage 5）触发，此时 PRD/SRS/Architecture 都已 approved（gated stage 已过人确认）。理论上 bug-triage 不会在前序 stage 内被调用。

异常路径：若 bug 在 Stage 4 development 自验证时被发现（非 Stage 5），按现有设计这不算 Bug Flow（development 自身处理），不进 bug-triage。bug-triage **仅响应 Stage 5 testing 触发的 bug**。

### 4.2 retest 后 bug 仍存在 / 派生新 bug

`bug-close` 前若 retest 仍 fail，testing-write 会写新 BUG report；新 BUG 走新一轮 bug-triage（可能 root_cause 同也可能不同）。

允许重 triage 同一现象（不同 BUG ID）。每次 triage 独立判定，不继承上次判定。

### 4.3 PRD exception 误判

如果 bug-triage 判 prd-exception 后，workflow-evolution 在 incident analysis 中发现实际是 srs / architecture / development 层问题，处理：

- 用户调 `incident-resolve --action continue` 退出 incident state（清空 bug_flow + workflow_incident，回到 testing review-passed）
- 若用户判定原 bug 仍需修复，**创建新 BUG-MMM.md**（new ID）触发新一轮 bug-triage
- 新一轮 bug-triage 重新判定 root_cause（应判 srs/architecture/development，不应再判 prd-exception）

**不允许**修改原 BUG-NNN.md 的 root_cause（保留 prd-exception 作历史记录，避免 reclassification 状态污染）。

### 4.4 testing-write 写的 BUG 描述不充分

bug-triage 在 active mode 进入时若发现 BUG-NNN.md body 信息不足（无重现步骤 / 影响范围 / 期望 vs 实际），应：

1. 拒绝立刻分类
2. 与用户对话补充信息
3. 由 testing-write 在 BUG report 加 Pending Changes + changelog promote
4. 重 invoke bug-triage（此时 BUG.root_cause 仍 null，重新走分类）

不要**凭模糊描述硬分类**。

### 4.4a Active mode 强制 4 类输出（v0.6 round 2 batch2-F3）

bug-triage active mode **必须**从 {srs, architecture, development, prd-exception} 中选 1 个写入 BUG-NNN.md frontmatter `root_cause`；不允许：

- 留 `root_cause: null` 后调 `progress.py bug-start`（progress.py 会拒绝；bug-start 要求 `--root-cause` 参数 ∈ 三类，与 frontmatter 一致校验）
- 写第五种值（如 `out-of-scope` / `rejected` / `documented` / `closed`）—— `bug-report` schema 没有该 enum，doc-guardian validate.py 会拒绝
- silently 关闭 BUG report（bug-triage 没有"关闭 BUG"的 progress.py 子命令；bug_flow 此时未启动）

**如果 bug-triage 判定 BUG 不在 SRS 范围内 / 反馈不属于产品方向**：

- 与用户对话升级决策（参 Example D in §7.4）：
  1. 用户希望扩 SRS 接收该需求 → root_cause = `srs`，下游 srs-write Change Mode
  2. 用户判定 BUG 应撤销 → 用户**手动删除** `docs/bug/BUG-NNN.md` 文件（bug-triage 无权撤销）；删除后 bug-triage 退出，不调 progress.py
  3. 用户判定触及产品方向问题 → root_cause = `prd-exception`，走 incident analysis

- bug-triage 等用户决策；不擅自做"out-of-scope"判断。

**为什么不引入 out-of-scope 状态**：早期设计考虑过加第五状态，但需要扩 `bug-report` schema 加 `triage_status` 字段 + 加 `progress.py bug-reject` 子命令 + 改 doc-guardian validate.py；这是 batch 1 已闭环的 design 层改动，不在 batch 2 引入。bug-triage 强制 4 类是设计选择，不是限制。

### 4.5 跨多个 task 的 bug

如果 bug 涉及多个 Stage 4 task（如 T1 + T3 都有问题），bug-triage 在 BUG-NNN.md body 标注**所有 affected tasks**：

```markdown
## Triage Analysis

**Root Cause**: development
**Affected Task(s)**: T1, T3
**Rationale**: bug 涉及登录服务 (T1) 与会话管理 (T3) 协作问题；
            两个 task 的 detailed_design 各自正确，但 integration 处实现错。
```

development Change Mode 时由 development-planning-write 决定如何 breakdown 修复（可能需新增 task 或调整既有 task）。

### 4.6 跨多个 release 的回归 bug（regression）

post-close 期间发现的 bug 可能是跨 release regression（之前 release 工作正常，本 release 引入回归）。处理：

- post-close mode 不分类（按 §4.3 of SKILL.md）
- BUG report body 应注明 "regression from release X.Y"
- 下次 release-start 时由 srs-write 决定是否需要在新 SRS 加 regression 测试覆盖

### 4.7 SRS 与 Architecture 都需要改

若 bug 同时暴露 SRS 漏需求 + Architecture 不支撑（如新加一个跨服务事务需求且架构没设计）：

- 取上层 `srs`（先 SRS 加需求）
- SRS Change Mode 完成后，回 Stage 5 retest
- retest 仍 fail 时再次 bug-triage，此时 SRS 已对，剩 architecture 问题 → 第二轮判 architecture
- architecture Change Mode 完成 → 再次 retest

允许同一 bug 在 Bug Flow 中走**两次** bug-triage（每次创建 BUG-NNN.md，新 ID），逐层修复。

### 4.8 development 根因下的 task 定位失败

如果 bug-triage 判 development 但**无法准确定位**到具体 task：

- 在 BUG body 注明 "Affected Task(s): unable to localize"
- development Change Mode 进入后由 development-planning-write 重新 breakdown 定位
- 不要为了"看起来精确"乱猜 task ID

### 4.9 bug 实际是测试本身错（test bug）

少数情况：bug 是 test 写错（不是 source code 错）。归类：

- 仍是 `development`（test 在 Stage 4 development-test 阶段产出，属 development 层）
- BUG body 注明 "Likely Cause: test code error in T<n> integration tests"
- development Change Mode → development-test-write 修 test 而非修 source code

---

## 5. 决策辅助：信号强度评分（可选，仅供 AI 参考）

bug-triage 在拿不准时可用**信号强度评分**辅助决策（不是硬规则，仅参考）：

| 信号 | prd-exception | srs | architecture | development |
|------|--------------|-----|-------------|------------|
| bug 修复需要改产品方向 | +5 | -5 | -5 | -5 |
| bug 修复需要重新定义功能集 | +3 | +1 | -1 | -3 |
| bug 修复需要在 SRS 加新需求 / 改需求 | -1 | +5 | -1 | -3 |
| bug 修复需要 NFR 重新设定 | 0 | +5 | -1 | -2 |
| bug 修复需要重新规划组件边界 | -1 | -1 | +5 | -3 |
| bug 修复需要改数据流方向 | -1 | -1 | +5 | -3 |
| bug 修复需要新增 / 移除组件 | -1 | -1 | +5 | -3 |
| bug 修复只需改 source code / test | -3 | -3 | -3 | +5 |
| bug 是边界条件 / null / 拼写 | -3 | -3 | -3 | +5 |
| bug 是测试遗漏 case | -3 | -3 | -3 | +5 |

取**最高分**类别作为根因。若两类同分，按 prd-exception > srs > architecture > development 优先级取上层。

**警告**：评分仅是 AI 辅助；最终判定必须基于对 bug 的**具体分析**，不是纯统计。bug-triage 在 BUG body Triage Analysis 段必须给出**自然语言 rationale**，不应该说"基于评分系统"。

---

## 6. Triage Analysis Body 模板

bug-triage 在 BUG-NNN.md body 必须加 `## Triage Analysis` 章节：

```markdown
## Triage Analysis

**Root Cause**: <prd-exception | srs | architecture | development>
**Affected Doc/Module**:
  - SRS: <如有，章节引用，例 "Section 3.2 登录功能">
  - Architecture: <如有，组件名>
  - Detailed Design: <如有，task ID + 文件路径>
  - Source Code: <如有，文件路径>
**Affected Task(s)**: <T1, T3 | "unable to localize" | N/A>
**Rationale**:
  <2-5 句自然语言：bug 现象 → 哪层判定为根因 → 为何不是其他层>

**Confidence**: <high | medium | low>
**Alternative Hypothesis**: <如 confidence != high，列其他可能根因 + 排除理由>

**Next Step**:
  - root_cause ∈ {srs, architecture, development}: 调用 progress.py bug-start
  - root_cause == prd-exception: 创建 INCIDENT skeleton + 调用 progress.py incident-start
```

`Confidence: low` 时 bug-triage 应**先与用户对话二次确认**再调 progress.py（避免错误分流到下游 stage）。

---

## 7. 端到端 Triage Examples

### 7.1 Example A：经典 srs 类

```
BUG-005 现象：登录在 IE11 浏览器崩溃，所有 JS 报错
SRS 检查：未提及 IE11 兼容性
Architecture 检查：合理
Detailed Design 检查：未提 polyfill
Source Code 检查：用了 ES2017 spread operator

Q1（prd-exception?）：No（修 SRS 加兼容性即可解决，产品方向不变）
Q2（srs?）：Yes（SRS 漏需求）
Q3（architecture?）：N/A（已判 srs）

→ root_cause: srs
→ 调 progress.py bug-start --bug docs/bug/BUG-005.md --root-cause srs
→ srs-write Change Mode 接管，加 IE11 兼容性需求 + 验收准则
```

### 7.2 Example B：经典 architecture 类

```
BUG-006 现象：用户资料服务与订单服务数据偶发不一致（用户改邮箱后订单显示旧邮箱）
SRS 检查：要求"修改资料后立即生效"，描述清楚
Architecture 检查：用户服务 / 订单服务两边各存一份 email；改用户服务时未通知订单服务

Q1（prd-exception?）：No
Q2（srs?）：No（SRS 已对）
Q3（architecture?）：Yes（强耦合数据放两服务，无 sync 机制）

→ root_cause: architecture
→ 调 progress.py bug-start --root-cause architecture
→ architecture-write Change Mode 接管，写 architecture_delta.md
```

### 7.3 Example C：经典 development 类

```
BUG-007 现象：注册时 email 未做格式校验，"abc" 也能注册
SRS 检查：第 4.2 节要求 "email 必须符合 RFC 5322"
Architecture 检查：合理
Detailed Design 检查：T2 task 已明确 "在 controller 层调 isValidEmail()"
Source Code 检查：T2 实现忘记调 isValidEmail()

Q1（prd-exception?）：No
Q2（srs?）：No
Q3（architecture?）：No
Q4（development）：Yes（design 已规定，code 没按 design 写）

→ root_cause: development
→ Affected Task: T2
→ 调 progress.py bug-start --root-cause development
→ development-code-write Change Mode 接管 T2
```

### 7.4 Example D：可疑 prd-exception 但实际是用户反馈"超出 SRS 范围"——dispatcher 层应拦截，不进 active triage（v0.6 round 2 batch2-F3）

```
BUG-008 现象：用户反馈"我们公司不允许用 Google 账号登录"
SRS 检查：明确要求 "Google OAuth 单一 SSO"
PRD 检查：定位 "面向通用消费者"，没提企业市场

理想路径（应在源头拦截）：
  - testing-write 在 Stage 5 跑测试时，只对 SRS 已规定的范围生成测试用例
  - "企业用户禁用 Google 登录"不在 SRS 范围 → 测试根本不会触发该现象
  - 此类反馈通常来自外部用户/产品反馈渠道；不是 testing 内部 bug
  - 应在 dispatcher 层（用户主动报"功能"类反馈）走 S2-1/S2-3 子场景判定，
    决定是否扩 SRS / 改 PRD，而不是创建 BUG report

实际情况（如果 BUG-008 已被错误地创建 + 进入 bug-triage active mode）：
bug-triage **必须**在 4 类之中选一个；不接受第五种"out-of-scope"状态。
  Q1: prd-exception？取决于"用户反馈是否要求扩展产品到企业市场"
    - 如果是 → root_cause = prd-exception（这是 PRD 定位与用户群的根本性问题）
    - 如果否（只是个别非目标用户的反馈）→ 升级用户决策

bug-triage 的 escalation 路径（**不**沉默自创第五状态）：
  与用户对话："此 bug 不在 SRS 范围内，无法用 4 类根因合理分类。建议：
  (a) 你是否希望扩展 SRS 增加'禁用 Google 登录的企业方案'需求？
      → root_cause = srs，下游 srs-write 在 Change Mode 加新需求
  (b) 你是否判定这反馈不在产品方向内（非目标用户群），应**撤销** BUG-008？
      → 用户负责手动删除 docs/bug/BUG-008.md（BUG report 是 testing-write 创建的，
        bug-triage 没有 progress.py 子命令撤销 BUG）
        删除后由 testing-write 在 testing report 注明该反馈被判定为 out-of-scope；
        bug-triage 退出，不调 progress.py，因为 bug_flow 还未启动
  (c) 你是否判定这反馈触及了产品方向问题？
      → root_cause = prd-exception，走 incident analysis
  
  bug-triage 不允许：
  - 自创"out-of-scope" / "rejected" / "documented" 第五状态
  - 在 BUG frontmatter 写非 4 类的 root_cause 值
  - silently 关闭 BUG report（删除责任在用户）
```

注（v0.6 round 2 batch2-F3 收敛）：bug-triage 强制 active mode 输出 4 类之一（srs / architecture / development / prd-exception）；不存在第五种 out-of-scope 状态。如果用户判定 BUG report 不应存在，必须由用户手动删除 BUG-NNN.md（不是 bug-triage 的责任，因为 bug_flow 此刻还未启动）；bug-triage 不调 progress.py，直接退出。早期版本提到的"关闭 BUG report，保留为 documented limitation"路径已废弃——`bug-report` schema 没有承载该状态的字段，progress.py 没有相应子命令，会成为 orphan doc。

### 7.5 Example E：真 prd-exception

```
BUG-009 现象：核心功能"自动生成会议纪要"在 testing 中始终无法达到 SRS 的 80% 准确率要求
深入分析：
  - SRS：要求 80% 准确率
  - Architecture：用了 GPT-4 + 专门 fine-tune 模型
  - Development：实现合理
  - 重测多次：实际平均准确率 50%，且**任何技术栈都达不到 80%**（自然语言任务的根本上限）

Q1（prd-exception?）：Yes
  - 修 SRS 把要求降到 50%? → 但产品定位"AI 替代人写纪要"已不成立（PRD 关键功能）
  - PRD 描述的产品在当前技术下**根本无法实现**

→ root_cause: prd-exception
→ 与用户二次确认："这看起来是 PRD 设定的 80% 不可达，要进入 incident 分析。确认吗？"
→ 用户确认
→ 写 BUG-009 frontmatter root_cause=prd-exception + Triage Analysis（含 Pending entry）
→ changelog.py promote docs/bug/BUG-009.md → validate.py file → pass
→ 创建 INCIDENT-001.md skeleton（triggered_by_bug: BUG-009，含 Pending entry "skeleton 创建"）
→ **changelog.py promote docs/incident/INCIDENT-001.md**（v0.6 round 2 batch2-F1）
→ **validate.py file docs/incident/INCIDENT-001.md → 必须 exit 0**（类 6 Change Log Discipline 要求 Pending 已空）
→ 调 progress.py incident-start --bug docs/bug/BUG-009.md --report docs/incident/INCIDENT-001.md
→ workflow-evolution 接管，分析后用户决策（可能 abort 或 reconstruct，或 continue 改 SRS 降低要求）
```

注（v0.6 round 2 batch2-F1）：早期版本本 Example E 缺 `changelog.py promote` 与 `validate.py file` 步骤，与 SKILL.md §3.1 Step 7d 主流程不一致；本轮同步对齐主契约。

---

## 8. 与 references/triage-decision-tree.md 的协作

本 reference 专注**根因判定**；`triage-decision-tree.md` 专注**双模式入口路由 + 端到端流程**。两者联合：

```
用户报 bug
  ↓
triage-decision-tree.md：判 active mode vs post-close mode
  ↓ active mode
root-cause-rubric.md（本 reference）：判 root_cause（4 类）
  ↓
triage-decision-tree.md：根据 root_cause 决定调 bug-start vs incident-start
```

post-close mode 路径完全在 `triage-decision-tree.md`，不进本 reference。

---

**End of Root Cause Rubric**
