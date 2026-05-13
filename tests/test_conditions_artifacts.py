from pathlib import Path
import tempfile
import unittest

from skills._shared.dev_workflow.artifacts import ArtifactError, get_required_artifacts
from skills._shared.dev_workflow.conditions import ConditionError, evaluate
from skills._shared.dev_workflow.frontmatter import render_markdown


class ConditionDslTests(unittest.TestCase):
    def setUp(self):
        self.variables = {
            "scenario": "S3",
            "scenario_subtype": "S2-2",
            "current_stage": "srs-specification",
            "release": "0.1",
            "srs.is_multi_module": True,
            "srs.architecture_change": False,
        }

    def test_required_parser_cases(self):
        self.assertTrue(evaluate("scenario == S3", self.variables))
        self.assertTrue(evaluate("srs.is_multi_module == true", self.variables))
        self.assertTrue(evaluate("(scenario == S2) || (current_stage == srs-specification)", self.variables))
        self.assertTrue(evaluate("(scenario == S2) && (current_stage == srs-specification)", {**self.variables, "scenario": "S2"}))

    def test_rejects_unknown_variable_function_and_enum(self):
        with self.assertRaises(ConditionError):
            evaluate("srs.unknown_field == true", self.variables)
        with self.assertRaises(ConditionError):
            evaluate("is_admin(scenario)", self.variables)
        with self.assertRaises(ConditionError):
            evaluate("current_stage == not-a-stage", self.variables)

    def test_rejects_quoted_enum_and_assignment(self):
        with self.assertRaises(ConditionError):
            evaluate('scenario == "S3"', self.variables)
        with self.assertRaises(ConditionError):
            evaluate("scenario = S3", self.variables)

    def test_rejects_property_chain_longer_than_two(self):
        with self.assertRaises(ConditionError):
            evaluate("srs.detail.is_multi_module == true", self.variables)

    def test_rejects_hyphenated_lhs_identifier(self):
        # Hyphens are only legal on the RHS as enum literals; LHS variables
        # must be plain identifiers per required-artifacts.md DSL grammar.
        with self.assertRaises(ConditionError):
            evaluate("scenario-fake == S3", self.variables)

    def test_rejects_type_mismatch_between_variable_and_literal(self):
        # bool variable cannot be compared with an enum literal.
        with self.assertRaises(ConditionError):
            evaluate("srs.is_multi_module == S3", self.variables)
        # Enum variable cannot be compared with a bool literal.
        with self.assertRaises(ConditionError):
            evaluate("scenario == true", self.variables)

    def test_and_has_higher_precedence_than_or(self):
        # Discriminating valuation (scenario=S1, current_stage=delivery) for the
        # expression `scenario == S1 || scenario == S2 && current_stage == testing`:
        #   - Correct precedence (&& > ||): True || (False && False) = True
        #   - Wrong precedence  (|| > &&): (True || False) && False = False
        # Result must be True if and only if && binds tighter than || per the
        # required-artifacts.md DSL grammar.
        v_disc = {**self.variables, "scenario": "S1", "current_stage": "delivery"}
        self.assertTrue(
            evaluate("scenario == S1 || scenario == S2 && current_stage == testing", v_disc)
        )

        # Sanity cases (these do not by themselves discriminate precedence but
        # cover the shape required-artifacts.md uses in practice).
        v = {**self.variables, "scenario": "S1", "current_stage": "testing"}
        # S1 || (S2 && testing) -> True because the LHS of || already holds.
        self.assertTrue(
            evaluate("scenario == S1 || scenario == S2 && current_stage == testing", v)
        )
        v2 = {**self.variables, "scenario": "S1", "current_stage": "delivery"}
        # (S1 && testing) || S2 -> False; current_stage=delivery makes S1 && testing False,
        # and scenario != S2.
        self.assertFalse(
            evaluate("scenario == S1 && current_stage == testing || scenario == S2", v2)
        )


class RequiredArtifactsTests(unittest.TestCase):
    def test_s3_prd_requires_source_analysis(self):
        progress = {"scenario": "S3", "scenario_subtype": None, "current_stage": "prd-inception", "release": "0.1"}
        paths = [artifact.path for artifact in get_required_artifacts(progress)]
        self.assertEqual(
            paths,
            [
                "docs/prd/prd.md",
                "docs/prd/supporting/source_product_prd_analysis.md",
                "docs/prd/supporting/feature_matrix.md",
            ],
        )

    def test_srs_conditionals_read_srs_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            srs = root / "docs/release0.1/srs/srs.md"
            srs.parent.mkdir(parents=True)
            srs.write_text(
                render_markdown(
                    {
                        "title": "SRS",
                        "type": "srs",
                        "status": "review-passed",
                        "created": "2026-05-15T10:00:00Z",
                        "updated": "2026-05-15T10:00:00Z",
                        "owner": "tester/srs-write",
                        "release": "0.1",
                        "is_multi_module": True,
                        "architecture_change": True,
                    },
                    "\n# SRS\n",
                )
            )
            progress = {"scenario": "S3", "scenario_subtype": None, "current_stage": "srs-specification", "release": "0.1"}
            paths = [artifact.path for artifact in get_required_artifacts(progress, root=root)]
            self.assertIn("docs/release0.1/srs/integration_plan.md", paths)
            self.assertIn("docs/release0.1/srs/source_product_srs_analysis.md", paths)
            self.assertIn("docs/release0.1/srs/source_module_analysis.md", paths)
            self.assertIn("docs/release0.1/srs/reuse_replace_capability.md", paths)

            arch_progress = {**progress, "current_stage": "architecture-design"}
            arch_paths = [artifact.path for artifact in get_required_artifacts(arch_progress, root=root)]
            self.assertIn("docs/release0.1/architecture_delta.md", arch_paths)

    def test_development_includes_stage_and_per_task_artifacts(self):
        progress = {
            "scenario": "S1",
            "scenario_subtype": None,
            "current_stage": "development",
            "release": "0.1",
            "development_state": {"task_states": {"T1": "verified", "T2": "verified"}},
        }
        paths = [artifact.path for artifact in get_required_artifacts(progress)]
        self.assertEqual(len(paths), 10)
        self.assertIn("docs/release0.1/development/plan.md", paths)
        self.assertIn("docs/release0.1/development/tasks/T2/verification_result.md", paths)

    def test_s1_prd_inception_has_no_source_system_analysis(self):
        # Spec source: required-artifacts.md §2 — source-system-analysis is
        # only required when scenario == S3.
        progress = {"scenario": "S1", "scenario_subtype": None, "current_stage": "prd-inception", "release": "0.1"}
        paths = [artifact.path for artifact in get_required_artifacts(progress)]
        self.assertEqual(paths, ["docs/prd/prd.md"])

    def test_s1_srs_specification_has_no_source_system_analysis(self):
        progress = {"scenario": "S1", "scenario_subtype": None, "current_stage": "srs-specification", "release": "0.1"}
        # No SRS file written -> condition variables default to false. The
        # only required artifacts should be the unconditional SRS + acceptance
        # plan; no integration plan, no source-system-analysis variants.
        paths = [artifact.path for artifact in get_required_artifacts(progress)]
        self.assertEqual(
            paths,
            [
                "docs/release0.1/srs/srs.md",
                "docs/release0.1/srs/acceptance_plan.md",
            ],
        )

    def test_architecture_design_without_change_omits_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            srs = root / "docs/release0.1/srs/srs.md"
            srs.parent.mkdir(parents=True)
            srs.write_text(
                render_markdown(
                    {
                        "title": "SRS",
                        "type": "srs",
                        "status": "review-passed",
                        "created": "2026-05-15T10:00:00Z",
                        "updated": "2026-05-15T10:00:00Z",
                        "owner": "tester/srs-write",
                        "release": "0.1",
                        "is_multi_module": False,
                        "architecture_change": False,
                    },
                    "\n# SRS\n",
                )
            )
            progress = {"scenario": "S1", "scenario_subtype": None, "current_stage": "architecture-design", "release": "0.1"}
            paths = [artifact.path for artifact in get_required_artifacts(progress, root=root)]
            self.assertEqual(paths, ["docs/architecture/architecture.md"])
            self.assertNotIn("docs/release0.1/architecture_delta.md", paths)

    def test_workflow_incident_analysis_raises_explicit_error(self):
        # Spec source: required-artifacts.md §9 — workflow-incident-analysis
        # bypasses P6 advance and must not be treated as "no required
        # artifacts" by the resolver.
        progress = {"scenario": "S1", "scenario_subtype": None, "current_stage": "workflow-incident-analysis", "release": "0.1"}
        with self.assertRaises(ArtifactError):
            get_required_artifacts(progress)


if __name__ == "__main__":
    unittest.main()
