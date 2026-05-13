# superpowers — Skill Design Archive

调研对象 source path: `/home/cgs/github_projects/superpowers/`
版本: v5.0.7（来自 `.claude-plugin/plugin.json`）
作者: Jesse Vincent / Prime Radiant

## Project Overview

superpowers 定位为 **"a complete software development methodology for your coding agents"**，把 TDD、root-cause debugging、subagent-driven development、code review 等通用最佳实践打包成 14 个 composable skills。设计目标是 **vendor-neutral**：同一套 skills 同时分发到 Claude Code、OpenAI Codex、Cursor、OpenCode、Copilot CLI、Gemini CLI 6 个平台。

整体哲学：

- **Skills are not prose, they are code that shapes agent behavior** —— SKILL 内容是行为塑造的"代码"，必须经过 adversarial pressure testing 才允许修改（CLAUDE.md 第 90-95 行明文）
- **General-purpose only** —— 拒绝 domain-specific skills；项目级 / 个人 / 团队规则必须发到独立 plugin（CLAUDE.md 第 39-41 行）
- **Zero third-party dependencies** —— 整个 plugin 不依赖任何外部 npm/python 包，只用 bash + plugin host 自带能力
- 强反 anti-pattern 的写法："This is not negotiable. This is not optional. You cannot rationalize your way out of this."

target users：使用支持 skills 的 coding agent harness 的开发者，希望让 agent 在没有人为干预下沿着系统化流程跑。

## Directory Structure

```
superpowers/
├── CLAUDE.md                      # contributor 指南（94% PR 拒绝率叙事）
├── README.md                      # 用户向 / 安装入口
├── RELEASE-NOTES.md
├── package.json                   # 元数据（不是 npm 包）
├── .claude-plugin/
│   ├── plugin.json                # Claude Code plugin 元数据
│   └── marketplace.json           # 自家 marketplace 入口
├── .codex-plugin/plugin.json      # Codex 适配
├── .cursor-plugin/plugin.json     # Cursor 适配
├── .opencode/INSTALL.md + plugins/
├── .codex/INSTALL.md
├── gemini-extension.json          # Gemini CLI extension manifest
├── GEMINI.md                      # Gemini bootstrap
├── AGENTS.md                      # symlink → CLAUDE.md（Codex 风格）
├── hooks/
│   ├── hooks.json                 # SessionStart hook 注册
│   ├── hooks-cursor.json          # Cursor 专用 hook
│   ├── run-hook.cmd               # Windows 兼容 launcher
│   └── session-start              # bash 脚本：注入 using-superpowers 内容
├── skills/                        # 14 个 SKILL，flat namespace
├── agents/code-reviewer.md        # subagent 角色定义
├── commands/{brainstorm,execute-plan,write-plan}.md
├── scripts/                       # 仓库自身的开发脚本
└── tests/                         # skills 的 pressure tests / eval harness
```

vendor-neutral 处理：每个平台一个 `.{platform}-plugin/` 目录承载该平台所需的 manifest，但 **skills 内容不复制**，统一来源是 `skills/`。Gemini 通过 `gemini-extension.json` + `GEMINI.md` 适配。Cursor 单独一份 `hooks-cursor.json`，因为 Cursor hook spec 字段名为 snake_case (`additional_context`) 而不是 nested `hookSpecificOutput.additionalContext`。

session-start 脚本本身就有针对 6 种平台的环境变量检测（`CURSOR_PLUGIN_ROOT` / `CLAUDE_PLUGIN_ROOT` / `COPILOT_CLI`），用 `printf` 而不是 heredoc 避免 bash 5.3+ heredoc hang bug（issue #571）—— 这种 vendor-aware 但 skill-content-neutral 的处理是该项目的标志性做法。

## Skill Inventory

14 个 skills，全部 flat 单层放在 `skills/<name>/`。按概念分类：

| Category | Skills | 一行描述 |
|---|---|---|
| Bootstrap | `using-superpowers` | session 起始 trigger，要求 agent 在 ANY response 前 invoke skill |
| Process | `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `dispatching-parallel-agents` | 设计 → 计划 → 执行 → 并行 |
| Discipline | `test-driven-development`, `systematic-debugging`, `verification-before-completion` | RED-GREEN-REFACTOR / 4-phase debug / evidence-before-claim |
| Collaboration | `requesting-code-review`, `receiving-code-review` | code review 双向流程 |
| Branch ops | `using-git-worktrees`, `finishing-a-development-branch` | 隔离 + 收尾 |
| Meta | `writing-skills` | 创建 / 改 skill 自身（含 anthropic-best-practices.md 完整副本） |

总行数约 3,300 行 SKILL.md（含 14 个），最大文件 `writing-skills/SKILL.md` 655 行；最小 `executing-plans/SKILL.md` 70 行。

## Skill Anatomy

**SKILL.md 必需 frontmatter** (`writing-skills/SKILL.md` 96-103 行)：

```yaml
---
name: kebab-case-name
description: Use when [triggering conditions and symptoms]
---
```

仅两个必填字段，max 1024 chars 整体；`description` 必须 third-person、以 "Use when..." 开头、**禁止概括 workflow**——文档里给了一段长篇论证：description 概括 workflow 会让 Claude 直接照 description 行动而跳过读 SKILL.md 正文（"the trap: descriptions that summarize workflow create a shortcut Claude will take"）。

**Subdirectory 约定**（无 `references/` / `templates/` 强制 split）：

- 主文件总是 `SKILL.md`
- 重型 reference (>100 行 API doc 等) 才独立成兄弟文件，例如 `anthropic-best-practices.md`、`testing-anti-patterns.md`
- 小工具 `scripts/`（仅 brainstorming 有，含一个本地 server 提供 visual companion 功能）
- subagent prompts 作为兄弟 markdown：`implementer-prompt.md` / `spec-reviewer-prompt.md` / `code-quality-reviewer-prompt.md`
- pressure test fixtures 作为兄弟文件：`test-pressure-1.md`、`test-academic.md`（systematic-debugging 内）
- `using-superpowers/` 是唯一带 `references/` 子目录的 skill，里面是 vendor 工具映射 (`copilot-tools.md` / `codex-tools.md` / `gemini-tools.md`)

命名 convention：动名词优先（`creating-skills`, `using-git-worktrees`）；按"做什么"或"核心 insight"命名而不是按概念域名。

## Cross-cutting Mechanisms

**SessionStart hook (Mechanism A)**: `hooks/hooks.json` 注册一个 SessionStart hook，匹配 `startup|clear|compact` 三种事件；脚本读取 `using-superpowers/SKILL.md` 内容并整段 inline 到 `additionalContext` 注入到系统上下文。这就是 superpowers 的"bootstrap"——`using-superpowers` skill 成为 session 起始唯一 always-loaded 内容，其他 skill 通过 `Skill` tool 按需加载。

**No central protocol skill**：与其他 3 个项目不同，superpowers **没有** `workflow-protocol` 之类的"被其他 skill 必读"的协议层。每个 skill 各自独立完整，需要时 cross-reference 用 markdown 写：`**REQUIRED BACKGROUND:** You MUST understand superpowers:test-driven-development`。

**No state machine / no progress.md**：superpowers 不管理项目状态、不写 dashboard。

**Validation enforcement = pressure test, not script**：`writing-skills/testing-skills-with-subagents.md` 是验证主入口——通过 dispatching subagent 跑 pressure scenario 看 skill 是否真的让 agent 遵守。没有 binary script 校验 frontmatter / structure；CLAUDE.md 明文拒绝任何"compliance check"风格的修改 PR。

**Hooks scope**：仅一个 SessionStart hook 注入 bootstrap；没有 PostToolUse / UserPromptSubmit / Stop hook。设计假设是 LLM 自驱式遵守 skill 内容。

## Inter-skill Coordination

**Mandatory invocation pattern**: `using-superpowers/SKILL.md` 用 `<EXTREMELY-IMPORTANT>` + 12 行 "Red Flags" 表反复说"任何 1% 可能 skill 适用就必须 invoke"。同时 SessionStart 注入又重复一遍这个原则。

**Cross-skill reference 风格**：

- `**REQUIRED SUB-SKILL:** Use superpowers:test-driven-development`
- `**REQUIRED BACKGROUND:** You MUST understand superpowers:systematic-debugging`
- 明令禁止 `@skills/.../SKILL.md` 这种 force-load 写法（"force-loads, burns context"）

**Workflow 链**（README 描述，但不是状态机）：brainstorming → using-git-worktrees → writing-plans → subagent-driven-development → test-driven-development → requesting-code-review → finishing-a-development-branch。每个 skill 的 flowchart 用 graphviz dot 嵌在 markdown 里，并在末端 box 标 `[shape=doublecircle]` 表示终态（往往是 invoke 下一个 skill）。

**Subagent dispatch**：`subagent-driven-development` 每个 task 都 dispatch fresh subagent，并强制两段 review（spec compliance review → code quality review），各自有专门 prompt 文件 (`spec-reviewer-prompt.md`、`code-quality-reviewer-prompt.md`)。subagent 通过工具 dispatch 实现，不依赖外部状态。

## Notable Patterns

**Borrowable**：

1. **Bootstrap via SessionStart**: 一个 hook 注入 bootstrap skill，其他 skill 按需加载，这是当前 4 个项目里最优雅的"避免 always-on context burn"方案
2. **Vendor adaptation in hook script**：`session-start` 单脚本通过环境变量分流 6 个平台输出格式，skill 内容统一不变
3. **`description` 不能概括 workflow** 的反 anti-pattern 论证（`writing-skills/SKILL.md` 154-167 行）—— 测试驱动得出，比直觉反直觉
4. **Pressure-test driven skill development**：`testing-skills-with-subagents.md` 给了 RED-GREEN-REFACTOR 应用到 documentation 的完整方法论
5. **Graphviz flowchart 内嵌 markdown**，在 dev 时通过 `render-graphs.js` 渲染 SVG 给人看；运行时仍是 LLM 读的 dot 文本
6. **Anti-pattern 段落格式**：每个有 disciplinary 性质的 skill 都有 "Red Flags" 表 + "Common Rationalizations" 列表

**Anti-pattern (with evidence)**：

- 没有项目状态管理这件事是个 design choice，但代价是无法支持 multi-session / 跨人协作的项目；不是 anti-pattern，而是 scope 限制
- `writing-skills/SKILL.md` 长达 655 行+多个 sibling reference，自己都违反"keep skills slim"的建议——某种程度上的 borderline 自相矛盾

## Concrete Evidence

Key file paths:

- `/home/cgs/github_projects/superpowers/skills/using-superpowers/SKILL.md` — bootstrap skill
- `/home/cgs/github_projects/superpowers/hooks/session-start` — vendor-aware hook 脚本
- `/home/cgs/github_projects/superpowers/skills/writing-skills/SKILL.md` — meta skill 自身（含 description anti-pattern 论证）
- `/home/cgs/github_projects/superpowers/skills/test-driven-development/SKILL.md` — Iron Law 式 discipline skill 范本
- `/home/cgs/github_projects/superpowers/skills/subagent-driven-development/{SKILL,implementer-prompt,spec-reviewer-prompt,code-quality-reviewer-prompt}.md` — 多 subagent 协作范本

代表性 excerpts (1-3 行)：

1. "If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill." (`using-superpowers/SKILL.md:11`)
2. "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST. Write code before the test? Delete it. Start over." (`test-driven-development/SKILL.md:33-37`)
3. "Skills are not prose — they are code that shapes agent behavior." (`CLAUDE.md:90`)
4. "the trap: descriptions that summarize workflow create a shortcut Claude will take. The skill body becomes documentation Claude skips." (`writing-skills/SKILL.md:158`)
5. SessionStart hook 输出 dispatcher：`if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then printf '{"additional_context":...}'; elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then printf '{"hookSpecificOutput":...}'; else printf '{"additionalContext":...}'; fi` (`hooks/session-start:46-55`)
