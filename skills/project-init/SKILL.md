---
name: project-init
description: dev-workflow-skills2 repo bootstrap orchestration skill。在用户想用本 workflow 管理一个**新** project（target dir 不含 progress.md / AGENTS.md / CLAUDE.md / docs/）时由 AGENTS.md Bootstrap 调用，或由 scenario-dispatcher 在判定 S1 / S3 后委派。本 skill 把 templates/managed-project/ 骨架拷贝到 target dir 并替换 placeholder，然后调 progress.py init 创建 progress.md / progress-history.md，最后把控制权交回 scenario-dispatcher / 上游 stage skill。本 skill 不判定 scenario / 不分 bug 根因 / 不写任何 doc body。
authority: 4
references: []
---

# project-init

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` 简写指代脚本；**实际 invocation 必须用完整路径** `skills/workflow-protocol/scripts/progress.py`。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4（与其他 vertical / orchestration skill 同级；位于 `workflow-protocol` / `AGENTS.md` / `doc-guardian` 之后）。

**职责（4 项）**：

1. 校验 target project root（无 `progress.md` / 无 `AGENTS.md` / 无既有 `docs/` 子目录冲突）
2. 拷贝 `templates/managed-project/` 骨架（AGENTS.md / CLAUDE.md / README.md + `docs/{prd,prd/supporting,architecture,retrospective,cr,bug,incident}/` 含 `.gitkeep` 占位）到 target
3. 替换 template 内的 placeholder（`<PROJECT_NAME>` / `<DEV_WORKFLOW_SKILLS_PATH>` / `<DEV_WORKFLOW_SKILLS_URL_OR_PATH>` / `<PROJECT_OVERRIDES_HERE>`）— 与 user 对话获取每个值
4. 调 `progress.py init --root <target> --project <name> --scenario <S1|S3> --release <x.y>` 创建 progress.md / progress-history.md

**不属于本 skill**：

- 判定 scenario（S1 / S2 / S3 / S4）→ `scenario-dispatcher`（本 skill 上游会传入 scenario，不自判）
- 直接 mutation `progress.md` / `progress-history.md`（必经 `progress.py`）
- 写任何 doc body（PRD / SRS / Architecture / BUG / INCIDENT）→ 对应 stage skill
- 创建源代码 / 测试代码 / 业务文件（仅 docs/ 骨架；src/ tests/ 由 user 按 project 习惯决定）
- 推进 stage（→ `progress.py update --advance` 等命令；不属于 init 步骤）
- post-close bug 处理（→ `bug-triage` post-close mode）

## 2. When to Invoke

**典型 invocation 路径**：

| 时机 | 由谁调用 | 期望输出 |
|------|---------|---------|
| 首次会话且用户想用本 workflow 管理一个**新** project | AGENTS.md Bootstrap 第 5 步检测到 user 输入是"新建项目"类指令（"我想用 dev-workflow 管理一个新项目"等）| 本 skill 走 §3 标准流程 |
| `scenario-dispatcher` 判定 S1 / S3 但 target 还没 `progress.md` | dispatcher 在调 `progress.py init` 前委派给本 skill | 本 skill bootstrap target dir + 调 `progress.py init`，再把控制权交回 dispatcher / 后续 stage skill |
| 用户已有部分 doc 草稿但没用本 workflow 管理 | 拒绝（详见 §3 Step 1 校验失败）| 提示用户先备份既有 doc 再 invoke 本 skill；或用 `--force` 选项（**不在 MVP**）|

**不被 invoke 的时机**：

- target dir 已有 `progress.md` → 已经是 managed project；应 invoke `scenario-dispatcher`（或 stage skill）而非 init
- target dir 是 dev-workflow-skills2 spec repo 自身（`skills/workflow-protocol/scripts/progress.py` 存在）→ **拒绝**：spec repo 不应被自管理（与 spec repo `AGENTS.md` "What this repo is NOT" 一致）
- `release_state == closed` 期间用户提新需求 → `scenario-dispatcher` S2 路径，不走本 skill
- post-close bug → `bug-triage` post-close mode

## 3. Standard Procedure（4 步）

### 3.1 Step 1: 校验 target dir 干净

读 target dir 状态：

| 检查 | 通过条件 | 失败处理 |
|------|---------|---------|
| target dir 存在 | 是（如不存在，让 user 先 `mkdir <target>`）| 拒绝 + 提示 |
| `<target>/progress.md` 不存在 | 是 | 拒绝 + 提示用户该 dir 已是 managed project |
| `<target>/progress-history.md` 不存在 | 是 | 同上 |
| `<target>/AGENTS.md` 不存在 | 是（如存在，user 必须先备份移除）| 拒绝 + 提示备份既有文件 |
| `<target>/CLAUDE.md` 不存在 | 是 | 同上 |
| `<target>/docs/` 不存在或为空 | 是（空目录 OK）| 拒绝 + 提示备份既有 docs |
| target 不在 dev-workflow-skills2 spec repo 内 | 是（按 `<target>/skills/workflow-protocol/scripts/progress.py` 是否存在判断）| **绝不**继续；显示与 spec repo `AGENTS.md` "What this repo is NOT" 一致的拒绝信息 |

任一校验失败 → 立即停止；提示用户 + 不做任何文件操作。

**禁止**：

- 在校验失败后用 `--force` / 强制覆盖（**不在 MVP**；如果将来需要，需走 design proposal 加显式 override）
- 静默跳过校验
- 假设 user 已确认（必须基于真实 fs 状态）

### 3.2 Step 2: 拷贝 templates/managed-project/ 骨架

从 spec repo 拷贝到 target：

```bash
cp -r <DEV_WORKFLOW_SKILLS_PATH>/templates/managed-project/* <target>/
```

具体动作（agent 跑这些命令时使用真实路径，不是 placeholder）：

- 拷贝 3 个 root docs：`AGENTS.md` / `CLAUDE.md` / `README.md`
- 拷贝 `docs/` 子目录骨架（含 `.gitkeep` 占位）：`docs/prd/`、`docs/prd/supporting/`、`docs/architecture/`、`docs/retrospective/`、`docs/cr/`、`docs/bug/`、`docs/incident/`

**不拷贝**（事实源 `templates/managed-project/` 不含这些）：

- `progress.md` / `progress-history.md` —— 由 Step 4 `progress.py init` 创建
- `.progress.lock` —— 由 lock 机制按需创建
- 各 release 子目录（如 `docs/release0.1/`）—— 由 stage skill 在 stage 进入时创建
- `src/` / `tests/` —— 项目自己决定结构

**幂等性**：本 skill 仅在 Step 1 校验通过后跑 Step 2。校验保证 target 是干净的；不需要复杂的 merge 逻辑。如果 cp 中途失败（disk full / 权限），让 user 修后从 Step 1 重跑。

### 3.3 Step 3: 替换 template placeholder

template 文件含以下 placeholder（必须在 cp 后立即替换；保留 placeholder 会让下游 session 读到无效引用）：

| Placeholder | 含义 | 来源 |
|-------------|------|------|
| `<PROJECT_NAME>` | 项目名（人读，可空格 / 中文）| 与 user 对话获取 |
| `<DEV_WORKFLOW_SKILLS_PATH>` | spec repo 的绝对路径（agent 用此路径调 `skills/...`）| 由 agent session 自身的 cwd / spec repo 位置决定；与 user 确认 |
| `<DEV_WORKFLOW_SKILLS_URL_OR_PATH>` | README.md 用：可选 spec repo 的 URL（github / GitLab）；不存在则同 `<DEV_WORKFLOW_SKILLS_PATH>` | 与 user 确认 |
| `<PROJECT_OVERRIDES_HERE>` | AGENTS.md "Project-specific overrides" 节占位 | 通常初始为空字符串（user 后续按需自加）|

替换流程：

1. 与 user 对话获取 4 个值；同时在对话中重述每个 placeholder 的含义
2. 用 `sed` 或等价 in-place 替换：

```bash
sed -i "s|<PROJECT_NAME>|<actual name>|g" <target>/AGENTS.md <target>/README.md
sed -i "s|<DEV_WORKFLOW_SKILLS_PATH>|<actual path>|g" <target>/AGENTS.md <target>/README.md
sed -i "s|<DEV_WORKFLOW_SKILLS_URL_OR_PATH>|<actual url or path>|g" <target>/README.md
sed -i "s|<PROJECT_OVERRIDES_HERE>||g" <target>/AGENTS.md
```

3. grep 验证全部 placeholder 已替换：

```bash
grep -rn '<PROJECT_NAME>\|<DEV_WORKFLOW_SKILLS_PATH>\|<DEV_WORKFLOW_SKILLS_URL_OR_PATH>\|<PROJECT_OVERRIDES_HERE>' <target>/
```

期望 0 行输出；若有残留 → 立即告知 user + 不进入 Step 4。

**禁止**：

- 跳过校验直接 Step 4（残留 placeholder 会让 session 读到 `<PLACEHOLDER>` literal 字符串）
- 替换 `progress.md` 内的 placeholder（progress.md 还不存在；Step 4 创建）

### 3.4 Step 4: 调 progress.py init

与 user 对话获取 init 参数：

| 参数 | 含义 | 来源 |
|------|------|------|
| `--project <name>` | 项目内部标识（regex `^[A-Za-z][A-Za-z0-9_.-]{0,63}$`）| 与 user 确认；与 `<PROJECT_NAME>` 可不同（前者是合法 ID，后者是人读名）|
| `--scenario <S1\|S3>` | 由上游传入；本 skill 不自判 | 上游 `scenario-dispatcher` 或 user 直接 |
| `--release <x.y>` | 首 release 版本号（regex `^\d+\.\d+$`，typically `0.1`）| 与 user 确认 |

跑命令：

```bash
python3 <DEV_WORKFLOW_SKILLS_PATH>/skills/workflow-protocol/scripts/progress.py \
    --root <target> \
    init --project <id> --scenario <S1|S3> --release <x.y>
```

期望 exit 0；输出 `progress.py init: created progress.md and progress-history.md (project=<id>, scenario=<S1|S3>, release=<x.y>)`。

非 0 退出 → 读 stderr 修后重试（typically `--scenario` 不在 {S1, S3} 内 / `--project` 含非法字符）。本 skill 不直接 mutation progress.md 修复；让 user / agent 修参数后重跑 init。

### 3.5 Step 5（optional）: 把控制权交回 scenario-dispatcher / stage skill

完成 Step 1-4 后告知 user：

- target dir 已 bootstrap：`<target>/AGENTS.md` / `CLAUDE.md` / `README.md` / `docs/` 骨架已就位
- `progress.md` 显示 `current_stage: prd-inception, sub_state: write`
- 后续动作：在 target dir 起新 session（`cd <target>` 然后 invoke Claude Code / Codex），那个 session 会读 target 的 `AGENTS.md`，按 §When you start a session 流程路由到 `prd-write`（S1 / S3 首次）
- 如果 scenario==S3，**额外提示**：后续 Stage 1 必备 supporting artifacts (`source_product_prd_analysis.md` + `feature_matrix.md`) — 事实源 `<DEV_WORKFLOW_SKILLS_PATH>/skills/doc-guardian/references/required-artifacts.md`

本 skill 在 Step 5 后**退出**；不路由后续 stage skill（target session 自行 bootstrap）。

## 4. Output Contract

本 skill 不直接 mutation `progress.md` / `progress-history.md`（mutation 由 Step 4 调用的 `progress.py init` 内部完成）。本 skill 的"输出"是以下形式：

| 阶段 | 副作用 | 报告给 user |
|------|--------|-----------|
| Step 1 校验失败 | 无文件改动 | 拒绝原因 + 修复建议 |
| Step 1 通过 + Step 2 完成 | target 多 7 个 .gitkeep + 3 个 root docs（含 placeholder）| "templates copied (待 placeholder 替换)" |
| Step 3 完成 | 3 个 root docs placeholder 已替换 | "placeholders replaced; progress.md 待 init" |
| Step 4 完成 | target 多 progress.md + progress-history.md | "init OK; current_stage=prd-inception/write" |
| Step 5 完成 | 无新文件 | "bootstrap finished; please start a new session in <target>" |

## 5. Forbidden Actions

- ❌ 在 target dir 是 dev-workflow-skills2 spec repo 时继续 bootstrap（spec repo 不应被自管理；事实源 spec repo `AGENTS.md` "What this repo is NOT"）
- ❌ 在 target 已有 `progress.md` / `AGENTS.md` / `CLAUDE.md` / 非空 `docs/` 时强制覆盖（必须先让 user 备份移除既有文件）
- ❌ 跳过 §3.3 placeholder 替换直接 Step 4（残留 placeholder 让下游 session 读到 literal `<...>`）
- ❌ 直接编辑 target 的 `progress.md` / `progress-history.md`（mutation 必须经 `progress.py init`）
- ❌ 自判 scenario（→ `scenario-dispatcher` 上游；本 skill 仅消费已传入的 `--scenario`）
- ❌ 创建源代码 / 测试代码 / 业务文件（仅 docs/ 骨架；src/ / tests/ 由 user 决定）
- ❌ 在 Step 4 失败后尝试 `progress.py recover`（recover 仅在 progress.md 与 history 自身不一致时使用；init 失败时 progress.md 不存在，recover 也帮不了）
- ❌ 创建任何 release 子目录 `docs/release<x.y>/`（由后续 stage skill 在 stage 进入时按需创建）

## 6. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| Step 1 检测到 target 已有 `progress.md` | 拒绝 + 提示用户 invoke `scenario-dispatcher`（target 已是 managed project，不是新建场景）|
| Step 1 检测到 target 是 spec repo（含 `skills/workflow-protocol/scripts/progress.py`）| 拒绝；不可在 spec repo 内 init 新 project；用户须 mkdir 独立 dir |
| Step 2 cp 中途失败（disk full / 权限）| 让 user 修 fs 问题后从 Step 1 重跑；不要尝试部分恢复 |
| Step 3 sed 替换后仍有 placeholder 残留 | 不进入 Step 4；显示残留行让 user 修；常见原因：placeholder 含特殊字符（`/` 等 sed delimiter 冲突）需要 escape |
| Step 4 `progress.py init` 退出非 0 | 读 stderr：(a) `--project` 不合法 → 改 ID；(b) `--scenario` 不是 S1/S3 → 与上游 scenario-dispatcher 确认；(c) `--release` 格式错 → 改为 `<int>.<int>` |
| Step 4 期间 target 被并发写入（罕见）| `progress.py init` 自身 flock 拒绝；让 user 释放并发 session 后重试 |
| 完成 bootstrap 后用户发现 placeholder 替换错（如 `<DEV_WORKFLOW_SKILLS_PATH>` 路径错）| 让 user 在 target dir 直接编辑 AGENTS.md / README.md 修；不需重跑 project-init |

## 7. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — `progress.py init` 的事实源
- `skills/workflow-protocol/references/command-reference.md §1` — `init` 子命令完整签名 + 前置条件
- `skills/scenario-dispatcher/SKILL.md` — 场景判定（上游或下游协作；本 skill 不替它判定）
- `skills/doc-guardian/references/directory-layout.md` — managed project 目录结构事实源
- `skills/doc-guardian/references/required-artifacts.md` — S3 后续 stage 必备 supporting artifacts（Step 5 提示用）

**模板源**：

- `templates/managed-project/AGENTS.md` — 下游 project 治理层模板
- `templates/managed-project/CLAUDE.md` — 下游 project Claude Code 入口模板
- `templates/managed-project/README.md` — 下游 project README 模板
- `templates/managed-project/docs/{prd,prd/supporting,architecture,retrospective,cr,bug,incident}/.gitkeep` — `docs/` 骨架占位

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md` — Workflow spec
- `docs/design/skill_set_design_proposal_v0.5.md` — 完整设计方案

**本 skill references**：

当前阶段骨架不含 references。如未来 placeholder / 校验逻辑复杂化，可拆出：
- `references/bootstrap-checklist.md`（详细 §3 步骤 + 边界处理）
- `references/template-placeholders.md`（每个 placeholder 的格式 / 替换规则 / 校验）

**Design Notes**：

- **Phase 7 Task 7-C 新增**：本 skill 解决 spec gap "init 应一步完成 repo bootstrap"；之前仅 `progress.py init` 创建 progress.md / history，AGENTS.md / CLAUDE.md / docs/ 骨架由 user 手动 cp。
- **不引入新 progress.py 子命令**：保持 `progress.py` 单一职责（只 mutate progress.md / history）；本 skill 是 prose-level orchestrator，cp / sed / progress.py init 由 agent 在 dialogue 中按 §3 流程跑。
- **未来扩展候选**：
  - 加 `--force` 校验 override（需 design proposal）
  - 加可选 `src/` / `tests/` 骨架模板（按 project 类型分）
  - 加 git init / `.gitignore` 默认（typically `.progress.lock` 应进 ignore）
