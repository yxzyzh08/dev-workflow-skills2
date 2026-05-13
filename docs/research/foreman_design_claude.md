# foreman — Skill Design Archive

调研对象 source path: `/home/cgs/github_projects/foreman/`
版本: v0.1（bootstrap 阶段，自身代码尚未实现 / 处于"自举工程师"阶段）
作者: cgs

## Project Overview

foreman 定位 **个人化 Workflow Architect Agent**——"资深工程经理 / 个人首席工程师"。foreman 自己不写代码，它**调度 Codex / Claude Code** 把项目从需求做到交付。

四个核心目标（来自 `README.md`）：

1. 为每个项目打造专属工作流、skill、AGENTS.md / docs 体系，让 Codex / Claude 能在节点里精确执行
2. 在同一项目下个版本时，基于经验自动优化 skill 和工作流
3. 学会使用自己产出的产品（读 manual → 派生 skill），用产品组合完成长期任务
4. 在执行中持续总结经验，反向改进流程和产品

整体哲学：

- **L0/L1/L2/L3 4 层文档体系** + 跨 SRS bug 池 / 变更池
- **Vendor-neutral skill 源 + dual-vendor symlink discovery**：真实 skill 内容放 `skills/<name>/SKILL.md`，`.claude/skills/<name>` 与 `.agents/skills/<name>` 都是 symlink
- **Binary-enforced workflow protocol**：progress 文件唯一可信入口是 `scripts/progress.py`；audit-gate 唯一可信入口是 `scripts/audit.py`；agent 不允许"声称跑了" + "没真跑"——exit code 0/1 + audit log JSONL 是事实证据
- **task-completion gate (audit-gate)**：每个 stage skill 完成一轮后**必须**调 audit-gate；author 不能跳过 audit-gate 自行 commit / 自行改 baseline / 自行进入下一 stage

target users：**自己**（cgs，个人项目）；当前是自举阶段，foreman 自身处于 v0.1 没写代码，agent 直接受人驱动作"foreman v0.1 的自举工程师"。

## Directory Structure

```
foreman/
├── AGENTS.md                            # 仓库级协作契约（106 行；workflow-protocol 必读硬约束）
├── CLAUDE.md                            # 8 行，引用 AGENTS.md
├── README.md
├── project.yaml                         # 完整元配置：paths.* / doc_status / skills 注册 / workflow.* 参数
├── progress.md / progress-history.md    # dashboard + append-only timeline
├── progress.md.lock / progress-history.md.lock / project.yaml.lock  # flock 文件
├── .progress-audit.jsonl                # progress.py 写入的 sha256 audit log
├── .audit-gate-trail.jsonl              # audit.py 调用 trail
├── active / in-review / stable          # 0-byte sentinel 文件（似乎是 stage 标记？）
├── skills/                              # 真实 skill 源（vendor-neutral）
│   ├── workflow-protocol/SKILL.md + scripts/progress.py
│   ├── audit-gate/SKILL.md + scripts/audit.py + references/{frontmatter-schema,concurrency,changelog,...}.md
│   ├── scaffold-project/SKILL.md + templates/  # 含 17 文件模板（含 skills/workflow-protocol 拷贝）
│   ├── write-prd/SKILL.md
│   ├── review-prd/SKILL.md
│   ├── write-architecture/SKILL.md
│   ├── review-architecture/SKILL.md
│   ├── write-srs/SKILL.md
│   ├── review-srs/SKILL.md
│   ├── write-feature-spec/SKILL.md     # deprecated alias
│   └── review-feature-spec/SKILL.md    # deprecated alias
├── .claude/skills/                     # Claude Code 自动发现路径
│   └── <name> -> ../../skills/<name>   # 全部 symlink
├── .agents/skills/                     # Codex CLI 自动发现路径
│   └── <name> -> ../../skills/<name>   # 全部 symlink
└── docs/
    ├── product/                         # L1 产品级
    │   ├── prd.md / glossary.md / architecture.md / deployment.md / manual.md
    │   ├── research/                    # L1 研究材料
    │   └── reviews/                     # L1 评审记录（含 prd-review-* / architecture-review-* / concurrency-review-* / write-architecture-skill-review-* 等几十份）
    ├── srs/v0.1/foreman-srs.md          # L2 SRS（每 release 唯一）
    ├── srs/README.md
    ├── features/F001-F005/              # legacy Feature Spec（C002 deprecated）
    ├── bugs/                            # 跨 SRS bug 池（B<NNN>-<slug>.md）
    ├── changes/                         # 变更池（C<NNN>-<slug>.md，CR）
    │   ├── C001-prd-agent-identity.md
    │   └── C002-l2-srs-taxonomy.md
    ├── handoff/                         # 跨 session 的交接文档（约 17 份）
    ├── archive/
    └── changes/                         # CR
```

vendor neutrality 处理 = **B-i 复制式 distribution**: scaffold-project 在创建新项目时把 `templates/skills/workflow-protocol/` 整目录复制到新项目 `skills/workflow-protocol/`，再建 `.claude/skills/workflow-protocol -> ../../skills/workflow-protocol` + `.agents/skills/workflow-protocol -> ../../skills/workflow-protocol` symlinks。`workflow-protocol` 内容 vendor-neutral / project-neutral，复制时不替换占位。

这个项目当前文档非常详细（11 个 SKILL.md 共 2,890 行；audit-gate 一个就 349 行 + 5 个 references），且自我评审做了大量轮次（progress.md 列出 10+ 次 review-* 修复 cycle）。

## Skill Inventory

11 个 SKILL.md（其中 2 个 deprecated alias），按 role 分类（来自 `project.yaml.skills`）：

| Skill | Role | Version | Lines | Trigger / Description (compressed) |
|---|---|---|---|---|
| `workflow-protocol` | protocol | v0.11 | 391 | 任何 stage / review / audit skill 启动第一步必读；承载 startup checklist + progress hook + state machine + CR + cascade limit + loop stop + cross-review + concurrency rules |
| `audit-gate` | cross-cutting | v0.11 | 349 | 任务完成稽核员；9 类 check（frontmatter / 状态机 / CR 引用 / progress 对齐 / git commit / baseline 小调整 / hash chain / lock / owner key）；Hook 闭环唯一可信入口 |
| `scaffold-project` | meta | — | 200 | 初始化新项目；生成 4 层文档骨架 + 复制 workflow-protocol skill + dual-vendor symlinks；只调用一次 |
| `write-prd` | stage | v0.11 | 439 | L1 产品级 PRD 起草 / 修订 / 迁移；8 节固定结构 + Lean Canvas / JTBD / OKR 方法论 + 联网调研 + 反向澄清 |
| `review-prd` | review | v0.2 | 238 | 独立 PRD 评审；reviewer ≠ author；不修改目标 PRD |
| `write-architecture` | stage | v0.7 | 690 | L1 架构基线起草；C4 Model + ADR + Capability Registry + Authority Model + QAW |
| `review-architecture` | review | v0.4 | 334 | 独立 architecture 评审；含 7 大块结构 + AF resolution packet + Navigation Rule 等校验 |
| `write-srs` | stage | v0.2 | 145 | L2 SRS 起草；每 release 唯一；Release Index / SRS Outline gate + Agent Responsibility Model |
| `review-srs` | review | v0.2 | 127 | L2 SRS 独立评审 |
| `write-feature-spec` | deprecated-alias | v0.5 | 26 | C002 后 deprecated；redirect 到 `write-srs` |
| `review-feature-spec` | deprecated-alias | v0.3 | 26 | C002 后 deprecated；redirect 到 `review-srs` |

平均 SKILL.md 240 行，最大 690 行（write-architecture）。文字密度极高，含大量"反 anti-pattern"段落。

## Skill Anatomy

**Frontmatter schema**：

```yaml
---
name: kebab-case-name
version: vX.Y                  # foreman 强制 version 字段
description: Use when ... 中文触发条件描述（非常长，常 200+ 字）含枚举触发场景与硬约束
---
```

`version` 字段是 foreman 独有的强约定（`workflow-protocol` 与 `write-prd` 等都标 v0.11 等版本），方便 audit-gate / cross-review 识别协议变化。

**Subdirectory 约定**：

- `SKILL.md`（必）
- `references/` —— 长 schema / changelog / 演化叙事
- `scripts/` —— **可执行 binary**（`progress.py` / `audit.py`），non-optional
- `templates/` —— 仅 `scaffold-project` 有，含 `templates/skills/workflow-protocol/` 整套副本以便 distribution

**强 enforcement via binary**：foreman 是 4 个项目里**唯一**把"协议规则"用真正的 Python script 执行的项目。`scripts/progress.py` 是 progress 文件唯一合法入口；`scripts/audit.py` 是 audit-gate 唯一合法入口；audit-gate Check 7 通过 `before_sha256` chain 检测 agent 是否绕过 progress.py 直接编辑。

**命名 convention**：动词前缀（`write-prd` / `review-prd` / `audit-gate` / `scaffold-project`）—— 比 dev-workflow-skills 的角色名（`requirements-analyst`）更有 trigger discoverability，且更紧凑。

## Cross-cutting Mechanisms

**workflow-protocol skill (Mechanism A core)**：与 dev-workflow-skills v1 同构，但更严格：

- Startup Checklist 8 步（前 7 步 mandatory hard gate；第 8 步可选）；每个 stage skill 都要按这个 checklist 走
- 第 6 步 active CR 检查极细：CR 目录不存在 + 项目尚无 frozen 文档 → 视为"无 active CR"且不中止；CR 目录不存在 + 已有 frozen 文档 → 中止报错（CR 流程缺失，工作流不完整）
- 第 7 步细分多种文件状态：`paths.<target>` key 缺失 → 中止；文件不存在 + doc_status=pending + stage skill 支持 create mode → 允许继续；其他 → 中止

**Progress Hook → audit-gate 闭环（Mechanism B/C 强 enforcement）**：

- 每个 stage skill 完成一轮**改变工作流状态**的工作后，**必须同 round 更新两个文件**（progress.md + progress-history.md）
- 双更新后，**必须**调 `audit-gate routine` mode；返回 `overall=pass`（exit 0）才算闭环；返回 `overall=blocked` 必须按 stdout report 修复后重跑 audit.py
- author skill 不能跳过 audit-gate 直接进入下一 stage 或 commit
- audit-gate description 已声明该硬约束（"author 不能跳过本 skill 自行 commit / 自行改 baseline 文档"）

**state management (Mechanism C)**：

- 状态枚举：`pending / draft / active / in-review / blocked / frozen / stable / completed / archived`
- 关键转换硬约束：`draft → active` 必须 human 显式授权；`active → in-review` 由独立 reviewer skill 启动；`in-review → frozen` 必须经 `audit-gate pre-freeze` mode PASS + human gate（v0.11 当前 `pre-freeze` 未实现，靠 routine + human ack 兜底）
- `baseline 小调整` (frozen-edit / stable-edit) 是 lightweight gate：author 不能自行原地改 frozen/stable baseline；必须 audit-gate 代为执行；当前 binary 未实现 baseline edit executor，所以即使请求合规仍 safe-blocking

**dashboard 写权限分层** (workflow-protocol/SKILL.md table)：

| 角色 | 能写 | 不能写 |
|---|---|---|
| 阶段 skill | 自己 stage 行的 active/in-review/blocked + blocker + 下一步 | 不能推到 frozen/completed |
| audit-gate routine | 报告漂移；当前不 auto-correct；baseline edit gatekeeper（safe-blocking） | 不能推进 stage 状态 |
| audit-gate pre-freeze（待实施） | **唯一**能推到 baseline 终态 | — |
| 元 skill (scaffold/router/protocol) | 自身被触发时记录一次 | 不修改其他 stage 状态 |

**Concurrency rules（4 项目里最详细）**：

- `progress.md` / `progress-history.md` 唯一可信入口 = `scripts/progress.py`
- `<paths.progress>.lock` flock(ttl=30s)；锁失败 → 脚本 exit 非 0 + 报错
- atomic write：同目录 tmp + fsync + chmod 保留原 mode + os.replace + fsync parent dir
- audit log sidecar `<root>/.progress-audit.jsonl`：每次写入 append `{ts, pid, command, actor, owner, target, before_sha256, after_sha256}`
- audit-gate Check 7 按 target 维度做 **per-target hash chain** 校验：每条 entry 的 `before_sha256` 必须等于上条同 target entry 的 `after_sha256`，且当前 sha256 必须等于最新 entry 的 `after_sha256`
- audit log 写入有 4 次演化：v0.2 lock mtime 启发式 → v0.3 sha audit log latest-only → v0.4 per-target hash chain（详见 `references/changelog.md`）
- Owner Key marker：`[owner:KEY]` exact match；agent 只能改自己 owner 的行，跨域修改脚本拒绝

**Hooks**: foreman 不依赖 plugin host hook（如 SessionStart），靠 SKILL.md description "硬约束语" + agent 自觉触发 + audit-gate binary 兜底。

## Inter-skill Coordination

**Mandatory invocation cascade**：

1. agent 启动任何 stage skill → 第一步读 `skills/workflow-protocol/SKILL.md`（cascade by AGENTS.md 顶部"必读"声明 + skill description "必须先读 protocol"）
2. 读完 protocol → 跑 Startup Checklist 8 步
3. 完成 stage 节点工作 → 调 progress.py 子命令更新 progress 双文件
4. 调 audit.py routine mode → 拿 exit code 决定能否结束

**audit-gate self-progress hook**: 即使 audit-gate 自己也跑 progress hook 记录 audit 触发；不会陷入 "audit-gate 调 audit-gate" 递归（audit-gate 自身不再触发 audit-gate；其 `When to Use` 边界明示）。

**Routine Audit Locality (v0.10/v0.11)**：

调用方传 `--owner-key` 时 audit-gate verdict 按当前 owner / target 收敛：

- **Local FAIL**：当前 target 自身的 frontmatter / project.yaml.doc_status / dashboard owner row 三方不一致；当前 target 引用的 CR 不存在；当前 owner 的 progress hook 缺失；progress 文件 sha 与最新 audit log after 不一致
- **Unrelated WARN**：active CR 存在但 affects 不含当前 target；其他 owner 的 blocker / dashboard 漂移；历史 progress hash-chain break 但当前文件 sha 已与最新写入对齐

这避免了"不相关 owner 的历史问题阻塞单个 agent routine 收尾"。`commit-only` / `pre-freeze` / release gate 仍可保持全局健康检查。

**Cross-review separation**: review skill (`review-prd` / `review-architecture` / `review-srs`) 都明确 `reviewer ≠ author`；review report frontmatter 必含 `target` / `reviewer` / `conclusion`（binary：pass / not pass）；severity 限定 `blocker` / `major` / `minor`。

## Notable Patterns

**Borrowable**：

1. **Binary-enforced protocol**：`progress.py` + `audit.py` 把"agent 必须做 X"从 prose 变成 exit code；agent 不能"声称跑了"；audit log JSONL + per-target hash chain 让绕过被检测
2. **Owner Key marker `[owner:KEY]`**：多 agent 并发时通过 marker exact match 隔离写入；脚本拒绝跨域修改
3. **Per-target hash chain** Check 7：4 次失败教训得出（lock mtime → sha latest-only → 洗白漏洞 → hash chain），changelog 完整记录设计演化
4. **Routine Audit Locality**：单 agent routine 收尾不被其他 owner 历史问题阻塞，但仍然检测当前 owner 自身的所有问题
5. **scaffold-project B-i 复制式 distribution**：把 `workflow-protocol` skill 复制到新项目而不是 reference，让新项目脱离原 skill 库后仍能独立运行
6. **dual-vendor symlink convention**：真实内容在 `skills/`，`.claude/skills/` + `.agents/skills/` 都 symlink；vendor 各自自动发现，源仍唯一
7. **Stage skill description 极长 + 硬约束语**: write-prd description 含 "即使用户没显式说'用 write-prd skill'，只要任务涉及产品全量 scope 的起草、修订、迁移，都应触发本 skill" —— description 的 trigger coverage 显式覆盖反语义场景
8. **Baseline 小调整 lightweight gate**：避免每个 typo 都建 CR 的开销，但仍然 enforce author 不能直接改（必须 audit-gate 代为执行）
9. **Severity blocker/major/minor + conclusion binary**：review 报告二元化；`review-feature-spec/review-prd/review-srs/review-architecture` 都共用同一 schema
10. **audit-gate self-progress-hook + actor whitelist** 避免无限递归：audit-gate 用 `<vendor>-audit-gate` actor 写自己 entry，被识别为合法 progress.py 写入，Check 7 hash chain 不破

**Anti-pattern (with evidence)**：

1. **SKILL.md 太长**：write-architecture 690 行 / write-prd 439 行 / workflow-protocol 391 行；每次 invoke 都加载这么多 token，超过 superpowers/dev-workflow-skills 的 avg 200 行
2. **description 也太长**（200+ 字）：把硬约束塞进 description 会被 LLM 当作 workflow summary（参考 superpowers `writing-skills/SKILL.md` 论证：description 概括 workflow 会让 Claude 跳过读 SKILL.md 正文）
3. **review skill 数量与 stage skill 1:1 重复**：`write-prd / review-prd / write-architecture / review-architecture / write-srs / review-srs` —— 每对 review skill 内容大量重复；可考虑用单 `cross-reviewer` 加 stage 参数化的方式合并
4. **deprecated alias skill 仍在仓库**：`write-feature-spec / review-feature-spec` 是 deprecated alias 但 SKILL.md 仍占位；compatibility window 设计但不清楚何时移除
5. **过度文档化的 design history**：每个 audit-gate references/changelog.md 演化叙事极详细，但运行时 LLM 不需要这些；放到 docs/archive/ 更合适
6. **0-byte sentinel 文件 `active / in-review / stable`**：仓库根有这 3 个 0-byte 文件，用途不明（猜测是 git stage 标记或 branch flag）；如非必要，可删除

## Concrete Evidence

Key file paths:

- `/home/cgs/github_projects/foreman/AGENTS.md` — 项目契约 + workflow-protocol 必读硬约束
- `/home/cgs/github_projects/foreman/project.yaml` — 完整元配置（200+ 行；paths.* / doc_status / skills 注册 / workflow.*）
- `/home/cgs/github_projects/foreman/skills/workflow-protocol/SKILL.md` — 协议事实源（391 行）
- `/home/cgs/github_projects/foreman/skills/workflow-protocol/scripts/progress.py` — progress 唯一可信入口
- `/home/cgs/github_projects/foreman/skills/audit-gate/SKILL.md` — 9-check 任务完成稽核员
- `/home/cgs/github_projects/foreman/skills/audit-gate/scripts/audit.py` — audit binary（含 hash chain check）
- `/home/cgs/github_projects/foreman/skills/audit-gate/references/{frontmatter-schema,concurrency,commit-rules,progress-alignment,changelog}.md` — 5 份长 reference
- `/home/cgs/github_projects/foreman/skills/scaffold-project/SKILL.md` + `templates/` — 项目初始化 + workflow-protocol 复制 distribution
- `/home/cgs/github_projects/foreman/.{claude,agents}/skills/<name>` — dual-vendor symlinks
- `/home/cgs/github_projects/foreman/.progress-audit.jsonl` + `.audit-gate-trail.jsonl` — runtime audit logs

代表性 excerpts：

1. "v0.9 起 audit-gate 实施为 binary—— `python3 skills/audit-gate/scripts/audit.py routine` 是 Hook 闭环唯一可信入口（类似 progress.py 强制路径）。agent 调 binary 拿机械 report，不能'声称跑了'同时'没真跑'——exit code 0/1 + stdout report 是事实证据。" (`workflow-protocol/SKILL.md:81-82`)
2. "`progress.md` / `progress-history.md` 的唯一可信更新入口是 `skills/workflow-protocol/scripts/progress.py`。任何 agent / stage skill 不允许直接编辑 progress 文件——必须调子命令。违反 = 协议错误，audit-gate Check 7 通过 sha256 audit log 检测并 FAIL。" (`workflow-protocol/SKILL.md:264-265`)
3. progress.py audit log entry: `{"ts":"2026-05-02T16:30:00+08:00","pid":12345,"command":"update-stage","actor":"claude-write-prd","owner":"docs/product/prd.md","target":"progress.md","before_sha256":"abc...","after_sha256":"def..."}` (`workflow-protocol/SKILL.md:323`)
4. "agent 启动时：从用户输入 / skill input 获得目标产物路径或 task slug → 这是它的 owner key；调脚本时传 `--owner <key>`；脚本用 `^\[owner:KEY\]` 正则在阶段表第 3 列做 exact match" (`workflow-protocol/SKILL.md:299-303`)
5. "Routine Audit Locality (v0.11)：当调用方提供 `--owner-key` 时，routine verdict 的阻塞范围按当前 owner / target 收敛 —— Local FAIL：当前 target_doc 自身漂移；Unrelated WARN：其他 owner 的历史问题已对齐当前文件" (`workflow-protocol/SKILL.md:90-108`)
