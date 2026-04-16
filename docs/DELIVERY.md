# NotebookLM PPT Workbench Delivery Notes

## What This Project Is

This repository is a semi-automatic workbench for:

1. preparing mixed source material for a presentation workflow
2. handing the prompt off to NotebookLM for manual generation and export
3. rebuilding the exported result into:
   - a display-faithful PowerPoint clone
   - a more editable reconstructed `.pptx`

The current product direction is intentionally semi-automatic. The system prepares, tracks, and rebuilds. The user still logs into NotebookLM, generates the deck there, and exports it manually.

## Current State

Implemented now:

- FastAPI local agent with:
  - health endpoint
  - project and job persistence
  - source ingestion scaffold
  - prompt preset service
  - NotebookLM runner state machine scaffold
  - display-clone PPT reconstruction
  - editable PPT reconstruction from OCR-like blocks
- React workbench with:
  - project rail
  - source intake area
  - prompt studio
  - NotebookLM handoff section
  - status section
  - rebuilt download section
- acceptance and regression scaffolding

## Verified Locally

The following checks were run successfully in the current environment:

- Agent tests: `python -m pytest -q`
- Web tests: `npm test -- --run`
- Web production build: `npm run build`
- FastAPI startup and `/health` response
- Python dependency import checks for:
  - `fastapi`
  - `sqlmodel`
  - `faster_whisper`
  - `ffmpeg-python`
  - `python-docx`
  - `fitz`
  - `python-pptx`
  - `playwright`
  - `rapidocr_onnxruntime`
- Playwright Chromium install

## How To Run

### 1. Start the agent

```powershell
cd agent
python -m uvicorn app.main:app --reload
```

### 2. Start the web app

```powershell
cd web
npm install
npm run dev
```

### 3. Open the web app

Use the local URL printed by Vite, typically:

```text
http://127.0.0.1:5173/
```

## How To Use The Current Semi-Automatic Flow

### Step A: Prepare the deck in the workbench

In the web UI:

- enter the project brief
- adjust the preset-based generation prompt
- review the NotebookLM handoff instructions

### Step B: Continue in NotebookLM

In NotebookLM, manually:

- sign in with your Google account
- paste or adapt the generated prompt
- generate the deck
- export the result

### Step C: Return for rebuild

After export, come back to the workbench flow and use the local reconstruction pipeline to produce:

- `Display clone`
- `Editable rebuild`

The current UI is already framed around this manual handoff model.

## Important Limitation

Google sign-in and NotebookLM generation are not currently automated end-to-end.

Reason:

- Google account login inside automation triggers security or risk warnings
- the controlled automation browser session does not reliably inherit your already logged-in personal browser state

Because of that, the safest production direction right now is:

- manual generation and export inside NotebookLM
- automated preparation and automated post-export reconstruction in this repo

## Project Structure

### `agent/`

Local backend and reconstruction logic.

Important areas:

- `agent/app/main.py`
- `agent/app/api/`
- `agent/app/services/`
- `agent/app/services/reconstruct/`

### `web/`

React workbench UI.

Important areas:

- `web/src/App.tsx`
- `web/src/components/`
- `web/src/styles.css`

### `samples/notebooklm_exports/`

Place example exported artifacts here for local regression and manual acceptance runs.

### `scripts/run_manual_acceptance.ps1`

Checklist-style script for the three planned manual acceptance scenarios.

## Recommended Next Steps

### Highest-value next step

Connect the current UI to a real local export intake flow so the user can:

1. select exported NotebookLM files
2. trigger rebuild from the UI
3. see rebuilt download links update from actual generated artifacts

### After that

- improve editable reconstruction quality:
  - multi-slide rebuild
  - text grouping
  - font/style approximation
  - shape and layout recovery
- connect prompt studio to real backend endpoints instead of static local values
- add true artifact indexing and history per project
- add export intake UX for PDF and PPTX separately

### Only after those

Revisit deeper NotebookLM automation. Treat it as an enhancement, not a dependency for the current product path.

## Suggested Demo Narrative

If you need to show this project to someone else, present it as:

1. a mixed-source preparation workbench
2. a semi-automatic NotebookLM generation workflow
3. a post-export editable reconstruction system

That story matches what the repository can honestly support today.
