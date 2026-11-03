"""Quick Take calculation and renderer regressions."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

from suites.harness import ROOT, check


def _run(
    skill_name: str,
    arguments: list[str],
) -> subprocess.CompletedProcess[str]:
    skill = ROOT / "skills" / skill_name
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=skill,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _facts(
    skill_name: str,
    arguments: list[str],
) -> dict[str, object]:
    result = _run(skill_name, arguments)
    check(
        result.returncode == 0,
        f"{skill_name}: facts command succeeds"
        + (f" — {(result.stderr or result.stdout)[-300:]}" if result.returncode else ""),
    )
    if result.returncode != 0:
        return {}
    return json.loads(result.stdout)


def _check_png(path: pathlib.Path, expected_size: tuple[int, int], label: str) -> None:
    if not path.is_file():
        check(False, f"{label}: renderer creates the expected PNG")
        return
    with Image.open(path) as image:
        check(
            image.size == expected_size and image.mode in {"RGB", "RGBA"},
            f"{label}: PNG is {expected_size[0]}×{expected_size[1]}",
        )


def quicktake_regressions() -> None:
    print("Quick Take checks")
    lens = _facts(
        "gradient-portfolio-lens",
        [
            "scripts/pa_viz.py",
            "facts",
            "--spec",
            "examples/post_capital_vs_risk.json",
        ],
    )
    lens_base = lens.get("base", {}) if isinstance(lens, dict) else {}
    lens_classes = (
        lens_base.get("classes", []) if isinstance(lens_base, dict) else []
    )
    check(
        lens.get("format") == "capital_vs_risk"
        and abs(float(lens_base.get("vol", 0)) - 0.09027606555788975) < 1e-12
        and len(lens_classes) > 0
        and abs(float(lens_classes[0].get("risk_share", 0)) - 0.5509213195523073)
        < 1e-12,
        "Portfolio Lens preserves expected volatility and Euler risk share",
    )

    spotlight = _facts(
        "gradient-signal-spotlight",
        [
            "scripts/render_spotlight.py",
            "--input",
            "../gradient-tactical-dashboard/examples/rr_2026-10-21.json",
            "--facts-only",
            "--allow-stale",
        ],
    )
    check(
        spotlight.get("pair_id") == "china_vs_india"
        and spotlight.get("move_pct") == -9.17
        and spotlight.get("percentile_abs") == 98,
        "Signal Spotlight preserves pair, move and percentile",
    )

    risk = _facts(
        "gradient-risk-pulse",
        [
            "scripts/render_riskpulse.py",
            "--input",
            "../gradient-tactical-dashboard/examples/grip_2026-10-21.json",
            "--facts-only",
            "--allow-stale",
        ],
    )
    pillars = risk.get("pillars", []) if isinstance(risk, dict) else []
    check(
        risk.get("score") == 72
        and risk.get("stance") == "Defensive"
        and len(pillars) == 5
        and pillars[3].get("score") == 87,
        "Risk Pulse preserves GRIP score, stance and pillar decomposition",
    )

    dashboard = _facts(
        "gradient-tactical-dashboard",
        [
            "scripts/render_dashboard.py",
            "--spec",
            "examples/dashboard_2026-10-21.json",
            "--facts-only",
        ],
    )
    dashboard_values = dashboard.get("values", [])
    check(
        dashboard.get("inputs", {}).get("rr", {}).get("validation_status")
        == "passed"
        and not any("error" in row for row in dashboard_values)
        and any(row.get("display") == "−2.1 pp" for row in dashboard_values),
        "Tactical Dashboard resolves validated inputs and CMA edges",
    )

    ask = _facts(
        "gradient-ask-gradient",
        [
            "scripts/render_ask.py",
            "--spec",
            "examples/ask_value_growth_2026-10-21.json",
            "--facts-only",
        ],
    )
    ask_displays = {row.get("display") for row in ask.get("values", [])}
    check(
        {"6.3%", "4.2%", "−9.6%", "+2.1 pp"} <= ask_displays,
        "Ask Gradient preserves expected-return, signal and spread values",
    )

    with tempfile.TemporaryDirectory(prefix="gradient-quicktakes-") as directory:
        output = pathlib.Path(directory)
        dashboard_example = (
            ROOT
            / "skills"
            / "gradient-tactical-dashboard"
            / "examples"
            / "dashboard_2026-10-21.json"
        )
        adaptive_dashboard = json.loads(
            dashboard_example.read_text(encoding="utf-8")
        )
        adaptive_dashboard["inputs"] = {
            name: str((dashboard_example.parent / source).resolve())
            for name, source in adaptive_dashboard["inputs"].items()
        }
        adaptive_dashboard["explain_square"] = (
            adaptive_dashboard["explain"]
            + " The complete committee analysis remains on the square canvas "
            "while the scorecard bands adapt to measured Inter font metrics."
        )
        adaptive_spec = output / "dashboard-adaptive.json"
        adaptive_spec.write_text(
            json.dumps(adaptive_dashboard),
            encoding="utf-8",
        )
        render_cases = (
            (
                "gradient-portfolio-lens",
                [
                    "scripts/pa_viz.py",
                    "render",
                    "--spec",
                    "examples/post_capital_vs_risk.json",
                    "--sizes",
                    "square",
                    "--out",
                    str(output / "lens"),
                ],
                output / "lens" / "pa_total_plan_capital_vs_risk_square.png",
            ),
            (
                "gradient-signal-spotlight",
                [
                    "scripts/render_spotlight.py",
                    "--input",
                    "../gradient-tactical-dashboard/examples/rr_2026-10-21.json",
                    "--allow-stale",
                    "--brand",
                    "gradient",
                    "--sizes",
                    "square",
                    "--out",
                    str(output / "spotlight"),
                    "--headline",
                    "China trails India in the latest relative-return signal",
                    "--subtitle",
                    "Falling line = China Equity trailing India Equity",
                    "--explain",
                    "Gradient flags a sharp relative move. Our read: this is evidence of divergence, not a forecast.",
                ],
                output
                / "spotlight"
                / "spotlight_china_vs_india_2026-10-21_square.png",
            ),
            (
                "gradient-risk-pulse",
                [
                    "scripts/render_riskpulse.py",
                    "--input",
                    "../gradient-tactical-dashboard/examples/grip_2026-10-21.json",
                    "--allow-stale",
                    "--brand",
                    "gradient",
                    "--sizes",
                    "square",
                    "--out",
                    str(output / "risk"),
                    "--headline",
                    "Risk pressure eased, but GRIP remains Defensive",
                    "--subtitle",
                    "0-100 scale: higher = more risk pressure",
                    "--explain",
                    "Rates remain the strongest source of pressure while credit is calmer. Our read: pressure remains elevated but uneven.",
                ],
                output / "risk" / "riskpulse_2026-10-21_square.png",
            ),
            (
                "gradient-tactical-dashboard",
                [
                    "scripts/render_dashboard.py",
                    "--spec",
                    "examples/dashboard_2026-10-21.json",
                    "--sizes",
                    "square",
                    "--brand",
                    "gradient",
                    "--out",
                    str(output / "dashboard"),
                ],
                output / "dashboard" / "dashboard_2026-10-21_square.png",
            ),
            (
                "gradient-tactical-dashboard",
                [
                    "scripts/render_dashboard.py",
                    "--spec",
                    str(adaptive_spec),
                    "--sizes",
                    "square",
                    "--brand",
                    "gradient",
                    "--out",
                    str(output / "dashboard-adaptive"),
                ],
                output
                / "dashboard-adaptive"
                / "dashboard_2026-10-21_square.png",
            ),
            (
                "gradient-ask-gradient",
                [
                    "scripts/render_ask.py",
                    "--spec",
                    "examples/ask_value_growth_2026-10-21.json",
                    "--sizes",
                    "square",
                    "--brand",
                    "gradient",
                    "--out",
                    str(output / "ask"),
                ],
                output / "ask" / "ask_value_vs_growth_2026-10-21_square.png",
            ),
        )
        for skill_name, arguments, png in render_cases:
            result = _run(skill_name, arguments)
            check(
                result.returncode == 0,
                f"{skill_name}: representative canvas renders"
                + (
                    f" — {(result.stderr or result.stdout)[-300:]}"
                    if result.returncode
                    else ""
                ),
            )
            _check_png(png, (1080, 1080), skill_name)
