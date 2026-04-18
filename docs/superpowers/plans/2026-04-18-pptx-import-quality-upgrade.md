# PPTX Import Quality Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade local PPTX import so editable rebuilds preserve more real PPT objects such as text boxes, pictures, tables, and simple icon-card structures instead of collapsing mostly into generic text reconstruction.

**Architecture:** Extend `agent/app/services/pptx_import.py` from a text-dump extractor into an object-aware importer. Add a normalized imported-block model that feeds the existing renderer in `editable_rebuild.py`, keeping the OCR path intact as a separate fallback. Improve tests from service-level extraction through rebuild-level object verification.

**Tech Stack:** FastAPI, SQLModel, python-pptx, React, TypeScript, Vitest, pytest

---

## File Structure

### Backend import layer

- Modify: `agent/app/services/pptx_import.py`
  - add object-aware PPTX extraction
  - add normalized imported block generation
- Modify: `agent/app/models.py`
  - expand import persistence if object metadata needs storage
- Modify: `agent/app/schemas.py`
  - expose richer imported slide asset fields when needed
- Modify: `agent/app/api/jobs.py`
  - rebuild imported PPTX from normalized imported blocks rather than ad-hoc text synthesis

### Backend reconstruction layer

- Modify: `agent/app/services/reconstruct/editable_rebuild.py`
  - accept imported object-aware blocks cleanly
- Modify: `agent/app/services/reconstruct/layout_analysis.py`
  - reuse or bypass OCR-oriented analysis depending on imported block type
- Optionally modify: `agent/app/services/reconstruct/display_clone.py`
  - only if object-aware import changes display clone input assumptions

### Backend tests

- Modify: `agent/tests/test_pptx_import_service.py`
  - add extraction tests for text, image, and table objects
- Modify: `agent/tests/test_pptx_import_api.py`
  - assert imported rebuild output contains better object structure
- Modify: `agent/tests/test_editable_rebuild.py`
  - verify imported object blocks render correctly
- Optionally create: `agent/tests/fixtures/pptx_import/`
  - sample decks for text/image/table/icon-card coverage

### Frontend

- Modify: `web/src/components/ProjectWorkspace.tsx`
  - show richer import metadata if exposed
- Modify: `web/src/lib/types.ts`
  - carry richer import slide asset data if added
- Modify: `web/src/lib/api.ts`
  - adapt to enriched import payloads if needed

### Docs

- Modify: `docs/DELIVERY.md`
  - describe upgraded imported editability strengths
- Modify: `docs/ACCEPTANCE.md`
  - add new import-quality checks

## Task 1: Add Object-Aware PPTX Extraction For Text And Images

**Files:**
- Modify: `agent/app/services/pptx_import.py`
- Modify: `agent/tests/test_pptx_import_service.py`
- Optionally modify: `agent/tests/conftest.py`

- [ ] **Step 1: Write the failing extraction tests**

Add tests that assert imported PPTX extraction produces object-aware slide blocks rather than only text dumps.

```python
def test_extract_pptx_text_boxes_as_imported_text_blocks(build_fixture_pptx, tmp_path):
    pptx_path = build_fixture_pptx("text-blocks.pptx", ["Quarterly update"])

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert bundle.slides[0].blocks[0]["content_type"] == "imported_text"
    assert bundle.slides[0].blocks[0]["text_role"] == "title"


def test_extract_pptx_picture_as_imported_image_block(tmp_path):
    pptx_path = build_fixture_pptx_with_picture(tmp_path)

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert any(block["content_type"] == "imported_image" for block in bundle.slides[0].blocks)
```

- [ ] **Step 2: Run the tests to verify failure**

Run: `python -m pytest agent/tests/test_pptx_import_service.py -v`
Expected: FAIL because `ImportedSlideBundle` does not yet expose object-aware blocks.

- [ ] **Step 3: Extend the import bundle types**

Update `agent/app/services/pptx_import.py` so slide bundles carry normalized imported blocks.

```python
@dataclass
class ImportedSlideBundle:
    slide_index: int
    preview_image_path: str
    text_dump: str
    structure_json_path: str
    blocks: list[dict]
```

- [ ] **Step 4: Implement text-box extraction**

Extract text shapes directly from PowerPoint slides and normalize them.

```python
def _extract_text_blocks(slide, slide_index: int) -> list[dict]:
    blocks = []
    for shape in slide.shapes:
        if not hasattr(shape, "text") or not shape.text or not shape.text.strip():
            continue
        blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_text",
                "text": shape.text.strip(),
                "text_role": "title" if shape == slide.shapes.title else "body",
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "font_size": 24,
                "bold": False,
                "italic": False,
            }
        )
    return blocks
```

- [ ] **Step 5: Implement picture extraction**

Add picture normalization using file-backed image artifacts.

```python
def _extract_picture_blocks(slide, slide_index: int, import_dir: Path) -> list[dict]:
    picture_blocks = []
    for picture_index, shape in enumerate(slide.shapes, start=1):
        if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
            continue
        image_path = import_dir / f"slide-{slide_index}-image-{picture_index}.png"
        image_path.write_bytes(shape.image.blob)
        picture_blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_image",
                "image_path": str(image_path),
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
            }
        )
    return picture_blocks
```

- [ ] **Step 6: Run the updated extraction tests**

Run: `python -m pytest agent/tests/test_pptx_import_service.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/app/services/pptx_import.py agent/tests/test_pptx_import_service.py agent/tests/conftest.py
git commit -m "feat: extract imported text and image blocks"
```

## Task 2: Extract PowerPoint Tables As Native Imported Table Blocks

**Files:**
- Modify: `agent/app/services/pptx_import.py`
- Modify: `agent/tests/test_pptx_import_service.py`
- Modify: `agent/tests/test_pptx_import_api.py`

- [ ] **Step 1: Write the failing table extraction test**

```python
def test_extract_powerpoint_table_as_imported_table_block(build_fixture_pptx_with_table, tmp_path):
    pptx_path = build_fixture_pptx_with_table(tmp_path)

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    table_block = next(block for block in bundle.slides[0].blocks if block["content_type"] == "imported_table")
    assert table_block["rows"] == 2
    assert table_block["cols"] == 2
```

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m pytest agent/tests/test_pptx_import_service.py::test_extract_powerpoint_table_as_imported_table_block -v`
Expected: FAIL because table extraction does not exist yet.

- [ ] **Step 3: Add table extraction**

Implement native table extraction in `agent/app/services/pptx_import.py`.

```python
def _extract_table_blocks(slide, slide_index: int) -> list[dict]:
    blocks = []
    for shape in slide.shapes:
        if not shape.has_table:
            continue
        table = shape.table
        blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_table",
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "rows": len(table.rows),
                "cols": len(table.columns),
                "cells": [[{"text": cell.text, "font_size": 18} for cell in row.cells] for row in table.rows],
                "column_widths": [column.width / EMU_PER_INCH for column in table.columns],
                "header_rows": 1,
            }
        )
    return blocks
```

- [ ] **Step 4: Merge table blocks into slide extraction output**

Update the slide extraction pipeline so tables are included alongside text and images.

```python
blocks = []
blocks.extend(_extract_text_blocks(slide, index))
blocks.extend(_extract_picture_blocks(slide, index, import_dir))
blocks.extend(_extract_table_blocks(slide, index))
```

- [ ] **Step 5: Run table-related tests**

Run:

- `python -m pytest agent/tests/test_pptx_import_service.py -v`
- `python -m pytest agent/tests/test_pptx_import_api.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/app/services/pptx_import.py agent/tests/test_pptx_import_service.py agent/tests/test_pptx_import_api.py
git commit -m "feat: extract imported powerpoint tables"
```

## Task 3: Normalize Imported Blocks For The Existing Renderer

**Files:**
- Modify: `agent/app/api/jobs.py`
- Modify: `agent/app/services/reconstruct/editable_rebuild.py`
- Modify: `agent/tests/test_pptx_import_api.py`
- Modify: `agent/tests/test_editable_rebuild.py`

- [ ] **Step 1: Write the failing rebuild test**

Add a test proving imported PPTX rebuilds preserve object types better than plain text synthesis.

```python
def test_imported_table_rebuild_stays_editable_table(client, pptx_with_table):
    imported = upload_fixture_import(client, pptx_with_table)

    client.post(f"/imports/{imported['id']}/rebuild")

    editable = Presentation(ARTIFACTS_ROOT / "1" / "rebuild-001" / "editable-rebuild.pptx")
    assert any(shape.has_table for shape in editable.slides[0].shapes)
```

- [ ] **Step 2: Run the failing test**

Run: `python -m pytest agent/tests/test_pptx_import_api.py::test_imported_table_rebuild_stays_editable_table -v`
Expected: FAIL because imported rebuild still synthesizes OCR-like text blocks.

- [ ] **Step 3: Replace ad-hoc OCR-like import rebuild synthesis**

Update `agent/app/api/jobs.py` so imported rebuild uses object-aware blocks from the stored import assets.

```python
ocr_blocks = []
for asset in slide_assets:
    structure_blocks = json.loads(asset.structure_json_path.read_text()) if asset.structure_json_path else []
    if structure_blocks:
        ocr_blocks.extend(structure_blocks)
    else:
        ocr_blocks.extend(_fallback_text_blocks(asset))
```

- [ ] **Step 4: Teach the renderer to consume imported block types**

Update `editable_rebuild.py` to recognize imported block content types and route them into existing rendering paths.

```python
if block.get("content_type") in {"imported_table", "table"}:
    ...
if block.get("content_type") in {"imported_image", "image"}:
    ...
if block.get("content_type") in {"imported_text", "text"}:
    ...
```

- [ ] **Step 5: Keep OCR path unchanged**

Verify OCR-based manual export rebuild still uses its current block flow and does not require imported PPTX structure data.

- [ ] **Step 6: Run rebuild-focused tests**

Run:

- `python -m pytest agent/tests/test_pptx_import_api.py -v`
- `python -m pytest agent/tests/test_editable_rebuild.py -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/app/api/jobs.py agent/app/services/reconstruct/editable_rebuild.py agent/tests/test_pptx_import_api.py agent/tests/test_editable_rebuild.py
git commit -m "feat: rebuild imported pptx from object-aware blocks"
```

## Task 4: Add Icon-Card Grouping For Imported PPTX Objects

**Files:**
- Modify: `agent/app/services/pptx_import.py`
- Modify: `agent/app/services/reconstruct/layout_analysis.py`
- Modify: `agent/tests/test_pptx_import_service.py`
- Modify: `agent/tests/test_pptx_import_api.py`

- [ ] **Step 1: Write the failing icon-card grouping test**

```python
def test_group_imported_icon_card_objects(build_fixture_pptx_with_icon_card, tmp_path):
    pptx_path = build_fixture_pptx_with_icon_card(tmp_path)

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert any(block["content_type"] == "imported_icon_card" for block in bundle.slides[0].blocks)
```

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m pytest agent/tests/test_pptx_import_service.py::test_group_imported_icon_card_objects -v`
Expected: FAIL because imported icon-card grouping does not exist yet.

- [ ] **Step 3: Add grouping logic in the import layer**

Implement a confidence-based grouping pass over imported text and image blocks.

```python
def group_imported_icon_cards(blocks: list[dict]) -> list[dict]:
    # find small image + nearby title + nearby body
    # replace those components with a single imported_icon_card block
```

- [ ] **Step 4: Keep layout analysis compatible**

Adjust `layout_analysis.py` only as needed so imported icon-card blocks pass through without OCR-specific reclassification.

```python
if block.get("content_type") == "imported_icon_card":
    return blocks
```

- [ ] **Step 5: Run grouping and rebuild tests**

Run:

- `python -m pytest agent/tests/test_pptx_import_service.py -v`
- `python -m pytest agent/tests/test_pptx_import_api.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/app/services/pptx_import.py agent/app/services/reconstruct/layout_analysis.py agent/tests/test_pptx_import_service.py agent/tests/test_pptx_import_api.py
git commit -m "feat: group imported icon cards"
```

## Task 5: Expose Richer Import Metadata And Verify In The Workspace

**Files:**
- Modify: `agent/app/api/projects.py`
- Modify: `agent/app/schemas.py`
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing frontend metadata test**

```tsx
it("shows richer imported pptx metadata", async () => {
  render(<ProjectWorkspace projectId={1} />);
  expect(await screen.findByText("导入对象摘要")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: FAIL because import object summaries are not yet shown.

- [ ] **Step 3: Expose richer import metadata from the API**

Add summary fields like object counts per import record.

```python
class ImportedPresentationRead(BaseModel):
    ...
    object_summary: dict[str, int] = {}
```

- [ ] **Step 4: Surface the summary in the UI**

Update `ProjectWorkspace.tsx` to show counts for text, image, table, and icon-card objects.

```tsx
<div className="import-object-summary">
  <span>Text: {entry.object_summary.imported_text ?? 0}</span>
  <span>Images: {entry.object_summary.imported_image ?? 0}</span>
  <span>Tables: {entry.object_summary.imported_table ?? 0}</span>
</div>
```

- [ ] **Step 5: Run frontend verification**

Run:

- `npm test -- --run ProjectWorkspace.test.tsx`
- `npm run build`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/app/api/projects.py agent/app/schemas.py web/src/lib/types.ts web/src/lib/api.ts web/src/components/ProjectWorkspace.tsx web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: show imported object summaries"
```

## Task 6: Update Acceptance Guidance And Sample Expectations

**Files:**
- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`
- Modify: `samples/notebooklm_exports/README.md`
- Optionally create or update: `agent/tests/fixtures/pptx_import/README.md`

- [ ] **Step 1: Document the upgraded import strengths**

Add to `docs/DELIVERY.md`:

```md
Imported PPTX rebuilds are now strongest on:
- text boxes
- pictures
- PowerPoint tables
- icon-card style image/text groups
```

- [ ] **Step 2: Add acceptance checks for editable structure**

Add to `docs/ACCEPTANCE.md`:

```md
After importing a local PPTX:
1. confirm text remains editable text boxes
2. confirm tables remain tables
3. confirm pictures remain picture objects
```

- [ ] **Step 3: Update sample guidance**

Document which sample decks are best for text/image/table/icon-card import validation.

- [ ] **Step 4: Run final verification**

Run:

- `cd agent && python -m pytest -q`
- `cd web && npm test -- --run`
- `cd web && npm run build`

Expected:

- backend suite passes
- frontend suite passes
- build succeeds

- [ ] **Step 5: Commit**

```bash
git add docs/DELIVERY.md docs/ACCEPTANCE.md samples/notebooklm_exports/README.md
git commit -m "docs: update pptx import quality guidance"
```

## Self-Review

### Spec coverage

- structure-first import objective: covered by Tasks 1-4
- object-aware extraction for text/images/tables: covered by Tasks 1-2
- icon-card grouping: covered by Task 4
- renderer reuse instead of parallel pipeline: covered by Task 3
- richer import metadata in UI: covered by Task 5
- docs and acceptance updates: covered by Task 6

### Placeholder scan

No `TODO`, `TBD`, or vague “handle later” instructions remain. Each task includes concrete files, verification commands, and implementation sketches.

### Type consistency

The plan consistently uses:

- `ImportedSlideBundle.blocks`
- `imported_text`
- `imported_image`
- `imported_table`
- `imported_icon_card`

These names are used consistently across extraction, API exposure, UI summary, and rebuild tasks.
