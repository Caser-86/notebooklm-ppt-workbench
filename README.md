# NotebookLM PPT Workbench

Personal workbench for preparing NotebookLM slide decks and rebuilding exported results into editable PowerPoint outputs.

The product is intentionally split into two parts:

1. `Workbench`
Prepare sources, prompts, project history, and NotebookLM handoff.
2. `Reconstruction engine`
Take exported slide assets and rebuild:
   - a display-faithful clone
   - a more editable `.pptx`

This repository is currently a `semi-automatic` system:

- the app prepares sources and prompts
- the user generates and exports inside NotebookLM
- the local agent rebuilds the export into editable outputs

## Current V1 Scope

### Part 1: Semi-automatic NotebookLM workbench

- project list and project switching
- project detail persistence
- source intake for:
  - links
  - file paths
  - image paths
  - audio paths
  - video paths
- source insight summaries
- source revision history
- source revision diff view
- source revision full manifest view
- source revision compare view
- compare filters and compare-to-prompt export

### Part 2: Editable PPT reconstruction

- display clone output
- editable rebuild output
- multi-slide rebuild
- OCR same-line merge
- title/body hierarchy
- list grouping and indentation
- image preservation and caption rendering
- two-column handling
- table reconstruction with:
  - `colspan`
  - first-column `rowspan`
  - non-first-column `rowspan`
  - multi-level headers
  - width-aware columns
  - header styling and borders
  - raw OCR box table detection
- icon card reconstruction for:
  - small icon or image
  - title
  - description

## Read First

- Delivery notes: `docs/DELIVERY.md`
- Acceptance checklist: `docs/ACCEPTANCE.md`

## Run locally

### One-click start

Double-click:

```text
start-workbench.bat
```

The launcher will:

1. check for `python`, `node`, and `npm`
2. verify backend imports by testing `agent/app`
3. verify `web/node_modules` exists
4. check that ports `8000` and `5174` are free
5. start:
   - the agent
   - the worker
   - the web app
6. open the local workbench in your browser

If something required is missing, the launcher stops and prints the exact install command to run instead of installing anything automatically.

### Agent

```powershell
cd agent
python -m uvicorn app.main:app --reload
```

### Web

```powershell
cd web
npm install
npm run dev
```

## Verification

### Agent

```powershell
cd agent
python -m pytest -q
```

### Web

```powershell
cd web
npm test -- --run
npm run build
```

### Manual acceptance

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_manual_acceptance.ps1
```
