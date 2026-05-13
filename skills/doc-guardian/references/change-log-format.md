# Change Log Format

本 reference 是 doc-guardian Section 6 (Change Log Mechanism) 的详细规范。`changelog.py` 的 `promote` 与 `validate` 子命令严格按本表实现。`validate.py` 类 6 (Change Log Discipline) check 也按本表。

**单一事实源**：本文件。SKILL.md 仅引用，不重复格式细节。

---

## 1. 适用 doc 类型

只有"增量类"doc 必须含 `## Pending Changes` 与 `## Change Log` 两个章节：

| Doc Type | 是否含 Change Log |
|----------|------------------|
| `prd` / `architecture` / `retrospective` | ✓ 项目级，跨 release 增量 |
| `srs` / `acceptance-plan` / `integration-plan` / `architecture-delta` | ✓ release 级，可能在 active release 内变更 |
| `development-plan` / `task-breakdown` | ✓ release 级，可能动态调整 |
| `cr` / `bug-report` / `workflow-incident` | ✓ 跨 release，状态推进时增量 |
| `detailed-design` | ✓ per-task，可能多次修订 |
| `test-preparation` / `test-procedure` / `test-report` | ✗ 一次性产出，不需 change log |
| `deployment-doc` / `operation-manual` / `installation-result` | ✗ 一次性 |
| `code-review-report` / `test-review-report` / `verification-result` | ✗ 一次性 |
| `source-system-analysis` 系列 | ✗ 一次性（特定 stage 的快照） |

`validate.py` 类 6 仅对前一类 doc 强制 Change Log 章节存在与格式合规；后一类 doc 可不含这两个章节。

---

## 2. Pending Changes 章节格式

### 2.1 章节位置

紧接 doc 主体后，`## Change Log` 之前。每份增量类 doc 必须有此章节，可为空：

```markdown
---
[frontmatter]
---

# Document Title

## 1. ...
## 2. ...
... (主体内容)

## Pending Changes

[entries here, or empty]

## Change Log

[grouped historical entries]
```

### 2.2 严格 entry 格式

每条 entry 必须严格符合：

```
- {timestamp} [{section_ref}]: {summary}
```

- `timestamp`：ISO8601 UTC 精确到秒（regex `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`）
- `section_ref`：方括号包裹的章节引用，可选值：
  - `Section X.Y`（如 `Section 3.2`）
  - `Section X`（如 `Section 4`）
  - `frontmatter`
  - `全文`（grand-scale rewrite）
- `summary`：单行变更描述，结尾不带句号

**合法示例**：

```markdown
## Pending Changes
- 2026-05-15T10:00:00Z [Section 3.2]: 新增用户认证需求
- 2026-05-15T10:30:00Z [Section 1.3]: 精简产品边界描述
- 2026-05-15T11:00:00Z [frontmatter]: 更新 status 至 review-passed
```

**非法示例**（`changelog.py` 拒绝）：

```markdown
- 2026-05-15: missing seconds and Z          # timestamp 不合法
- [Section 3.2]: missing timestamp            # 缺 timestamp
- 2026-05-15T10:00:00Z 新增需求               # 缺 [section_ref]
- 2026-05-15T10:00:00Z [3.2]: missing 'Section' prefix  # section_ref 不合法
```

### 2.3 空章节

`## Pending Changes` 章节 body 为空（或仅空白行）即合法。`validate.py` 类 6 校验：

- ✓ `## Pending Changes\n\n## Change Log` （空）
- ✓ `## Pending Changes\n<!-- comments allowed -->\n\n## Change Log` （仅注释）
- ✗ 章节内有任何非注释、非空白行的内容

---

## 3. Change Log 章节格式

### 3.1 章节结构

```markdown
## Change Log

### 2026-05-15

- 2026-05-15T10:00:00Z [Section 3.2]: 新增用户认证需求
- 2026-05-15T10:30:00Z [Section 1.3]: 精简产品边界描述
- 2026-05-15T11:00:00Z [frontmatter]: 更新 status 至 review-passed

### 2026-05-10

- 2026-05-10T08:00:00Z [Section 4.1]: 初始版本创建
```

### 3.2 日期分组规则

- 同一天的 entries 合并到一个 `### YYYY-MM-DD` 块（按 timestamp 的日期部分判断）
- 日期块按时间倒序排列（最新日期在最上）
- 日期块内 entries 按 timestamp 升序（同一天内时间从早到晚）

### 3.3 严格性

`changelog.py validate` 与 `validate.py` 类 6 校验：

- 日期格式必须是 `### YYYY-MM-DD`
- 日期块之间必须空一行
- entry 格式同 §2.2

---

## 4. `changelog.py promote` 算法

```python
def promote(doc_path: str) -> None:
    content = read_file(doc_path)
    pending_section = extract_section(content, "## Pending Changes")
    changelog_section = extract_section(content, "## Change Log")

    # 1. 解析 pending entries
    pending_entries = parse_entries(pending_section)
    if not pending_entries:
        return  # 无内容可 promote，直接 exit 0

    # 2. 校验每条 entry 格式
    for entry in pending_entries:
        if not is_valid_entry(entry):
            sys.exit(1)  # 非法 entry → fail，不修改文件

    # 3. 合并到 changelog（按日期分组）
    grouped_pending = group_by_date(pending_entries)
    existing_groups = parse_changelog_groups(changelog_section)
    merged_groups = merge_groups(existing_groups, grouped_pending)
    sorted_groups = sort_by_date_desc(merged_groups)

    # 4. 渲染新 changelog 内容
    new_changelog_body = render_groups(sorted_groups)

    # 5. atomic 写回：备份 → 写新内容 → 校验 → 解备份
    new_content = replace_section(content, "## Change Log", new_changelog_body)
    new_content = replace_section(new_content, "## Pending Changes", "")  # 清空 pending

    write_atomic(doc_path, new_content)


def is_valid_entry(line: str) -> bool:
    pattern = r'^- (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \[(Section \d+(\.\d+)?|frontmatter|全文)\]: \S.*$'
    return re.match(pattern, line) is not None
```

---

## 5. `changelog.py validate` 算法

```python
def validate_changelog(doc_path: str) -> ValidateResult:
    content = read_file(doc_path)
    pending_section = extract_section(content, "## Pending Changes")
    changelog_section = extract_section(content, "## Change Log")

    issues = []

    # 1. 必须有这两个章节（仅对增量类 doc）
    if doc_type_requires_changelog(get_frontmatter(content)["type"]):
        if pending_section is None:
            issues.append("Missing ## Pending Changes section")
        if changelog_section is None:
            issues.append("Missing ## Change Log section")

    # 2. Pending Changes 必须为空（已 promote）
    pending_entries = parse_entries(pending_section)
    if pending_entries:
        issues.append(f"Pending Changes has {len(pending_entries)} unpromoted entries; run changelog.py promote first")

    # 3. Pending entries（如有）必须符合格式
    for entry in pending_entries:
        if not is_valid_entry(entry):
            issues.append(f"Invalid pending entry: {entry}")

    # 4. Change Log 日期分组与 entry 必须符合格式
    for group_header in extract_group_headers(changelog_section):
        if not re.match(r'^### \d{4}-\d{2}-\d{2}$', group_header):
            issues.append(f"Invalid changelog group header: {group_header}")
    for entry in extract_changelog_entries(changelog_section):
        if not is_valid_entry(entry):
            issues.append(f"Invalid changelog entry: {entry}")

    return ok() if not issues else fail(issues)
```

---

## 6. validate.py 类 6 (Change Log Discipline) 集成

`validate.py file <doc-path>` 调用 `changelog.py validate <doc-path>` 作为类 6 实现。

任一类 6 issue → exit 1。

---

## 7. `*-write` skill 调用模式

每个增量类 doc 的 `*-write` skill 流程：

```
1. 生成/修改 doc 主体内容
2. 在 ## Pending Changes 章节追加新 entry（按严格格式）
3. 运行 skills/doc-guardian/scripts/changelog.py promote <doc-path>
   - 若有未 promote 的 entries：移到 Change Log
   - 若 entries 格式非法：exit 1，AI 必须修复 entry 格式后重试
4. 运行 skills/doc-guardian/scripts/validate.py file <doc-path>
   - 类 6 此时应通过（Pending Changes 为空、Change Log 格式合法）
   - 若失败：AI 修复后重试
5. 提交给对应 *-review skill
```

第 2-3 步可重复（每次新变更追加 → promote → 追加）。第 4-5 步是该 doc 完成阶段才需要。

### 7.1 `status_transition.py` helper 调用模式（Task 6 Gap-2）

`skills/doc-guardian/scripts/status_transition.py apply --event <event> --doc <path> ...` 是 doc frontmatter `status` mutation owner。对增量类 doc，helper 必须在同一 transaction 内执行：

1. 更新 frontmatter `status` 与 `updated`
2. 追加 Pending Changes entry：
   `- <ISO8601 UTC> [frontmatter]: 更新 status 至 <new-status>`
3. 调用与 `changelog.py promote` 等价的内存 promote 逻辑
4. 写回前校验 Change Log discipline
5. 多 doc 任一失败时 rollback 全部已写 doc

若 doc 已经处于目标 status，helper 应幂等 exit 0，不重复添加 Change Log entry。

---

## 8. Forbidden Actions（防 bypass）

`validate.py` 与 `changelog.py` 共同防止以下 bypass：

| Bypass 尝试 | 防御机制 |
|------------|---------|
| 直接编辑 `## Change Log` 章节 | `validate.py` 类 6 校验 entries 格式；恶意编辑会被发现（如格式不严格、日期错误等）。本身不能 100% 防御，但脚本流程鼓励 promote 路径 |
| 直接清空 `## Pending Changes`（绕过 promote）| `validate.py` 类 6 通过；但 `progress-history.md` 没有对应 promote 事件 → 一致性校验失败（cross-check via history audit） |
| 修改 `## Change Log` 已有 entry | 现版本无强加密验证；依赖 git diff review；未来可加 hash-chain |
| 改 entry 时间戳 | 弱防御：timestamp 必须递增（同一天内）；validate.py 检查时间戳单调性 |

强约束：

- ❌ 跳过 `changelog.py promote` 直接清空 `## Pending Changes`
- ❌ 不通过 `*-write` skill 直接编辑 doc 的 `## Pending Changes`（必须经 skill 流程）
- ❌ 修改 `## Change Log` 中已 promote 的历史 entry

如果 v1 实现暴露 bypass 风险，未来通过 git pre-commit hook 增强（不在本 skill 范围）。

---

## 9. 演化

新增 entry section_ref 类型时（如 `Appendix A`），更新 §2.2 的 enum 与 `is_valid_entry` regex。

当前对应 design proposal 版本：v0.5（2026-05-06）+ batch 1 review fixes。
