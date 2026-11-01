"""Self-contained skill packaging regression checks."""

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from suites.harness import FIX, ROOT, check


def _registered_validator_cases(registration):
    cases = []
    default_validator = registration.get("validator")
    cases.extend(
        (default_validator, fixture_name)
        for fixture_name in registration.get("fixtures", [])
    )
    for mode_registration in registration.get("modes", {}).values():
        if isinstance(mode_registration, dict):
            validator = mode_registration.get("validator")
            fixture_names = mode_registration.get("fixtures", [])
        else:
            validator = default_validator
            fixture_names = mode_registration
        cases.extend((validator, fixture_name) for fixture_name in fixture_names)
    return cases


def self_contained_report_skill_checks(skills, validator_manifest):
    runtime_files = (
        "analysis_quality.py",
        "construction_report_validator.py",
        "idd_report_validator.py",
        "report_constants.py",
        "report_json_validator.py",
        "report_layout.py",
        "report_vocab.py",
    )
    font_files = (
        "inter-latin-regular.ttf",
        "inter-latin-semibold.ttf",
        "inter-latin-ext-regular.ttf",
        "inter-latin-ext-semibold.ttf",
    )
    report_skills = [
        skill for skill in skills if (skill / "scripts" / "gradient_report.py").is_file()
    ]
    check(
        all(
            all((skill / "scripts" / name).is_file() for name in runtime_files)
            and all((skill / "assets" / "fonts" / name).is_file() for name in font_files)
            and (skill / "references" / "public-tools.json").is_file()
            and (skill / "references" / "known-tools.json").is_file()
            for skill in report_skills
        ),
        "report skills ship validator dependencies, tool catalogs, and Inter fonts locally",
    )

    failures = []
    exercised = 0
    expected = sum(
        len(_registered_validator_cases(registration))
        for registration in validator_manifest.values()
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    for skill_name, registration in validator_manifest.items():
        with tempfile.TemporaryDirectory() as temporary:
            isolated_root = pathlib.Path(temporary)
            isolated_fixtures = isolated_root / "fixtures"
            isolated_fixtures.mkdir()
            source_skill = ROOT / "skills" / skill_name
            isolated_skill = isolated_root / "skills" / skill_name
            shutil.copytree(source_skill, isolated_skill)
            for validator_name, fixture_name in _registered_validator_cases(
                registration
            ):
                if not validator_name:
                    failures.append(f"{skill_name}/{fixture_name}: missing validator")
                    continue
                source_fixture = FIX / fixture_name
                isolated_fixture = isolated_fixtures / fixture_name
                isolated_fixture.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_fixture, isolated_fixture)
                validator_path = (
                    isolated_root / pathlib.Path(validator_name)
                ).resolve()
                expected_prefix = (
                    isolated_root / "skills" / skill_name
                ).resolve()
                try:
                    validator_path.relative_to(expected_prefix)
                except ValueError:
                    failures.append(
                        f"{skill_name}/{fixture_name}: validator is outside its skill"
                    )
                    continue
                validated = subprocess.run(
                    [
                        sys.executable,
                        str(validator_path),
                        str(isolated_fixture),
                    ],
                    cwd=isolated_skill / "scripts",
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                exercised += 1
                if validated.returncode != 0:
                    detail = (validated.stdout or validated.stderr).strip()[-500:]
                    failures.append(
                        f"{skill_name}/{fixture_name}: {detail}"
                    )
            if skill_name == "gradient-portfolio-attribution":
                font_probe = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import gradient_report; "
                            "assert '@font-face' in gradient_report.FONT_LINK"
                        ),
                    ],
                    cwd=isolated_skill / "scripts",
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if (
                    font_probe.returncode != 0
                    or "using system fonts"
                    in (font_probe.stdout + font_probe.stderr)
                ):
                    failures.append(
                        "gradient-portfolio-attribution: packaged Inter probe failed"
                    )
    check(
        not failures and exercised == expected,
        f"all {expected} registered report fixtures validate from isolated skill copies"
        + (f": {failures}" if failures else ""),
    )
