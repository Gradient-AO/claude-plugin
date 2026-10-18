"""Dependency-free static repository checks and suite ordering."""

from suites.connector_contracts import (
    contract_checker,
    contract_checker_static_edges,
    contract_manifest,
)
from suites.renderer_regressions import chart_renderer
from suites.report_validators import connector_cutover
from suites.static.attribution import (
    attribution_compare_contract_checks,
    attribution_skill_contract_checks,
)
from suites.static.catalog_routing import catalog_routing_checks
from suites.static.examples import analysis_example_checks, public_example_cover_checks
from suites.static.handoffs import handoff_contract_checks
from suites.static.packaging import self_contained_report_skill_checks
from suites.static.report_validators import (
    portfolio_import_governed_contract_checks,
    private_markets_pme_contract_checks,
    registered_json_validator_checks,
    sources_appendix_contract_checks,
)
from suites.static.source_hygiene import source_hygiene_checks


def static(allow_branded):
    print("Static checks")
    skills, validator_manifest = catalog_routing_checks()
    attribution_skill_contract_checks()
    self_contained_report_skill_checks(skills, validator_manifest)
    sources_appendix_contract_checks()
    registered_json_validator_checks(validator_manifest)
    handoff_contract_checks()
    attribution_compare_contract_checks()
    public_example_cover_checks()
    analysis_example_checks()
    private_markets_pme_contract_checks()
    portfolio_import_governed_contract_checks()
    source_hygiene_checks(allow_branded)
    connector_cutover()
    chart_renderer()
    contract_manifest()
    contract_checker_static_edges()
    contract_checker()
