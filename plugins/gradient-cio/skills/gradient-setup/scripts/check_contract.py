#!/usr/bin/env python3
"""Check responses and resolve chained arguments from contracts.json.

Usage: python check_contract.py contracts.json <probe_id> response.json
       python check_contract.py --resolve-args contracts.json <probe_id> responses_dir
       python check_contract.py --validate-connector contracts.json capabilities.json
Prints PASS or FAIL with the missing paths; exit code 0 = pass, 1 = fail.
Paths use dots and [n] indexes, e.g. "organizations[0].id". An empty list counts as present.
"""
import json, math, re, sys

MISSING = object()
PLACEHOLDER = re.compile(r"^<([a-z0-9_]+):([^>]+)>$")
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

def get(obj, path):
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if part.startswith("["):
            i = int(part[1:-1])
            if not isinstance(obj, list) or i >= len(obj):
                return MISSING
            obj = obj[i]
        else:
            if not isinstance(obj, dict) or part not in obj:
                return MISSING
            obj = obj[part]
    return obj

def load(p):
    d = json.load(open(p, encoding="utf-8"))
    if isinstance(d, list) and d and isinstance(d[0], dict) and "text" in d[0]:   # MCP content wrapper
        d = json.loads(d[0]["text"])
    return d

def probe_by_id(contracts, probe_id):
    return next((p for p in contracts["probes"] if p["id"] == probe_id), None)

def resolve_value(value, contracts, responses_dir):
    if isinstance(value, dict):
        return {k: resolve_value(v, contracts, responses_dir) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_value(v, contracts, responses_dir) for v in value]
    if not isinstance(value, str):
        return value
    match = PLACEHOLDER.fullmatch(value)
    if not match:
        return value
    dependency_id, path = match.groups()
    if probe_by_id(contracts, dependency_id) is None:
        raise ValueError(f"unknown dependency probe {dependency_id}")
    response_path = responses_dir / f"{dependency_id}.json"
    if not response_path.is_file():
        raise ValueError(f"missing dependency response {response_path}")
    resolved = get(load(response_path), path)
    if resolved is MISSING or resolved is None:
        raise ValueError(f"dependency {dependency_id} has no non-null {path}")
    return resolved

def placeholder_dependencies(value):
    if isinstance(value, dict):
        return {item for child in value.values() for item in placeholder_dependencies(child)}
    if isinstance(value, list):
        return {item for child in value for item in placeholder_dependencies(child)}
    match = PLACEHOLDER.fullmatch(value) if isinstance(value, str) else None
    return {match.group(1)} if match else set()

def validate_manifest(contracts, public_tools=None):
    probes = contracts.get("probes")
    if not isinstance(probes, list):
        return ["probes is not a list"]
    errors = []
    probe_ids = [
        probe.get("id")
        for probe in probes
        if isinstance(probe, dict)
    ]
    if len(probe_ids) != len(probes) or any(
        not isinstance(probe_id, str) or not probe_id
        for probe_id in probe_ids
    ):
        return ["every probe must have a non-empty string id"]
    if len(probe_ids) != len(set(probe_ids)):
        errors.append("probe ids are not unique")
    known_ids = set(probe_ids)
    allowed_tools = set(public_tools) if public_tools is not None else None
    for index, probe in enumerate(probes):
        probe_id = probe["id"]
        declared = probe.get("depends_on", [])
        if not isinstance(declared, list):
            errors.append(f"{probe_id}: depends_on is not a list")
            continue
        unknown = set(declared) - known_ids
        later = {
            dependency
            for dependency in declared
            if dependency in known_ids
            and probe_ids.index(dependency) >= index
        }
        used = placeholder_dependencies(probe.get("args", {}))
        if unknown:
            errors.append(f"{probe_id}: unknown {sorted(unknown)}")
        if later:
            errors.append(f"{probe_id}: non-prior {sorted(later)}")
        undeclared = used - set(declared)
        if undeclared:
            errors.append(
                f"{probe_id}: placeholders reference undeclared "
                f"dependencies {sorted(undeclared)}"
            )
        tool_name = probe.get("tool")
        if allowed_tools is not None and tool_name not in allowed_tools:
            errors.append(f"{probe_id}: unknown public tool {tool_name!r}")
        for path, assertion in probe.get("approx", {}).items():
            if not isinstance(path, str) or not isinstance(assertion, dict):
                errors.append(f"{probe_id}: invalid approx assertion")
                continue
            if not isinstance(assertion.get("unit"), str):
                errors.append(f"{probe_id}: approx {path} requires unit")
            if not _finite_number(assertion.get("expected")):
                errors.append(f"{probe_id}: approx {path} expected is not finite")
            if not _valid_tolerance(assertion):
                errors.append(f"{probe_id}: approx {path} requires a finite non-negative tolerance")
        for assertion in probe.get("reconciles", []):
            if (
                not isinstance(assertion, dict)
                or not isinstance(assertion.get("left"), str)
                or not isinstance(assertion.get("right"), str)
                or not isinstance(assertion.get("unit"), str)
                or not _valid_tolerance(assertion)
            ):
                errors.append(f"{probe_id}: invalid reconciliation assertion")
    errors.extend(_validate_minimum_connector_contract(
        contracts,
        probes,
        allowed_tools,
    ))
    return errors

def _validate_minimum_connector_contract(contracts, probes, allowed_tools):
    contract = contracts.get("minimum_connector_contract")
    if contract is None:
        return []
    if not isinstance(contract, dict):
        return ["minimum_connector_contract is not an object"]
    errors = []
    minimum_version = contract.get("minimum_service_version")
    if not isinstance(minimum_version, str) or SEMVER.fullmatch(minimum_version) is None:
        errors.append("minimum_connector_contract minimum_service_version is not semver")
    epoch = contract.get("compatibility_epoch")
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
        errors.append("minimum_connector_contract compatibility_epoch is not a positive integer")
    required_tools = contract.get("required_tools")
    if (
        not isinstance(required_tools, list)
        or any(not isinstance(tool, str) or not tool for tool in required_tools)
        or len(required_tools) != len(set(required_tools or []))
    ):
        errors.append("minimum_connector_contract required_tools must be unique strings")
        required_tools = []
    elif allowed_tools is not None:
        unknown_tools = set(required_tools) - allowed_tools
        if unknown_tools:
            errors.append(
                "minimum_connector_contract references unknown public tools "
                f"{sorted(unknown_tools)}"
            )
    required_probe_ids = contract.get("required_probe_ids")
    probe_ids = {
        probe.get("id")
        for probe in probes
        if isinstance(probe, dict)
    }
    if (
        not isinstance(required_probe_ids, list)
        or any(
            not isinstance(probe_id, str) or not probe_id
            for probe_id in required_probe_ids
        )
        or len(required_probe_ids) != len(set(required_probe_ids or []))
    ):
        errors.append("minimum_connector_contract required_probe_ids must be unique strings")
        required_probe_ids = []
    else:
        unknown_probe_ids = set(required_probe_ids) - probe_ids
        if unknown_probe_ids:
            errors.append(
                "minimum_connector_contract references unknown probes "
                f"{sorted(unknown_probe_ids)}"
            )
    required_paths = contract.get("required_response_field_paths")
    if not isinstance(required_paths, dict) or not required_paths:
        errors.append(
            "minimum_connector_contract required_response_field_paths is not an object"
        )
        return errors
    path_tools = set(required_paths)
    undeclared_path_tools = path_tools - set(required_tools)
    if undeclared_path_tools:
        errors.append(
            "minimum_connector_contract response paths reference undeclared tools "
            f"{sorted(undeclared_path_tools)}"
        )
    tools_without_paths = set(required_tools) - path_tools
    if tools_without_paths:
        errors.append(
            "minimum_connector_contract required tools lack response paths "
            f"{sorted(tools_without_paths)}"
        )
    envelope = set(contracts.get("envelope", []))
    for tool, paths in required_paths.items():
        if (
            not isinstance(paths, list)
            or not paths
            or any(not isinstance(path, str) or not path for path in paths)
            or len(paths) != len(set(paths or []))
        ):
            errors.append(
                f"minimum_connector_contract {tool} response paths must be unique strings"
            )
            continue
        asserted_paths = set()
        for probe in probes:
            if not isinstance(probe, dict) or probe.get("tool") != tool:
                continue
            asserted_paths.update(probe.get("required", []))
            asserted_paths.update(probe.get("non_null", []))
            asserted_paths.update(probe.get("equals", {}))
            asserted_paths.update(probe.get("approx", {}))
            if probe.get("envelope", True):
                asserted_paths.update(envelope)
        unasserted_paths = set(paths) - asserted_paths
        if unasserted_paths:
            errors.append(
                f"minimum_connector_contract {tool} paths are not probed "
                f"{sorted(unasserted_paths)}"
            )
    required_probe_tools = {
        probe.get("tool")
        for probe in probes
        if isinstance(probe, dict) and probe.get("id") in required_probe_ids
    }
    uncovered_tools = set(required_tools) - required_probe_tools
    if uncovered_tools:
        errors.append(
            "minimum_connector_contract required tools lack required probes "
            f"{sorted(uncovered_tools)}"
        )
    return errors

def _finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def _valid_tolerance(assertion):
    tolerances = [
        assertion.get("absolute_tolerance"),
        assertion.get("relative_tolerance"),
    ]
    supplied = [value for value in tolerances if value is not None]
    return bool(supplied) and all(_finite_number(value) and value >= 0 for value in supplied)

def _approximately_equal(actual, expected, assertion):
    if not _finite_number(actual) or not _finite_number(expected):
        return False
    absolute = assertion.get("absolute_tolerance", 0)
    relative = assertion.get("relative_tolerance", 0)
    return math.isclose(actual, expected, rel_tol=relative, abs_tol=absolute)

def load_and_validate_catalog(contracts_path):
    catalog_path = contracts_path.parent / "public-tools.json"
    if not catalog_path.is_file():
        return None, [f"missing generated public-tool catalog {catalog_path}"]
    catalog = load(catalog_path)
    if (
        not isinstance(catalog, dict)
        or catalog.get("generated") is not True
        or not isinstance(catalog.get("tools"), list)
    ):
        return None, ["public-tools.json is not a generated tool catalog"]
    tools = catalog["tools"]
    if (
        any(not isinstance(tool, str) or not tool for tool in tools)
        or len(tools) != len(set(tools))
        or tools != sorted(tools)
    ):
        return None, ["public-tools.json tools must be unique sorted strings"]
    return tools, []

def resolve_args(argv):
    import pathlib
    if len(argv) != 5:
        raise SystemExit(__doc__)
    contracts_path = pathlib.Path(argv[2])
    contracts = load(contracts_path); probe_id = argv[3]
    public_tools, catalog_errors = load_and_validate_catalog(contracts_path)
    manifest_errors = catalog_errors + validate_manifest(
        contracts,
        public_tools,
    )
    if manifest_errors:
        print(f"FAIL manifest: {'; '.join(manifest_errors)}")
        return 1
    probe = probe_by_id(contracts, probe_id)
    if not probe:
        raise SystemExit(f"unknown probe {probe_id}")
    dependencies = probe.get("depends_on", [])
    if not isinstance(dependencies, list):
        raise SystemExit(f"invalid depends_on for {probe_id}")
    undeclared = placeholder_dependencies(probe["args"]) - set(dependencies)
    if undeclared:
        print(f"FAIL {probe_id}: undeclared dependencies {', '.join(sorted(undeclared))}")
        return 1
    unknown = [item for item in dependencies if probe_by_id(contracts, item) is None]
    if unknown:
        print(f"FAIL {probe_id}: unknown dependencies {', '.join(unknown)}")
        return 1
    responses_dir = pathlib.Path(argv[4])
    try:
        args = resolve_value(probe["args"], contracts, responses_dir)
    except ValueError as error:
        print(f"FAIL {probe_id}: {error}"); return 1
    print(json.dumps(args, separators=(",", ":")))
    return 0

def validate_connector(argv):
    import pathlib
    if len(argv) != 4:
        raise SystemExit(__doc__)
    contracts_path = pathlib.Path(argv[2])
    contracts = load(contracts_path)
    capabilities = load(argv[3])
    public_tools, catalog_errors = load_and_validate_catalog(contracts_path)
    manifest_errors = catalog_errors + validate_manifest(contracts, public_tools)
    if manifest_errors:
        print(f"FAIL manifest: {'; '.join(manifest_errors)}")
        return 1
    contract = contracts["minimum_connector_contract"]
    actual_version = capabilities.get("version") if isinstance(capabilities, dict) else None
    minimum_version = contract["minimum_service_version"]
    if (
        not isinstance(actual_version, str)
        or SEMVER.fullmatch(actual_version) is None
        or tuple(map(int, SEMVER.fullmatch(actual_version).groups()))
        < tuple(map(int, SEMVER.fullmatch(minimum_version).groups()))
    ):
        print(
            "FAIL connector: service version "
            f"{actual_version!r} is below required {minimum_version}"
        )
        return 1
    identity = capabilities.get("contract_identity", {})
    actual_epoch = identity.get("compatibility_epoch") if isinstance(identity, dict) else None
    required_epoch = contract["compatibility_epoch"]
    if actual_epoch != required_epoch:
        print(
            "FAIL connector: compatibility epoch "
            f"{actual_epoch!r} does not equal required {required_epoch}"
        )
        return 1
    tool_rows = capabilities.get("tools", [])
    advertised_tools = {
        row.get("name")
        for row in tool_rows
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    missing_tools = set(contract["required_tools"]) - advertised_tools
    if missing_tools:
        print(
            "FAIL connector: missing required tools "
            + ", ".join(sorted(missing_tools))
        )
        return 1
    print(
        f"PASS connector (service {actual_version}, compatibility epoch "
        f"{actual_epoch}, {len(contract['required_tools'])} required tools)"
    )
    return 0

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--resolve-args":
        raise SystemExit(resolve_args(sys.argv))
    if len(sys.argv) > 1 and sys.argv[1] == "--validate-connector":
        raise SystemExit(validate_connector(sys.argv))
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    import pathlib
    contracts_path = pathlib.Path(sys.argv[1])
    c = load(contracts_path); pid = sys.argv[2]; resp = load(sys.argv[3])
    public_tools, catalog_errors = load_and_validate_catalog(contracts_path)
    manifest_errors = catalog_errors + validate_manifest(c, public_tools)
    if manifest_errors:
        print(f"FAIL manifest: {'; '.join(manifest_errors)}")
        sys.exit(1)
    probe = probe_by_id(c, pid)
    if not probe:
        raise SystemExit(f"unknown probe {pid}")
    if isinstance(resp, dict) and "error" in resp:
        e = resp["error"]; print(f"FAIL {pid}: error {e.get('code')} http {e.get('http_status')}"); sys.exit(1)
    paths = list(probe["required"]) + (c["envelope"] if probe.get("envelope", True) else [])
    missing = [p for p in paths if get(resp, p) is MISSING]
    if missing:
        print(f"FAIL {pid}: missing {', '.join(missing)}"); sys.exit(1)
    null = [p for p in probe.get("non_null", []) if get(resp, p) in (MISSING, None)]
    if null:
        print(f"FAIL {pid}: null {', '.join(null)}"); sys.exit(1)
    unequal = [
        f"{p} expected {expected!r}, got {get(resp, p)!r}"
        for p, expected in probe.get("equals", {}).items()
        if get(resp, p) is MISSING or get(resp, p) != expected
    ]
    if unequal:
        print(f"FAIL {pid}: {'; '.join(unequal)}"); sys.exit(1)
    approximate_failures = [
        f"{path} expected approximately {assertion['expected']!r} "
        f"{assertion['unit']}, got {get(resp, path)!r}"
        for path, assertion in probe.get("approx", {}).items()
        if not _approximately_equal(
            get(resp, path),
            assertion["expected"],
            assertion,
        )
    ]
    if approximate_failures:
        print(f"FAIL {pid}: {'; '.join(approximate_failures)}"); sys.exit(1)
    reconciliation_failures = [
        f"{assertion['left']} does not reconcile to {assertion['right']} "
        f"in {assertion['unit']}"
        for assertion in probe.get("reconciles", [])
        if not _approximately_equal(
            get(resp, assertion["left"]),
            get(resp, assertion["right"]),
            {
                **assertion,
                "expected": get(resp, assertion["right"]),
            },
        )
    ]
    if reconciliation_failures:
        print(f"FAIL {pid}: {'; '.join(reconciliation_failures)}"); sys.exit(1)
    asof = get(resp, "provenance.as_of"); val = get(resp, "validation.status")
    print(f"PASS {pid}" + (f" (as of {asof}" if asof is not MISSING else "") + (f", validation {val})" if val is not MISSING else (")" if asof is not MISSING else "")))

if __name__ == "__main__":
    main()
