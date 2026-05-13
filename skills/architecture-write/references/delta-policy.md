# Architecture Delta Policy: Main Doc vs Delta Decision

**配套**：`skills/architecture-write/SKILL.md` §3 Full Mode vs Change Mode + Delta 决策 + §7 Bug Flow Re-entry。

本 reference 详细规定 architecture-write 在 S2 / Bug Flow 场景下的决策树：什么时候改主 doc `docs/architecture/architecture.md`、什么时候新建（或改）`docs/release<x.y>/architecture_delta.md`、什么时候**两者同步改**。SKILL.md §3.1 给出核心 2-branch 决策树 + §7.1 Bug Flow 性质表；本文展开决策依据、典型例子、recovery、与 architecture-review 维度 6 配套的校验对照。

---

## 1. 核心决策原则（v0.6 round 1 H3 决议）

**workflow-protocol release-close 不做 delta → 主 doc 自动合并**（事实源 `command-reference.md §5`：release-close 仅 mutate `release_state` / `release_close_reason` / `previous_releases`）。因此：

> **长期事实必须由 architecture-write 在同一轮 write 中同时改 architecture_delta + architecture.md。** 漏写主 doc 的长期事实会导致下个 release 起点错误。

**保守原则**：决策不清时**倾向归类"长期事实"路径**——同步主 doc + delta；让 architecture-review 评审是否过度同步。这比漏写主 doc 风险小：过度同步可在下一轮 revise 移除；漏写主 doc 在下个 release 才会暴露，已经迟了。

---

## 2. 决策树（SKILL.md §3.1 展开）

```
本次改动是否引入运行时架构差异？
（新组件 / 接口变更 / 数据流改变 / 部署拓扑改变 / 数据模型改变）
├ 否 → 仅改 architecture.md（视为文档级修订；如 typo / 描述清晰化）
└ 是 → 进一步判断
        ├ 改动是本 release 局部
        │   （不影响 release close 后下一 release 的"长期架构事实"）
        │   → 仅写 architecture_delta；不动 architecture.md
        │     • 主 doc 保持 release-N-1 状态
        │     • 下次 release 仍以未变的主 doc 为起点
        │     • 本 release 的局部改动作为历史记录留在 release<x.y>/ 目录下
        └ 改动是长期事实
            （下个 release 起点应包含本变化）
            → **同一轮 write 中同时改 architecture_delta + architecture.md**：
              • delta 描述本 release 增量 / 时间线说明
              • architecture.md 反映新长期事实（接口签名 / 组件清单 / 部署假设 已更新）
              • 两份 doc 必须 atomic 同步（同一 §6 4-step 提交）
```

---

## 3. "长期事实" vs "本 release 局部" 判别 heuristic

### 3.1 长期事实信号（满足任一 → 同步主 doc + delta）

| 信号 | 例子 | 为什么是长期事实 |
|------|------|----------------|
| **新增持久组件** | 新增 search service / cache layer / event bus | 下个 release 起点应包含；不是临时方案 |
| **API breaking change** | path / method / required field / response shape 改变 | 客户端必须升级；下个 release 仍是新 API |
| **数据模型 schema 改变** | 新表 / 新字段 / migration | 数据已 migrate，下个 release 起点是新 schema |
| **部署拓扑长期改变** | 单机 → 多实例；云 region 增加；新增 secret store | 运维基线变了 |
| **认证 / 安全模型改变** | OAuth → OIDC；增加 mTLS | 安全基线 |
| **跨 component 契约改变** | 同步调用 → 异步 event；shared DB → API | 系统耦合方式变了 |
| **第三方依赖大类改变** | 切换 message broker；切换搜索引擎 | 技术栈 baseline 变了 |

### 3.2 本 release 局部信号（满足任一 → 仅写 delta；不改主 doc）

| 信号 | 例子 | 为什么是局部 |
|------|------|------------|
| **临时 workaround** | 本 release 临时启用 throttle；下 release 用更好方案替代 | 显式临时；不应进主 doc |
| **试验性 / feature flag** | 本 release 部分用户试 A/B 实验；非默认行为 | 实验性；可能下 release 砍掉 |
| **特定客户定制** | 仅本 release 为客户 X 加的特殊路径 | 不是产品 baseline |
| **monitor / alert 临时调整** | 加临时 alert 排查问题；问题解决后撤 | 短期可观测性变化 |
| **disaster recovery 演练记录** | 演练步骤 / 学习 | 不是架构本身的改动 |
| **测试 / staging 专用配置** | 仅 staging 跑的某个测试 hook | 不影响 prod 架构 |

### 3.3 模糊场景（保守按"长期事实"处理）

| 模糊场景 | 处理 | 后续 |
|---------|------|------|
| 新组件，但可能下 release 整合到既有组件 | 主 doc + delta 同步加；delta body 标注"may consolidate in v<x.y+1>" | architecture-review 决定是否过度 |
| 接口 signature 改但保留 deprecated 旧 signature | 主 doc + delta 同步改；保留 deprecated 注记 | 下 release 删 deprecated 时改主 doc |
| 数据 model 加 nullable field | 主 doc + delta 同步加 | nullable 也是 baseline；不要漏主 doc |
| 部署单元数从 1 → 2（高可用）| 主 doc + delta 同步改 §7.1 | 长期事实 |
| 临时 1 周性能压测特殊配置 | 仅 delta 不动主 doc + delta 标 "rolled back at <date>" | 局部 |

---

## 4. Bug Flow re-entry 决策表（SKILL.md §7.1 展开）

`bug-triage` 判定 `root_cause==architecture` 时切回本 stage。Bug 触发的 doc 改动按 bug 性质分类：

| Bug 性质 | 改 architecture.md | 改 architecture_delta | 备注 |
|---------|---------------------|----------------------|------|
| 主 doc 描述错误（与运行时实现不符）| ✓ | ✗ | 运行时是事实；改主 doc 让其反映；不需 delta（不是本 release 实施改动）|
| delta 描述错误（与本 release 实现不符）| ✗ | ✓ | 仅本 release 范围 |
| 运行时架构有 bug（实现层缺陷反推到设计）| ✓（典型）| ✓ | 长期事实候选；同步两份 doc |
| 集成 / 接口 bug 暴露架构假设错误 | ✓ | ✓ | 长期事实层；下个 release 应基于修订后主 doc |
| 性能 / 容量假设需修订 | ✓ | ✓ | 同上 |
| 临时性能/可用性补丁（不改 design）| ✗ | ✓ | 仅 delta；不动主 doc |
| 安全漏洞修复（改设计）| ✓ | ✓ | 安全基线变了，长期事实 |

**保守路径**（v0.6 round 2 M2 修正）：bug 引发的改动**绝大多数是长期事实**——bug 暴露的架构问题大概率影响下个 release 起点。不确定时按"长期事实"处理，同步主 doc + delta，并在 delta body 标注"需 architecture-review 确认是否过度同步主 doc"。

---

## 5. 同步主 doc + delta 的 4-step 标准操作

### 5.1 顺序（先 delta，再回写主 doc）

```
1. 写 architecture_delta.md（本 release 增量 + §3 Long-Term Fact Sync 表）
   - 在 §3 表中明确每条改动是 long-term 还是 local
2. 对长期事实条目，回写到 architecture.md 对应章节
   - architecture.md §3 Component Catalog 加 / 改 / 删
   - architecture.md §4 Interfaces 改
   - architecture.md §5 Data Flows 改
   - architecture.md §7 Deployment 改
3. 两份 doc 各自加 ## Pending Changes 段
   - delta 加 entry 描述本 release 增量（含 BUG-NNN linkage 如 Bug Flow）
   - 主 doc 加 entry 描述长期事实变化（不写"in release x.y"，只写抽象事实）
4. 各跑 changelog.py promote
5. 各跑 validate.py file
6. 一起调 progress.py update --event write-complete（不允许部分 submit）
```

### 5.2 §3 Long-Term Fact Sync 表的填写规则

每条本 release 改动一行：

| Change | Long-term fact? | Synced to architecture.md? | Notes |
|--------|-----------------|----------------------------|-------|

- **Long-term fact?** 列：yes / no（按 §3.1 vs §3.2 信号决定）
- **Synced to architecture.md?** 列：必须与 Long-term fact? 一致：
  - yes → yes（同步主 doc）
  - no → no（仅 delta）
  - 不一致 → architecture-review 维度 6 blocking
- **Notes** 列：解释决策依据 1-2 句

---

## 6. Pending Changes 与 Change Log 内容差异

### 6.1 delta 的 Pending Changes / Change Log

```markdown
## Pending Changes

- 2026-05-15T10:30:00Z [Section 2.1]: Add component "search service" — long-term fact, synced to architecture.md §3.4
- 2026-05-15T10:33:00Z [Section 2.2]: Modify auth flow to OIDC — long-term fact (security baseline), synced
- 2026-05-15T10:35:00Z [Section 2.3]: Temporary throttle on /search (release-only), NOT synced

## Change Log

### 2026-05-15

- 2026-05-15T10:30:00Z [Section 2.1]: Add component "search service" — long-term fact, synced to architecture.md §3.4
- 2026-05-15T10:33:00Z [Section 2.2]: Modify auth flow to OIDC — long-term fact (security baseline), synced
- 2026-05-15T10:35:00Z [Section 2.3]: Temporary throttle on /search (release-only), NOT synced
```

### 6.2 主 doc 的 Pending Changes / Change Log（仅含长期事实条目）

```markdown
## Pending Changes

- 2026-05-15T10:31:00Z [Section 3.4]: Add search service component (responsibility, scaling, failure mode)
- 2026-05-15T10:34:00Z [Section 4.3]: Migrate auth from OAuth2 to OIDC

## Change Log

### 2026-05-15

- 2026-05-15T10:31:00Z [Section 3.4]: Add search service component (responsibility, scaling, failure mode)
- 2026-05-15T10:34:00Z [Section 4.3]: Migrate auth from OAuth2 to OIDC
```

主 doc Change Log entry **不写**"in release x.y"等 release 级时间锚定（主 doc 是抽象事实层；时间锚定靠 architecture_delta.md 的 release 字段间接给出）。

---

## 7. 与 architecture-review 维度 6 配套的校验对照

architecture-review §3 维度 6（主 doc vs delta 决策合理性）按本 policy 校验：

| Check | severity if 失败 |
|-------|----------------|
| delta §3 Long-Term Fact Sync 表存在 | blocking |
| 表中每行 Long-term fact? 列有 yes / no 决策 | blocking |
| 表中每行 Synced 列与 Long-term fact? 一致（yes→yes / no→no）| blocking |
| 主 doc Change Log 含全部"yes synced"条目 | blocking |
| 主 doc Change Log **不含**"no synced"条目（避免污染主 doc）| medium |
| Bug Flow re-entry 时 §5 Bug Flow Linkage 节存在 | blocking |
| Bug Flow re-entry 引发的改动按 SKILL.md §7.1 表分类合理 | blocking（如长期事实仅写 delta → blocking）|

---

## 8. Edge Cases

### 8.1 同 release 多次进入 architecture write（advance 失败回退 / Bug Flow re-entry）

每次进入都按 §5 规则同步：增量加新条目到 §3 表 + delta Change Log + 主 doc Change Log（如果触及长期事实）。**不**回滚之前的同步——每次同步是 append-only。

### 8.2 用户在 architecture-review 反馈"过度同步主 doc"

revise 路径：从主 doc 移除被认定为"local"的条目；§3 表对应行改为 no synced；本 doc 加 Pending Changes 描述。两份 doc 同步重 submit。

### 8.3 长期事实在多个 release 增量积累（无 release-close hook 自动合并）

每个 release 都必须自己同步主 doc。Multi-release 项目下，主 doc 应是 cumulative 的（包含全部 release 的长期事实），delta 是 per-release 增量。

### 8.4 主 doc 与 delta 真正冲突（罕见但需识别）

如 delta §2 引入新 API path `/v2/search` 但主 doc §4.1 仍然只列 `/v1/search` → 长期事实漏同步。修复：主 doc §4.1 加 `/v2/search` 章节 + deprecated `/v1/search` 注记。

### 8.5 Release close 后再发现长期事实漏同步

Release close 后 historic release 目录只读；不能改原 delta。但是 architecture.md（主 doc）是项目级单文件，没有 release close 限制——下个 release 启动后，architecture-write 在新 release 的 Change Mode 中可以补主 doc（说明"补 v<x.y> 漏写的长期事实"）。这是 acceptable 的修复路径，但应该尽量在原 release 内捕获。

---

## 9. Anti-Patterns

| Anti-pattern | 后果 | 替代 |
|--------------|------|------|
| 长期事实仅写 delta，期待 release-close 自动合并 | spec 无该 hook；下 release 起点错误 | 同 §5 同步主 doc + delta |
| 把 release-only workaround 写进主 doc | 主 doc 污染；下 release 难删 | 仅 delta；§3 表标 no synced |
| §3 Long-Term Fact Sync 表未填写 | review 维度 6 blocking | 必须每条改动一行 |
| 主 doc 与 delta 同步时不 atomic（先后 commit） | review 期间状态不一致 | 必须同一 §6 4-step 一起 submit |
| Bug Flow 引发 architecture 改动但不更新主 doc | bug 暴露的设计缺陷在下 release 重现 | 保守按长期事实处理 |
| 修历史 release 的 architecture_delta（已 release-closed）| 拒绝；目录只读 | 在新 release 中改主 doc 补救 |

---

## 10. 演化

- 修改本 policy 必须在 SKILL.md §3 / §7 / §10 References 节同步说明
- 改变长期事实判别标准需走 design proposal review cycle
- 当前对应 design proposal 版本：v0.5（2026-05-06）+ v0.6 round 1 H3 + v0.6 round 2 M2 + Phase 7 polish
