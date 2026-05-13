# Required Artifacts (Scenario-Aware Map)

本 reference 是 doc-guardian 与 workflow-protocol 共享的"P6 必备 artifact 数据源"。`progress.py update --advance` 调用 `validate.py file <each artifact>` 时按本文件查询应校验哪些 artifact 路径。

**消费方**：

- `progress.py update --advance`：按 `(scenario, scenario_subtype, current_stage, release, srs.is_multi_module, srs.architecture_change)` 查找 stage 必备清单
- `validate.py consistency`：cross-file 一致性 check 时按本文件确认所有应存在的 artifact 都在
- 各 `*-write` skill：知道自己应产出哪些 artifact

**单一事实源**：本文件。workflow-protocol 不重复列必备清单，仅引用本文件。

## Condition DSL 规范（v0.6 round 2 H1 新加）

condition 字段使用受限 DSL，**仅允许以下变量与运算符**（实现者用白名单 parser，禁止裸 `eval`）：

**允许的变量**（来自 progress.md 或指定 doc 的 frontmatter）：

| 变量 | 类型 | 来源 | 默认值 |
|------|------|------|--------|
| `scenario` | enum (S1\|S2\|S3\|S4) | progress.md `scenario` | 必有 |
| `scenario_subtype` | enum or null | progress.md `scenario_subtype` | null |
| `current_stage` | enum | progress.md `current_stage` | 必有 |
| `release` | string | progress.md `release` | 必有 |
| `srs.is_multi_module` | bool | `<srs artifact>` frontmatter `is_multi_module` | false（若 SRS 不存在或字段缺失）|
| `srs.architecture_change` | bool | `<srs artifact>` frontmatter `architecture_change` | false |

**允许的运算符**：`==`、`!=`、`&&`（and）、`||`（or）、`()` 分组。不允许函数调用、属性链长度 > 2、字面量除 enum/bool/string。

**完整 grammar（v0.6 round 4 M2 补全）**：

```
<expr>       = <or-expr>
<or-expr>    = <and-expr> ( '||' <and-expr> )*
<and-expr>   = <primary> ( '&&' <primary> )*
<primary>    = <comparison> | '(' <expr> ')'
<comparison> = <variable> ('==' | '!=') <literal>
<variable>   = <identifier> ('.' <identifier>)?         # 属性链长度 ≤ 2
<literal>    = <enum-literal> | <bool> | <quoted-string>
<bool>       = 'true' | 'false'
<enum-literal>   = unquoted token from whitelist below
<quoted-string>  = '"' [^"]* '"'                         # hyphenated 或包含特殊字符的 literal 必须加引号
<identifier> = [a-z][a-z0-9_]*                           # 不允许 hyphen 或大写
```

**Enum literal 白名单**（仅以下 unquoted token 视为 enum literal；其他 token 一律按 identifier 解析）：

| 来源变量 | 合法 enum literal |
|---------|-------------------|
| `scenario` | `S1` / `S2` / `S3` / `S4` |
| `scenario_subtype` | `S2-1` / `S2-2` / `S2-3` / `S2-4` |
| `current_stage` | `prd-inception` / `srs-specification` / `architecture-design` / `development` / `testing` / `delivery` / `project-retrospective` / `workflow-incident-analysis` |

**注意 hyphenated enum**（`S2-1`、`srs-specification` 等）由 tokenizer 按"字母数字-连字符"识别，但**仅**当出现在 `<comparison>` RHS 位置才视为 enum literal；其他位置（变量名等）报错。

**示例合法 condition**：

- `scenario == S3`（最简）
- `srs.is_multi_module == true`（bool）
- `scenario == S3 && current_stage == srs-specification`（hyphenated enum）
- `(scenario == S2 && scenario_subtype == S2-2) || scenario == S3`（带括号）

**示例非法 condition**（parser 应 reject）：

- `scenario == "S3"`（quoted enum——加引号转 string，与 enum 类型不匹配）
- `srs.is_multi_module && srs.architecture_change`（缺比较运算符）
- `is_admin(scenario)`（函数调用）
- `srs.detail.is_multi == true`（属性链长度 > 2）
- `scenario = S3`（用 `=` 而非 `==`）

**Parser test cases（实现者应至少覆盖）**：

1. `scenario == S3` → True/False 取决于 progress
2. `srs.is_multi_module == true` → 同上
3. `(scenario == S2) && (current_stage == srs-specification)` → 括号支持
4. `srs.unknown_field == true` → ValueError（变量不在白名单）
5. `is_admin(scenario)` → ValueError（函数调用）
6. `current_stage == not-a-stage` → ValueError（hyphenated enum 但不在白名单）

---

## 1. 路径模板约定

所有路径相对项目根，使用 forward slash。模板变量：

| 变量 | 取值来源 |
|------|---------|
| `{release}` | progress.md `release` 字段（如 `0.1`、`0.2`）|
| `{task_id}` | progress.md `development_state.task_states` 中的 key（如 `T1`、`T2`）|

---

## 2. Stage 1: PRD Inception

```yaml
prd_inception:
  required:
    - type: prd
      path: docs/prd/prd.md
  conditional:
    - type: source-system-analysis
      analysis_kind: prd-level
      path: docs/prd/supporting/source_product_prd_analysis.md
      condition: scenario == S3
    - type: source-system-analysis
      analysis_kind: feature-matrix
      path: docs/prd/supporting/feature_matrix.md
      condition: scenario == S3
  optional:
    - type: competitor-research
      path: docs/prd/supporting/competitor_research.md
    - type: competitor-architecture
      path: docs/prd/supporting/competitor_architecture.md
    - type: market-research
      path: docs/prd/supporting/market_research.md
    - type: user-scenario-analysis
      path: docs/prd/supporting/user_scenario_analysis.md
    - type: non-goals
      path: docs/prd/supporting/non_goals.md
    - type: risk-analysis
      path: docs/prd/supporting/risk_analysis.md
```

---

## 3. Stage 2: SRS Specification

```yaml
srs_specification:
  required:
    - type: srs
      path: docs/release{release}/srs/srs.md
    - type: acceptance-plan
      path: docs/release{release}/srs/acceptance_plan.md
  conditional:
    - type: integration-plan
      path: docs/release{release}/srs/integration_plan.md
      condition: srs.is_multi_module == true   # 由 srs frontmatter 字段 is_multi_module 决定
    - type: source-system-analysis
      analysis_kind: srs-level
      path: docs/release{release}/srs/source_product_srs_analysis.md
      condition: scenario == S3
    - type: source-system-analysis
      analysis_kind: module-level
      path: docs/release{release}/srs/source_module_analysis.md
      condition: scenario == S3
    - type: source-system-analysis
      analysis_kind: reuse-replace
      path: docs/release{release}/srs/reuse_replace_capability.md
      condition: scenario == S3
  optional:
    - type: source-system-analysis
      analysis_kind: technical-debt
      path: docs/release{release}/srs/technical_debt_analysis.md
      # 推荐但非必备（v0.6 决议；与 v0.5 §5.3 一致）
```

**S3 Stage 2 必备 = 3 类**（srs-level / module-level / reuse-replace），technical-debt 推荐但不必备。如果未来基于实践发现 technical-debt 也应必备，单独通过 review cycle 升级。

---

## 4. Stage 3: Architecture Design

```yaml
architecture_design:
  required:
    - type: architecture
      path: docs/architecture/architecture.md
  conditional:
    - type: architecture-delta
      path: docs/release{release}/architecture_delta.md
      condition: srs.architecture_change == true   # 由 SRS frontmatter 字段 architecture_change 决定（默认 false）
```

---

## 5. Stage 4: Development

Stage 4 done 由 task state 决定（all task_states[Tn] == "verified"）。Stage 4 advance 时**对每个 task 无条件校验全部 4 个 per-task artifacts**（v0.6 round 2 M6 简化：避免 substate_matches 语义模糊）：

```yaml
development_per_task:
  required:
    # Stage 4 advance 时，对每个 task_id ∈ task_states 无条件全部校验
    - type: detailed-design
      path: docs/release{release}/development/tasks/{task_id}/detailed_design.md
    - type: test-review-report
      path: docs/release{release}/development/tasks/{task_id}/test_review_report.md
    - type: code-review-report
      path: docs/release{release}/development/tasks/{task_id}/code_review_report.md
    - type: verification-result
      path: docs/release{release}/development/tasks/{task_id}/verification_result.md
```

**Note**：之前 v0.6 round 1 写过 `task_substate_required` 字段意图按子状态匹配，但 round 2 评审指出语义模糊（"verified" 时朴素实现可能只校验 verification-result）。简化为无条件全校验，task 自身子状态推进的中间合法性由 `progress.py update --task` 的状态机转移表保证（command-reference.md `状态机转移合法性表` § Stage 4 task state 转换）。

**Stage 级 artifacts**（非 per-task）：

```yaml
development_stage_level:
  required:
    - type: development-plan
      path: docs/release{release}/development/plan.md
    - type: task-breakdown
      path: docs/release{release}/development/breakdown.md
```

注：测试代码（`tests/unit/`、`tests/integration/`）和源代码（`src/`）不在 doc-guardian 管辖；doc-guardian 仅校验 review report artifact。

---

## 6. Stage 5: Testing

```yaml
testing:
  required:
    - type: test-preparation
      path: docs/release{release}/testing/preparation.md
    - type: test-procedure
      path: docs/release{release}/testing/procedure.md
    - type: test-report
      path: docs/release{release}/testing/report.md
  optional:
    - type: bug-report
      path_pattern: docs/bug/BUG-*.md
      # 仅 testing 发现 bug 时存在；不阻塞 advance
```

**E 维度（verification）**：Stage 5 advance 还要求 test-report frontmatter `verification_status: pass`。fail → bug-start。

---

## 7. Stage 6: Delivery

```yaml
delivery:
  required:
    - type: deployment-doc
      path: docs/release{release}/delivery/deployment.md
    - type: operation-manual
      path: docs/release{release}/delivery/operation_manual.md
    - type: installation-result
      path: docs/release{release}/delivery/installation_result.md
```

**E 维度**：installation-result `verification_status: pass`。

---

## 8. Stage 7: Project Retrospective

```yaml
project_retrospective:
  required:
    - type: retrospective
      path: docs/retrospective/retrospective.md
      # 项目级单文件，每 release 增量加节
```

注：Stage 7 review-passed + close release 后才算项目此 release 完成。

---

## 9. Workflow Incident Analysis（特殊伪 stage）

```yaml
workflow_incident_analysis:
  required:
    - type: workflow-incident
      path_pattern: docs/incident/INCIDENT-*.md
      # 由 progress.md incident_report_path 字段指定具体路径
```

不走 P6 矩阵；workflow-evolution skill 接管，由 incident-resolve 退出。

---

## 10. Bug Flow（Active）

Active Bug Flow 期间，对应 stage Change Mode 的 done 条件 = "影响范围内 artifacts 重新通过 A/B/C/D/E"。"影响范围"由 BUG-NNN.md 的 `affected_artifacts` 字段（可选）声明，未声明则按 root_cause 默认：

| root_cause | 默认影响范围 |
|-----------|--------------|
| `srs` | SRS + Acceptance Plan + 可能 Architecture |
| `architecture` | Architecture 或 architecture_delta |
| `development` | 涉及 task 的 detailed_design / test_review_report / code_review_report / verification_result |

---

## 11. Cross-Release Artifacts（不绑定 stage）

```yaml
cross_release:
  ondemand:
    - type: cr
      path_pattern: docs/cr/CR-*.md
      # 仅 SRS 变更时由 srs-write 创建
    - type: bug-report
      path_pattern: docs/bug/BUG-*.md
      # 任何时机由 testing-write / bug-triage 创建
    - type: workflow-incident
      path_pattern: docs/incident/INCIDENT-*.md
      # 仅 PRD root cause 时由 bug-triage 创建
```

这些 artifact 不出现在 stage required 清单，但 validate.py `ids` 子命令校验其唯一性。

---

## 12. 实现 Hint（v0.6 round 3 H1 重写）

**关键变化**：

- Stage 4 advance **无条件**校验每个 task 的 4 个 per-task artifacts（不再按 substate 匹配）
- condition DSL 实现**必须用白名单 parser**，**严禁 `eval` / `exec` / `ast.literal_eval`** 解析用户字符串

`progress.py update --advance` 算法：

```python
def get_required_artifacts(progress: ProgressMd, doc_guardian_required: dict) -> list[str]:
    stage_key = stage_to_key(progress.current_stage)  # e.g. "srs_specification"
    stage_spec = doc_guardian_required[stage_key]

    artifacts = []

    # required（无条件必备）
    for entry in stage_spec.get("required", []):
        artifacts.append(render_path(entry["path"], progress))

    # conditional（按 condition DSL）
    for entry in stage_spec.get("conditional", []):
        if eval_condition_whitelist(entry["condition"], progress):
            artifacts.append(render_path(entry["path"], progress))

    # Stage 4 special: per-task — 无条件校验每个 task 的全部 4 个 per-task artifacts
    if progress.current_stage == "development":
        for task_id in progress.development_state.task_states.keys():
            for entry in doc_guardian_required["development_per_task"]["required"]:
                artifacts.append(render_path(entry["path"], progress, task_id=task_id))

    return artifacts


def render_path(template: str, progress, **extra) -> str:
    return template.format(release=progress.release, **extra)


def eval_condition_whitelist(condition: str, progress) -> bool:
    """
    白名单 parser。**禁用 eval/exec/ast.literal_eval**。

    Grammar / tokenization / enum literal 白名单 / hyphenated 规则
    完全按本文件顶部 §Condition DSL 规范实现，**本 docstring 不再重复 grammar
    定义**（v0.6 round 5 M1 修正）。

    实现者必须：
      - 按 §Condition DSL 的 6 条产生式（expr / or-expr / and-expr / primary / comparison / variable / literal 等）实现 recursive descent parser
      - 按 16 个 enum literal 白名单识别 RHS hyphenated literal
      - 通过 §Condition DSL 列出的 6 个 parser test cases
    """
    tokens = tokenize(condition)
    ast = parse(tokens)
    return evaluate(ast, progress)


def tokenize(s: str) -> list[Token]:
    """
    识别：identifier、enum-literal（白名单内）、bool、quoted-string、operators (==, !=, &&, ||, (, ))、'.'。
    hyphenated token（如 srs-specification）仅当出现在 comparison RHS 时视为 enum literal；其他位置报错。
    具体 token 规则见 §Condition DSL。
    """
    ...


def parse(tokens) -> AST:
    """recursive descent，按 §Condition DSL grammar；遇 unknown token / 非法结构 → ValueError"""
    ...


def evaluate(ast, progress) -> bool:
    # 按 AST 求值；变量 lookup 走白名单字典
    var_resolver = {
        "scenario": progress.scenario,
        "scenario_subtype": progress.scenario_subtype,
        "current_stage": progress.current_stage,
        "release": progress.release,
        "srs.is_multi_module": read_srs_field(progress, "is_multi_module", default=False),
        "srs.architecture_change": read_srs_field(progress, "architecture_change", default=False),
    }
    ...
```

`validate.py consistency` 算法：

```python
def check_consistency(progress, doc_guardian_required):
    required_artifacts = get_required_artifacts(progress, doc_guardian_required)
    for path in required_artifacts:
        assert os.path.exists(path), f"Required artifact missing: {path}"
        validate_file(path)  # 重用 validate.py file 单文件 check
```

**禁止实现**：

- ❌ `eval(condition_str)` / `exec(condition_str)` / `ast.literal_eval(condition_str)`
- ❌ 任何允许变量逃逸出白名单 6 个的 dynamic lookup
- ❌ Stage 4 实现仍按 `task_substate_required` 字段匹配（该字段已删除）

---

## 13. 演化与版本

本文件随 doc-guardian skill 演化。任何对必备清单的修改都会影响 P6 advance 行为，需走 design proposal 评审循环（不能直接改本文件）。

当前对应 design proposal 版本：v0.5（2026-05-06）+ batch 1 review fixes。
