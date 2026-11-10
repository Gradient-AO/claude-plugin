"""Chart, PDF, PPTX, layout, and artifact regression checks coordinator."""

from suites.renderer.chart_svg_units import chart_svg_unit_checks
from suites.renderer.layout_budget_units import layout_budget_unit_checks
from suites.renderer.pdf_render_matrix import render
from suites.renderer.pptx_render_units import pptx_render_unit_checks

__all__ = ["chart_renderer", "render"]


def chart_renderer():
    chart_svg_unit_checks()
    layout_budget_unit_checks()
    pptx_render_unit_checks()
