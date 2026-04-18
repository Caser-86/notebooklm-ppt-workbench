# PPTX Import Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a complete local `.pptx` import workflow that records imported presentations at the project level, normalizes slide assets, and feeds the existing display-clone and editable-rebuild pipeline.

**Architecture:** Extend the existing FastAPI agent with a dedicated PPTX import service, new import persistence models, and project/import APIs. Keep import parsing isolated from reconstruction by converting uploaded `.pptx` files into normalized slide assets, then reuse the existing artifact and rebuild flow. Add a matching web workspace entry point and import history UI so PPTX import becomes a new input path inside the current workbench rather than a separate product flow.

**Tech Stack:** FastAPI, SQLModel, python-pptx, React, TypeScript, Vite, Vitest

---

## File Structure

### Backend

- Modify: `agent/app/models.py`
  - add `ImportedPresentation` and `ImportedSlideAsset`
- Modify: `agent/app/schemas.py`
  - add import read/write response models
- Create: `agent/app/services/pptx_import.py`
  - implement source classification, extraction, and normalized asset creation
- Modify: `agent/app/services/artifacts.py`
  - add import storage directories and import asset path helpers
- Modify: `agent/app/api/projects.py`
  - add project-level import history endpoints
- Modify: `agent/app/api/jobs.py`
  - add PPTX upload endpoint and rebuild-from-import endpoint
- Modify: `agent/app/main.py`
  - ensure new routes are exposed if router wiring changes

### Backend tests

- Create: `agent/tests/test_pptx_import_service.py`
  - unit tests for classification and import extraction
- Modify: `agent/tests/test_projects_api.py`
  - cover project import history
- Create: `agent/tests/test_pptx_import_api.py`
  - cover upload, detail, and rebuild endpoints
- Modify: `agent/tests/conftest.py`
  - add helpers/fixtures for temporary `.pptx` generation if needed

### Frontend

- Modify: `web/src/lib/types.ts`
  - add imported presentation and imported slide asset types
- Modify: `web/src/lib/api.ts`
  - add fetch/upload/rebuild functions for PPTX imports
- Modify: `web/src/lib/i18n.tsx`
  - add import-related bilingual strings
- Modify: `web/src/components/ProjectWorkspace.tsx`
  - add `Import PPTX` workspace section and imported revision list
- Modify: `web/src/components/ArtifactGallery.tsx`
  - optionally surface imported-presentation-driven rebuild context
- Modify: `web/src/styles.css`
  - add styles for the new import UI

### Frontend tests

- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`
  - cover PPTX upload, import status, and rebuild actions
- Optionally modify: `web/src/components/__tests__/ArtifactGallery.test.tsx`
  - cover any new artifact labels or import-driven output states

### Docs and samples

- Modify: `docs/DELIVERY.md`
  - describe PPTX import support and first-phase boundaries
- Modify: `docs/ACCEPTANCE.md`
  - add PPTX import acceptance path
- Create or update sample inputs under:
  - `samples/notebooklm_exports/`
  - `samples/generated_demo/`

## Task 1: Add Import Persistence Models And Schemas

**Files:**
- Modify: `agent/app/models.py`
- Modify: `agent/app/schemas.py`
- Test: `agent/tests/test_projects_api.py`

- [ ] **Step 1: Write the failing schema/model test**

Add a backend API test that expects project import records to exist and serialize with slide asset metadata.

```python
def test_project_import_history_returns_import_records(client):
    project = client.post("/projects", json={"title": "Import Demo", "preferred_language": "zh-CN"}).json()

    response = client.get(f"/projects/{project['id']}/imports")

    assert response.status_code == 200
    assert response.json() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest agent/tests/test_projects_api.py::test_project_import_history_returns_import_records -v`
Expected: FAIL with `404` or missing route/schema support.

- [ ] **Step 3: Add the new persistence models**

Update `agent/app/models.py` with the minimum import tables.

```python
class ImportedPresentation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    source_type: str = "generic_pptx"
    filename: str
    original_file_path: str
    status: str = "uploaded"
    page_count: int = 0
    error_message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ImportedSlideAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    import_id: int = Field(index=True)
    slide_index: int
    preview_image_path: str
    text_dump: str = ""
    structure_json_path: str = ""
```

- [ ] **Step 4: Add import schemas**

Update `agent/app/schemas.py` with import DTOs.

```python
class ImportedSlideAssetRead(BaseModel):
    id: int
    slide_index: int
    preview_image_path: str
    text_dump: str
    structure_json_path: str


class ImportedPresentationRead(BaseModel):
    id: int
    project_id: int
    source_type: str
    filename: str
    status: str
    page_count: int
    error_message: str
    slide_assets: list[ImportedSlideAssetRead] = []
```

- [ ] **Step 5: Run targeted tests**

Run: `python -m pytest agent/tests/test_projects_api.py::test_project_import_history_returns_import_records -v`
Expected: still FAIL, but no model import or schema definition errors.

- [ ] **Step 6: Commit**

```bash
git add agent/app/models.py agent/app/schemas.py agent/tests/test_projects_api.py
git commit -m "feat: add pptx import persistence models"
```

## Task 2: Implement The PPTX Import Service

**Files:**
- Create: `agent/app/services/pptx_import.py`
- Modify: `agent/app/services/artifacts.py`
- Modify: `agent/tests/conftest.py`
- Create: `agent/tests/test_pptx_import_service.py`

- [ ] **Step 1: Write the failing service tests**

Create tests for source classification and slide asset extraction.

```python
def test_classify_internal_generated_pptx(tmp_path):
    pptx_path = build_fixture_pptx(tmp_path, title="Editable rebuild")
    result = classify_pptx_source(pptx_path)
    assert result == "internal_generated"


def test_extract_import_assets_creates_slide_entries(tmp_path):
    pptx_path = build_fixture_pptx(tmp_path, title="NotebookLM export")
    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path)
    assert bundle.page_count == 1
    assert bundle.slides[0].slide_index == 1
```

- [ ] **Step 2: Run the service tests to verify failure**

Run: `python -m pytest agent/tests/test_pptx_import_service.py -v`
Expected: FAIL because the service and fixtures do not exist yet.

- [ ] **Step 3: Add artifact path helpers**

Extend `agent/app/services/artifacts.py` with import-specific directories.

```python
def ensure_import_dir(project_id: int, import_id: int) -> Path:
    path = ensure_project_artifact_dir(project_id) / "imports" / f"import-{import_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def import_asset_href(project_id: int, import_id: int, filename: str) -> str:
    return f"/artifacts/{project_id}/imports/import-{import_id}/{filename}"
```

- [ ] **Step 4: Implement the import service**

Create `agent/app/services/pptx_import.py` with explicit helpers for classification and extraction.

```python
from dataclasses import dataclass
from pathlib import Path
from pptx import Presentation


@dataclass
class ImportedSlideBundle:
    slide_index: int
    preview_image_path: str
    text_dump: str
    structure_json_path: str


@dataclass
class ImportedPresentationBundle:
    source_type: str
    page_count: int
    slides: list[ImportedSlideBundle]


def classify_pptx_source(pptx_path: Path) -> str:
    presentation = Presentation(pptx_path)
    texts = " ".join(
        shape.text for slide in presentation.slides for shape in slide.shapes if hasattr(shape, "text") and shape.text
    ).lower()
    if "editable rebuild" in texts or "display clone" in texts:
        return "internal_generated"
    if "notebooklm" in texts:
        return "notebooklm_export"
    return "generic_pptx"
```

- [ ] **Step 5: Use a minimal extraction strategy**

Inside the same service, extract slide text and emit normalized slide records even when preview generation is basic.

```python
def extract_pptx_assets(project_id: int, pptx_path: Path, import_dir: Path) -> ImportedPresentationBundle:
    presentation = Presentation(pptx_path)
    source_type = classify_pptx_source(pptx_path)
    slides: list[ImportedSlideBundle] = []

    for index, slide in enumerate(presentation.slides, start=1):
        text_dump = "\n".join(
            shape.text.strip()
            for shape in slide.shapes
            if hasattr(shape, "text") and shape.text and shape.text.strip()
        )
        preview_path = import_dir / f"slide-{index}.png"
        preview_path.write_bytes(b"placeholder-preview")
        slides.append(
            ImportedSlideBundle(
                slide_index=index,
                preview_image_path=str(preview_path),
                text_dump=text_dump,
                structure_json_path="",
            )
        )

    return ImportedPresentationBundle(source_type=source_type, page_count=len(slides), slides=slides)
```

- [ ] **Step 6: Run service tests**

Run: `python -m pytest agent/tests/test_pptx_import_service.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/app/services/artifacts.py agent/app/services/pptx_import.py agent/tests/conftest.py agent/tests/test_pptx_import_service.py
git commit -m "feat: add pptx import service"
```

## Task 3: Expose Import APIs And Wire Rebuild

**Files:**
- Modify: `agent/app/api/projects.py`
- Modify: `agent/app/api/jobs.py`
- Modify: `agent/app/schemas.py`
- Create: `agent/tests/test_pptx_import_api.py`

- [ ] **Step 1: Write the failing API tests**

Add API tests for upload, detail, and rebuild.

```python
def test_upload_pptx_creates_import_record(client, pptx_file):
    project = client.post("/projects", json={"title": "PPTX Import", "preferred_language": "zh-CN"}).json()
    with open(pptx_file, "rb") as handle:
        response = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("demo.pptx", handle, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        )

    assert response.status_code == 201
    assert response.json()["status"] in {"analyzing", "ready"}
```

- [ ] **Step 2: Run API tests to verify failure**

Run: `python -m pytest agent/tests/test_pptx_import_api.py -v`
Expected: FAIL with missing endpoints.

- [ ] **Step 3: Add project import listing and detail serialization**

Update `agent/app/api/projects.py` to list imports.

```python
@router.get("/projects/{project_id}/imports", response_model=list[ImportedPresentationRead])
def list_project_imports(project_id: int, session: Session = Depends(get_session)) -> list[ImportedPresentationRead]:
    imports = list(
        session.exec(
            select(ImportedPresentation)
            .where(ImportedPresentation.project_id == project_id)
            .order_by(ImportedPresentation.created_at.desc())
        )
    )
    return [serialize_import_record(record, session) for record in imports]
```

- [ ] **Step 4: Add upload and rebuild endpoints**

Update `agent/app/api/jobs.py` with upload and rebuild-from-import handlers.

```python
@router.post("/projects/{project_id}/imports/pptx", response_model=ImportedPresentationRead, status_code=status.HTTP_201_CREATED)
async def upload_pptx_import(project_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    record = ImportedPresentation(project_id=project_id, filename=file.filename or "upload.pptx", original_file_path="", status="uploaded")
    session.add(record)
    session.commit()
    session.refresh(record)
    import_dir = ensure_import_dir(project_id, record.id or 0)
    pptx_path = import_dir / record.filename
    pptx_path.write_bytes(await file.read())
    bundle = extract_pptx_assets(project_id, pptx_path, import_dir)
    record.original_file_path = str(pptx_path)
    record.source_type = bundle.source_type
    record.page_count = bundle.page_count
    record.status = "ready"
```

- [ ] **Step 5: Reuse the existing rebuild pipeline**

In the rebuild endpoint, map imported slide assets into the existing artifact flow.

```python
@router.post("/imports/{import_id}/rebuild")
def rebuild_from_import(import_id: int, session: Session = Depends(get_session)):
    imported = session.get(ImportedPresentation, import_id)
    assert imported is not None
    slide_assets = list(session.exec(select(ImportedSlideAsset).where(ImportedSlideAsset.import_id == import_id).order_by(ImportedSlideAsset.slide_index)))
    slide_paths = [Path(asset.preview_image_path) for asset in slide_assets]
    # then reuse the current versioned rebuild flow
```

- [ ] **Step 6: Run API tests**

Run: `python -m pytest agent/tests/test_pptx_import_api.py agent/tests/test_projects_api.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add agent/app/api/projects.py agent/app/api/jobs.py agent/app/schemas.py agent/tests/test_pptx_import_api.py agent/tests/test_projects_api.py
git commit -m "feat: add pptx import api"
```

## Task 4: Add Frontend PPTX Import UI

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/lib/i18n.tsx`
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/styles.css`
- Test: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing frontend test**

Add a workspace test that expects an import section, upload action, and import history.

```tsx
it("uploads a pptx import and lists imported revisions", async () => {
  render(<App />);
  expect(await screen.findByText("导入 PPTX")).toBeInTheDocument();
  expect(screen.getByText("已导入的 PPTX 版本")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the frontend test to verify failure**

Run: `npm test -- --run ProjectWorkspace.test.tsx`
Expected: FAIL because the new UI is missing.

- [ ] **Step 3: Add API and type support**

Extend `web/src/lib/types.ts` and `web/src/lib/api.ts`.

```ts
export type ImportedPresentation = {
  id: number;
  project_id: number;
  source_type: string;
  filename: string;
  status: string;
  page_count: number;
  error_message: string;
  slide_assets: ImportedSlideAsset[];
};

export async function uploadProjectPptx(projectId: number, file: File): Promise<ImportedPresentation> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/projects/${projectId}/imports/pptx`, { method: "POST", body: formData });
  return response.json();
}
```

- [ ] **Step 4: Add localized copy**

Add bilingual copy in `web/src/lib/i18n.tsx`.

```ts
importPptxTitle: "导入 PPTX",
importPptxDescription: "上传本地 PowerPoint 文件，并接入当前重建流程。",
importedPptxRevisions: "已导入的 PPTX 版本",
rebuildFromImport: "从导入版本重建",
```

- [ ] **Step 5: Render the import UI**

Update `web/src/components/ProjectWorkspace.tsx`.

```tsx
<section className="workspace-panel">
  <h3>{t("importPptxTitle")}</h3>
  <p>{t("importPptxDescription")}</p>
  <input type="file" accept=".pptx" onChange={handlePptxSelection} />
  <button onClick={handleUploadPptx} disabled={!selectedPptx || !activeProjectId}>
    {t("importPptxAction")}
  </button>
</section>
```

- [ ] **Step 6: Show imported revision history**

Still in `ProjectWorkspace.tsx`, render import records under the history area.

```tsx
<section className="workspace-panel">
  <h3>{t("importedPptxRevisions")}</h3>
  {importedPresentations.map((entry) => (
    <article key={entry.id}>
      <strong>{entry.filename}</strong>
      <span>{entry.source_type}</span>
      <span>{entry.status}</span>
      <button onClick={() => handleRebuildImport(entry.id)}>{t("rebuildFromImport")}</button>
    </article>
  ))}
</section>
```

- [ ] **Step 7: Run frontend verification**

Run:

- `npm test -- --run ProjectWorkspace.test.tsx`
- `npm run build`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add web/src/lib/types.ts web/src/lib/api.ts web/src/lib/i18n.tsx web/src/components/ProjectWorkspace.tsx web/src/styles.css web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: add pptx import workspace ui"
```

## Task 5: Complete End-To-End Import And Rebuild Verification

**Files:**
- Modify: `agent/tests/test_pptx_import_api.py`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`
- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`

- [ ] **Step 1: Add the failing end-to-end API contract test**

Add a test that uploads a `.pptx`, lists it, and rebuilds from it.

```python
def test_imported_pptx_can_be_rebuilt_into_artifacts(client, pptx_file):
    project = client.post("/projects", json={"title": "Import Flow", "preferred_language": "zh-CN"}).json()
    with open(pptx_file, "rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("flow.pptx", handle, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        ).json()

    response = client.post(f"/imports/{imported['id']}/rebuild")
    assert response.status_code == 200
    assert {artifact["id"] for artifact in response.json()["artifacts"]} == {"display-clone", "editable-rebuild"}
```

- [ ] **Step 2: Run the targeted backend tests**

Run: `python -m pytest agent/tests/test_pptx_import_api.py -v`
Expected: FAIL until rebuild wiring and artifact versioning are fully connected.

- [ ] **Step 3: Implement the missing glue**

Finish any API/service gaps so imported PPTX rebuilds create versioned artifacts using the same output contract as manual-export rebuilds.

```python
display_path = artifact_dir / "display-clone.pptx"
editable_path = artifact_dir / "editable-rebuild.pptx"
build_display_clone(slide_paths, display_path)
build_editable_rebuild(ocr_like_blocks, editable_path)
```

- [ ] **Step 4: Update docs**

Add the new import path to both docs files.

```md
### Local PPTX import

The workbench can now import local `.pptx` files, classify their source type, and run the same display clone plus editable rebuild pipeline used by manual NotebookLM export uploads.
```

- [ ] **Step 5: Run full verification**

Run:

- `cd agent && python -m pytest -q`
- `cd web && npm test -- --run`
- `cd web && npm run build`

Expected:

- backend suite passes
- frontend suite passes
- production build succeeds

- [ ] **Step 6: Commit**

```bash
git add agent/tests/test_pptx_import_api.py web/src/components/__tests__/ProjectWorkspace.test.tsx docs/DELIVERY.md docs/ACCEPTANCE.md
git commit -m "feat: verify pptx import rebuild flow"
```

## Task 6: Add Sample Coverage For Supported Import Tiers

**Files:**
- Modify: `samples/notebooklm_exports/README.md`
- Modify: `samples/generated_demo/`
- Optionally create: `samples/pptx_import/README.md`

- [ ] **Step 1: Add sample inventory notes**

Document three sample categories:

```md
- internal-generated.pptx
- notebooklm-related-export.pptx
- generic-local-demo.pptx
```

- [ ] **Step 2: Store or reference fixture files**

Place representative `.pptx` files into the sample area or describe how to regenerate them from existing outputs.

- [ ] **Step 3: Update acceptance guidance**

Extend acceptance notes so testers know how to validate each tier:

```md
1. Upload the internal generated PPTX and confirm import status becomes `ready`.
2. Rebuild from the import and verify both artifact links appear.
3. Repeat with the NotebookLM-related PPTX and one generic PPTX.
```

- [ ] **Step 4: Perform a quick manual smoke check**

Run the app locally, upload one sample PPTX, and confirm:

- import record appears
- rebuild button works
- output artifacts download

- [ ] **Step 5: Commit**

```bash
git add samples/notebooklm_exports/README.md samples/generated_demo docs/ACCEPTANCE.md
git commit -m "docs: add pptx import sample coverage"
```

## Self-Review

### Spec coverage

- upload local `.pptx`: covered by Tasks 3 and 4
- persist import records: covered by Tasks 1 and 3
- normalized asset bundle: covered by Task 2
- rebuild from import: covered by Tasks 3 and 5
- project-level import history: covered by Tasks 1, 3, and 4
- support internal generated and NotebookLM-related PPTX first: covered by Tasks 2 and 6
- best-effort generic `.pptx`: covered by Tasks 2 and 6

### Placeholder scan

No `TODO`, `TBD`, or deferred implementation markers remain in task steps. Each task includes exact files, commands, and minimum code sketches.

### Type consistency

The plan consistently uses:

- `ImportedPresentation`
- `ImportedSlideAsset`
- `ImportedPresentationRead`
- `slide_assets`
- `source_type`

These names match across model, schema, API, and frontend task sections.
