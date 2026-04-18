# Local Job Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a SQLite-backed local job queue so long-running operations enqueue immediately, run in a separate local worker process, and expose persistent job state back to the frontend.

**Architecture:** Extend the existing `Job` model into a persistent queue record, add worker-side claim/execute/update flow, convert synchronous long-running endpoints into enqueue endpoints, and expose job detail/history APIs for frontend polling. Keep the design single-machine and SQLite-first with no external broker.

**Tech Stack:** FastAPI, SQLModel, SQLite, Alembic, Python worker process, React, TypeScript, Vitest, pytest

---

## File Structure

### Backend queue model and persistence

- Modify: `agent/app/models.py`
  - expand `Job` with queue and execution metadata
- Modify: `agent/app/schemas.py`
  - add job read/write payloads for queue endpoints
- Modify: `agent/alembic/versions/`
  - add revision for expanded job schema

### Backend queue and worker

- Create: `agent/app/services/job_queue.py`
  - queue insert, claim, retry, completion helpers
- Create: `agent/app/worker.py`
  - local worker entrypoint and polling loop
- Modify: `agent/app/api/jobs.py`
  - convert long-running actions into enqueue behavior
- Optionally modify: `agent/app/main.py`
  - only if startup should launch/coordinate worker-related checks

### Backend tests

- Create: `agent/tests/test_job_queue.py`
  - queue creation, claim, retry, stale-lock behavior
- Create: `agent/tests/test_worker.py`
  - worker handler execution tests
- Modify: `agent/tests/test_projects_api.py`
  - verify project job listing if added there
- Modify: `agent/tests/test_pptx_import_api.py`
  - verify import and rebuild enqueue instead of blocking

### Frontend

- Modify: `web/src/lib/types.ts`
  - add job state types
- Modify: `web/src/lib/api.ts`
  - add submit and fetch job methods
- Modify: `web/src/components/JobTimeline.tsx`
  - render queued/running/succeeded/failed states
- Modify: `web/src/components/ProjectWorkspace.tsx`
  - submit async actions and poll status
- Modify: `web/src/components/__tests__/JobTimeline.test.tsx`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

### Docs

- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`

## Task 1: Expand The `Job` Model Into A Persistent Queue Record

**Files:**
- Modify: `agent/app/models.py`
- Modify: `agent/app/schemas.py`
- Create: `agent/tests/test_job_queue.py`
- Modify: `agent/alembic/versions/`

- [ ] **Step 1: Write the failing queue model test**

```python
def test_job_queue_fields_persist(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'jobs.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        job = Job(
            project_id=1,
            job_type="import_pptx",
            status="queued",
            payload_json="{}",
            result_json="{}",
            error_message="",
            attempt_count=0,
            max_attempts=3,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job.id is not None
        assert job.status == "queued"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_job_queue.py::test_job_queue_fields_persist -v`
Expected: FAIL because the new queue fields do not exist yet.

- [ ] **Step 3: Expand the `Job` model**

Update `agent/app/models.py`.

```python
class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    job_type: str
    mode: str = "auto"
    status: str = "queued"
    attention_reason: str = ""
    notebook_session_path: str = ""
    retry_count: int = 0
    payload_json: str = "{}"
    result_json: str = "{}"
    error_message: str = ""
    attempt_count: int = 0
    max_attempts: int = 3
    available_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    locked_by: str = ""
    locked_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

- [ ] **Step 4: Add queue schemas**

Update `agent/app/schemas.py`.

```python
class JobRead(BaseModel):
    id: int
    project_id: int
    job_type: str
    status: str
    result_json: dict
    error_message: str


class JobEnqueueResponse(BaseModel):
    job_id: int
    status: str
```

- [ ] **Step 5: Add the migration revision**

Create a new Alembic revision adding the new `job` columns.

```python
def upgrade() -> None:
    with op.batch_alter_table("job") as batch_op:
        batch_op.add_column(sa.Column("payload_json", sa.String(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("result_json", sa.String(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("error_message", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"))
        batch_op.add_column(sa.Column("available_at", sa.DateTime(), nullable=False))
        batch_op.add_column(sa.Column("started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("finished_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("locked_by", sa.String(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("locked_at", sa.DateTime(), nullable=True))
```

- [ ] **Step 6: Run backend verification**

Run:

- `python -m pytest tests/test_job_queue.py -v`
- `python -m pytest tests/test_migrations.py -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/models.py app/schemas.py alembic/versions tests/test_job_queue.py tests/test_migrations.py
git commit -m "feat: expand job model for local queue"
```

## Task 2: Add Queue Helpers And Worker Entry Point

**Files:**
- Create: `agent/app/services/job_queue.py`
- Create: `agent/app/worker.py`
- Create: `agent/tests/test_worker.py`
- Modify: `agent/tests/test_job_queue.py`

- [ ] **Step 1: Write the failing queue helper tests**

```python
def test_claim_next_job_marks_job_running(session):
    ...
    claimed = claim_next_job(session, worker_id="worker-1")
    assert claimed.status == "running"
    assert claimed.locked_by == "worker-1"
```

- [ ] **Step 2: Run the queue helper tests to verify failure**

Run: `python -m pytest tests/test_job_queue.py::test_claim_next_job_marks_job_running -v`
Expected: FAIL because queue helpers do not exist yet.

- [ ] **Step 3: Add queue helper module**

Create `agent/app/services/job_queue.py`.

```python
def enqueue_job(session: Session, project_id: int, job_type: str, payload: dict) -> Job:
    job = Job(project_id=project_id, job_type=job_type, status="queued", payload_json=json.dumps(payload))
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def claim_next_job(session: Session, worker_id: str) -> Job | None:
    ...
```

- [ ] **Step 4: Add the worker entry point**

Create `agent/app/worker.py`.

```python
def main() -> None:
    worker_id = socket.gethostname()
    while True:
        with Session(engine) as session:
            job = claim_next_job(session, worker_id)
            if job is None:
                time.sleep(2)
                continue
            run_job_handler(session, job)
```

- [ ] **Step 5: Add worker tests**

Add `agent/tests/test_worker.py` with a minimal success-path handler test.

- [ ] **Step 6: Run queue/worker verification**

Run:

- `python -m pytest tests/test_job_queue.py -v`
- `python -m pytest tests/test_worker.py -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/services/job_queue.py app/worker.py tests/test_job_queue.py tests/test_worker.py
git commit -m "feat: add local job queue worker"
```

## Task 3: Convert Long-Running Endpoints Into Queue Submission

**Files:**
- Modify: `agent/app/api/jobs.py`
- Modify: `agent/tests/test_pptx_import_api.py`
- Optionally modify: `agent/tests/test_projects_api.py`

- [ ] **Step 1: Write the failing enqueue test**

```python
def test_import_pptx_enqueues_job(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Queued Import", "preferred_language": "zh-CN"}).json()
    ...
    response = client.post(f"/projects/{project['id']}/imports/pptx", files={...})
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
```

- [ ] **Step 2: Run the enqueue test to verify failure**

Run: `python -m pytest tests/test_pptx_import_api.py::test_import_pptx_enqueues_job -v`
Expected: FAIL because import currently executes synchronously.

- [ ] **Step 3: Change import submission to queue behavior**

Update `agent/app/api/jobs.py`.

```python
@router.post("/projects/{project_id}/imports/pptx", response_model=JobEnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_pptx_import(...):
    saved_upload = persist_upload_tempfile(...)
    job = enqueue_job(session, project_id, "import_pptx", {"file_path": str(saved_upload)})
    return {"job_id": job.id or 0, "status": job.status}
```

- [ ] **Step 4: Convert rebuild submission to queue behavior**

```python
@router.post("/imports/{import_id}/rebuild", response_model=JobEnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
def rebuild_from_import(...):
    job = enqueue_job(session, imported.project_id, "rebuild_import", {"import_id": import_id})
    return {"job_id": job.id or 0, "status": job.status}
```

- [ ] **Step 5: Add job read endpoints**

Add:

- `GET /jobs/{job_id}`
- `GET /projects/{project_id}/jobs`

- [ ] **Step 6: Run API verification**

Run:

- `python -m pytest tests/test_pptx_import_api.py -v`
- `python -m pytest tests/test_projects_api.py -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/api/jobs.py tests/test_pptx_import_api.py tests/test_projects_api.py
git commit -m "feat: enqueue long-running job api calls"
```

## Task 4: Add Worker Handlers For The First Job Types

**Files:**
- Modify: `agent/app/worker.py`
- Modify: `agent/app/services/job_queue.py`
- Modify: `agent/tests/test_worker.py`

- [ ] **Step 1: Write the failing handler tests**

```python
def test_worker_executes_import_pptx_job(...):
    ...
    run_job_handler(session, job)
    assert refreshed.status == "succeeded"
```

- [ ] **Step 2: Run the tests to verify failure**

Run: `python -m pytest tests/test_worker.py -v`
Expected: FAIL because handlers do not exist yet.

- [ ] **Step 3: Implement handlers for the first three job types**

Add handlers for:

- `analyze_sources`
- `import_pptx`
- `rebuild_import`

```python
def run_job_handler(session: Session, job: Job) -> None:
    payload = json.loads(job.payload_json or "{}")
    if job.job_type == "import_pptx":
        ...
    elif job.job_type == "rebuild_import":
        ...
```

- [ ] **Step 4: Persist result and failure state**

On success:

- status -> `succeeded`
- write `result_json`
- set `finished_at`

On failure:

- set `error_message`
- choose `retryable` or `failed`

- [ ] **Step 5: Run worker verification**

Run: `python -m pytest tests/test_worker.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/worker.py app/services/job_queue.py tests/test_worker.py
git commit -m "feat: add worker handlers for import and rebuild jobs"
```

## Task 5: Add Frontend Polling And Job-State UX

**Files:**
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/components/JobTimeline.tsx`
- Modify: `web/src/components/ProjectWorkspace.tsx`
- Modify: `web/src/components/__tests__/JobTimeline.test.tsx`
- Modify: `web/src/components/__tests__/ProjectWorkspace.test.tsx`

- [ ] **Step 1: Write the failing frontend polling test**

```tsx
it("shows queued and running job states for async rebuild actions", async () => {
  render(<ProjectWorkspace projectId={1} />);
  expect(await screen.findByText("Queued")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify failure**

Run: `npm test -- --run ProjectWorkspace.test.tsx JobTimeline.test.tsx`
Expected: FAIL because frontend does not yet poll job state.

- [ ] **Step 3: Add job APIs and types**

Update:

- `web/src/lib/types.ts`
- `web/src/lib/api.ts`

with:

- `JobRead`
- `ProjectJobSummary`
- fetch methods for job detail and project jobs

- [ ] **Step 4: Add polling behavior**

In `ProjectWorkspace.tsx`:

- submit async job
- poll `GET /jobs/{id}`
- stop polling on terminal states
- refresh relevant data when done

- [ ] **Step 5: Expand `JobTimeline`**

Render:

- queued
- running
- succeeded
- failed

with simple readable labels.

- [ ] **Step 6: Run frontend verification**

Run:

- `npm test -- --run`
- `npm run build`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add web/src/lib/types.ts web/src/lib/api.ts web/src/components/JobTimeline.tsx web/src/components/ProjectWorkspace.tsx web/src/components/__tests__/JobTimeline.test.tsx web/src/components/__tests__/ProjectWorkspace.test.tsx
git commit -m "feat: add local job queue polling ui"
```

## Task 6: Update Delivery And Acceptance Guidance

**Files:**
- Modify: `docs/DELIVERY.md`
- Modify: `docs/ACCEPTANCE.md`

- [ ] **Step 1: Update delivery notes**

Add:

```md
Long-running work is now submitted through a local persistent queue and executed by a separate worker process.
```

- [ ] **Step 2: Update acceptance checks**

Add:

```md
1. confirm queued work returns immediately
2. confirm worker executes queued jobs
3. confirm job state is visible and refreshes the UI
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
git commit -m "docs: add local job queue guidance"
```

## Self-Review

### Spec coverage

- persistent queue built on `Job`: covered by Task 1
- separate worker process: covered by Task 2
- enqueue APIs and job status/history endpoints: covered by Task 3
- first three job types: covered by Task 4
- frontend polling: covered by Task 5
- docs and acceptance updates: covered by Task 6

### Placeholder scan

No `TODO`, `TBD`, or vague deferred instructions remain. Each task contains concrete files, commands, and implementation sketches.

### Type consistency

The plan consistently uses:

- `payload_json`
- `result_json`
- `attempt_count`
- `max_attempts`
- `available_at`
- `locked_by`
- `locked_at`

These names are aligned across model, queue helper, worker, and API steps.
