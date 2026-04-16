# NotebookLM PPT Workbench

Personal workspace for generating NotebookLM slide decks and rebuilding them into editable PowerPoint outputs.

See `docs/DELIVERY.md` for the current project handoff, usage flow, and next-step recommendations.

## Run locally

### Agent
`cd agent && python -m uvicorn app.main:app --reload`

### Web
`cd web && npm install && npm run dev`

## Run tests

- Agent: `cd agent && python -m pytest`
- Web: `cd web && npm test -- --run`
- Manual acceptance: `powershell -ExecutionPolicy Bypass -File scripts/run_manual_acceptance.ps1`
