import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "gradient-setup"
    / "scripts"
    / "check_contract.py"
)
SPEC = importlib.util.spec_from_file_location("check_contract", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CHECK_CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_CONTRACT)


def _contracts(assertion: dict) -> dict:
    return {
        "probes": [
            {
                "id": "numeric",
                "tool": "example_tool",
                "args": {},
                "required": [],
                **assertion,
            }
        ]
    }


def test_manifest_accepts_bounded_numeric_assertions() -> None:
    errors = CHECK_CONTRACT.validate_manifest(
        _contracts(
            {
                "approx": {
                    "result.value": {
                        "expected": 0.1,
                        "absolute_tolerance": 1e-9,
                        "unit": "decimal_fraction",
                    }
                },
                "reconciles": [
                    {
                        "left": "result.total",
                        "right": "result.parts",
                        "relative_tolerance": 1e-8,
                        "unit": "decimal_fraction",
                    }
                ],
            }
        ),
        ["example_tool"],
    )

    assert errors == []


def test_manifest_rejects_unbounded_or_unitless_numeric_assertions() -> None:
    errors = CHECK_CONTRACT.validate_manifest(
        _contracts(
            {
                "approx": {
                    "result.value": {
                        "expected": float("inf"),
                    }
                }
            }
        ),
        ["example_tool"],
    )

    assert any("requires unit" in error for error in errors)
    assert any("expected is not finite" in error for error in errors)
    assert any("requires a finite non-negative tolerance" in error for error in errors)


def test_approximate_comparison_rejects_non_finite_values() -> None:
    assertion = {
        "absolute_tolerance": 1e-6,
        "relative_tolerance": 0,
    }

    assert CHECK_CONTRACT._approximately_equal(1.0, 1.0000001, assertion)
    assert not CHECK_CONTRACT._approximately_equal(
        float("nan"),
        1.0,
        assertion,
    )
