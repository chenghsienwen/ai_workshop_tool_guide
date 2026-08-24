# Compose site pages into a single PDF

## Context

Distributing the guide via a Dropbox folder link doesn't work because Dropbox's web
preview can't navigate between linked HTML documents (confirmed in the prior turn —
Dropbox previews one document at a time, it isn't a real static host). Instead of
relying on Dropbox to serve a multi-page site, we'll pre-render all the pages into one
linear PDF that anyone can open directly, no click-through navigation required.

The user pointed at `~/vsi/VS-API-Gateway`'s existing PDF-generation skill
(`.claude/skills/gen-userguide-pdf.md` → `docs/userguide/scripts/generate_pdf.py`) as
the pattern to follow: render HTML to PDF with headless Chromium via Playwright. That
script goes Markdown → pandoc → HTML → Playwright → PDF for a single doc; we only need
the HTML → Playwright → PDF half, run once per page, then merge the pages in order.

Confirmed in this environment already:
- `playwright` (Python) is installed and its Chromium browser launches successfully.
- `pdfunite` (poppler-utils) is available on PATH for merging PDFs — no need for
  `pypdf`/`pikepdf`.
- None of the 8 pages load external scripts/iframes/CDN resources (checked via grep),
  so rendering from local `file://` paths needs no network access.
- Several pages (`install/windows.html`, `install/macos.html`, all 3
  `workshop/session-*/index.html`) use native `<details>` elements for collapsible
  sections, closed by default. Chromium's print-to-PDF omits the content of a closed
  `<details>`, so it must be force-opened via `page.evaluate()` before calling
  `page.pdf()`, or those steps will silently vanish from the PDF.

## Approach

New script: `scripts/generate_pdf.py` (Python, same directory as the existing
`scripts/package-release.sh`).

**Page order** (mirrors `README.md`'s "Site structure" section / the real click-through
path):
1. `index.html`
2. `install/index.html`
3. `install/windows.html`
4. `install/macos.html`
5. `workshop/index.html`
6. `workshop/session-1/index.html`
7. `workshop/session-2/index.html`
8. `workshop/session-3/index.html`

**Per-page render** (Playwright, headless Chromium, one shared browser instance):
- `page.goto(f"file://{abs_path}", wait_until="networkidle")`
- `page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")`
  to expand every collapsible section so nothing is missing from the PDF.
- `page.pdf(path=tmp_pdf, format="A4", print_background=True, margin={"top": "20mm",
  "bottom": "20mm", "left": "18mm", "right": "18mm"})` — same margins as the
  VS-API-Gateway script, kept for visual consistency across our PDF tooling.
- Write each page's PDF to a temp file in order.

**Merge**: `subprocess.run(["pdfunite", *tmp_pdfs, out_path])` to concatenate the 8
per-page PDFs into one file, then delete the temp files.

**Output path & versioning**: reuse the same version scheme as
`scripts/package-release.sh` (`<date>-<short-sha>`, overridable via a CLI arg) so both
artifacts stay named consistently — `dist/ai-workshop-tool-guide-<version>.pdf`.
`dist/` is already gitignored from the earlier packaging work.

**Visual fidelity — explicit decision**: render pages exactly as they look on screen
(dark theme, `print_background=True`), rather than injecting a separate light
print-stylesheet. This matches the "render as viewed" spirit of the reference script
and needs no new CSS. Flagging this because a dark-themed PDF is heavier to print on
paper — if that turns out to matter, a follow-up would add a `print.css` override
(same pattern as `VS-API-Gateway/docs/userguide/print.css`), but that's out of scope
unless requested.

**Cross-page links**: on-page `#anchor` TOC links already work as intra-page PDF
destinations (Chromium handles this natively per-document). Cross-*page* links
(`<a href="install/index.html">`, breadcrumbs back to `../index.html`, etc.) were
initially left as-is — see Revision 2026-08-24 (#2) below for why that had to change.
External `https://` links (Gemini, Node.js installer, Dropbox asset links, etc.)
remain clickable, since those survive as normal link annotations untouched by any of
this.

## Files touched

- **New**: `scripts/generate_pdf.py`
- **New**: `scripts/requirements.txt` (`playwright`, `pypdf`)

No existing files change.

## Verification

1. Run `python3 scripts/generate_pdf.py` from the repo root.
2. Confirm `dist/ai-workshop-tool-guide-<version>.pdf` exists and has a non-trivial
   size (sanity check, e.g. `ls -lh`).
3. Extract text (`pdftotext dist/*.pdf -`) and confirm content from a closed-by-default
   `<details>` block (e.g. one of the Windows/macOS admin-access notes) appears in the
   output — proves the force-open step worked.
4. Spot-check page count / ordering is sane (`pdfinfo`), and render a couple of pages
   to PNG (`pdftoppm -png -f 1 -l 1 ...`) to eyeball that the first page is the root
   picker and images (e.g. `assets/workshop-session-3/*.png`) actually appear.

## Revision 2026-08-24: fix gray icons and a vanishing screenshot

Reviewing the first generated PDF page-by-page (`pdftoppm` renders of every page)
surfaced two real defects, both in Chromium's print-to-PDF path rather than in the
site content itself:

1. **Some emoji render as blank gray boxes.** `🆓` and `💳` (the "方案 A"/"方案 B"
   labels in `install/windows.html` / `install/macos.html`) came out as plain gray
   rectangles, while other emoji on the same pages (🤖⚙️🛠️🔑🪟🍎💬🎨📊⚠️✅ℹ️) rendered
   in full color. This is a known Chromium headless print-to-PDF limitation: some
   color-emoji glyphs don't survive the PDF font/glyph path even though they display
   correctly on screen. Confirmed by rendering page 4 of the PDF to PNG and comparing
   against the source HTML at that line.

2. **A screenshot vanishes behind a blank page.** `workshop/session-3/index.html`'s
   `vscode_open_folder.png` (the one with the red "Open Folder" highlight box the
   step depends on) is tall enough that Chromium's paginator can't fit it in the
   remaining space on the current page. Instead of shrinking or breaking it, the
   browser pushes the whole image forward — landing an entirely blank page in
   between before the image finally appears on the page after that. A reader would
   flip through a blank page with no warning a screenshot is coming. Confirmed by
   rendering pages 33–35: page 33 ends with mostly empty space after the step-3
   heading, page 34 is completely blank, and the image only appears on page 35.

**Fix, both applied inside `render_page()` in `scripts/generate_pdf.py`, right after
the `<details>` force-open step and before `page.pdf()` — no site HTML changes:**

- **Emoji → canvas image.** Run a `page.evaluate()` script that walks all text nodes
  under `<body>`, finds every grapheme matching `\p{Extended_Pictographic}️?`,
  draws it onto an offscreen `<canvas>` using the same OS emoji font that already
  renders it correctly on screen, and replaces the matched text with an inline
  `<img>` built from `canvas.toDataURL('image/png')` (sized to `1em`, so it flows
  with surrounding text). This sidesteps Chromium's PDF glyph path entirely and
  applies uniformly to all emoji on the page — not just the two found today — so a
  future emoji hitting the same Chromium bug is covered without touching this
  script again.
- **Cap image height to fit one page.** Inject a `<style>` tag via
  `page.add_style_tag()` that sets `img { max-height: 230mm !important; }`
  (A4 minus the existing 20mm top/bottom margins, with a small buffer for a caption
  below). Combined with an image's existing `width: 100%`, this uses the standard
  CSS replaced-element sizing algorithm to shrink an oversized screenshot to fit
  within one page's content box, preserving aspect ratio, instead of triggering the
  paginator's "reserve a blank page" behavior for content taller than one page.

Both fixes are general (regex-driven / CSS-driven), not special-cased to `🆓`, `💳`,
or `vscode_open_folder.png` specifically, since new workshop sessions will keep
adding emoji and screenshots.

### Updated verification

5. Re-render page 4 (`pdftoppm -png -f 4 -l 4 -r 100 dist/*.pdf out`) and confirm
   "方案 A"/"方案 B" now show colored icons, not gray boxes.
6. Re-render pages 33–35 of the Session 3 range and confirm the `vscode_open_folder.png`
   screenshot (with its red "Open Folder" highlight) now appears without an
   intervening blank page.
7. Spot-check that already-correct emoji (e.g. the root picker's 🤖⚙️🛠️) still look
   right after the canvas-image swap — same size, same position in the sentence.

## Revision 2026-08-24 (#2): cross-page links can't point at a local file path

The picker cards (root → install/workshop, install picker → Windows/macOS, workshop
picker → sessions) and every "← 返回首頁"/breadcrumb link are ordinary `<a href="...">`
tags pointing at sibling HTML files. Chromium prints these as PDF link annotations
with a `/URI` action — but the URI is the *absolute local file path on the machine
that generated the PDF* (e.g. `file:///<repo-checkout-path>/install/index.html`,
confirmed by inspecting the annotation dict with `pypdf`). Anyone who only has the
PDF (the whole point of this exercise) gets a dead link, or worse, a link that
leaks the generator's local directory layout. Same root cause as the original
Dropbox problem, just surfacing again one layer down.

**Fix**: added `pypdf` as a new dependency (`scripts/requirements.txt`) and a
post-merge pass, `fix_internal_links()` in `scripts/generate_pdf.py`:

1. While rendering each of the 8 pages, record how many PDF pages it produced
   (`len(pypdf.PdfReader(tmp_pdf).pages)`) and accumulate a
   `{resolved source path: starting page index}` map — e.g. `install/windows.html`
   starts at page 2 of the merged document.
2. After `pdfunite` merges everything, re-open the merged PDF with `pypdf`. For
   every link annotation whose action is a `file://` URI, resolve that path back
   to one of the 8 known source pages via the map, and replace the annotation's
   action with a real `/GoTo` destination pointing at that page's object
   (`writer.pages[offset].indirect_reference`) — a genuine internal PDF jump, not
   text.
3. Overwrite the merged PDF in place with the rewritten version.

This is a general fix, not hardcoded to specific cards: it rewrites *every*
cross-page link found, so it keeps working if new pages/sessions are added later.
Verified on the 2026-08-24 build: 15 cross-page links were found and rewritten, 0
leftover `file://` links remained, and every rewritten `/GoTo` target was confirmed
(via `PdfReader.get_page_number()`) to resolve to the correct page — e.g. the root
page's two cards jump to pages 1 and 15 (0-indexed), matching `install/index.html`
and `workshop/index.html`'s actual positions in the merged 36-page document.

### Updated verification

8. Run `python3 scripts/generate_pdf.py` and confirm the "Rewrote N cross-page
   link(s)" line reports 0 dropped/unresolved links.
9. Programmatically re-open the output with `pypdf`, assert no remaining annotation
   has a `/URI` action starting with `file://`, and for each `/GoTo` annotation
   resolve `get_page_number()` on its destination and sanity-check it against the
   expected section (e.g. the root page's cards should land on the install and
   workshop picker pages).
10. Re-render page 1 to PNG after the `pypdf` rewrite and confirm the page still
    looks correct (the rewrite didn't corrupt the PDF).
