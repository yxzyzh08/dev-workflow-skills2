# forge — Skill Design Archive

调研对象 source path: `/home/cgs/github_projects/forge/`
版本: 0.4-draft（self-bootstrap 阶段）
作者: cgs

## Project Overview

forge 不是 skill 集合，是 **AI 生命体工厂 / Control Plane**。它定义、生成、治理、评估和进化 **Lifeform**（AI 生命体），并把生命体编译到 Hermes / OpenClaw 等 Runtime 运行。Claude Code / Codex 是 Runtime 可调用的 Executor，不是一等 Runtime。

整体哲学（来自 `AGENTS.md` Product Boundary）：

- **Forge runtime-agnostic / Hermes-first / OpenClaw-compatible** —— Forge 自己不绑定具体 runtime
- **Lifeform 是 canonical asset，runtime artifact 是 projection** —— 通过 `forge compile hermes <lifeform>` 把 canonical 编译成 runtime 可消费格式；projection 永远不能反向成为 canonical source
- **Self-bootstrap 中**：本仓库既是 Forge 产品定义项目，也是 `research-dev` lifeform 的首个 workspace
- **Risk-based review** 而不是默认 cross-review：低风险变更可跳过 independent review，但高风险（release gate / canonical schema / LifeformSpec / SkillSpec / runtime adapter / external publish / security）必须 review
- **runtime / executor 解耦**：Hermes 是 Runtime；Claude / Codex 是 Executor；Forge 是 Control Plane；不允许绕过 Runtime 直接 schedule Executor

target users：在多个项目中使用同一类 AI 生命体（如 `software-rd`）的人；希望生命体的工作方法论可治理 / 可评估 / 可演进。

## Directory Structure

```
forge/
├── AGENTS.md                          # 仓库级协作契约（self-bootstrap 流程 9 步）
├── CLAUDE.md                          # 引用 AGENTS.md + Claude Code 专属角色
├── README.md
├── pyproject.toml                     # Python package
├── progress.md / progress-history.md  # 自 dogfood 进度文件
├── forge/                             # CLI/library Python 实现
│   ├── __main__.py                    # `forge validate / compile / run / status / attach / stop` 命令
│   ├── validation.py                  # canonical asset JSON Schema validator
│   ├── projection.py                  # Lifeform → Hermes projection compiler
│   ├── result_ingestion.py            # RunRecord validator
│   ├── runtime_instance.py            # Runtime Instance handoff validator
│   └── runtime_session.py             # 本地 Hermes Runtime Session 启动
├── lifeforms/                         # Canonical Lifeform assets
│   ├── research-dev/lifeform.yaml + skills/ + context-packs/
│   ├── software-rd/lifeform.yaml + skills/project-workflow.md
│   └── novelist/README.md             # 占位
├── schemas/                           # JSON Schemas
│   ├── lifeform.schema.json
│   ├── skill.schema.json
│   ├── workflow.schema.json
│   ├── context-pack.schema.json
│   ├── lifeform-design-session.schema.json
│   └── run-record.schema.json
├── docs/
│   ├── prd/forge-prd.md               # 产品事实源
│   ├── concepts/                      # canonical specs（lifeform / skill / workflow / context-pack 等）
│   ├── architecture/                  # runtime-adapters / repo-layout
│   ├── decisions/                     # ADR
│   ├── reviews/                       # review prompts + reports + dispositions
│   ├── releases/0.1 / 0.2 / 0.3 / 0.4/ # release packages
│   ├── prd/  research/  runbooks/  testing/  design/  specs/
│   └── archive/
├── examples/
│   ├── lifeforms/                     # 人类可读 canonical examples
│   ├── design-sessions/               # 提交的 LifeformDesignSession examples
│   ├── projections/hermes/<lifeform>/  # 已提交 sample projection（验证用）
│   ├── runtime-instances/             # Runtime Instance handoff samples
│   ├── runtime-results/               # RunRecord samples
│   └── validation-runs/
├── workspaces/                        # workspace attachments（multi-workspace direction）
├── build/                             # 默认 projection 输出 dir（gitignored）
├── scripts/
└── tests/
```

vendor neutrality 处理与 dev-workflow-skills 完全不同：forge 不直接出 plugin。Lifeform → Runtime projection 是编译关系；Hermes 是一等 runtime，Claude Code / Codex 是 second-tier executor。`lifeforms/<id>/lifeform.yaml` 通过 `runtime_targets` 字段声明支持哪些 runtime，`executor_targets` 声明支持哪些 executor。

## Skill Inventory

forge 不直接出"a skill library"，但 lifeforms 内部有 SkillSpec。当前 in-tree 的实际 skill 极少：

| Lifeform | Skill 数 | Skills |
|---|---|---|
| `research-dev` | 0（仅 README 占位） | — |
| `software-rd` | 1 | `project-workflow.md`（128 行；project-local workflow + risk-based review policy） |
| `novelist` | 0（仅 README） | — |

`software-rd` 的 lifeform.yaml `skill_policy.mandatory_skills` 列了 `requirements-clarification`；`optional_risk_based_skills` 列了 `acceptance-design / architecture-planning / test-driven-development / requesting-code-review / delivery-qa / completion-verification`，但这些 SkillSpec 文件并未真实存在——它们是 reference 到 `../dev-workflow-skills/`（`skill_policy.reference_sources`）。

forge 的设计是：**SkillSpec 是 canonical**，runtime/executor 看到的 skill 是 projection；`docs/concepts/skill-spec.md` 把 skill 分类为 task / communication / governance / reflection 4 类，并定义了 SkillProposal（人类未批准的 candidate skill 修改）。

## Skill Anatomy

forge 用 **SkillSpec YAML schema**（`schemas/skill.schema.json`），不是 markdown frontmatter。required 字段：`id` / `name` / `version` / `category` / `purpose`。可选 / additionalProperties true：`applies_to`、`inputs`、`outputs`、`runtime_targets`、`executor_targets`、`governance`。

实际 in-tree 唯一一个 SkillSpec-style skill (`lifeforms/software-rd/skills/project-workflow.md`) 用 markdown + YAML frontmatter 混合：

```yaml
---
id: software-rd-project-workflow
name: Software R&D Project Workflow
version: 0.4.0-draft
category: governance
purpose: skill-driven project workflow and risk-based review policy ...
applies_to:
  lifeforms: [software-rd]
  workflow_nodes: [intake, requirements-confirmation, execute, verify, deliver]
inputs: [user_task, project_context, git_diff, risk_level]
outputs: [task_contract, verification_summary, risk_based_review_decision, delivery_report]
runtime_targets: { hermes: { load_as: project_workflow_skill } }
executor_targets:
  codex: { role: executor_under_runtime_control }
  claude_code: { role: optional_independent_reviewer, trigger: risk_based_review }
review_policy:
  mode: risk_based_review
  default_review_required: false
  required_when: [release_gate, canonical_schema_change, lifeform_spec_change, ...]
  optional_when: [documentation_only, low_risk_local_script, ...]
governance:
  owner: forge
  canonical_source: SkillSpec
  change_requires_approval: true
---

# Software R&D Project Workflow
...
```

skill 不放在 `skills/` 顶级目录，而是 `lifeforms/<lifeform-id>/skills/`——按 lifeform 隔离。

**LifeformSpec schema** (`schemas/lifeform.schema.json`)：required `id` / `name` / `version` / `type` / `charter` / `workflow_spec` / `runtime_targets`；可选 `task_contract_policy`、`tool_policy`、`skill_policy`、`context_policy`、`learning_policy`、`evolution_policy`、`evaluation`。

`charter` 含 `role` / `purpose` / `long_term_outcomes` / `principles` / `boundaries`。`workflow_spec` 是真正的状态机：`mode: task_workflow` / `start_node` / `end_nodes` / `actors` / `nodes`，每个 node 有 `type` / `actor` / `next` 或 `rules`。

## Cross-cutting Mechanisms

**workflow-spec 是真状态机，不是 prose**: forge 的 lifeform.yaml `workflow_spec.nodes` 用 `rules: [{when: ..., then: ...}]` 表达 condition-based transition。例如 `software-rd` lifeform 的 `execute` node：

```yaml
execute:
  type: execution
  actor: primary_runtime_instance
  rules:
  - when: task_needs_code_generation == true and actor_available("codex_executor") == true
    then: codex-exec
  - when: task_needs_independent_review == true and actor_available("claude_code_executor") == true
    then: claude-review
  - when: execution_done == true
    then: verify
```

这是 4 个项目里**唯一**形式化的 workflow state machine（dev-workflow-skills 的状态机是 prose；foreman 也是 prose）。

**risk-based review** 替代 mandatory cross-review：每个改动按风险类型决定要不要 independent review；可执行的判定列在 `software-rd/skills/project-workflow.md` 的 `review_policy.required_when` / `optional_when`。低风险跳过 review 时必须在 progress / disposition 写 skipped reason。

**Approval & disposition gates**：

- LifeformSpec / SkillSpec / template 等 long-term assets 修改必须经 `evolution_policy.human_approval_required: true` + `changelog_required: true` + `rollback_required: true`
- learning_policy 强 enforce: `auto_append_allowed.workspace_session_observations: true` 但 `lifeform_memory: false` / `skill_spec: false` / `template: false`
- 任何 SkillProposal 必须经 disposition (decision / human_reviewer / evidence_refs / rollback_path) 才能成 canonical

**state management**：与 dev-workflow-skills 类似，根目录 `progress.md`（dashboard）+ `progress-history.md`（append-only）；但 forge 没有 binary script enforce，而是 self-bootstrap research workflow 9 步流程让 agent 手动遵守。

**validation enforcement** = Python CLI binary：

- `python3 -m forge validate <lifeform> --workspace <id>` 校验 canonical assets schema 一致性
- `python3 -m forge compile hermes <lifeform>` 编译 projection（含 manifest + sha256 of source files）
- `python3 -m forge validate-projection hermes <output>` 校验生成的 projection 完整性
- `python3 -m forge validate-result <RunRecord>` 校验 runtime result schema
- `python3 -m forge validate-runtime-instance hermes <handoff>` 校验 Runtime Instance handoff
- 每个 Validation 返回 `ValidationResult` 含 `errors: tuple[ValidationError, ...]`，CLI 据此 exit 0/1

projection 生成时会写 `.forge/manifest.json` 含 source assets 的 id / version / sha256 checksum + projection_id + generated_at + drift 字段；后续 drift detection 可用 manifest 作为 ground truth。

**hooks**: forge 不依赖 plugin host hook；self-bootstrap workflow 是 prose discipline。

## Inter-skill Coordination

forge 的"skill 之间"协调实际上是 **lifeform.yaml workflow_spec.nodes 之间**的协调：

- node 之间通过 `next` 字段串联（线性）
- 通过 `rules` 字段做条件跳转（带条件）
- 通过 `actors` map 把不同 actor（runtime_instance / human / codex_executor / claude_code_executor）绑到 node
- 通过 `gate` 字段标识 node 是 gate（如 `requirements-confirmation`）—— 必须满足条件才能继续
- skill 在 node 上通过 `skills:` 列表声明（如 `intake.skills: [requirements-clarification]`）

discovery 机制：runtime（Hermes）拿到 projection 后按 workflow_spec 执行 nodes；skill 在 node 触发时按 lifeform 的 skill_policy 加载（`reference_sources: [../dev-workflow-skills/]`）。

**没有 SessionStart hook 注入 bootstrap**：bootstrap 责任在 Hermes runtime 自己（forge 不管 runtime 怎么启动），projection 里的 `system_prompt.md` + `runtime_notes.md` + `skills/index.md` 是 runtime 启动时的内容。

## Notable Patterns

**Borrowable**：

1. **Canonical / projection separation**：SkillSpec 是 canonical，runtime/executor skill 是 projection；projection 文件里写 `<!-- Generated by Forge. Do not edit as canonical source. -->` + manifest 引用——彻底解决"agent 改了运行时文件，下次重新生成被覆盖"的问题
2. **Drift detection via manifest**：每个 projection 有 `.forge/manifest.json` 带 source sha256；任何手工修改 projection 文件可被检测
3. **JSON Schema 校验 canonical assets**：Python `jsonschema` lib + 5 个 schema (lifeform / skill / workflow / context-pack / run-record / lifeform-design-session)；validation result tuple-of-error 而不是 throw exception
4. **Workflow as data, not prose**：lifeform.yaml `workflow_spec.nodes.{name}.rules` 是真 condition rule，可被 runtime 直接执行
5. **Risk-based review**：避免 mandatory cross-review 的"每个改动都要找另一个 agent"代价；列举 `required_when` 让"什么必须 review"机械可判定
6. **Lifeform charter 4 字段** (role / purpose / long_term_outcomes / principles / boundaries)：把 agent identity 形式化
7. **learning_policy 显式列 `auto_append_allowed` 与 `proposal_required_for`**：哪些可自动累积、哪些必须 SkillProposal 走人审，零模糊

**Anti-pattern (with evidence)**：

1. **概念过密 / lifeform vs skill vs workflow vs context-pack vs runtime-instance vs run-record 6 个新概念** 一齐引入，新人 onboarding 重；`docs/concepts/` 9 篇 markdown 才能讲清
2. **Skill schema 太开放** (`additionalProperties: true` + 仅 5 必填)：实质上是 prose with frontmatter，没机械约束
3. **In-tree 真实 skill 极少** (1 个)：reference 到 `../dev-workflow-skills/` 的依赖关系当前是相对路径，不是 distribution 机制
4. **risk-based review 当前没有自动判定 driver**：`required_when` 列表是 prose，agent 自己判断是否触发；没有 binary 像 audit-gate 那样 enforce

## Concrete Evidence

Key file paths:

- `/home/cgs/github_projects/forge/AGENTS.md` — self-bootstrap workflow 9 步
- `/home/cgs/github_projects/forge/lifeforms/software-rd/lifeform.yaml` — 完整 LifeformSpec 范本（含 workflow_spec / actors / 6 个 policy）
- `/home/cgs/github_projects/forge/lifeforms/software-rd/skills/project-workflow.md` — 唯一 in-tree 完整 SkillSpec 样例
- `/home/cgs/github_projects/forge/schemas/{lifeform,skill,workflow,context-pack,run-record}.schema.json` — JSON Schema
- `/home/cgs/github_projects/forge/forge/__main__.py` — CLI 入口（validate / compile / run）
- `/home/cgs/github_projects/forge/forge/projection.py` — Hermes projection 编译器（含 sha256 manifest）
- `/home/cgs/github_projects/forge/examples/projections/hermes/software-rd/skills/index.md` — 生成 projection 范本（含 `<!-- Generated by Forge. Do not edit as canonical source. -->` 头）
- `/home/cgs/github_projects/forge/docs/concepts/skill-spec.md` — Skill 4 类分类 + SkillProposal lifecycle

代表性 excerpts：

1. "Forge 是 AI 生命体工厂 / Control Plane，负责定义、生成、治理、评估和进化 Lifeform。Hermes / OpenClaw 是 Runtime Engine。Claude Code / Codex 是 Runtime 可调用的 Executor，不是一等 Runtime。" (`AGENTS.md:7-11`)
2. "`SkillSpec` 是事实源。Hermes skill、OpenClaw skill、Claude Code skill、Codex skill 都是 projection，不应反向成为 canonical source。" (`docs/concepts/skill-spec.md:14-15`)
3. workflow_spec rules: `when: task_needs_code_generation == true and actor_available("codex_executor") == true / then: codex-exec` (`lifeforms/software-rd/lifeform.yaml:86-89`)
4. learning_policy 显式区分： `auto_append_allowed: { workspace_session_observations: true, lifeform_memory: false, skill_spec: false, template: false }` (`lifeforms/software-rd/lifeform.yaml:170-174`)
5. projection 头：`<!-- Generated by Forge. Do not edit as canonical source. -->\n<!-- Source manifest: .forge/manifest.json -->` (`examples/projections/hermes/software-rd/skills/index.md:1-2`)
