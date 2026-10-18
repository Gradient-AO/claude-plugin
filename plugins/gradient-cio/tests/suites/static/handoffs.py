"""IDD, ODD, and IC handoff contract checks."""

import json
import pathlib
import subprocess
import sys
import tempfile

from suites.harness import FIX, ROOT, check


def handoff_contract_checks():
    validator = ROOT / "shared" / "validate_handoff.py"
    schema_path = ROOT / "shared" / "contracts" / "idd-odd-ic-handoff.schema.json"
    fixture = FIX / "idd-handoff.json"
    document = json.loads(fixture.read_text(encoding="utf-8"))
    valid = subprocess.run(
        [sys.executable, str(validator), str(fixture)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(valid.returncode == 0, "canonical IDD handoff passes validation")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    object_schemas = []

    def collect_object_schemas(value, path="$"):
        if isinstance(value, dict):
            if value.get("type") == "object":
                object_schemas.append((path, value))
            for key, child in value.items():
                collect_object_schemas(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                collect_object_schemas(child, f"{path}[{index}]")

    collect_object_schemas(schema)
    open_objects = [
        path
        for path, object_schema in object_schemas
        if object_schema.get("additionalProperties") is not False
    ]
    check(
        not open_objects,
        "handoff schema closes every declared object"
        + (f": {open_objects}" if open_objects else ""),
    )

    legacy = json.loads(json.dumps(document))
    legacy["return_series"] = [legacy["return_series"][0]]
    legacy["return_series"][0].pop("benchmark_status")
    legacy["evidence"] = [legacy["evidence"][0]]
    legacy["evidence"][0].pop("status")

    mutations = []

    def mutate(label, source, apply):
        changed = json.loads(json.dumps(source))
        apply(changed)
        mutations.append((label, changed))

    mutate(
        "server-matched benchmark without series ID",
        document,
        lambda value: value["return_series"][0].pop("benchmark_series_id"),
    )
    mutate(
        "advisory benchmark without rationale",
        document,
        lambda value: value["return_series"][1].pop("benchmark_rationale"),
    )
    mutate(
        "unavailable benchmark with series ID",
        document,
        lambda value: value["return_series"][2].update(
            {"benchmark_series_id": "benchmark-must-be-null"}
        ),
    )
    mutate(
        "unavailable benchmark without reason",
        document,
        lambda value: value["return_series"][2].pop("unavailable_reason"),
    )
    mutate(
        "legacy benchmark without rationale",
        legacy,
        lambda value: value["return_series"][0].pop("benchmark_rationale"),
    )
    mutate(
        "successful evidence without methodology",
        document,
        lambda value: value["evidence"][0].pop("methodology_version"),
    )
    mutate(
        "failed evidence without failure detail",
        document,
        lambda value: value["evidence"][1].pop("error_code"),
    )
    mutate(
        "unavailable evidence without reason",
        document,
        lambda value: value["evidence"][2].pop("unavailable_reason"),
    )
    mutate(
        "not-run evidence without reason",
        document,
        lambda value: value["evidence"][3].pop("unavailable_reason"),
    )
    mutate(
        "failed evidence with success digest",
        document,
        lambda value: value["evidence"][1].update(
            {"digest": "sha256:" + ("0" * 64)}
        ),
    )
    mutate(
        "successful evidence with malformed digest",
        document,
        lambda value: value["evidence"][0].update({"digest": "test-digest"}),
    )
    mutate(
        "legacy evidence without methodology key",
        legacy,
        lambda value: value["evidence"][0].pop("methodology_version"),
    )
    mutate(
        "unknown return-series property",
        document,
        lambda value: value["return_series"][0].update({"extra": True}),
    )

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = pathlib.Path(temporary)
        legacy_path = temporary_path / "legacy-handoff.json"
        legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
        legacy_result = subprocess.run(
            [sys.executable, str(validator), str(legacy_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        failures = []
        unstable = []
        for index, (label, invalid_document) in enumerate(mutations):
            invalid_path = temporary_path / f"invalid-handoff-{index}.json"
            invalid_path.write_text(json.dumps(invalid_document), encoding="utf-8")
            results = [
                subprocess.run(
                    [sys.executable, str(validator), str(invalid_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                for _ in range(2)
            ]
            if results[0].returncode != 1:
                failures.append(label)
            if results[0].stderr != results[1].stderr:
                unstable.append(label)
    check(legacy_result.returncode == 0, "legacy v1 handoff remains valid")
    check(
        not failures,
        "handoff validator rejects status, digest and closed-object mutations"
        + (f": {failures}" if failures else ""),
    )
    check(
        not unstable,
        "handoff validation errors are deterministic"
        + (f": {unstable}" if unstable else ""),
    )
    preservation = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; from compose_report import compose; "
                f"h=json.load(open(r'{fixture}', encoding='utf-8')); "
                "m={'title':'Test','eyebrow':'IDD','header_label':'IDD',"
                "'running_head':'Test','data_as_of':'2025-12-31','handoff':h}; "
                "r=compose('# Test\\n\\n## 1. Summary\\nEvidence [S1].', {}, m); "
                "raise SystemExit(0 if r['meta']['handoff']==h else 1)"
            ),
        ],
        cwd=ROOT / "shared",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        preservation.returncode == 0,
        "report composition preserves the typed handoff unchanged",
    )
    report_validation = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "skills"
                / "gradient-idd-manager-performance"
                / "scripts"
                / "validate_manager_performance.py"
            ),
            str(FIX / "idd-manager-performance-single.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        report_validation.returncode == 0,
        "canonical IDD report passes its skill-specific strict validator",
    )
