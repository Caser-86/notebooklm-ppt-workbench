# Sample NotebookLM Exports

Place manually downloaded NotebookLM export fixtures here for local regression and acceptance runs.

Recommended sample packs:

- `link-heavy/`
- `table-heavy/`
- `icon-card/`

Each sample folder should contain:

- exported slide images such as `slide-1.png`
- optional OCR JSON such as `ocr.json`
- optional original export artifact such as `export.pptx`
- the local notes file in this repo that explains what the sample is meant to validate

Suggested layout:

- `link-heavy/README.md`
- `link-heavy/prompt.txt`
- `link-heavy/source-manifest.json`
- `link-heavy/slide-1.png`
- `link-heavy/ocr.json`

- `table-heavy/README.md`
- `table-heavy/prompt.txt`
- `table-heavy/source-manifest.json`
- `table-heavy/slide-1.png`
- `table-heavy/ocr.json`

- `icon-card/README.md`
- `icon-card/prompt.txt`
- `icon-card/source-manifest.json`
- `icon-card/slide-1.png`
- `icon-card/ocr.json`

## Direct PPTX Import Samples

For the local PPTX import workflow, you can also use decks from:

- `samples/generated_demo/ai-history-cn-demo.pptx`
- `samples/generated_demo/editable-rebuild-demo.pptx`

Recommended validation order:

1. import an internally generated PPTX first
2. verify the imported revision appears in the workbench
3. verify the imported object summary shows meaningful counts for text, image, table, or card blocks
4. trigger rebuild from that imported revision
5. confirm the editable rebuild preserves those structures where expected
6. then repeat with a NotebookLM-related export or a generic local `.pptx`
