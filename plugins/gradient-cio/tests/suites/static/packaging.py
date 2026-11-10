"""Plugin-level shared-runtime packaging regression checks."""

import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from suites.harness import FIX, ROOT, check, iter_registered_validator_cases


def marketplace_packaging_checks():
    checker_path = ROOT / "tools" / "check_skill_packaging.py"
    checker_spec = importlib.util.spec_from_file_location(
        "gradient_check_skill_packaging",
        checker_path,
    )
    if checker_spec is None or checker_spec.loader is None:
        check(False, "skill packaging checker can be imported")
        return
    checker = importlib.util.module_from_spec(checker_spec)
    checker_spec.loader.exec_module(checker)
    plugin = checker.plugin_manifest()

    with tempfile.TemporaryDirectory(prefix="gradient-packaging-paths-") as temporary:
        scratch = pathlib.Path(temporary)
        installed_root = scratch / "install" / "gradient-cio"
        installed_root.mkdir(parents=True)
        installed_failures = checker.check_versions(
            plugin,
            repository=scratch,
            plugin_root=installed_root,
        )

        checkout = scratch / "checkout"
        checkout_root = checkout / "plugins" / "gradient-cio"
        checkout_root.mkdir(parents=True)
        (checkout / "CLAUDE.md").write_text("checkout marker\n", encoding="utf-8")
        checkout_failures = checker.check_versions(
            plugin,
            repository=checkout,
            plugin_root=checkout_root,
        )

    check(
        installed_failures == []
        and checkout_failures == ["repository marketplace.json is missing"],
        "packaging skips an absent repo marketplace only in installed copies",
    )


def _registered_validator_cases(registration, *, include_chat=False):
    return [
        (validator, fixture_name)
        for _mode, fixture_name, validator in iter_registered_validator_cases(
            registration, include_chat=include_chat
        )
    ]


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
    check(
        all((ROOT / "shared" / name).is_file() for name in runtime_files)
        and all((ROOT / "assets" / "fonts" / name).is_file() for name in font_files)
        and (ROOT / "shared" / "public-tools.json").is_file(),
        "plugin ships shared validator dependencies, tool catalog, and Inter fonts",
    )

    failures = []
    exercised = 0
    expected = sum(
        len(_registered_validator_cases(registration, include_chat=True))
        for registration in validator_manifest.values()
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory() as temporary:
        isolated_root = pathlib.Path(temporary)
        installed_root = isolated_root / "gradient-cio"
        shutil.copytree(
            ROOT,
            installed_root,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        isolated_fixtures = isolated_root / "fixtures"
        isolated_fixtures.mkdir()
        smoke_tested_validators = set()
        for skill_name, registration in validator_manifest.items():
            isolated_skill = installed_root / "skills" / skill_name
            for validator_name, fixture_name in _registered_validator_cases(
                registration, include_chat=True
            ):
                source_fixture = FIX / fixture_name
                isolated_fixture = isolated_fixtures / fixture_name
                isolated_fixture.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_fixture, isolated_fixture)
                if validator_name is None:
                    exercised += 1
                    continue
                validator_path = (
                    installed_root / pathlib.Path(validator_name)
                ).resolve()
                expected_prefix = (
                    installed_root / "skills" / skill_name
                ).resolve()
                try:
                    validator_path.relative_to(expected_prefix)
                except ValueError:
                    failures.append(
                        f"{skill_name}/{fixture_name}: validator is outside its skill"
                    )
                    continue
                if not validator_path.is_file():
                    failures.append(
                        f"{skill_name}/{fixture_name}: missing validator {validator_name}"
                    )
                    continue
                exercised += 1
                smoke_key = (skill_name, validator_name)
                if smoke_key in smoke_tested_validators:
                    continue
                smoke_tested_validators.add(smoke_key)
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
                            f"import sys; sys.path.insert(0, {str(installed_root / 'shared')!r}); "
                            "import gradient_report; "
                            "assert '@font-face' in gradient_report.FONT_LINK"
                        ),
                    ],
                    cwd=installed_root / "shared",
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
