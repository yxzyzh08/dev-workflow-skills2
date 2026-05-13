# Directory Layout (Full)

本 reference 是 doc-guardian Section 3 (Doc Type Catalog) 与 frontmatter-schema.md (Path Rules) 的权威路径来源。`validate.py` 的类 1 (Path) check 严格按本表。

**单一事实源**：本文件。SKILL.md 与 frontmatter-schema.md 仅引用，不重复。

---

## 1. 完整目录树

```
my-project/
├── AGENTS.md                              # 治理层
├── CLAUDE.md                              # @AGENTS.md
├── progress.md                            # workflow-protocol 管理
├── progress-history.md                    # workflow-protocol 管理
├── .progress.lock                         # flock 文件，自动管理
│
├── docs/
│   ├── prd/                               # 项目级
│   │   ├── prd.md
│   │   └── supporting/
│   │       ├── competitor_research.md
│   │       ├── competitor_architecture.md
│   │       ├── market_research.md
│   │       ├── user_scenario_analysis.md
│   │       ├── non_goals.md
│   │       ├── risk_analysis.md
│   │       ├── feature_matrix.md                       # S3 必备
│   │       └── source_product_prd_analysis.md          # S3 必备
│   │
│   ├── architecture/                      # 项目级
│   │   └── architecture.md
│   │
│   ├── release0.1/                        # 第 1 个 release
│   │   ├── srs/
│   │   │   ├── srs.md                                  # 必备
│   │   │   ├── acceptance_plan.md                      # 必备
│   │   │   ├── integration_plan.md                     # 多模块必备
│   │   │   ├── source_product_srs_analysis.md          # S3 必备
│   │   │   ├── source_module_analysis.md               # S3 必备
│   │   │   ├── reuse_replace_capability.md             # S3 必备
│   │   │   └── technical_debt_analysis.md              # S3 推荐
│   │   ├── architecture_delta.md                       # 本 release 改架构时
│   │   ├── development/
│   │   │   ├── plan.md
│   │   │   ├── breakdown.md
│   │   │   └── tasks/
│   │   │       ├── T1/
│   │   │       │   ├── detailed_design.md
│   │   │       │   ├── test_review_report.md           # v0.6 新增（与 code-review-report 对称）
│   │   │       │   ├── code_review_report.md
│   │   │       │   └── verification_result.md
│   │   │       └── T2/...
│   │   ├── testing/
│   │   │   ├── preparation.md
│   │   │   ├── procedure.md
│   │   │   └── report.md
│   │   └── delivery/
│   │       ├── deployment.md
│   │       ├── operation_manual.md
│   │       └── installation_result.md
│   │
│   ├── release0.2/  ...                   # 后续 release（结构同 0.1）
│   │
│   ├── retrospective/                     # 项目级，每 release 增量加节
│   │   └── retrospective.md
│   │
│   ├── cr/                                # 跨 release，按 ID 命名
│   │   ├── CR-001.md
│   │   └── CR-002.md
│   │
│   ├── bug/                               # 跨 release
│   │   ├── BUG-001.md
│   │   └── BUG-002.md
│   │
│   └── incident/                          # PRD 异常 incident report
│       └── INCIDENT-001.md
│
├── src/                                   # 源代码（doc-guardian 不管辖）
└── tests/                                 # 测试代码（doc-guardian 不管辖）
    ├── unit/
    └── integration/
```

---

## 2. Type → Path 严格映射

`validate.py` 类 1 (Path) check 按下表严格匹配。文件 frontmatter 的 `type` 必须对应正确路径。

### 2.1 项目级（不绑定 release）

| Type | 路径 |
|------|------|
| `prd` | `docs/prd/prd.md`（**唯一一份**）|
| `architecture` | `docs/architecture/architecture.md`（**唯一一份**）|
| `retrospective` | `docs/retrospective/retrospective.md`（**唯一一份**）|

### 2.2 PRD 附属（项目级）

| Type | 路径 |
|------|------|
| `competitor-research` | `docs/prd/supporting/competitor_research.md` |
| `competitor-architecture` | `docs/prd/supporting/competitor_architecture.md` |
| `market-research` | `docs/prd/supporting/market_research.md` |
| `user-scenario-analysis` | `docs/prd/supporting/user_scenario_analysis.md` |
| `non-goals` | `docs/prd/supporting/non_goals.md` |
| `risk-analysis` | `docs/prd/supporting/risk_analysis.md` |

### 2.3 source-system-analysis（按 analysis_kind）

| `analysis_kind` | 路径 |
|-----------------|------|
| `prd-level` | `docs/prd/supporting/source_product_prd_analysis.md`（项目级）|
| `feature-matrix` | `docs/prd/supporting/feature_matrix.md`（项目级）|
| `srs-level` | `docs/release{release}/srs/source_product_srs_analysis.md`（release 级）|
| `module-level` | `docs/release{release}/srs/source_module_analysis.md`（release 级）|
| `reuse-replace` | `docs/release{release}/srs/reuse_replace_capability.md`（release 级）|
| `technical-debt` | `docs/release{release}/srs/technical_debt_analysis.md`（release 级）|

### 2.4 Release 级（绑定 `release` 字段）

| Type | 路径 |
|------|------|
| `srs` | `docs/release{release}/srs/srs.md` |
| `acceptance-plan` | `docs/release{release}/srs/acceptance_plan.md` |
| `integration-plan` | `docs/release{release}/srs/integration_plan.md` |
| `architecture-delta` | `docs/release{release}/architecture_delta.md` |
| `development-plan` | `docs/release{release}/development/plan.md` |
| `task-breakdown` | `docs/release{release}/development/breakdown.md` |
| `test-preparation` | `docs/release{release}/testing/preparation.md` |
| `test-procedure` | `docs/release{release}/testing/procedure.md` |
| `test-report` | `docs/release{release}/testing/report.md` |
| `deployment-doc` | `docs/release{release}/delivery/deployment.md` |
| `operation-manual` | `docs/release{release}/delivery/operation_manual.md` |
| `installation-result` | `docs/release{release}/delivery/installation_result.md` |

### 2.5 Per-Task（绑定 `release` + `task_id`）

| Type | 路径 |
|------|------|
| `detailed-design` | `docs/release{release}/development/tasks/{task_id}/detailed_design.md` |
| `test-review-report` | `docs/release{release}/development/tasks/{task_id}/test_review_report.md` |
| `code-review-report` | `docs/release{release}/development/tasks/{task_id}/code_review_report.md` |
| `verification-result` | `docs/release{release}/development/tasks/{task_id}/verification_result.md` |

### 2.6 跨 Release（带 ID，v0.6 round 2 M8 统一为 `{cr_id}` 形式）

| Type | 路径模板 | 示例 |
|------|---------|------|
| `cr` | `docs/cr/{cr_id}.md` | `docs/cr/CR-001.md` |
| `bug-report` | `docs/bug/{bug_id}.md` | `docs/bug/BUG-007.md` |
| `workflow-incident` | `docs/incident/{incident_id}.md` | `docs/incident/INCIDENT-003.md` |

ID 字段值（`cr_id` / `bug_id` / `incident_id`）必须符合 `^(CR|BUG|INCIDENT)-\d{3}$`（3 位 zero-padded）。validate.py 类 1 (Path) 用 ID 字段渲染期望路径，与实际 doc_path 比较。

---

## 3. 命名 Convention

### 3.1 文件名

- **doc 文件**：lowercase + underscore + `.md`（如 `prd.md`、`acceptance_plan.md`）
- **不带 `_claude` 后缀**（早期约定已废弃）
- **ID 类**：大写 + 连字符 + **3 位 zero-padded 数字**（强制：`CR-001.md` ✓ / `CR-1.md` ✗ / `CR-42.md` ✗ — 必须 `CR-042.md`）|

### 3.2 目录名

- **Stage 目录**：lowercase（`prd/`、`srs/`、`architecture/`、`development/`、`testing/`、`delivery/`、`retrospective/`）
- **跨 release 目录**：lowercase 单数名（`cr/`、`bug/`、`incident/`）
- **Release 目录**：`release{x.y}/`（lowercase + 版本号；如 `release0.1/`、`release0.10/`）
- **Task 子目录**：大写 `T` + 数字（`T1/`、`T2/`、`T15/`）

### 3.3 路径格式

- 全部使用 forward slash `/`
- 相对项目根
- 不允许 `./` 前缀
- 不允许 `..` 上行

---

## 4. 不在 doc-guardian 管辖的目录

- `src/`：源代码，由 development-code-write skill 决定结构
- `tests/`：测试代码，由 development-test-write skill 决定结构（按 convention `tests/unit/`、`tests/integration/`）
- `.git/`、`.claude/`、`.agents/`：版本控制 / vendor-specific
- 其他用户自定义目录：doc-guardian 不感知

`validate.py` 类 1 仅校验 `docs/` 目录下的 doc 文件路径合规。`docs/` 之外的文件被忽略。

---

## 5. validate.py 类 1 (Path) 算法

```python
def validate_path(doc_path: str, fm: dict) -> ValidateResult:
    type_id = fm["type"]
    expected_path_template = TYPE_PATH_MAP[type_id]   # 见 §2 表

    # 渲染模板
    expected_path = expected_path_template.format(
        release=fm.get("release"),
        task_id=fm.get("task_id"),
        analysis_kind=fm.get("analysis_kind"),
        # ID 类用 frontmatter 的 cr_id/bug_id/incident_id
        cr_id=fm.get("cr_id"),
        bug_id=fm.get("bug_id"),
        incident_id=fm.get("incident_id"),
    )

    if doc_path != expected_path:
        return fail(f"Path mismatch: {doc_path} should be {expected_path} based on type={type_id}")

    return ok()
```

特殊情况：

- `source-system-analysis` 按 `analysis_kind` 分路径（用 §2.3 表）
- 项目级唯一文件（prd / architecture / retrospective）：路径已 hard-coded，不依赖任何字段
- 跨 release 类（cr / bug-report / workflow-incident）：用 ID 字段渲染

---

## 6. 演化

新增 doc type 时必须：

1. 在本文件 §2 加路径条目
2. 在 frontmatter-schema.md 加 frontmatter 字段定义
3. 在 required-artifacts.md 加 stage 必备/可选清单（如适用）
4. 走 design proposal review cycle，不可直接修订

当前对应 design proposal 版本：v0.5（2026-05-06）+ batch 1 review fixes。
