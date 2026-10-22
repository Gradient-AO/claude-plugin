"""Deterministic provider-recipe golden checks."""

import copy
import importlib.util
import pathlib
import sys

from suites.harness import ROOT, check


TOOL_PATH = ROOT / "tools" / "portfolio_import_recipe.py"
SPEC = importlib.util.spec_from_file_location("portfolio_import_recipe", TOOL_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {TOOL_PATH}")
RECIPE_TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECIPE_TOOL)

EMULATOR_PATH = ROOT / "tools" / "provider_connector_emulator.py"
EMULATOR_SPEC = importlib.util.spec_from_file_location(
    "provider_connector_emulator",
    EMULATOR_PATH,
)
if EMULATOR_SPEC is None or EMULATOR_SPEC.loader is None:
    raise RuntimeError(f"Unable to load {EMULATOR_PATH}")
EMULATOR = importlib.util.module_from_spec(EMULATOR_SPEC)
sys.modules[EMULATOR_SPEC.name] = EMULATOR
EMULATOR_SPEC.loader.exec_module(EMULATOR)


def raises_golden_error(callback):
    try:
        callback()
    except RECIPE_TOOL.GoldenError:
        return True
    return False


def raises_emulator_error(callback):
    try:
        callback()
    except EMULATOR.EmulatorError:
        return True
    return False


def provider_recipe_golden_checks():
    fixture_root = ROOT / "tests" / "fixtures" / "portfolio-import"
    manifest = RECIPE_TOOL.load_json(fixture_root / "golden-manifest.json")
    recipe = RECIPE_TOOL.load_json(
        fixture_root / "example-provider-test.recipe.json"
    )
    source = RECIPE_TOOL.load_json(
        fixture_root / "source" / "commitment-master.json"
    )
    schema_snapshot = RECIPE_TOOL.load_json(
        fixture_root / "runtime-schemas" / "commitment-master.json"
    )
    readiness_path = (
        ROOT
        / "skills"
        / "gradient-portfolio-import"
        / "references"
        / "provider-readiness-catalog.json"
    )
    readiness = RECIPE_TOOL.load_json(readiness_path)

    try:
        RECIPE_TOOL.run(record=False)
        golden_check_passed = True
    except RECIPE_TOOL.GoldenError:
        golden_check_passed = False
    check(
        golden_check_passed and len(manifest["cases"]) == 3,
        "provider recipe goldens deterministically match all three staged fixtures",
    )
    check(
        not raises_golden_error(RECIPE_TOOL.validate_governance_artifacts),
        "provider governance artifacts satisfy machine-readable schemas",
    )

    atomic_readiness = copy.deepcopy(readiness)
    chronograph_lane = next(
        provider["lanes"][0]
        for provider in atomic_readiness["providers"]
        if provider["id"] == "chronograph"
    )
    chronograph_lane["evidence"] = {
        "connector_identity": "Example Connector (TEST)",
        "observed_tools": ["example.list_commitments"],
    }
    commitment_coverage = next(
        row
        for row in chronograph_lane["coverage"]
        if row["data_type"] == "commitment_master"
    )
    commitment_coverage.update(
        {
            "status": "reviewed",
            "source_schema_digest": f"sha256:{'a' * 64}",
            "terms_status": "reviewed",
            "dry_run_reference": "private://example/commitments",
            "golden_case_ids": ["example-commitments"],
        }
    )
    check(
        not raises_golden_error(
            lambda: RECIPE_TOOL.validate_readiness_catalog(
                atomic_readiness,
                pathlib.Path("atomic-readiness-test.json"),
            )
        )
        and all(
            row["status"] == "discovery_required"
            for row in chronograph_lane["coverage"]
            if row["data_type"] != "commitment_master"
        ),
        "one reviewed data type never promotes sibling provider coverage",
    )

    duplicate_coverage = copy.deepcopy(atomic_readiness)
    duplicate_lane = next(
        provider["lanes"][0]
        for provider in duplicate_coverage["providers"]
        if provider["id"] == "chronograph"
    )
    duplicate_lane["coverage"].append(copy.deepcopy(duplicate_lane["coverage"][0]))
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.validate_readiness_catalog(
                duplicate_coverage,
                pathlib.Path("duplicate-readiness-test.json"),
            )
        ),
        "provider readiness rejects duplicate lane and data-type coverage",
    )

    onboarding = RECIPE_TOOL.build_onboarding_skeleton(
        provider_id="example_provider_test",
        display_name="Example Provider (TEST)",
        connector_identity="Example Connector (TEST)",
        coverage_targets=[
            ("private_markets_portfolio", "commitment_master"),
            ("private_markets_portfolio", "valuation_snapshot"),
        ],
    )
    recipe_schema = RECIPE_TOOL.load_json(
        ROOT
        / "skills"
        / "gradient-portfolio-import"
        / "references"
        / "provider-recipe.schema.json"
    )
    check(
        not raises_golden_error(
            lambda: RECIPE_TOOL.validate_schema(
                onboarding,
                recipe_schema,
                recipe_schema,
            )
        )
        and onboarding["mapping"] == []
        and all(
            row["status"] == "unreviewed"
            for row in onboarding["review"]["coverage"]
        )
        and len(RECIPE_TOOL.onboarding_checklist()) == 6,
        "onboarding generator emits schema-valid unreviewed skeletons only",
    )
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.build_onboarding_skeleton(
                provider_id="example_provider_test",
                display_name="Example Provider (TEST)",
                connector_identity="Example Connector (TEST)",
                coverage_targets=[
                    ("private_markets_portfolio", "commitment_master"),
                    ("private_markets_portfolio", "commitment_master"),
                ],
            )
        ),
        "onboarding generator rejects duplicate coverage targets",
    )
    check(
        all(
            not raises_golden_error(
                lambda data_type=data_type: RECIPE_TOOL.validate_recipe_coverage(
                    recipe,
                    data_type,
                    pathlib.Path("example-provider-test.recipe.json"),
                )
            )
            for data_type in (
                "commitment_master",
                "cash_flow_event_ledger",
                "valuation_snapshot",
            )
        ),
        "synthetic recipes carry reviewed per-data-type lifecycle evidence",
    )

    missing_coverage = copy.deepcopy(recipe)
    missing_coverage["review"]["coverage"] = []
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.validate_recipe_coverage(
                missing_coverage,
                "commitment_master",
                pathlib.Path("missing-coverage-test.recipe.json"),
            )
        ),
        "provider recipe goldens reject missing per-data-type review evidence",
    )

    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.load_case(
                {
                    "recipe_file": "../escape.json",
                    "schema_file": "runtime-schemas/commitment-master.json",
                    "source_file": "source/commitment-master.json",
                    "staged_file": "staged/commitment-master.json",
                }
            )
        ),
        "provider recipe manifests reject paths outside the fixture root",
    )

    pages = EMULATOR.example_pages()
    emulator = EMULATOR.SyntheticConnectorEmulator(
        provider="Example Provider (TEST)",
        data_type="commitment_master",
        pages=pages,
    )
    first_collection = emulator.collect()
    second_collection = emulator.collect()
    check(
        first_collection == second_collection
        and first_collection.page_count == 2
        and first_collection.requested_cursors == (None, "page-2")
        and len(first_collection.records) == 2,
        "fictional connector emulator exhausts pages deterministically",
    )

    drifted_pages = copy.deepcopy(pages)
    drifted_pages["page-2"] = EMULATOR.EmulatedPage(
        records=drifted_pages["page-2"].records,
        schema_digest=f"sha256:{'f' * 64}",
        next_cursor=None,
        complete=True,
    )
    duplicate_pages = copy.deepcopy(pages)
    duplicate_pages["page-2"] = EMULATOR.EmulatedPage(
        records=duplicate_pages[None].records,
        schema_digest=duplicate_pages["page-2"].schema_digest,
        next_cursor=None,
        complete=True,
    )
    incomplete_pages = copy.deepcopy(pages)
    incomplete_pages["page-2"] = EMULATOR.EmulatedPage(
        records=incomplete_pages["page-2"].records,
        schema_digest=incomplete_pages["page-2"].schema_digest,
        next_cursor=None,
        complete=False,
    )
    check(
        raises_emulator_error(
            lambda: EMULATOR.SyntheticConnectorEmulator(
                provider="Example Provider (TEST)",
                data_type="commitment_master",
                pages=drifted_pages,
            ).collect()
        )
        and raises_emulator_error(
            lambda: EMULATOR.SyntheticConnectorEmulator(
                provider="Example Provider (TEST)",
                data_type="commitment_master",
                pages=duplicate_pages,
            ).collect()
        )
        and raises_emulator_error(
            lambda: EMULATOR.SyntheticConnectorEmulator(
                provider="Example Provider (TEST)",
                data_type="commitment_master",
                pages=incomplete_pages,
            ).collect()
        ),
        "fictional connector emulator rejects drift, duplicates, and truncation",
    )
    corrected_collection = EMULATOR.EmulatedCollection(
        provider=first_collection.provider,
        data_type=first_collection.data_type,
        records=(
            {
                "external_record_id": "example-record-1",
                "value": "125",
                "unit": "currency_units",
            },
            {
                "external_record_id": "example-record-3",
                "value": "300",
                "unit": "currency_units",
            },
        ),
        schema_digest=first_collection.schema_digest,
        page_count=1,
        requested_cursors=(None,),
    )
    correction_delta = EMULATOR.compare_collections(
        first_collection,
        corrected_collection,
    )
    check(
        correction_delta.created_source_ids == ("example-record-3",)
        and correction_delta.updated_source_ids == ("example-record-1",)
        and correction_delta.unchanged_source_ids == ()
        and correction_delta.omitted_source_ids == ("example-record-2",),
        "fictional connector emulator separates corrections from omissions",
    )

    first = RECIPE_TOOL.apply_recipe(recipe, source, "commitment_master")
    second = RECIPE_TOOL.apply_recipe(recipe, source, "commitment_master")
    check(
        RECIPE_TOOL.canonical_json(first) == RECIPE_TOOL.canonical_json(second),
        "provider recipe application is byte-deterministic",
    )

    unavailable = copy.deepcopy(recipe)
    next(
        row
        for row in unavailable["mapping"]
        if row["data_type"] == "commitment_master"
        and row["target_field"] == "reported_metrics"
    )["availability"] = "unavailable"
    unavailable_output = RECIPE_TOOL.apply_recipe(
        unavailable,
        source,
        "commitment_master",
    )
    check(
        "reported_metrics" not in unavailable_output["records"][0],
        "provider recipes never stage unavailable fields",
    )

    invalid_mode = copy.deepcopy(recipe)
    invalid_mode["mapping"][0]["copy_mode"] = "convert"
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.apply_recipe(
                invalid_mode, source, "commitment_master"
            )
        ),
        "provider recipes reject non-verbatim copy modes",
    )

    missing_required = copy.deepcopy(source)
    del missing_required["records"][0]["external_record_id"]
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.apply_recipe(
                recipe, missing_required, "commitment_master"
            )
        ),
        "provider recipes reject missing required source fields",
    )

    incomplete_page = copy.deepcopy(source)
    incomplete_page["pagination"]["complete"] = False
    incomplete_page["pagination"]["next_cursor"] = "page-2"
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.require_complete_pagination(
                incomplete_page,
                pathlib.Path("incomplete-page-test-fixture.json"),
            )
        ),
        "provider recipe goldens reject incomplete pagination",
    )

    schema_invalid = copy.deepcopy(first["records"][0])
    schema_invalid["unexpected"] = True
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.validate_schema(
                schema_invalid,
                schema_snapshot["json_schema"],
                schema_snapshot["json_schema"],
            )
        ),
        "provider recipe outputs reject fields outside the runtime schema",
    )

    unsafe = copy.deepcopy(source)
    unsafe["records"][0]["api_key"] = "not-allowed"
    check(
        raises_golden_error(
            lambda: RECIPE_TOOL.require_synthetic_fixture(
                unsafe, pathlib.Path("unsafe-test-fixture.json")
            )
        ),
        "provider recipe fixtures reject credential-shaped content",
    )

    reviewed = copy.deepcopy(recipe)
    reviewed["review"] = {
        "status": "reviewed",
        "schema_identity": "gradient.import.commitment_master.v1",
        "live_dry_run": {"result": "passed"},
        "coverage": [
            {
                "lane_id": "commitments",
                "status": "reviewed",
                "source_schema_digest": f"sha256:{'b' * 64}",
                "live_dry_run": {"result": "passed"},
            },
            {
                "lane_id": "valuations",
                "status": "reviewed",
                "source_schema_digest": f"sha256:{'d' * 64}",
                "live_dry_run": {"result": "passed"},
            },
        ],
    }
    reviewed["gradient_approval"]["approval_status"] = "reviewed"
    check(
        RECIPE_TOOL.provider_lane_schema_drifted(
            reviewed,
            "commitments",
            f"sha256:{'b' * 64}",
        )
        is False
        and RECIPE_TOOL.provider_lane_schema_drifted(
            reviewed,
            "commitments",
            f"sha256:{'c' * 64}",
        )
        is True,
        "provider recipe drift is evaluated independently per lane",
    )
    one_lane_drifted = RECIPE_TOOL.downgrade_recipe_lane_for_drift(
        reviewed,
        "commitments",
        f"sha256:{'c' * 64}",
    )
    all_lanes_drifted = RECIPE_TOOL.downgrade_recipe_lane_for_drift(
        one_lane_drifted,
        "valuations",
        f"sha256:{'e' * 64}",
    )
    check(
        one_lane_drifted["review"]["coverage"][0]["status"] == "unreviewed"
        and one_lane_drifted["review"]["coverage"][1]["status"] == "reviewed"
        and one_lane_drifted["review"]["status"] == "reviewed"
        and all_lanes_drifted["review"]["status"] == "unreviewed"
        and all_lanes_drifted["gradient_approval"]["approval_status"]
        == "unreviewed",
        "provider lane drift preserves unaffected reviewed lanes and fails closed",
    )
