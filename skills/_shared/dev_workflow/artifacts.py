"""Required artifact derivation for workflow P6 checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .conditions import evaluate
from .frontmatter import FrontmatterError, read_markdown


class ArtifactError(ValueError):
    """Raised when required artifacts cannot be derived."""


@dataclass(frozen=True)
class ArtifactSpec:
    type: str
    path: str
    analysis_kind: str | None = None
    condition: str | None = None


@dataclass(frozen=True)
class ProgressLike:
    scenario: str
    scenario_subtype: str | None
    current_stage: str
    release: str
    task_states: Mapping[str, str]


STAGE_KEY_BY_STAGE = {
    "prd-inception": "prd_inception",
    "srs-specification": "srs_specification",
    "architecture-design": "architecture_design",
    "development": "development_stage_level",
    "testing": "testing",
    "delivery": "delivery",
    "project-retrospective": "project_retrospective",
    "workflow-incident-analysis": "workflow_incident_analysis",
}

REQUIRED_ARTIFACTS: dict[str, dict[str, list[ArtifactSpec]]] = {
    "prd_inception": {
        "required": [ArtifactSpec("prd", "docs/prd/prd.md")],
        "conditional": [
            ArtifactSpec(
                "source-system-analysis",
                "docs/prd/supporting/source_product_prd_analysis.md",
                analysis_kind="prd-level",
                condition="scenario == S3",
            ),
            ArtifactSpec(
                "source-system-analysis",
                "docs/prd/supporting/feature_matrix.md",
                analysis_kind="feature-matrix",
                condition="scenario == S3",
            ),
        ],
    },
    "srs_specification": {
        "required": [
            ArtifactSpec("srs", "docs/release{release}/srs/srs.md"),
            ArtifactSpec("acceptance-plan", "docs/release{release}/srs/acceptance_plan.md"),
        ],
        "conditional": [
            ArtifactSpec("integration-plan", "docs/release{release}/srs/integration_plan.md", condition="srs.is_multi_module == true"),
            ArtifactSpec(
                "source-system-analysis",
                "docs/release{release}/srs/source_product_srs_analysis.md",
                analysis_kind="srs-level",
                condition="scenario == S3",
            ),
            ArtifactSpec(
                "source-system-analysis",
                "docs/release{release}/srs/source_module_analysis.md",
                analysis_kind="module-level",
                condition="scenario == S3",
            ),
            ArtifactSpec(
                "source-system-analysis",
                "docs/release{release}/srs/reuse_replace_capability.md",
                analysis_kind="reuse-replace",
                condition="scenario == S3",
            ),
        ],
    },
    "architecture_design": {
        "required": [ArtifactSpec("architecture", "docs/architecture/architecture.md")],
        "conditional": [
            ArtifactSpec("architecture-delta", "docs/release{release}/architecture_delta.md", condition="srs.architecture_change == true"),
        ],
    },
    "development_stage_level": {
        "required": [
            ArtifactSpec("development-plan", "docs/release{release}/development/plan.md"),
            ArtifactSpec("task-breakdown", "docs/release{release}/development/breakdown.md"),
        ],
        "conditional": [],
    },
    "development_per_task": {
        "required": [
            ArtifactSpec("detailed-design", "docs/release{release}/development/tasks/{task_id}/detailed_design.md"),
            ArtifactSpec("test-review-report", "docs/release{release}/development/tasks/{task_id}/test_review_report.md"),
            ArtifactSpec("code-review-report", "docs/release{release}/development/tasks/{task_id}/code_review_report.md"),
            ArtifactSpec("verification-result", "docs/release{release}/development/tasks/{task_id}/verification_result.md"),
        ],
        "conditional": [],
    },
    "testing": {
        "required": [
            ArtifactSpec("test-preparation", "docs/release{release}/testing/preparation.md"),
            ArtifactSpec("test-procedure", "docs/release{release}/testing/procedure.md"),
            ArtifactSpec("test-report", "docs/release{release}/testing/report.md"),
        ],
        "conditional": [],
    },
    "delivery": {
        "required": [
            ArtifactSpec("deployment-doc", "docs/release{release}/delivery/deployment.md"),
            ArtifactSpec("operation-manual", "docs/release{release}/delivery/operation_manual.md"),
            ArtifactSpec("installation-result", "docs/release{release}/delivery/installation_result.md"),
        ],
        "conditional": [],
    },
    "project_retrospective": {
        "required": [ArtifactSpec("retrospective", "docs/retrospective/retrospective.md")],
        "conditional": [],
    },
    # `workflow-incident-analysis` is a special pseudo-stage that bypasses the
    # P6 matrix (see required-artifacts.md §9). The active incident artifact
    # path is recorded in `progress.md incident_report_path` and validated by
    # `progress.py incident-start` / `incident-resolve` directly. The empty
    # entry exists to keep STAGE_KEY_BY_STAGE consistent for diagnostic tools;
    # `get_required_artifacts` raises ArtifactError if it is ever consulted at
    # this stage so callers do not silently treat incident state as "no
    # required artifacts" during P6 advance.
    "workflow_incident_analysis": {
        "required": [],
        "conditional": [],
    },
}


def progress_from_mapping(progress: Mapping[str, Any]) -> ProgressLike:
    dev = progress.get("development_state") or {}
    return ProgressLike(
        scenario=str(progress["scenario"]),
        scenario_subtype=progress.get("scenario_subtype"),
        current_stage=str(progress["current_stage"]),
        release=str(progress["release"]),
        task_states={str(k): str(v) for k, v in (dev.get("task_states") or {}).items()},
    )


def render_path(template: str, progress: ProgressLike, task_id: str | None = None) -> str:
    values = {"release": progress.release}
    if task_id is not None:
        values["task_id"] = task_id
    return template.format(**values)


def get_required_artifacts(progress: Mapping[str, Any] | ProgressLike, root: str | Path = ".") -> list[ArtifactSpec]:
    progress_like = progress if isinstance(progress, ProgressLike) else progress_from_mapping(progress)
    stage_key = STAGE_KEY_BY_STAGE.get(progress_like.current_stage)
    if stage_key is None:
        raise ArtifactError(f"Unknown current_stage: {progress_like.current_stage}")
    if stage_key == "workflow_incident_analysis":
        # Spec source: required-artifacts.md §9 — workflow-incident-analysis
        # bypasses the P6 advance matrix; the incident artifact is tracked
        # via `progress.md incident_report_path` and validated by
        # incident-start / incident-resolve, not by this resolver.
        raise ArtifactError(
            "workflow-incident-analysis bypasses P6 advance; use progress.md "
            "incident_report_path with progress.py incident-start / "
            "incident-resolve instead of get_required_artifacts"
        )

    variables = condition_variables(progress_like, root=root)
    artifacts: list[ArtifactSpec] = []
    stage_spec = REQUIRED_ARTIFACTS[stage_key]
    artifacts.extend(_render_specs(stage_spec.get("required", []), progress_like))
    for spec in stage_spec.get("conditional", []):
        if spec.condition and evaluate(spec.condition, variables):
            artifacts.extend(_render_specs([spec], progress_like))

    if progress_like.current_stage == "development":
        for task_id in progress_like.task_states:
            artifacts.extend(_render_specs(REQUIRED_ARTIFACTS["development_per_task"]["required"], progress_like, task_id=task_id))
    return artifacts


def _render_specs(specs: list[ArtifactSpec], progress: ProgressLike, task_id: str | None = None) -> list[ArtifactSpec]:
    return [ArtifactSpec(spec.type, render_path(spec.path, progress, task_id=task_id), spec.analysis_kind, spec.condition) for spec in specs]


def condition_variables(progress: ProgressLike, root: str | Path = ".") -> dict[str, Any]:
    srs_fields = read_srs_condition_fields(progress, root=root)
    return {
        "scenario": progress.scenario,
        "scenario_subtype": progress.scenario_subtype,
        "current_stage": progress.current_stage,
        "release": progress.release,
        "srs.is_multi_module": srs_fields.get("is_multi_module", False),
        "srs.architecture_change": srs_fields.get("architecture_change", False),
    }


def read_srs_condition_fields(progress: ProgressLike, root: str | Path = ".") -> dict[str, bool]:
    srs_path = Path(root) / f"docs/release{progress.release}/srs/srs.md"
    if not srs_path.exists():
        return {"is_multi_module": False, "architecture_change": False}
    try:
        fm = read_markdown(srs_path).frontmatter
    except FrontmatterError:
        return {"is_multi_module": False, "architecture_change": False}
    return {
        "is_multi_module": bool(fm.get("is_multi_module", False)),
        "architecture_change": bool(fm.get("architecture_change", False)),
    }
