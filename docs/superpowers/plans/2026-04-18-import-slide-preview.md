# Imported Slide Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an editor-like imported-slide review surface with a left filmstrip and a right selected-slide preview plus per-slide object summary for imported PPTX revisions.

**Architecture:** Enrich `ImportedSlideAsset` payloads with per-slide `object_summary`, then extend the current imported revision section in `ProjectWorkspace.tsx` into a two-pane review surface. Reuse the existing `preview_image_path` and import list endpoint instead of adding new APIs or a new page.

**Tech Stack:** FastAPI, SQLModel, React, TypeScript, Vite, Vitest, pytest

---

## File Structure

### Backend

- Modify: `agent/app/models.py`
  - expand `ImportedSlideAsset` if per-slide summary needs persistence
- Modify: `agent/app/schemas.py`
  - add `object_summary` to `ImportedSlideAssetRead`
- Modify: `agent/app/api/projects.py`
  - compute and serialize per-slide object summaries

### Frontend

- Modify: `web/src/lib/types.ts`
  - add per-slide `object_summary`
- Modify: `web/src/lib/api.ts`
  - adapt imported slide payload mapping if needed
- Modify: `web/src/lib/i18n.tsx`
  - add labels for filmstrip and selected-slide summary
- Modify: `web/src/components/ProjectWorkspace.tsx`
  - render filmstrip, selected slide state, and preview pane
- Modify: `web/src/styles.css`
  - add layout styles for the new two-pane imported-slide review surface

### Tests

- Modify: `agent/tests/test_projects_api.py`
  - verify per-slide object summaries are exposed
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`
  - verify filmstrip selection and selected-slide detail rendering

### Docs

- Modify: `docs/DELIVERY.md`
  - describe the imported-slide review surface
- Modify: `docs/ACCEPTANCE.md`
  - add checks for filmstrip, default selection, and selected-slide summary

## Task 1: Add Per-Slide Object Summary To Imported Slide Assets

**Files:**
- Modify: `agent/app/schemas.py`
- Modify: `agent/app/api/projects.py`
- Modify: `agent/tests/test_projects_api.py`

- [ ] **Step 1: Write the failing backend test**

Add a test showing imported slide assets return `object_summary`.

```python
def test_project_import_history_returns_slide_object_summary(client, build_fixture_pptx):
    project = client.post("/projects", json={"title": "Preview Demo", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("preview-demo.pptx", ["Editable rebuild"])

    with pptx_path.open("rb") as handle:
        client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("preview-demo.pptx", handle, PPTX_MIME)},
        )

    history = client.get(f"/projects/{project['id']}/imports").json()
    assert "object_summary" in history[0]["slide_assets"][0]
```

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m pytest agent/tests/test_projects_api.py::test_project_import_history_returns_slide_object_summary -v`
Expected: FAIL because `ImportedSlideAssetRead` does not yet include `object_summary`.

- [ ] **Step 3: Add schema support**

Update `agent/app/schemas.py`.

```python
class ImportedSlideAssetRead(BaseModel):
    id: int
    slide_index: int
    preview_image_path: str
    text_dump: str
    structure_json_path: str
    object_summary: dict[str, int] = {}
```

- [ ] **Step 4: Serialize per-slide summaries**

Update `serialize_import_record` in `agent/app/api/projects.py` so each slide asset carries its own summary.

```python
def _build_slide_object_summary(asset: ImportedSlideAsset) -> dict[str, int]:
    if not asset.structure_json_path:
        return {}
    structure_path = Path(asset.structure_json_path)
    if not structure_path.exists():
        return {}
    summary: dict[str, int] = {}
    for block in json.loads(structure_path.read_text(encoding="utf-8")):
        content_type = block.get("content_type")
        if content_type:
            summary[content_type] = summary.get(content_type, 0) + 1
    return summary
```

- [ ] **Step 5: Pass per-slide summaries into the response**

```python
slide_assets=[
    ImportedSlideAssetRead(
        id=asset.id or 0,
        slide_index=asset.slide_index,
        preview_image_path=...,
        text_dump=asset.text_dump,
        structure_json_path=asset.structure_json_path,
        object_summary=_build_slide_object_summary(asset),
    )
    for asset in slide_assets
]
```

- [ ] **Step 6: Run backend verification**

Run: `python -m pytest agent/tests/test_projects_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/app/schemas.py agent/app/api/projects.py agent/tests/test_projects_api.py
git commit -m "feat: expose per-slide import object summaries"
```

## Task 2: Add Filmstrip Selection State To The Workspace

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing frontend test**

Add a test for default slide selection and selection changes.

```tsx
it("defaults to the first imported slide and updates when another slide is selected", async () => {
  render(<ProjectWorkspace projectId={7} />);
  expect(await screen.findByText("第 1 页")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "第 2 页" }));
  expect(screen.getByText("当前预览：第 2 页")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: FAIL because there is no selected-slide state or filmstrip UI.

- [ ] **Step 3: Extend the frontend type**

Update `web/src/lib/types.ts`.

```ts
export type ImportedSlideAsset = {
  id: number;
  slide_index: number;
  preview_image_path: string;
  text_dump: string;
  structure_json_path: string;
  object_summary: Record<string, number>;
};
```

- [ ] **Step 4: Add selected-slide state**

In `ProjectWorkspace.tsx`, add state for the selected import id and selected slide index.

```tsx
const [selectedImportId, setSelectedImportId] = useState<number | null>(null);
const [selectedImportedSlideIndex, setSelectedImportedSlideIndex] = useState<number | null>(null);
```

- [ ] **Step 5: Default to the first slide**

When imports load, select the first import and its first slide.

```tsx
setImports(importedPresentations);
setSelectedImportId(importedPresentations[0]?.id ?? null);
setSelectedImportedSlideIndex(importedPresentations[0]?.slide_assets[0]?.slide_index ?? null);
```

- [ ] **Step 6: Run targeted frontend verification**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: still FAIL, but now due to missing rendered preview surface rather than missing state.

- [ ] **Step 7: Commit**

```bash
git add web/src/lib/types.ts web/src/components/ProjectWorkspace.tsx web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: add imported slide selection state"
```

## Task 3: Render The Left Filmstrip And Right Preview Pane

**Files:**
- Modify: `web/src/lib/i18n.tsx`
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/styles.css`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing UI assertions**

Extend the existing import test to expect:

- a filmstrip list
- a selected-slide preview image
- a selected-slide heading

```tsx
expect(await screen.findByText("已导入页面")).toBeInTheDocument();
expect(screen.getByText("当前预览：第 1 页")).toBeInTheDocument();
expect(screen.getByRole("img", { name: "第 1 页预览" })).toBeInTheDocument();
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: FAIL because the filmstrip and preview pane are not rendered yet.

- [ ] **Step 3: Add localized labels**

Update `web/src/lib/i18n.tsx` with minimum keys.

```ts
importedSlidesTitle: "已导入页面",
selectedImportedSlide: (index: number) => `当前预览：第 ${index} 页`,
importedSlideLabel: (index: number) => `第 ${index} 页`,
importedSlidePreviewAlt: (index: number) => `第 ${index} 页预览`,
```

- [ ] **Step 4: Render the filmstrip**

Update `ProjectWorkspace.tsx` to render imported slides as a selectable filmstrip.

```tsx
<aside className="import-filmstrip">
  <h5>{messages.workspace.importedSlidesTitle}</h5>
  {activeImport?.slide_assets.map((slide) => (
    <button
      key={slide.id}
      type="button"
      className={slide.slide_index === selectedImportedSlideIndex ? "filmstrip-slide is-active" : "filmstrip-slide"}
      onClick={() => setSelectedImportedSlideIndex(slide.slide_index)}
    >
      <img src={slide.preview_image_path} alt={messages.workspace.importedSlidePreviewAlt(slide.slide_index)} />
      <span>{messages.workspace.importedSlideLabel(slide.slide_index)}</span>
    </button>
  ))}
</aside>
```

- [ ] **Step 5: Render the selected-slide preview pane**

Still in `ProjectWorkspace.tsx`, render the selected slide on the right.

```tsx
<section className="import-preview-detail">
  <h5>{messages.workspace.selectedImportedSlide(selectedSlide.slide_index)}</h5>
  <img src={selectedSlide.preview_image_path} alt={messages.workspace.importedSlidePreviewAlt(selectedSlide.slide_index)} />
</section>
```

- [ ] **Step 6: Add layout styles**

Update `web/src/styles.css`.

```css
.import-review-shell {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 1rem;
}

.import-filmstrip {
  display: grid;
  gap: 0.75rem;
  max-height: 28rem;
  overflow-y: auto;
}

.filmstrip-slide.is-active {
  border-color: rgba(23, 32, 51, 0.35);
  background: rgba(255, 255, 255, 0.92);
}
```

- [ ] **Step 7: Run frontend verification**

Run:

- `npm test -- --run ProjectWorkspace.test.tsx`
- `npm run build`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add web/src/lib/i18n.tsx web/src/components/ProjectWorkspace.tsx web/src/styles.css web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: add imported slide filmstrip preview"
```

## Task 4: Show Per-Slide Object Summary In The Detail Pane

**Files:**
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing summary test**

Add assertions for selected-slide object summary.

```tsx
expect(screen.getByText("Text: 2")).toBeInTheDocument();
expect(screen.getByText("Images: 1")).toBeInTheDocument();
expect(screen.getByText("Tables: 0")).toBeInTheDocument();
expect(screen.getByText("Cards: 0")).toBeInTheDocument();
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: FAIL because the selected-slide summary is not shown in the preview pane.

- [ ] **Step 3: Render selected-slide object summary**

Update `ProjectWorkspace.tsx`.

```tsx
<div className="import-slide-summary">
  <span>Text: {selectedSlide.object_summary?.imported_text ?? 0}</span>
  <span>Images: {selectedSlide.object_summary?.imported_image ?? 0}</span>
  <span>Tables: {selectedSlide.object_summary?.imported_table ?? 0}</span>
  <span>Cards: {selectedSlide.object_summary?.imported_icon_card ?? 0}</span>
</div>
```

- [ ] **Step 4: Run frontend verification**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/ProjectWorkspace.tsx web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: show selected imported slide summary"
```

## Task 5: Update Docs And Acceptance Guidance

**Files:**
- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`

- [ ] **Step 1: Update delivery notes**

Add a short section describing the imported-slide review surface.

```md
Imported PPTX revisions now include:
- a left-side slide filmstrip
- a selected-slide preview
- a per-slide object summary
```

- [ ] **Step 2: Update acceptance checks**

Add validation steps:

```md
After importing a local PPTX:
1. confirm the first slide is selected automatically
2. confirm the filmstrip can switch slides
3. confirm the selected slide shows preview and object summary
```

- [ ] **Step 3: Run final verification**

Run:

- `cd agent && python -m pytest -q`
- `cd web && npm test -- --run`
- `cd web && npm run build`

Expected:

- backend suite passes
- frontend suite passes
- production build succeeds

- [ ] **Step 4: Commit**

```bash
git add docs/DELIVERY.md docs/ACCEPTANCE.md
git commit -m "docs: add imported slide preview guidance"
```

## Self-Review

### Spec coverage

- left filmstrip: covered by Tasks 2-3
- right selected-slide preview: covered by Task 3
- per-slide object summary: covered by Tasks 1 and 4
- first-slide default selection: covered by Task 2
- no new endpoints: preserved by Task 1
- docs and acceptance updates: covered by Task 5

### Placeholder scan

No `TODO`, `TBD`, or vague deferred instructions remain. Each task includes exact files, commands, and code sketches.

### Type consistency

The plan consistently uses:

- `ImportedSlideAssetRead.object_summary`
- `ImportedSlideAsset.object_summary`
- `selectedImportedSlideIndex`
- `selectedImportId`

These names are aligned across backend payloads and frontend selection state.
