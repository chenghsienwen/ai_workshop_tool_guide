Generate a single PDF of the whole guide (root picker, install guides, workshop
sessions) by running the existing `generate_pdf.py` script (Playwright renders each
page → pypdf rewrites cross-page links into internal PDF jumps → pdfunite merges them
in order). See `docs/PLAN_pdf-generation.md` for the full design and known quirks it
works around (gray-box emoji, oversized screenshots, dead local-file links).

Output written to `dist/`:
- `ai-workshop-tool-guide-<date>-<git-sha>.pdf`

```bash
cd "$(git rev-parse --show-toplevel)" && python3 scripts/generate_pdf.py
```

Requires `playwright` + `pypdf` (`pip3 install -r scripts/requirements.txt`) and the
system `pdfunite` binary (poppler-utils).

Report success/failure, the file size, and the "Rewrote N cross-page link(s)" line
from the script output.
