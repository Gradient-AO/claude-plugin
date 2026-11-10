"""Report and composer validator regression checks coordinator."""

from suites.cutover.construction_and_idd import construction_and_idd_checks
from suites.cutover.gips_composer import gips_composer_checks
from suites.cutover.memo_and_review import memo_and_review_checks
from suites.cutover.pptx_contracts import pptx_cutover_checks


def connector_cutover():
    pptx_cutover_checks()
    memo_and_review_checks()
    gips_composer_checks()
    construction_and_idd_checks()
