#!/usr/bin/env python3
"""Validate deterministic, synthetic portfolio-import recipe goldens."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "portfolio-import"
MANIFEST_PATH = FIXTURE_ROOT / "golden-manifest.json"
MISSING = object()
FORBIDDEN_PATTERN = re.compile(
    r"(?i)(api[_-]?key|client[_-]?secret|access[_-]?token|password|bearer\s+[A-Za-z0-9])"
)
SOURCE_SCHEMA_DIGEST_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
REFERENCE_ROOT = (
    ROOT
    / "skills"
    / "gradient-portfolio-import"
    / "references"
)


class GoldenError(ValueError):
    """Raised when a recipe golden violates the deterministic contract."""


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def deep_get(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING
        current = current[part]
    return current


def deep_set(value: dict[str, Any], path: str, item: Any) -> None:
    current = value
    parts = path.split(".")
    for part in parts[:-1]:
        child = current.setdefault(part, {})
        if not isinstance(child, dict):
            raise GoldenError(f"Target path collides with scalar value: {path}")
        current = child
    leaf = parts[-1]
    if leaf in current:
        raise GoldenError(f"Duplicate target mapping: {path}")
    current[leaf] = copy.deepcopy(item)


def resolve_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise GoldenError(f"Only local schema references are supported: {reference}")
    current: Any = root_schema
    for part in reference[2:].split("/"):
        current = current[part.replace("~1", "/").replace("~0", "~")]
    if not isinstance(current, dict):
        raise GoldenError(f"Schema reference does not resolve to an object: {reference}")
    return current


def matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    raise GoldenError(f"Unsupported JSON Schema type: {expected}")


def validate_format(value: str, format_name: str, path: str) -> None:
    try:
        if format_name == "date":
            dt.date.fromisoformat(value)
        elif format_name == "date-time":
            dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif format_name == "uuid":
            import uuid

            uuid.UUID(value)
    except ValueError as exc:
        raise GoldenError(f"{path}: invalid {format_name}: {value}") from exc


def validate_schema(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> None:
    if "$ref" in schema:
        validate_schema(value, resolve_ref(root_schema, schema["$ref"]), root_schema, path)
        return

    if "oneOf" in schema:
        matches = 0
        errors: list[str] = []
        for option in schema["oneOf"]:
            try:
                validate_schema(value, option, root_schema, path)
                matches += 1
            except GoldenError as exc:
                errors.append(str(exc))
        if matches != 1:
            raise GoldenError(
                f"{path}: expected exactly one schema match, got {matches}; "
                + " | ".join(errors)
            )
        return

    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = (
            expected_type if isinstance(expected_type, list) else [expected_type]
        )
        if not any(matches_type(value, item) for item in expected_types):
            raise GoldenError(
                f"{path}: expected type {expected_type}, got {type(value).__name__}"
            )

    if "const" in schema and value != schema["const"]:
        raise GoldenError(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise GoldenError(f"{path}: value {value!r} is not in the allowed enum")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise GoldenError(f"{path}: string is shorter than minLength")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise GoldenError(f"{path}: string is longer than maxLength")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise GoldenError(f"{path}: string does not match {schema['pattern']}")
        if "format" in schema:
            validate_format(value, schema["format"], path)

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise GoldenError(f"{path}: array is shorter than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise GoldenError(f"{path}: array is longer than maxItems")
        if schema.get("uniqueItems") is True:
            canonical_items = [canonical_json(item) for item in value]
            if len(canonical_items) != len(set(canonical_items)):
                raise GoldenError(f"{path}: array items must be unique")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], root_schema, f"{path}[{index}]")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise GoldenError(f"{path}: value is below minimum")

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - set(value)
        if missing:
            raise GoldenError(f"{path}: missing required fields {sorted(missing)}")
        property_names = schema.get("propertyNames")
        if property_names:
            for key in value:
                validate_schema(key, property_names, root_schema, f"{path}.<key>")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], root_schema, f"{path}.{key}")
            elif additional is False:
                raise GoldenError(f"{path}: unexpected field {key}")
            elif isinstance(additional, dict):
                validate_schema(item, additional, root_schema, f"{path}.{key}")


def require_synthetic_fixture(value: dict[str, Any], path: pathlib.Path) -> None:
    if value.get("fixture_kind") != "synthetic":
        raise GoldenError(f"{path}: fixture_kind must be synthetic")
    if value.get("contains_client_data") is not False:
        raise GoldenError(f"{path}: contains_client_data must be false")
    serialized = canonical_json(value)
    if "(TEST)" not in serialized:
        raise GoldenError(f"{path}: synthetic identities must include (TEST)")
    if FORBIDDEN_PATTERN.search(serialized):
        raise GoldenError(f"{path}: possible credential material found")


def require_complete_pagination(source: dict[str, Any], path: pathlib.Path) -> None:
    pagination = source.get("pagination")
    if not isinstance(pagination, dict):
        raise GoldenError(f"{path}: pagination evidence is required")
    if pagination.get("complete") is not True:
        raise GoldenError(f"{path}: source pagination is incomplete")
    if pagination.get("next_cursor") is not None:
        raise GoldenError(f"{path}: completed pagination must not have a next cursor")
    page_count = pagination.get("page_count")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        raise GoldenError(f"{path}: pagination page_count must be a positive integer")


def validate_recipe_coverage(
    recipe: dict[str, Any],
    data_type: str,
    path: pathlib.Path,
) -> None:
    if recipe.get("contract") != "gradient-portfolio-import-provider-recipe/v1":
        raise GoldenError(f"{path}: unsupported provider recipe contract")
    coverage = recipe.get("review", {}).get("coverage")
    if not isinstance(coverage, list):
        raise GoldenError(f"{path}: review.coverage must be an array")
    rows = [
        row
        for row in coverage
        if isinstance(row, dict) and row.get("data_type") == data_type
    ]
    if len(rows) != 1:
        raise GoldenError(
            f"{path}: expected exactly one coverage row for {data_type}"
        )
    row = rows[0]
    required = {
        "lane_id",
        "status",
        "persistence_mode",
        "gradient_schema_identity",
        "source_schema_digest",
        "provider_terms_reviewed",
        "read_operation",
        "live_dry_run",
        "gradient_approval",
        "goldens",
    }
    missing = required - set(row)
    if missing:
        raise GoldenError(
            f"{path}: coverage row for {data_type} is missing {sorted(missing)}"
        )
    if row["status"] != "reviewed":
        raise GoldenError(f"{path}: synthetic golden coverage must be reviewed")
    if row["provider_terms_reviewed"] is not True:
        raise GoldenError(f"{path}: coverage terms must be reviewed")
    if row["persistence_mode"] not in {"persistent_import", "both"}:
        raise GoldenError(f"{path}: coverage does not permit persistence")
    if not isinstance(row["read_operation"], str) or not row["read_operation"]:
        raise GoldenError(f"{path}: coverage read operation is required")
    if (
        not isinstance(row["source_schema_digest"], str)
        or SOURCE_SCHEMA_DIGEST_PATTERN.fullmatch(row["source_schema_digest"]) is None
    ):
        raise GoldenError(f"{path}: coverage source schema digest is invalid")
    live_dry_run = row["live_dry_run"]
    if (
        not isinstance(live_dry_run, dict)
        or {
            "completed_at",
            "connector",
            "schema_identity",
            "result",
            "evidence_reference",
        }
        - set(live_dry_run)
        or live_dry_run.get("result") != "passed"
        or live_dry_run.get("connector")
        != recipe.get("provider", {}).get("connector")
        or live_dry_run.get("schema_identity")
        != row["gradient_schema_identity"]
        or not live_dry_run.get("evidence_reference")
    ):
        raise GoldenError(f"{path}: coverage dry run must be passed")
    approval = row["gradient_approval"]
    if (
        not isinstance(approval, dict)
        or approval.get("approval_status") != "reviewed"
        or approval.get("gradient_schema_identity")
        != row["gradient_schema_identity"]
        or not approval.get("mapping_profile_id")
        or not approval.get("mapping_profile_version")
        or not approval.get("approval_scope")
        or not isinstance(approval.get("mapping_profile_digest"), str)
        or SOURCE_SCHEMA_DIGEST_PATTERN.fullmatch(
            approval["mapping_profile_digest"]
        )
        is None
    ):
        raise GoldenError(f"{path}: coverage approval is not current and reviewed")
    goldens = row["goldens"]
    if (
        not isinstance(goldens, dict)
        or not goldens.get("recorded_fixture_reference")
        or not goldens.get("synthetic_fixture_paths")
    ):
        raise GoldenError(f"{path}: coverage golden evidence is incomplete")


def validate_recipe_lifecycle(
    recipe: dict[str, Any],
    path: pathlib.Path,
) -> None:
    review = recipe.get("review")
    if not isinstance(review, dict):
        raise GoldenError(f"{path}: review must be an object")
    coverage = review.get("coverage")
    if not isinstance(coverage, list):
        raise GoldenError(f"{path}: review.coverage must be an array")
    coverage_keys = [
        (row.get("lane_id"), row.get("data_type"))
        for row in coverage
        if isinstance(row, dict)
    ]
    if len(coverage_keys) != len(coverage) or len(coverage_keys) != len(
        set(coverage_keys)
    ):
        raise GoldenError(f"{path}: coverage lane/data-type pairs must be unique")

    mapping_types = {
        row.get("data_type")
        for row in recipe.get("mapping", [])
        if isinstance(row, dict)
    }
    supported_types = set(recipe.get("supported_data_types", []))
    if not mapping_types <= supported_types:
        raise GoldenError(f"{path}: mappings must use supported data types")

    if review.get("status") == "unreviewed":
        if any(row.get("status") != "unreviewed" for row in coverage):
            raise GoldenError(
                f"{path}: unreviewed recipe cannot contain reviewed coverage"
            )
        if recipe.get("mapping"):
            raise GoldenError(f"{path}: unreviewed recipe cannot contain mappings")
        return

    if review.get("status") != "reviewed":
        raise GoldenError(f"{path}: review status is invalid")
    if not coverage or not any(row.get("status") == "reviewed" for row in coverage):
        raise GoldenError(f"{path}: reviewed recipe requires reviewed coverage")
    connector = recipe.get("provider", {}).get("connector")
    if not isinstance(connector, str) or not connector:
        raise GoldenError(f"{path}: reviewed recipe requires an observed connector")
    for row in coverage:
        if row.get("status") == "reviewed":
            validate_recipe_coverage(recipe, row["data_type"], path)


def validate_readiness_catalog(
    catalog: dict[str, Any],
    path: pathlib.Path,
) -> None:
    provider_ids = [provider.get("id") for provider in catalog.get("providers", [])]
    if len(provider_ids) != len(set(provider_ids)):
        raise GoldenError(f"{path}: provider IDs must be unique")
    for provider in catalog.get("providers", []):
        lanes = provider.get("lanes", [])
        lane_ids = [lane.get("lane_id") for lane in lanes]
        if len(lane_ids) != len(set(lane_ids)):
            raise GoldenError(
                f"{path}: lane IDs must be unique for {provider.get('id')}"
            )
        for lane in lanes:
            coverage = lane.get("coverage", [])
            coverage_types = [row.get("data_type") for row in coverage]
            if len(coverage_types) != len(set(coverage_types)):
                raise GoldenError(
                    f"{path}: coverage data types must be unique for "
                    f"{provider.get('id')}:{lane.get('lane_id')}"
                )
            candidate_types = set(lane.get("candidate_data_types", []))
            typed_coverage = {item for item in coverage_types if item is not None}
            if candidate_types != typed_coverage:
                raise GoldenError(
                    f"{path}: candidate types and coverage differ for "
                    f"{provider.get('id')}:{lane.get('lane_id')}"
                )
            if candidate_types and None in coverage_types:
                raise GoldenError(
                    f"{path}: typed lanes cannot contain null coverage"
                )
            if not candidate_types and coverage_types != [None]:
                raise GoldenError(
                    f"{path}: workflow-only lanes require one null coverage row"
                )
            evidence = lane.get("evidence", {})
            for row in coverage:
                if row.get("status") == "discovery_required":
                    if (
                        row.get("source_schema_digest") is not None
                        or row.get("terms_status") != "unreviewed"
                        or row.get("dry_run_reference") is not None
                        or row.get("golden_case_ids")
                    ):
                        raise GoldenError(
                            f"{path}: discovery-required coverage claims evidence"
                        )
                elif row.get("status") == "reviewed":
                    if (
                        not isinstance(evidence.get("connector_identity"), str)
                        or not evidence.get("observed_tools")
                        or not isinstance(row.get("source_schema_digest"), str)
                        or SOURCE_SCHEMA_DIGEST_PATTERN.fullmatch(
                            row["source_schema_digest"]
                        )
                        is None
                        or row.get("terms_status") != "reviewed"
                        or not row.get("dry_run_reference")
                        or not row.get("golden_case_ids")
                    ):
                        raise GoldenError(
                            f"{path}: reviewed coverage lacks complete evidence"
                        )


def validate_governance_artifacts() -> None:
    artifacts = (
        (
            REFERENCE_ROOT / "provider-readiness-catalog.json",
            REFERENCE_ROOT / "provider-readiness-catalog.schema.json",
        ),
        (
            REFERENCE_ROOT / "provider-recipe-catalog.json",
            REFERENCE_ROOT / "provider-recipe-catalog.schema.json",
        ),
        (
            REFERENCE_ROOT / "provider-recipe-template.json",
            REFERENCE_ROOT / "provider-recipe.schema.json",
        ),
        (
            REFERENCE_ROOT / "providers" / "chronograph.recipe.json",
            REFERENCE_ROOT / "provider-recipe.schema.json",
        ),
        (
            FIXTURE_ROOT / "example-provider-test.recipe.json",
            REFERENCE_ROOT / "provider-recipe.schema.json",
        ),
    )
    loaded: dict[pathlib.Path, dict[str, Any]] = {}
    for artifact_path, schema_path in artifacts:
        artifact = load_json(artifact_path)
        schema = load_json(schema_path)
        if not isinstance(artifact, dict) or not isinstance(schema, dict):
            raise GoldenError(f"{artifact_path}: artifact and schema must be objects")
        validate_schema(artifact, schema, schema)
        loaded[artifact_path] = artifact

    readiness_path = REFERENCE_ROOT / "provider-readiness-catalog.json"
    validate_readiness_catalog(loaded[readiness_path], readiness_path)
    for recipe_path in (
        REFERENCE_ROOT / "provider-recipe-template.json",
        REFERENCE_ROOT / "providers" / "chronograph.recipe.json",
        FIXTURE_ROOT / "example-provider-test.recipe.json",
    ):
        validate_recipe_lifecycle(loaded[recipe_path], recipe_path)

    catalog_path = REFERENCE_ROOT / "provider-recipe-catalog.json"
    catalog = loaded[catalog_path]
    provider_ids: set[str] = set()
    for row in catalog.get("providers", []):
        provider_id = row["id"]
        if provider_id in provider_ids:
            raise GoldenError(f"{catalog_path}: duplicate provider {provider_id}")
        provider_ids.add(provider_id)
        recipe_path = (REFERENCE_ROOT / row["recipe_file"]).resolve()
        if not recipe_path.is_relative_to((REFERENCE_ROOT / "providers").resolve()):
            raise GoldenError(f"{catalog_path}: recipe path escapes providers")
        recipe = load_json(recipe_path)
        if recipe.get("provider", {}).get("id") != provider_id:
            raise GoldenError(f"{catalog_path}: provider identity mismatch")
        connector = recipe.get("provider", {}).get("connector")
        if not isinstance(connector, str) or not connector:
            raise GoldenError(
                f"{catalog_path}: cataloged provider requires observed connector"
            )


def apply_recipe(
    recipe: dict[str, Any],
    source: dict[str, Any],
    data_type: str,
) -> dict[str, Any]:
    coverage_rows = [
        row for row in recipe.get("mapping", []) if row.get("data_type") == data_type
    ]
    if not coverage_rows:
        raise GoldenError(f"No mappings found for {data_type}")
    allowed_availability = {
        "available",
        "ambiguous",
        "unsupported",
        "unavailable",
    }
    invalid_availability = [
        row.get("availability")
        for row in coverage_rows
        if row.get("availability") not in allowed_availability
    ]
    if invalid_availability:
        raise GoldenError(
            f"Invalid mapping availability for {data_type}: {invalid_availability}"
        )
    rows = [
        row for row in coverage_rows if row.get("availability") == "available"
    ]
    if not rows:
        raise GoldenError(f"No available mappings found for {data_type}")
    targets = [row["target_field"] for row in rows]
    if len(targets) != len(set(targets)):
        raise GoldenError(f"Duplicate target mapping for {data_type}")

    output_records: list[dict[str, Any]] = []
    for index, source_record in enumerate(source.get("records", [])):
        output: dict[str, Any] = {}
        for row in rows:
            if row.get("copy_mode") != "verbatim":
                raise GoldenError(
                    f"{data_type} mapping {row.get('source_field')} is not verbatim"
                )
            source_value = deep_get(source_record, row["source_field"])
            if source_value is MISSING:
                if row.get("required") is True:
                    raise GoldenError(
                        f"{data_type} record {index}: missing required source field "
                        f"{row['source_field']}"
                    )
                continue
            deep_set(output, row["target_field"], source_value)
        output_records.append(output)

    return {
        "fixture_kind": "synthetic",
        "contains_client_data": False,
        "provider": source["provider"],
        "data_type": data_type,
        "records": output_records,
    }


def load_case(
    case: dict[str, Any],
) -> tuple[
    pathlib.Path,
    pathlib.Path,
    pathlib.Path,
    pathlib.Path,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    fixture_root = FIXTURE_ROOT.resolve()

    def confined_path(field: str) -> pathlib.Path:
        relative = case.get(field)
        if not isinstance(relative, str) or not relative.endswith(".json"):
            raise GoldenError(f"Golden case {field} must be a relative JSON path")
        path = (fixture_root / relative).resolve()
        if not path.is_relative_to(fixture_root):
            raise GoldenError(f"Golden case {field} escapes the fixture root")
        return path

    recipe_path = confined_path("recipe_file")
    schema_path = confined_path("schema_file")
    source_path = confined_path("source_file")
    staged_path = confined_path("staged_file")
    return (
        recipe_path,
        schema_path,
        source_path,
        staged_path,
        load_json(recipe_path),
        load_json(schema_path),
        load_json(source_path),
    )


def process_case(case: dict[str, Any], record: bool) -> dict[str, str]:
    (
        recipe_path,
        schema_path,
        source_path,
        staged_path,
        recipe,
        schema_snapshot,
        source,
    ) = load_case(case)
    require_synthetic_fixture(recipe, recipe_path)
    require_synthetic_fixture(source, source_path)
    require_complete_pagination(source, source_path)
    if recipe.get("runtime_eligible") is not False:
        raise GoldenError(f"{recipe_path}: runtime_eligible must be false")

    data_type = case["data_type"]
    validate_recipe_coverage(recipe, data_type, recipe_path)
    if source.get("data_type") != data_type:
        raise GoldenError(f"{source_path}: data_type mismatch")
    if schema_snapshot.get("data_type") != data_type:
        raise GoldenError(f"{schema_path}: data_type mismatch")
    coverage_row = next(
        row
        for row in recipe["review"]["coverage"]
        if row.get("data_type") == data_type
    )
    if coverage_row["gradient_schema_identity"] != schema_snapshot.get("schema_id"):
        raise GoldenError(f"{schema_path}: coverage Gradient schema mismatch")
    if source.get("provider") != recipe.get("provider", {}).get("display_name"):
        raise GoldenError(f"{source_path}: provider identity mismatch")
    records = source.get("records")
    if not isinstance(records, list) or not records:
        raise GoldenError(f"{source_path}: records must be a non-empty array")
    source_ids = [record.get("external_record_id") for record in records]
    if any(not isinstance(item, str) or not item for item in source_ids):
        raise GoldenError(f"{source_path}: every record needs an external_record_id")
    if len(source_ids) != len(set(source_ids)):
        raise GoldenError(f"{source_path}: external_record_id values must be unique")

    staged = apply_recipe(recipe, source, data_type)
    schema_id = schema_snapshot.get("schema_id")
    if any(item.get("schema_id") != schema_id for item in staged["records"]):
        raise GoldenError(f"{data_type}: staged schema identity mismatch")
    json_schema = schema_snapshot.get("json_schema")
    if not isinstance(json_schema, dict):
        raise GoldenError(f"{schema_path}: json_schema must be an object")
    for index, item in enumerate(staged["records"]):
        validate_schema(item, json_schema, json_schema, f"records[{index}]")

    if record:
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        staged_path.write_text(canonical_json(staged), encoding="utf-8")
    else:
        expected = load_json(staged_path)
        if staged != expected:
            raise GoldenError(
                f"{staged_path}: generated staged golden differs; "
                "run --record-goldens and review the diff"
            )

    return {
        "recipe_sha256": digest(recipe),
        "schema_sha256": digest(schema_snapshot),
        "source_sha256": digest(source),
        "staged_sha256": digest(staged),
    }


def run(record: bool) -> None:
    validate_governance_artifacts()
    manifest = load_json(MANIFEST_PATH)
    require_synthetic_fixture(manifest, MANIFEST_PATH)
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise GoldenError(f"{MANIFEST_PATH}: cases must be a non-empty array")
    case_ids = [
        (
            case.get("data_type"),
            case.get("recipe_file"),
            case.get("source_file"),
        )
        for case in cases
        if isinstance(case, dict)
    ]
    if len(case_ids) != len(cases) or len(case_ids) != len(set(case_ids)):
        raise GoldenError(f"{MANIFEST_PATH}: cases must be unique objects")
    updated = copy.deepcopy(manifest)
    for index, case in enumerate(cases):
        calculated = process_case(case, record)
        if record:
            updated["cases"][index]["digests"] = calculated
        elif case.get("digests") != calculated:
            raise GoldenError(
                f"{case.get('data_type')}: golden digest drift; "
                "run --record-goldens and review the diff"
            )
    if record:
        MANIFEST_PATH.write_text(canonical_json(updated), encoding="utf-8")


def provider_recipe_path(provider: str) -> pathlib.Path:
    if not provider.replace("-", "").replace("_", "").isalnum():
        raise GoldenError("Provider must be identifier-safe.")
    path = (
        ROOT
        / "skills"
        / "gradient-portfolio-import"
        / "references"
        / "providers"
        / f"{provider}.recipe.json"
    )
    if not path.is_file():
        raise GoldenError(f"Provider recipe not found: {provider}")
    return path


def provider_lane_schema_drifted(
    recipe: dict[str, Any],
    lane_id: str,
    observed_source_schema_digest: str,
) -> bool:
    if SOURCE_SCHEMA_DIGEST_PATTERN.fullmatch(observed_source_schema_digest) is None:
        raise GoldenError("Observed source schema digest must be sha256:<64 lowercase hex>.")
    coverage = recipe.get("review", {}).get("coverage")
    if not isinstance(coverage, list):
        raise GoldenError("Provider recipe review.coverage must be an array.")
    lane = next(
        (
            row
            for row in coverage
            if isinstance(row, dict) and row.get("lane_id") == lane_id
        ),
        None,
    )
    if lane is None:
        raise GoldenError(f"Provider recipe lane not found: {lane_id}")
    reviewed_digest = lane.get("source_schema_digest")
    if (
        not isinstance(reviewed_digest, str)
        or SOURCE_SCHEMA_DIGEST_PATTERN.fullmatch(reviewed_digest) is None
    ):
        raise GoldenError(f"Provider recipe lane has no valid source schema digest: {lane_id}")
    return reviewed_digest != observed_source_schema_digest


def downgrade_recipe_lane_for_drift(
    recipe: dict[str, Any],
    lane_id: str,
    observed_source_schema_digest: str,
) -> dict[str, Any]:
    downgraded = copy.deepcopy(recipe)
    coverage = downgraded.get("review", {}).get("coverage")
    if not isinstance(coverage, list):
        raise GoldenError("Provider recipe review.coverage must be an array.")
    lane = next(
        (
            row
            for row in coverage
            if isinstance(row, dict) and row.get("lane_id") == lane_id
        ),
        None,
    )
    if lane is None:
        raise GoldenError(f"Provider recipe lane not found: {lane_id}")
    lane["status"] = "unreviewed"
    lane["live_dry_run"] = None
    lane["drifted_source_schema_digest"] = observed_source_schema_digest

    review = downgraded["review"]
    if not any(
        isinstance(row, dict) and row.get("status") == "reviewed"
        for row in coverage
    ):
        review["status"] = "unreviewed"
        review["schema_identity"] = None
        review["live_dry_run"] = None
        downgraded["gradient_approval"] = {
            "mapping_profile_id": None,
            "mapping_profile_version": None,
            "mapping_profile_digest": None,
            "gradient_schema_identity": None,
            "approval_scope": None,
            "approval_status": "unreviewed",
        }
    notes = downgraded.setdefault("notes", [])
    note = (
        f"Schema drift invalidated lane {lane_id}; re-record evidence for "
        f"{observed_source_schema_digest} before review."
    )
    if note not in notes:
        notes.append(note)
    return downgraded


def check_provider_lane_drift(
    provider: str,
    lane_id: str,
    observed_source_schema_digest: str,
    downgrade_on_drift: bool,
) -> bool:
    path = provider_recipe_path(provider)
    recipe = load_json(path)
    drifted = provider_lane_schema_drifted(
        recipe,
        lane_id,
        observed_source_schema_digest,
    )
    if drifted and downgrade_on_drift:
        path.write_text(
            canonical_json(
                downgrade_recipe_lane_for_drift(
                    recipe,
                    lane_id,
                    observed_source_schema_digest,
                )
            ),
            encoding="utf-8",
        )
    return drifted


def unreviewed_approval() -> dict[str, Any]:
    return {
        "mapping_profile_id": None,
        "mapping_profile_version": None,
        "mapping_profile_digest": None,
        "gradient_schema_identity": None,
        "approval_scope": None,
        "approval_status": "unreviewed",
    }


def build_onboarding_skeleton(
    *,
    provider_id: str,
    display_name: str,
    connector_identity: str,
    coverage_targets: list[tuple[str, str]],
) -> dict[str, Any]:
    if not provider_id.replace("-", "").replace("_", "").isalnum():
        raise GoldenError("Provider ID must be identifier-safe.")
    if not display_name.strip():
        raise GoldenError("Provider display name is required.")
    if not connector_identity.strip():
        raise GoldenError("Observed connector identity is required.")
    if not coverage_targets:
        raise GoldenError("At least one lane/data-type target is required.")
    if len(coverage_targets) != len(set(coverage_targets)):
        raise GoldenError("Lane/data-type targets must be unique.")
    if any(not lane_id or not data_type for lane_id, data_type in coverage_targets):
        raise GoldenError("Lane and data type values must be non-empty.")

    coverage = [
        {
            "lane_id": lane_id,
            "data_type": data_type,
            "status": "unreviewed",
            "persistence_mode": None,
            "gradient_schema_identity": None,
            "source_schema_digest": None,
            "provider_terms_reviewed": False,
            "read_operation": None,
            "live_dry_run": None,
            "gradient_approval": unreviewed_approval(),
            "goldens": {
                "recorded_fixture_reference": None,
                "synthetic_fixture_paths": [],
            },
        }
        for lane_id, data_type in coverage_targets
    ]
    recipe = {
        "contract": "gradient-portfolio-import-provider-recipe/v1",
        "provider": {
            "id": provider_id,
            "display_name": display_name.strip(),
            "connector": connector_identity.strip(),
        },
        "provider_terms_reviewed": False,
        "persistence_mode": None,
        "review": {
            "status": "unreviewed",
            "schema_identity": None,
            "live_dry_run": None,
            "coverage": coverage,
        },
        "gradient_approval": unreviewed_approval(),
        "source": {
            "read_operation": None,
            "source_schema_digest": None,
            "write_operations": [],
            "pagination": {
                "request_cursor_field": None,
                "response_cursor_field": None,
                "completion_condition": None,
            },
        },
        "mapping": [],
        "supported_data_types": sorted(
            {data_type for _, data_type in coverage_targets}
        ),
        "supported_asset_classes": [],
        "limits": {
            "max_source_page_size": None,
            "max_stage_batch_size": None,
        },
        "goldens": {
            "recorded_fixture_reference": None,
            "synthetic_fixture_paths": [],
        },
        "notes": [
            "Generated from observed connector identity only; no field mapping is claimed.",
            "Keep every lane unreviewed until its own authorized dry run passes.",
        ],
    }
    validate_recipe_lifecycle(
        recipe,
        pathlib.Path(f"{provider_id}.recipe.json"),
    )
    return recipe


def onboarding_checklist() -> list[str]:
    return [
        "Record exact read operation and pagination completion semantics.",
        "Capture the source schema identity and sha256 digest.",
        "Review persistence, retention, and attribution terms per data type.",
        "Run a client-authorized read-only dry run with complete pagination.",
        "Record private sanitized evidence and publish shape-equivalent TEST fixtures.",
        "Review every field mapping and obtain a Gradient approval artifact.",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-goldens", action="store_true")
    mode.add_argument("--record-goldens", action="store_true")
    mode.add_argument("--check-provider-lane-drift", action="store_true")
    mode.add_argument("--generate-onboarding-skeleton", action="store_true")
    parser.add_argument("--provider")
    parser.add_argument("--provider-id")
    parser.add_argument("--display-name")
    parser.add_argument("--connector-identity")
    parser.add_argument("--coverage-target", action="append", default=[])
    parser.add_argument("--lane-id")
    parser.add_argument("--observed-source-schema-digest")
    parser.add_argument("--downgrade-on-drift", action="store_true")
    args = parser.parse_args()
    try:
        if args.generate_onboarding_skeleton:
            if (
                args.provider_id is None
                or args.display_name is None
                or args.connector_identity is None
                or not args.coverage_target
            ):
                raise GoldenError(
                    "--generate-onboarding-skeleton requires --provider-id, "
                    "--display-name, --connector-identity, and --coverage-target."
                )
            coverage_targets: list[tuple[str, str]] = []
            for target in args.coverage_target:
                lane_id, separator, data_type = target.partition(":")
                if not separator:
                    raise GoldenError(
                        "Coverage targets must use lane_id:data_type."
                    )
                coverage_targets.append((lane_id, data_type))
            package = {
                "recipe": build_onboarding_skeleton(
                    provider_id=args.provider_id,
                    display_name=args.display_name,
                    connector_identity=args.connector_identity,
                    coverage_targets=coverage_targets,
                ),
                "checklist": onboarding_checklist(),
            }
            print(canonical_json(package), end="")
            return 0
        if args.check_provider_lane_drift:
            if (
                args.provider is None
                or args.lane_id is None
                or args.observed_source_schema_digest is None
            ):
                raise GoldenError(
                    "--check-provider-lane-drift requires --provider, --lane-id, "
                    "and --observed-source-schema-digest."
                )
            drifted = check_provider_lane_drift(
                args.provider,
                args.lane_id,
                args.observed_source_schema_digest,
                args.downgrade_on_drift,
            )
            if drifted:
                print("ERROR: Provider lane source schema drift detected.", file=sys.stderr)
                return 1
        else:
            if (
                args.provider is not None
                or args.provider_id is not None
                or args.display_name is not None
                or args.connector_identity is not None
                or args.coverage_target
                or args.lane_id is not None
                or args.observed_source_schema_digest is not None
                or args.downgrade_on_drift
            ):
                raise GoldenError(
                    "Provider lane drift options require --check-provider-lane-drift."
                )
            run(record=args.record_goldens)
    except (GoldenError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("Portfolio-import recipe goldens are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
