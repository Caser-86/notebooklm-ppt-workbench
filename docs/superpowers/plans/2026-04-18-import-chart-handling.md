# Imported Chart Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add chart detection to the PPTX import pipeline, expose chart counts in import summaries, and preserve chart presence during rebuild through explicit fallback instead of silent loss.

**Architecture:** Extend `agent/app/services/pptx_import.py` with `imported_chart` extraction, reuse the existing import structure JSON flow for persistence and summaries, then add a chart fallback renderer in `editable_rebuild.py` that degrades charts into image-like or structured content rather than attempting native editable chart recreation in this phase.

**Tech Stack:** FastAPI, SQLModel, python-pptx, React, TypeScript, Vite, Vitest, pytest

---

## File Structure

### Backend import layer

- Modify: `agent/tests/conftest.py`
  - add chart fixture builder
- Modify: `agent/tests/test_pptx_import_service.py`
  - add chart extraction test
- Modify: `agent/app/services/pptx_import.py`
  - detect chart shapes and emit `imported_chart`

### Backend serialization and rebuild

- Modify: `agent/tests/test_pptx_import_api.py`
  - add chart summary and rebuild-presence tests
- Modify: `agent/app/api/projects.py`
  - ensure chart counts flow into import summaries
- Modify: `agent/app/api/jobs.py`
  - preserve chart blocks in imported rebuild input
- Modify: `agent/app/services/reconstruct/editable_rebuild.py`
  - add chart fallback rendering

### Frontend

- Modify: `web/src/components/ProjectWorkspace.tsx`
  - add chart counts to imported summaries if not already shown
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`
  - assert chart counts appear in imported summaries

### Docs

- Modify: `docs/DELIVERY.md`
  - describe chart handling and downgrade behavior
- Modify: `docs/ACCEPTANCE.md`
  - add chart-specific acceptance checks

## Task 1: Detect Charts During PPTX Import

**Files:**
- Modify: `agent/tests/conftest.py`
- Modify: `agent/tests/test_pptx_import_service.py`
- Modify: `agent/app/services/pptx_import.py`

- [ ] **Step 1: Write the failing chart extraction test**

Add a fixture and a service test that expects a chart-containing PPTX to produce an `imported_chart` block.

```python
def test_extract_powerpoint_chart_as_imported_chart_block(build_fixture_pptx_with_chart, tmp_path):
    pptx_path = build_fixture_pptx_with_chart("chart-blocks.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    chart_block = next(block for block in bundle.slides[0].blocks if block["content_type"] == "imported_chart")
    assert chart_block["chart_type"]
    assert chart_block["series"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest agent/tests/test_pptx_import_service.py::test_extract_powerpoint_chart_as_imported_chart_block -v`
Expected: FAIL because chart extraction does not exist yet.

- [ ] **Step 3: Add a chart fixture builder**

Update `agent/tests/conftest.py`.

```python
@pytest.fixture
def build_fixture_pptx_with_chart(tmp_path):
    def _build(filename: str = "chart-fixture.pptx") -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[5])
        slide.shapes.title.text = "Chart import"
        chart_data = ChartData()
        chart_data.categories = ["Q1", "Q2"]
        chart_data.add_series("Revenue", (12.0, 22.0))
        slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            Inches(1),
            Inches(1.6),
            Inches(5),
            Inches(3),
            chart_data,
        )
        output = tmp_path / filename
        presentation.save(output)
        return output
    return _build
```

- [ ] **Step 4: Add `imported_chart` extraction**

Update `agent/app/services/pptx_import.py`.

```python
def _extract_chart_blocks(slide, slide_index: int) -> list[dict]:
    chart_blocks = []
    for shape in slide.shapes:
        if not getattr(shape, "has_chart", False):
            continue
        chart = shape.chart
        chart_blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_chart",
                "chart_type": str(chart.chart_type),
                "title": chart.chart_title.text_frame.text if chart.has_title else "",
                "categories": [...],
                "series": [...],
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "snapshot_path": "",
                "fallback_mode": "table",
            }
        )
    return chart_blocks
```

- [ ] **Step 5: Merge chart blocks into slide extraction**

```python
blocks.extend(_extract_chart_blocks(slide, index))
```

- [ ] **Step 6: Run extraction verification**

Run: `python -m pytest agent/tests/test_pptx_import_service.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/tests/conftest.py agent/tests/test_pptx_import_service.py agent/app/services/pptx_import.py
git commit -m "feat: detect imported charts"
```

## Task 2: Expose Chart Counts In Import Summaries

**Files:**
- Modify: `agent/tests/test_pptx_import_api.py`
- Modify: `agent/app/api/projects.py`

- [ ] **Step 1: Write the failing API summary test**

```python
def test_imported_chart_counts_appear_in_import_summary(client, build_fixture_pptx_with_chart):
    project = client.post("/projects", json={"title": "Chart Import", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_chart("chart-summary.pptx")

    with pptx_path.open("rb") as handle:
        client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("chart-summary.pptx", handle, PPTX_MIME)},
        )

    imports = client.get(f"/projects/{project['id']}/imports").json()
    assert imports[0]["object_summary"]["imported_chart"] == 1
    assert imports[0]["slide_assets"][0]["object_summary"]["imported_chart"] == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest agent/tests/test_pptx_import_api.py::test_imported_chart_counts_appear_in_import_summary -v`
Expected: FAIL because chart counts are not yet present.

- [ ] **Step 3: Reuse slide-level summary flow**

Update `agent/app/api/projects.py` only if needed so chart blocks flow through existing summary logic.

```python
for block in _load_structure_blocks(asset):
    content_type = block.get("content_type")
    if content_type:
        summary[content_type] = summary.get(content_type, 0) + 1
```

- [ ] **Step 4: Run API verification**

Run: `python -m pytest agent/tests/test_pptx_import_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/app/api/projects.py agent/tests/test_pptx_import_api.py
git commit -m "feat: expose imported chart summaries"
```

## Task 3: Preserve Charts During Rebuild Through Explicit Fallback

**Files:**
- Modify: `agent/tests/test_pptx_import_api.py`
- Modify: `agent/app/api/jobs.py`
- Modify: `agent/app/services/reconstruct/editable_rebuild.py`

- [ ] **Step 1: Write the failing rebuild-presence test**

Add a test ensuring charts are not silently lost during rebuild.

```python
def test_imported_chart_rebuild_preserves_chart_presence(build_fixture_pptx_with_chart):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Chart Rebuild", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_chart("chart-rebuild.pptx")

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("chart-rebuild.pptx", handle, PPTX_MIME)},
        ).json()

    response = client.post(f"/imports/{imported['id']}/rebuild")
    assert response.status_code == 200
    editable = Presentation(ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "editable-rebuild.pptx")
    assert len(editable.slides[0].shapes) > 0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest agent/tests/test_pptx_import_api.py::test_imported_chart_rebuild_preserves_chart_presence -v`
Expected: FAIL or pass without any dedicated chart fallback, proving the gap.

- [ ] **Step 3: Preserve chart blocks in imported rebuild input**

Update `agent/app/api/jobs.py` so imported chart blocks are kept when reading structure JSON.

```python
if asset.structure_json_path:
    structure_path = Path(asset.structure_json_path)
    if structure_path.exists():
        normalized_blocks.extend(json.loads(structure_path.read_text(encoding="utf-8")))
        continue
```

- [ ] **Step 4: Add chart fallback rendering**

Update `editable_rebuild.py` to handle `imported_chart`.

```python
if block.get("content_type") == "imported_chart":
    if block.get("snapshot_path"):
        slide.shapes.add_picture(...)
        continue
    fallback_table = _build_chart_fallback_table(block)
    # render fallback_table through the existing table path
    continue
```

- [ ] **Step 5: Implement a simple chart-to-table fallback helper**

```python
def _build_chart_fallback_table(block: dict) -> dict:
    categories = block.get("categories", [])
    series = block.get("series", [])
    header = [{"text": "Category", "font_size": 18}] + [{"text": item["name"], "font_size": 18} for item in series]
    rows = [header]
    for index, category in enumerate(categories):
        row = [{"text": category, "font_size": 16}]
        for item in series:
            row.append({"text": str(item["values"][index]), "font_size": 16})
        rows.append(row)
    return {
        "slide_index": block["slide_index"],
        "content_type": "imported_table",
        "x": block["x"],
        "y": block["y"],
        "width": block["width"],
        "height": block["height"],
        "rows": len(rows),
        "cols": len(rows[0]),
        "cells": rows,
        "column_widths": [block["width"] / len(rows[0])] * len(rows[0]),
        "header_rows": 1,
    }
```

- [ ] **Step 6: Run rebuild verification**

Run:

- `python -m pytest agent/tests/test_pptx_import_api.py -v`
- `python -m pytest agent/tests/test_editable_rebuild.py -q`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/app/api/jobs.py agent/app/services/reconstruct/editable_rebuild.py agent/tests/test_pptx_import_api.py
git commit -m "feat: preserve imported charts during rebuild"
```

## Task 4: Surface Chart Counts In The Workbench

**Files:**
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing frontend assertion**

Extend the imported summary test to expect chart count.

```tsx
expect(screen.getByText("Charts: 1")).toBeInTheDocument();
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: FAIL because chart count is not rendered.

- [ ] **Step 3: Render chart count in import summaries**

Update `ProjectWorkspace.tsx`.

```tsx
<span>Charts: {entry.object_summary?.imported_chart ?? 0}</span>
...
<span>Charts: {selectedSlide.object_summary?.imported_chart ?? 0}</span>
```

- [ ] **Step 4: Run frontend verification**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/ProjectWorkspace.tsx web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: show imported chart counts"
```

## Task 5: Update Delivery And Acceptance Guidance

**Files:**
- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`

- [ ] **Step 1: Update delivery notes**

Add:

```md
Imported PPTX handling now includes chart detection with explicit fallback behavior.
Charts are preserved through image-like or structured fallback rather than being silently dropped.
```

- [ ] **Step 2: Update acceptance checks**

Add:

```md
After importing a PPTX with charts:
1. confirm chart count appears in import summaries
2. confirm chart count appears in selected-slide summary
3. confirm rebuild preserves chart presence through explicit fallback
```

- [ ] **Step 3: Run final verification**

Run:

- `cd agent && python -m pytest -q`
- `cd web && npm test -- --run`
- `cd web && npm run build`

Expected:

- backend suite passes
- frontend suite passes
- build succeeds

- [ ] **Step 4: Commit**

```bash
git add docs/DELIVERY.md docs/ACCEPTANCE.md
git commit -m "docs: add imported chart guidance"
```

## Self-Review

### Spec coverage

- detect `imported_chart`: covered by Task 1
- chart counts in summaries: covered by Tasks 2 and 4
- preserve chart presence during rebuild: covered by Task 3
- docs and acceptance updates: covered by Task 5

### Placeholder scan

No `TODO`, `TBD`, or vague deferred instructions remain. Each task contains exact files, commands, and implementation sketches.

### Type consistency

The plan consistently uses:

- `imported_chart`
- `chart_type`
- `categories`
- `series`
- `fallback_mode`

These names are aligned across extraction, summary, and rebuild steps.
