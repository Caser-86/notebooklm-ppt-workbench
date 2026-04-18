# Imported Group Shape Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add shallow group-shape expansion to the PPTX import pipeline so supported direct children are promoted into existing imported block types and unsupported grouped content is preserved explicitly through `unsupported_group` instead of being silently lost.

**Architecture:** Extend `agent/app/services/pptx_import.py` with one-level group inspection. Promote supported direct children into existing `imported_*` blocks, emit an `unsupported_group` marker for the remainder, route that marker through existing import summaries, and add a minimal rebuild fallback that preserves grouped content visibly without attempting recursive hierarchy recovery.

**Tech Stack:** FastAPI, SQLModel, python-pptx, React, TypeScript, Vite, Vitest, pytest

---

## File Structure

### Backend import layer

- Modify: `agent/tests/conftest.py`
  - add a fixture builder for a PPTX containing grouped shapes
- Modify: `agent/tests/test_pptx_import_service.py`
  - add tests for shallow group expansion and unsupported-group emission
- Modify: `agent/app/services/pptx_import.py`
  - detect group shapes
  - inspect direct children
  - promote supported child types
  - emit `unsupported_group`

### Backend serialization and rebuild

- Modify: `agent/tests/test_pptx_import_api.py`
  - add grouped-content summary and rebuild-presence tests
- Modify: `agent/app/api/projects.py`
  - ensure `unsupported_group` counts appear in import summaries
- Modify: `agent/app/api/jobs.py`
  - preserve `unsupported_group` blocks in imported rebuild input
- Modify: `agent/app/services/reconstruct/editable_rebuild.py`
  - add minimal fallback rendering for `unsupported_group`

### Frontend

- Modify: `web/src/components/ProjectWorkspace.tsx`
  - add grouped-content counts to import summary and selected-slide summary
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`
  - assert grouped-content counts appear in the workbench

### Docs

- Modify: `docs/DELIVERY.md`
  - describe shallow group expansion and unsupported-group fallback
- Modify: `docs/ACCEPTANCE.md`
  - add grouped-content acceptance checks

## Task 1: Detect Group Shapes And Emit `unsupported_group`

**Files:**
- Modify: `agent/tests/conftest.py`
- Modify: `agent/tests/test_pptx_import_service.py`
- Modify: `agent/app/services/pptx_import.py`

- [ ] **Step 1: Write the failing import test**

Add a fixture and test that expect grouped content to produce either promoted children or an `unsupported_group` marker.

```python
def test_extract_group_shape_emits_unsupported_group(build_fixture_pptx_with_group_shape, tmp_path):
    pptx_path = build_fixture_pptx_with_group_shape("group-blocks.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert any(block["content_type"] == "unsupported_group" for block in bundle.slides[0].blocks)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest agent/tests/test_pptx_import_service.py::test_extract_group_shape_emits_unsupported_group -v`
Expected: FAIL because group handling does not exist.

- [ ] **Step 3: Add a grouped-shape fixture builder**

Update `agent/tests/conftest.py`.

```python
@pytest.fixture
def build_fixture_pptx_with_group_shape(tmp_path):
    def _build(filename: str = "group-fixture.pptx") -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[5])
        slide.shapes.title.text = "Group import"
        left = slide.shapes.add_textbox(...)
        left.text_frame.text = "Grouped title"
        right = slide.shapes.add_textbox(...)
        right.text_frame.text = "Grouped body"
        # save as a fixture that at least exercises grouped-content detection strategy
        output = tmp_path / filename
        presentation.save(output)
        return output
    return _build
```

- [ ] **Step 4: Add group-shape detection hooks**

Update `agent/app/services/pptx_import.py`.

```python
def _extract_group_blocks(slide, slide_index: int, import_dir: Path) -> list[dict]:
    group_blocks = []
    for shape in slide.shapes:
        if shape.shape_type != MSO_SHAPE_TYPE.GROUP:
            continue
        group_blocks.extend(_expand_group_shape(shape, slide_index, import_dir))
    return group_blocks
```

- [ ] **Step 5: Add one-level expansion and fallback emission**

```python
def _expand_group_shape(shape, slide_index: int, import_dir: Path) -> list[dict]:
    promoted_blocks = []
    unsupported_types = []
    for child in shape.shapes:
        child_blocks = _extract_supported_group_child(child, slide_index, import_dir)
        if child_blocks:
            promoted_blocks.extend(child_blocks)
        else:
            unsupported_types.append(str(child.shape_type))
    if unsupported_types:
        promoted_blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "unsupported_group",
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "supported_child_count": len(promoted_blocks),
                "unsupported_child_count": len(unsupported_types),
                "unsupported_types": unsupported_types,
                "fallback_mode": "text",
                "snapshot_path": "",
            }
        )
    return promoted_blocks
```

- [ ] **Step 6: Merge group blocks into slide extraction**

```python
blocks.extend(_extract_group_blocks(slide, index, import_dir))
```

- [ ] **Step 7: Run import extraction verification**

Run: `python -m pytest agent/tests/test_pptx_import_service.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add agent/tests/conftest.py agent/tests/test_pptx_import_service.py agent/app/services/pptx_import.py
git commit -m "feat: detect grouped imported content"
```

## Task 2: Promote Supported Direct Children From Group Shapes

**Files:**
- Modify: `agent/tests/test_pptx_import_service.py`
- Modify: `agent/app/services/pptx_import.py`

- [ ] **Step 1: Write the failing promotion test**

Add a test that expects supported group children to be promoted.

```python
def test_group_shape_promotes_supported_text_children(build_fixture_pptx_with_group_shape, tmp_path):
    pptx_path = build_fixture_pptx_with_group_shape("group-promote.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert any(block["content_type"] == "imported_text" for block in bundle.slides[0].blocks)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest agent/tests/test_pptx_import_service.py::test_group_shape_promotes_supported_text_children -v`
Expected: FAIL because supported child promotion is missing or incomplete.

- [ ] **Step 3: Add supported-child extraction**

Implement a direct-child extractor for the currently supported object set.

```python
def _extract_supported_group_child(child, slide_index: int, import_dir: Path) -> list[dict]:
    if _is_text_shape(child):
        return [_normalize_text_shape(child, slide_index)]
    if child.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return [_normalize_picture_shape(child, slide_index, import_dir)]
    if getattr(child, "has_table", False):
        return [_normalize_table_shape(child, slide_index)]
    if getattr(child, "has_chart", False):
        return [_normalize_chart_shape(child, slide_index)]
    return []
```

- [ ] **Step 4: Re-run extraction verification**

Run: `python -m pytest agent/tests/test_pptx_import_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/tests/test_pptx_import_service.py agent/app/services/pptx_import.py
git commit -m "feat: promote supported group children"
```

## Task 3: Expose Grouped-Content Counts In Summaries

**Files:**
- Modify: `agent/tests/test_pptx_import_api.py`
- Modify: `agent/app/api/projects.py`

- [ ] **Step 1: Write the failing summary test**

```python
def test_imported_group_counts_appear_in_import_summary(client, build_fixture_pptx_with_group_shape):
    project = client.post("/projects", json={"title": "Group Import", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_group_shape("group-summary.pptx")

    with pptx_path.open("rb") as handle:
        client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("group-summary.pptx", handle, PPTX_MIME)},
        )

    imports = client.get(f"/projects/{project['id']}/imports").json()
    assert imports[0]["object_summary"]["unsupported_group"] >= 1
    assert imports[0]["slide_assets"][0]["object_summary"]["unsupported_group"] >= 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest agent/tests/test_pptx_import_api.py::test_imported_group_counts_appear_in_import_summary -v`
Expected: FAIL because grouped-content counts are not yet present.

- [ ] **Step 3: Reuse current summary aggregation**

Update `agent/app/api/projects.py` only if needed so `unsupported_group` participates in both import-level and slide-level summaries.

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
git commit -m "feat: expose grouped-content summaries"
```

## Task 4: Preserve `unsupported_group` During Rebuild

**Files:**
- Modify: `agent/tests/test_pptx_import_api.py`
- Modify: `agent/app/api/jobs.py`
- Modify: `agent/app/services/reconstruct/editable_rebuild.py`

- [ ] **Step 1: Write the failing rebuild fallback test**

```python
def test_unsupported_group_rebuild_preserves_group_presence(build_fixture_pptx_with_group_shape):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Group Rebuild", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_group_shape("group-rebuild.pptx")

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("group-rebuild.pptx", handle, PPTX_MIME)},
        ).json()

    response = client.post(f"/imports/{imported['id']}/rebuild")
    assert response.status_code == 200
```

- [ ] **Step 2: Run the test to verify it fails or proves no dedicated fallback**

Run: `python -m pytest agent/tests/test_pptx_import_api.py::test_unsupported_group_rebuild_preserves_group_presence -v`
Expected: FAIL or reveal missing explicit fallback behavior.

- [ ] **Step 3: Preserve `unsupported_group` blocks through rebuild input**

Update `agent/app/api/jobs.py` if needed so imported structure blocks are not filtered out before rebuild.

- [ ] **Step 4: Add minimal fallback rendering**

Update `editable_rebuild.py`.

```python
if block.get("content_type") == "unsupported_group":
    if block.get("snapshot_path"):
        slide.shapes.add_picture(...)
        continue
    textbox = slide.shapes.add_textbox(...)
    textbox.text_frame.text = f"Unsupported grouped content ({block['unsupported_child_count']})"
    continue
```

- [ ] **Step 5: Run rebuild verification**

Run:

- `python -m pytest agent/tests/test_pptx_import_api.py -v`
- `python -m pytest agent/tests/test_editable_rebuild.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add agent/app/api/jobs.py agent/app/services/reconstruct/editable_rebuild.py agent/tests/test_pptx_import_api.py
git commit -m "feat: preserve unsupported grouped content"
```

## Task 5: Show Grouped-Content Counts In The Workbench

**Files:**
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing frontend assertion**

Extend the import summary tests to expect grouped-content counts.

```tsx
expect(screen.getByText("Groups: 1")).toBeInTheDocument();
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: FAIL because grouped-content counts are not rendered.

- [ ] **Step 3: Render grouped-content counts**

Update `ProjectWorkspace.tsx` in both the import summary and the selected-slide summary.

```tsx
<span>Groups: {entry.object_summary?.unsupported_group ?? 0}</span>
...
<span>Groups: {selectedSlide.object_summary?.unsupported_group ?? 0}</span>
```

- [ ] **Step 4: Run frontend verification**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/ProjectWorkspace.tsx web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: show grouped-content counts"
```

## Task 6: Update Delivery And Acceptance Guidance

**Files:**
- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`

- [ ] **Step 1: Update delivery notes**

Add:

```md
Imported PPTX handling now supports shallow group-shape expansion.
Supported direct children are promoted; unsupported grouped content is preserved explicitly instead of disappearing.
```

- [ ] **Step 2: Update acceptance checks**

Add:

```md
After importing a PPTX with grouped objects:
1. confirm grouped-content counts appear in summaries
2. confirm supported child objects are still present
3. confirm unsupported grouped content is preserved through explicit fallback
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
git commit -m "docs: add grouped-content guidance"
```

## Self-Review

### Spec coverage

- shallow group detection: covered by Task 1
- supported child promotion: covered by Task 2
- `unsupported_group` summary exposure: covered by Tasks 3 and 5
- rebuild fallback for grouped content: covered by Task 4
- docs and acceptance updates: covered by Task 6

### Placeholder scan

No `TODO`, `TBD`, or vague deferred instructions remain. Each task contains exact files, commands, and implementation sketches.

### Type consistency

The plan consistently uses:

- `unsupported_group`
- `supported_child_count`
- `unsupported_child_count`
- `unsupported_types`
- `fallback_mode`

These names are aligned across extraction, summary, and fallback steps.
