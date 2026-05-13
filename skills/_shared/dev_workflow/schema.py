"""Schema constants shared by Task 6 scripts."""

from __future__ import annotations

UNIVERSAL_FIELDS = ("title", "type", "status", "created", "updated", "owner")

STATUSES = {"draft", "in-review", "revising", "review-passed", "approved"}
GATED_APPROVED_TYPES = {"prd", "srs", "architecture", "cr"}

INCREMENTAL_DOC_TYPES = {
    "prd",
    "architecture",
    "retrospective",
    "srs",
    "acceptance-plan",
    "integration-plan",
    "architecture-delta",
    "development-plan",
    "task-breakdown",
    "detailed-design",
    "cr",
    "bug-report",
    "workflow-incident",
}

SNAPSHOT_DOC_TYPES = {
    "test-preparation",
    "test-procedure",
    "test-report",
    "deployment-doc",
    "operation-manual",
    "installation-result",
    "code-review-report",
    "test-review-report",
    "verification-result",
    "source-system-analysis",
    "competitor-research",
    "competitor-architecture",
    "market-research",
    "user-scenario-analysis",
    "non-goals",
    "risk-analysis",
}

DOC_TYPES = INCREMENTAL_DOC_TYPES | SNAPSHOT_DOC_TYPES

PER_TYPE_REQUIRED_FIELDS = {
    "prd": (),
    "architecture": (),
    "retrospective": (),
    "srs": ("release", "is_multi_module", "architecture_change"),
    "acceptance-plan": ("release", "related_srs"),
    "integration-plan": ("release",),
    "architecture-delta": ("release", "parent_architecture"),
    "development-plan": ("release",),
    "task-breakdown": ("release", "total_tasks"),
    "test-preparation": ("release",),
    "test-procedure": ("release",),
    "test-report": ("release", "verification_status", "total_test_cases", "passed", "failed"),
    "deployment-doc": ("release",),
    "operation-manual": ("release",),
    "installation-result": ("release", "verification_status"),
    "detailed-design": ("release", "task_id"),
    "test-review-report": (
        "release",
        "task_id",
        "findings_count",
        "severity_distribution",
        "review_status",
        "blocking_findings_count",
        "max_severity",
    ),
    "code-review-report": (
        "release",
        "task_id",
        "findings_count",
        "severity_distribution",
        "review_status",
        "blocking_findings_count",
        "max_severity",
    ),
    "verification-result": ("release", "task_id", "verification_status"),
    "cr": ("cr_id", "target_release", "affected_doc"),
    "bug-report": ("bug_id", "found_in_release", "target_release", "root_cause", "consumed_in_release"),
    "workflow-incident": ("incident_id", "triggered_by_bug", "triggered_in_release", "resolution_action"),
    "source-system-analysis": ("release", "analysis_kind", "source_system_name"),
    "competitor-research": (),
    "competitor-architecture": (),
    "market-research": (),
    "user-scenario-analysis": (),
    "non-goals": (),
    "risk-analysis": (),
}

TYPE_PATHS = {
    "prd": "docs/prd/prd.md",
    "architecture": "docs/architecture/architecture.md",
    "retrospective": "docs/retrospective/retrospective.md",
    "competitor-research": "docs/prd/supporting/competitor_research.md",
    "competitor-architecture": "docs/prd/supporting/competitor_architecture.md",
    "market-research": "docs/prd/supporting/market_research.md",
    "user-scenario-analysis": "docs/prd/supporting/user_scenario_analysis.md",
    "non-goals": "docs/prd/supporting/non_goals.md",
    "risk-analysis": "docs/prd/supporting/risk_analysis.md",
    "srs": "docs/release{release}/srs/srs.md",
    "acceptance-plan": "docs/release{release}/srs/acceptance_plan.md",
    "integration-plan": "docs/release{release}/srs/integration_plan.md",
    "architecture-delta": "docs/release{release}/architecture_delta.md",
    "development-plan": "docs/release{release}/development/plan.md",
    "task-breakdown": "docs/release{release}/development/breakdown.md",
    "test-preparation": "docs/release{release}/testing/preparation.md",
    "test-procedure": "docs/release{release}/testing/procedure.md",
    "test-report": "docs/release{release}/testing/report.md",
    "deployment-doc": "docs/release{release}/delivery/deployment.md",
    "operation-manual": "docs/release{release}/delivery/operation_manual.md",
    "installation-result": "docs/release{release}/delivery/installation_result.md",
    "detailed-design": "docs/release{release}/development/tasks/{task_id}/detailed_design.md",
    "test-review-report": "docs/release{release}/development/tasks/{task_id}/test_review_report.md",
    "code-review-report": "docs/release{release}/development/tasks/{task_id}/code_review_report.md",
    "verification-result": "docs/release{release}/development/tasks/{task_id}/verification_result.md",
    "cr": "docs/cr/{cr_id}.md",
    "bug-report": "docs/bug/{bug_id}.md",
    "workflow-incident": "docs/incident/{incident_id}.md",
}

SOURCE_ANALYSIS_PATHS = {
    "prd-level": "docs/prd/supporting/source_product_prd_analysis.md",
    "feature-matrix": "docs/prd/supporting/feature_matrix.md",
    "srs-level": "docs/release{release}/srs/source_product_srs_analysis.md",
    "module-level": "docs/release{release}/srs/source_module_analysis.md",
    "reuse-replace": "docs/release{release}/srs/reuse_replace_capability.md",
    "technical-debt": "docs/release{release}/srs/technical_debt_analysis.md",
}

VERIFICATION_STATUSES = {"pass", "fail", "partial"}
REVIEW_STATUSES = {"pending", "pass", "fail"}
ROOT_CAUSES = {"srs", "architecture", "development", "prd-exception"}
