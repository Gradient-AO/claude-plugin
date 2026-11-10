"""Chromium PDF launch, page-overflow checks, merging, and metadata/outline post-processing."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_theme import PDF_PAGE_MARGINS_IN, PPTX_SLIDE_HEIGHT_IN, PPTX_SLIDE_WIDTH_IN, THEME_VERSION

OVERFLOW_JS = """() => Array.from(document.querySelectorAll('.slide')).map((s, i) => {
  const b = s.querySelector('.s-body'); if (!b) return null;
  const limit = s.getBoundingClientRect().bottom - parseFloat(getComputedStyle(s).paddingBottom);
  return b.getBoundingClientRect().bottom > limit + 1 ? i + 1 : null; }).filter(x => x)"""

WIDTH_OVERFLOW_JS = """() => {
  const limit = window.innerWidth + 1, found = [];
  for (const el of document.body.querySelectorAll('table, svg, pre, img, div')) {
    const right = el.getBoundingClientRect().right;
    if (right > limit && !found.some(item => item.el.contains(el))) {
      found.push({el, right});
    }
  }
  return found.slice(0, 3).map(item => [
    Math.round(item.right - window.innerWidth),
    (item.el.closest('.keep, .atomic-table, section, .sec') || item.el).textContent.trim().slice(0, 80),
  ]);
}"""


def page_spec(meta):
    return (
        ("landscape", f"{PPTX_SLIDE_WIDTH_IN}in", f"{PPTX_SLIDE_HEIGHT_IN}in")
        if meta.get("orientation") == "landscape"
        else ("portrait", "8.5in", "11in")
    )


def _width_overflow_warning(pg, meta):
    """Warn when body content is wider than the printable page width."""
    page_width_in = float(page_spec(meta)[1].removesuffix("in"))
    width = round(
        (page_width_in - PDF_PAGE_MARGINS_IN["left"] - PDF_PAGE_MARGINS_IN["right"])
        * 96
    )
    pg.set_viewport_size({"width": width, "height": 1000})
    overflow = pg.evaluate(WIDTH_OVERFLOW_JS)
    if overflow:
        details = "; ".join(f"{px}px over in '{text}'" for px, text in overflow)
        print(
            "WARNING: content is wider than the page, so Chromium would shrink every page — "
            f"narrow the table or chart ({details})",
            file=sys.stderr,
        )


def _launch(p):
    kw = {}
    if os.path.isfile("/opt/pw-browsers/chromium"):
        kw["executable_path"] = "/opt/pw-browsers/chromium"
    return p.chromium.launch(**kw)


def _set(pg, src):
    pg.set_content(src, wait_until="load")
    pg.evaluate("document.fonts.ready.then(() => true)")
    pg.emulate_media(media="print")


def _postprocess_pdf(
    source,
    target,
    document,
    deck=False,
    *,
    author=None,
    renderer_version="1.2.0",
):
    """Apply metadata, language and title outlines after Chromium rendering."""
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject, TextStringObject
    except ImportError:
        if os.path.abspath(source) != os.path.abspath(target):
            shutil.move(source, target)
        print(
            "warning: pypdf not installed; PDF metadata and bookmarks were not added",
            file=sys.stderr,
        )
        return

    reader = PdfReader(source)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    meta = document["meta"]
    writer.add_metadata(
        {
            "/Title": str(meta.get("title", "")),
            "/Author": author or "GradientCIO",
            "/Subject": str(meta.get("header_label", "Gradient report")),
            "/Creator": f"Gradient CIO report renderer {renderer_version}",
            "/GradientThemeVersion": THEME_VERSION,
        }
    )
    writer._root_object.update({NameObject("/Lang"): TextStringObject("en-US")})

    entries = [(str(meta.get("title", "Cover")), 0)]
    if deck:
        entries.extend(
            (str(slide.get("title", "Slide")), None)
            for slide in document.get("slides", [])
        )
    else:
        entries.extend(
            (str(section.get("title", "Section")), None)
            for section in document.get("sections", [])
        )
    page_text = [(page.extract_text() or "") for page in reader.pages]
    search_from = 0
    for title, fixed_page in entries:
        page_index = fixed_page
        if page_index is None:
            page_index = next(
                (
                    index
                    for index in range(search_from, len(page_text))
                    if title in page_text[index]
                ),
                None,
            )
        if page_index is None:
            continue
        writer.add_outline_item(title, page_index)
        search_from = page_index

    output = target
    temporary = None
    if os.path.abspath(source) == os.path.abspath(target):
        handle, temporary = tempfile.mkstemp(
            suffix=".pdf", dir=os.path.dirname(os.path.abspath(target)) or None
        )
        os.close(handle)
        output = temporary
    with open(output, "wb") as stream:
        writer.write(stream)
    if temporary:
        os.replace(temporary, target)


def merge_pdf_files(p1: str, p2: str, merged: str) -> None:
    """Merge cover and body PDFs using pdfunite, qpdf, or pypdf."""
    if shutil.which("pdfunite"):
        subprocess.run(["pdfunite", p1, p2, merged], check=True)
    elif shutil.which("qpdf"):
        subprocess.run(
            ["qpdf", "--empty", "--pages", p1, p2, "--", merged], check=True
        )
    else:
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError as error:
            raise RuntimeError(
                "PDF merge requires pdfunite, qpdf, or the pypdf package"
            ) from error
        writer = PdfWriter()
        for source in (p1, p2):
            for page in PdfReader(source).pages:
                writer.add_page(page)
        with open(merged, "wb") as output:
            writer.write(output)
