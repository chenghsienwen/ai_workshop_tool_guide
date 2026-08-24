#!/usr/bin/env python3
"""Render the site's HTML pages to PDF via Playwright and merge them in order."""

import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

import pypdf
from pypdf.generic import ArrayObject, DictionaryObject, NameObject

BASE = Path(__file__).parent.parent

PAGES = [
    "index.html",
    "install/index.html",
    "install/windows.html",
    "install/macos.html",
    "workshop/index.html",
    "workshop/session-1/index.html",
    "workshop/session-2/index.html",
    "workshop/session-3/index.html",
]


def version() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=BASE, capture_output=True, text=True
    ).stdout.strip()
    date = subprocess.run(["date", "+%Y%m%d"], capture_output=True, text=True).stdout.strip()
    return f"{date}-{sha}"


# A4 (297mm) minus the top/bottom print margins below, with a little slack for a
# caption under the image. Without this, an image taller than one page's content box
# makes Chromium's paginator reserve a whole blank page before placing it on the next.
IMAGE_MAX_HEIGHT_CSS = "img { max-height: 230mm !important; }"

# Some color-emoji glyphs (e.g. 🆓, 💳) render as blank gray boxes through Chromium's
# print-to-PDF font/glyph path even though they display correctly on screen. Redrawing
# each one onto an offscreen canvas with the same OS emoji font and swapping in the
# resulting <img> sidesteps that PDF-only rendering path entirely.
EMOJI_TO_IMAGE_JS = r"""
() => {
  const emojiRe = /\p{Extended_Pictographic}️?/gu;

  function toImage(ch, fontSize) {
    const scale = 4;
    const size = Math.ceil(fontSize * scale);
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    ctx.font = `${size * 0.86}px "Noto Color Emoji", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(ch, size / 2, size / 2 + size * 0.06);
    const img = document.createElement('img');
    img.src = canvas.toDataURL('image/png');
    img.style.height = '1em';
    img.style.width = '1em';
    img.style.verticalAlign = '-0.15em';
    img.style.display = 'inline-block';
    return img;
  }

  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const targets = [];
  let node;
  while ((node = walker.nextNode())) {
    emojiRe.lastIndex = 0;
    if (emojiRe.test(node.nodeValue)) targets.push(node);
  }

  for (const textNode of targets) {
    const text = textNode.nodeValue;
    const fontSize = parseFloat(getComputedStyle(textNode.parentElement).fontSize) || 16;
    const frag = document.createDocumentFragment();
    let last = 0;
    let m;
    emojiRe.lastIndex = 0;
    while ((m = emojiRe.exec(text))) {
      if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      frag.appendChild(toImage(m[0], fontSize));
      last = m.index + m[0].length;
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
    textNode.parentNode.replaceChild(frag, textNode);
  }
}
"""


def render_page(page, html_path: Path, out_path: Path) -> None:
    """Render one HTML file to a PDF, expanding closed <details> and working
    around two Chromium print-to-PDF quirks: gray-box emoji and screenshots
    tall enough to orphan a blank page (see docs/PLAN_pdf-generation.md)."""
    page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
    page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    page.add_style_tag(content=IMAGE_MAX_HEIGHT_CSS)
    page.evaluate(EMOJI_TO_IMAGE_JS)
    page.pdf(
        path=str(out_path),
        format="A4",
        print_background=True,
        margin={"top": "20mm", "bottom": "20mm", "left": "18mm", "right": "18mm"},
    )


def fix_internal_links(merged_pdf: Path, page_offsets: dict) -> None:
    """Replace cross-page <a href> links (which Chromium prints as file:// URI
    actions pointing at the machine that generated the PDF — meaningless to
    anyone who only has the PDF) with real internal "jump to page" links,
    using the page_offsets map of {resolved source path: start page index}."""
    reader = pypdf.PdfReader(str(merged_pdf))
    writer = pypdf.PdfWriter()
    writer.append(reader)

    fixed, dropped = 0, 0
    for pdf_page in writer.pages:
        annots = pdf_page.get("/Annots")
        if not annots:
            continue
        for annot in annots:
            obj = annot.get_object()
            action = obj.get("/A")
            if not action or action.get("/S") != "/URI":
                continue
            uri = action.get("/URI", "")
            if not uri.startswith("file://"):
                continue
            target = Path(urllib.parse.unquote(urllib.parse.urlparse(uri).path))
            offset = page_offsets.get(target)
            if offset is None:
                # Shouldn't happen (every internal link points at one of our
                # PAGES), but don't leave a dead local-file link in either.
                del obj[NameObject("/A")]
                dropped += 1
                continue
            goto = DictionaryObject()
            goto[NameObject("/S")] = NameObject("/GoTo")
            goto[NameObject("/D")] = ArrayObject(
                [writer.pages[offset].indirect_reference, NameObject("/Fit")]
            )
            obj[NameObject("/A")] = goto
            fixed += 1

    writer.write(str(merged_pdf))
    print(f"Rewrote {fixed} cross-page link(s) to internal page jumps"
          + (f", dropped {dropped} unresolved link(s)" if dropped else ""))


def main() -> None:
    from playwright.sync_api import sync_playwright

    out = BASE / "dist" / f"ai-workshop-tool-guide-{version()}.pdf"
    out.parent.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir, sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        tmp_pdfs = []
        page_offsets = {}
        next_offset = 0
        for i, rel_path in enumerate(PAGES):
            html_path = BASE / rel_path
            tmp_pdf = Path(tmp_dir) / f"{i:02d}.pdf"
            print(f"Rendering {rel_path}")
            render_page(page, html_path, tmp_pdf)
            tmp_pdfs.append(str(tmp_pdf))
            page_offsets[html_path.resolve()] = next_offset
            next_offset += len(pypdf.PdfReader(str(tmp_pdf)).pages)

        browser.close()

        print(f"Merging {len(tmp_pdfs)} pages -> {out}")
        subprocess.run(["pdfunite", *tmp_pdfs, str(out)], check=True)

        fix_internal_links(out, page_offsets)

    print(f"\nDone: {out.name}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
