# dev-workflow-skills v1 — Skill Design Archive

调研对象 source path: `/home/cgs/github_projects/dev-workflow-skills/`
版本: v1.0.0（来自 `.claude-plugin/plugin.json`）
作者: cgs

## Project Overview

dev-workflow-skills v1 是 dev-workflow-skills2 的前身，定位 **"multi-platform skill pack for stage-based software delivery"**。把软件交付分成若干 stage（requirements / acceptance / architecture / dev / test / qa），每个 stage 一个 skill；同时配套一组 cross-cutting skills（workflow-protocol / workflow-router / completion-verifier / doc-guardian / parallel-dispatcher / git-manager / security-auditor / systematic-debugger / skill-writer）。

整体哲学：

- **Stage-based + frozen baseline + Change Request** —— 每个 stage 的产物有 `draft → active → in-review → frozen` 状态机，frozen 后只能经 human-approved CR 重开；通过这种方式把"防止 LLM 自己改基线"做成机制
- **Path-key indirection** —— 所有 skill 通过 `paths.requirements` / `paths.acceptance` 等 logical key 引用文档路径，禁止硬编码（`scripts/check-hardcoded-paths.sh` 强制）
- **Single source for shared rules** —— `workflow-protocol` 是协议事实源，其他 skill `should reference rather than repeat`
- **Multi-platform from a single skills/ source** —— 一份 `skills/` 同时分发到 Claude Code、Codex Anthropic Agents、Codex CLI

target users：在自己项目里需要 staged delivery + workflow discipline 的开发者，使用 Claude Code / Codex CLI。

## Directory Structure

```
dev-workflow-skills/
├── AGENT.md                          # 唯一权威 manifest（约 65 行，列 16 skills）
├── CLAUDE.md                         # @AGENT.md（一行，引用 AGENT.md）
├── workflow-project.yaml             # 自身 dogfood 的元配置（仅 progress paths）
├── startclaude.sh / startcode.sh     # 启动脚本
├── skills/                           # 16 skills（vendor-neutral 源）
│   └── <skill-name>/
│       ├── SKILL.md                  # frontmatter + body
│       ├── references/               # 支撑 reference docs
│       ├── templates/                # 输出模板（部分 skill 有）
│       └── scripts/                  # validation 脚本（仅 skill-writer / git-manager）
├── .claude-plugin/                   # Claude Code plugin 元数据
│   ├── plugin.json
│   └── marketplace.json
├── .agents/                          # Anthropic Agents plugin
│   ├── plugins/marketplace.json
│   └── skills/                       # 空目录（plugin host 通过 marketplace 自己解析）
├── plugins/dev-workflow-skills/      # Codex CLI plugin layout
│   ├── .codex-plugin/                # Codex 元数据
│   └── skills -> ../../skills        # symlink，避免内容复制
├── docs/
│   ├── workflow/                     # 自身 progress.md / progress-history.md
│   └── variant-c-skill-acceptance/   # design / decisions / fixtures / reviews
└── .npm/                             # npm package metadata（plugin 经 npm 分发）
```

**Vendor-neutral / multi-runtime** 处理三种方式同时用：

1. **`.claude-plugin/`**: Claude Code 直接读这里
2. **`.agents/plugins/marketplace.json`**: Anthropic Agents（独立产品，CLI 名 `agents` / Codex 早期形式）声明 `source.local.path: ./plugins/dev-workflow-skills`
3. **`plugins/dev-workflow-skills/skills -> ../../skills`** symlink: Codex CLI 读 `plugins/dev-workflow-skills/`，但内部 `skills` 是 symlink，避免复制带来漂移

## Skill Inventory

16 skills（AGENT.md 列出的全部），按概念分类，全部 flat 单层：

| Skill | Category | Trigger | Lines |
|---|---|---|---|
| `workflow-protocol` | Protocol | Shared freeze / CR / review rules — read by all other skills | 136 |
| `workflow-router` | Navigation | Session start or next-step is unclear | 84 |
| `requirements-analyst` | Stage | Collect, structure, review, freeze requirements | 91 |
| `acceptance-designer` | Stage | Frozen requirements → formal acceptance docs (Variant A/B/C) | 299 |
| `system-architect` | Stage | Architecture design and review from frozen baselines | 88 |
| `tech-lead` | Stage | Release design + dev plan + detailed design | 92 |
| `developer` | Stage | Implementation, TDD, code-review response | 89 |
| `test-engineer` | Stage | E2E test plans + automated setup | 79 |
| `delivery-qa` | Stage | E2E execution + failure analysis + delivery report | 86 |
| `parallel-dispatcher` | Cross-cutting | Split independent tasks for parallel execution | 85 |
| `git-manager` | Cross-cutting | Worktree + branch naming + serial integration | 72 |
| `systematic-debugger` | Cross-cutting | Root-cause diagnosis for bugs / test failures | 72 |
| `security-auditor` | Cross-cutting | Security review for code/architecture/deps | 82 |
| `doc-guardian` | Cross-cutting | Document compliance + frozen-baseline checks | 74 |
| `completion-verifier` | Cross-cutting | Evidence checks before marking a stage complete | 75 |
| `skill-writer` | Meta | Create / revise / validate workflow skills | 103 |

总行数约 1,860 行 SKILL.md 内容；最大 `acceptance-designer/SKILL.md` 299 行；最小 `git-manager` 72 行。这与 superpowers 的"少而厚"（avg ~200 行）形成对比——v1 的"多而薄"（avg ~115 行）+ 重 references。

## Skill Anatomy

**Frontmatter** (AGENT.md 第 44 行)：

```yaml
---
name: kebab-case-name
description: Use when ... including 中文触发词/中文触发词
---
```

要求：

- `description` 必须以 `Use when …` 开头（discovery trigger）
- 高频 skill 包含中文触发词覆盖（"在中文协作中也能被 trigger"）

**Subdirectory 约定** (AGENT.md 第 28-40 行)：

```
skills/{skill-name}/
  SKILL.md                # frontmatter + 主体说明
  references/             # 支撑 reference docs（几乎每个 skill 都有）
  templates/              # 输出模板（部分 skill：completion-verifier、parallel-dispatcher、systematic-debugger）
  scripts/                # validation 脚本（仅 skill-writer + git-manager）
```

**强制结构（来自 `skill-writer/scripts/check-skill-structure.sh`）**：

- frontmatter 存在 + valid YAML
- description 以 `Use when` 开头
- 顶级标题存在
- 没有未解析占位符 (`{{...}}`)

**命名 convention**：通常是名词（`requirements-analyst`、`tech-lead`、`developer`）—— 表达 **角色** 而不是动作；这与 superpowers 的"动名词优先"是分歧。

## Cross-cutting Mechanisms

**workflow-protocol skill (Mechanism A core)**: 唯一的"必须 first read" skill。每个 stage skill 的 `First Step` 都是 `Read skills/workflow-protocol/SKILL.md, then read repository-root workflow-project.yaml, then read paths.progress`。`workflow-protocol/SKILL.md` 本身承载：

- 共享 startup checklist
- progress update hook（mandatory）
- document & metadata 规则
- state machine：`draft → active → frozen`，`active → stable`（仅 architecture）
- Change Request rules（cascade ≤ 2，否则 major change 升级）
- Loop Stop rules（同 artifact 最多 7 轮）
- Cross-review rules（`reviewer != author`）
- Dashboard 写权限分层

**No SessionStart hook**：v1 不依赖 plugin host 的 hook 注入；完全靠每个 skill 内的 "First Step" 文字让 LLM 自己 cascade 加载 protocol。这是 v1 与 superpowers 的最大区别。

**state management（Mechanism B/C）**：

- `paths.progress` (默认 `docs/workflow/progress.md`) 是 dashboard，only current state（不积累历史）
- `paths.progress_history` (默认 `docs/workflow/progress-history.md`) append-only 时间线
- progress 更新规则在 `workflow-protocol/SKILL.md` 第 47-54 行：每个改 workflow 状态的 round 必须同时更新 dashboard + history
- Dashboard 写权限分层（第 114-120 行）：`completion-verifier` 才能 advance stage 到 `frozen`；`doc-guardian` 只能纠正不一致；stage skill 只能更新自己的行；`workflow-router` 完全只读

**validation enforcement（Mechanism D）**：

- 全 prose 描述 + 一组 bash/python 校验脚本（`skill-writer/scripts/`）
- `check-skill-structure.sh`、`check-language-policy.sh`、`check-skill-discovery.py`、`check-project-config.py`、`check-hardcoded-paths.sh`
- `run-skill-library-regression.sh` 把上述串成单 entrypoint，**支持 `--skills` `--hardcoded-scope` `--discovery-prompt` 参数**
- 这些是 skill-writer 自检脚本，**不是 workflow runtime 验证**；rerun by author，不是 CI 自动跑

**hooks**：v1 没有 plugin host hook（不像 superpowers 有 SessionStart 注入；不像 foreman 有 progress.py 强制路径）

**Recursive paradox（值得记录）**：因为本仓库自己就是 `acceptance-designer` 的源头，无法 dogfood 完整 workflow。`docs/variant-c-skill-acceptance/decisions.md` D-003 + D-006 记录 scoped reversal：只绑定 `paths.progress` / `paths.progress_history`，不绑定 `paths.requirements` / `paths.acceptance` / `paths.architecture`，避免"用旧版 acceptance-designer 给新版 acceptance-designer 写验收"的语义冲突。

## Inter-skill Coordination

**Mandatory invocation pattern (cascade reads)**：

每个 stage skill 顶部都有 `First Step` 段：
```
Read `skills/workflow-protocol/SKILL.md`, then read repository-root
`workflow-project.yaml`, then read the progress dashboard at `paths.progress`
before doing stage work.
```

通过这种文本协议把 protocol cascade 起来；没有机械 enforcement。

**workflow-router 是 navigation-only**：明确"do not perform stage work"。读 progress + CR 状态后给 recommendation，但不修改任何东西。

**completion-verifier 是 evidence gate**：唯一能把 stage advance 到 frozen 的 skill；输出 `templates/verification-report.md` 必须 ends with `PASS` or `NOT PASS`；NOT PASS 也要 append 到 progress-history（audit trail）。

**doc-guardian 是 metadata corrector**：可以纠正 dashboard 与 frontmatter 不一致，但 **cannot advance stage status**。

**parallel-dispatcher**：明确说"workers 必须遵守 developer skill 的完整 working loop（TDD + 两段 review），并行不豁免任何 quality gate"；通过 `templates/dispatch-context-pack.md` 给每个 worker 准备 context；integration 必须 serial 且经 completion-verifier。

**没有 explicit subagent dispatch primitive**：parallel-dispatcher 描述行为但不提供脚本——依赖外层（人或 router）实际启动 worker session。

## Notable Patterns

**Borrowable**：

1. **Path-key indirection**（`paths.requirements` 等 logical key）让 skill 可被多项目复用；`workflow-project.yaml` 在每个项目自己绑定具体路径
2. **Dashboard 写权限分层** 把"谁能 advance stage"用文字明确化，加上 `completion-verifier` 这个唯一 advance entrypoint
3. **State machine + CR + cascade depth limit**：`draft / active / in-review / frozen / stable`；CR cascade > 2 stages 升 major change；防止 LLM 滚雪球修改
4. **Loop stop = 7 rounds**：同 artifact review/repair 7 轮未收敛必须 escalate
5. **Severity 限定 `blocker` / `minor`，conclusion 限定 `pass` / `not pass`**：二元化 review 报告，避免中间态
6. **Three-vendor distribution via symlink + marketplace**: 单一 skills 源被 3 个 plugin host 都消费
7. **`completion-verifier/templates/verification-report.md`**：把 PASS/NOT PASS gate 做成模板而不是 free-form 文本
8. **Recursive paradox 决策记录**：D-003/D-006 体现"知道何时 NOT to dogfood"的 design maturity

**Anti-pattern (with evidence)**：

1. **Mandatory invocation pattern 100% 靠 LLM 自觉**：每个 skill 顶部写 "First Step: read protocol" 就期待 LLM 真去读；没有 mechanism 检测 "did agent actually read it"。foreman 后来用 binary script 解决这点
2. **Validation 脚本是 author-run，不是 runtime gate**：`run-skill-library-regression.sh` 是 skill-writer 自检；workflow runtime 没有任何脚本保证 "agent 真的更新了 progress"
3. **角色名 (`requirements-analyst`/`tech-lead`/`developer`) trigger discoverability 弱**：用户说"帮我写需求"，LLM 不一定会优先匹配到 `requirements-analyst`；description 加了中文触发词补救，但描述长度增加
4. **completion-verifier 单点**：只有它能 advance stage，但它本身仍然是 LLM 执行 `templates/verification-report.md` 模板填空；没有 binary 强 enforcement，agent 可以 self-claim PASS

## Concrete Evidence

Key file paths:

- `/home/cgs/github_projects/dev-workflow-skills/AGENT.md` — manifest + 设计概览
- `/home/cgs/github_projects/dev-workflow-skills/skills/workflow-protocol/SKILL.md` — 协议事实源
- `/home/cgs/github_projects/dev-workflow-skills/skills/workflow-router/SKILL.md` — navigation-only 范本
- `/home/cgs/github_projects/dev-workflow-skills/skills/completion-verifier/SKILL.md` + `templates/verification-report.md` — 单点 stage gate
- `/home/cgs/github_projects/dev-workflow-skills/skills/skill-writer/scripts/run-skill-library-regression.sh` — 校验 entrypoint
- `/home/cgs/github_projects/dev-workflow-skills/docs/variant-c-skill-acceptance/decisions.md` — recursive paradox 设计记录
- `/home/cgs/github_projects/dev-workflow-skills/workflow-project.yaml` — 自 dogfood 元配置（仅 progress paths）

代表性 excerpts：

1. "Every `SKILL.md` has YAML frontmatter with `name` (kebab-case) and `description`. `description` must begin with `Use when …` — this is the discovery trigger." (`AGENT.md:43-45`)
2. "**Stage advancement**: Only `completion-verifier` with a PASS verdict may advance a stage's status to `frozen` or mark a stage complete on the dashboard." (`workflow-protocol/SKILL.md:115`)
3. "Any formal review, revise, recheck, or repair loop on the same artifact or fix direction may run at most 7 consecutive rounds without convergence." (`workflow-protocol/SKILL.md:103`)
4. "this repo intentionally binds **only** `paths.progress` and `paths.progress_history` in `workflow-project.yaml`. ... (recursive paradox: this repo IS the source of `acceptance-designer`)" (`AGENT.md:64`)
5. "Read `skills/workflow-protocol/SKILL.md`, then repository-root `workflow-project.yaml`. Resolve `paths.progress` ... before doing stage work." (`completion-verifier/SKILL.md:23`)
