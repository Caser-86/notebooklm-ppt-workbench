# Acceptance Checklist

## Goal

Use this checklist to verify the current `V1` honestly supports the intended semi-automatic flow.

## Environment

1. Start the backend agent.
2. Start the web app.
3. Open the local workbench in the browser.

## Happy Path

### Part 1: Workbench

1. Create or select a project.
2. Enter a brief.
3. Add at least one source link.
4. Optionally add file, image, audio, or video paths.
5. Save project details.
6. Run source analysis.
7. Confirm:
   - source insight summary appears
   - source revision history appears
   - revision compare view works
   - compare summary can be pushed into Prompt Studio

### Local PPTX import

1. In the same project, find the `Import PPTX` section.
2. Upload a local `.pptx`.
3. Confirm:
   - an imported PPTX revision appears
   - source type is shown
   - page count is shown
   - object summary appears for imported text, image, table, or card blocks
   - chart count appears if the PPTX includes charts
   - the first imported slide is selected automatically
   - the imported slide filmstrip appears
   - the selected slide shows a preview image
4. Trigger rebuild from the imported revision.
5. Confirm:
   - display clone artifact appears
   - editable rebuild artifact appears
   - imported text stays editable
   - imported tables stay tables when available
   - imported images stay picture objects when available
   - imported charts remain represented through explicit fallback
   - switching slides in the filmstrip updates the selected preview and summary

### NotebookLM handoff

1. Open NotebookLM from the workbench.
2. Manually generate and export the deck in NotebookLM.
3. Return to the workbench.

### Part 2: Reconstruction

1. Upload exported slide images.
2. Optionally upload OCR JSON.
3. Trigger rebuild.
4. Confirm:
   - display clone artifact appears
   - editable rebuild artifact appears

## Recommended Real Samples

Use at least these three slide patterns:

1. Text-heavy slide
Title, paragraphs, and list items.
2. Table slide
Include grouped headers or merged cells if possible.
3. Icon card slide
Small icon plus title plus short description, repeated across the slide.

Recommended sample directories in this repo:

1. `samples/notebooklm_exports/link-heavy/`
2. `samples/notebooklm_exports/table-heavy/`
3. `samples/notebooklm_exports/icon-card/`
4. `samples/generated_demo/`

## Pass Criteria

The build is acceptable for `V1` if all of the following are true:

1. The user can reach NotebookLM from the workbench and complete the manual handoff.
2. The app stores project details and source history.
3. The app can import a local `.pptx` and record it in project history.
4. The app rebuilds exported or imported assets into downloadable outputs.
5. Editable rebuild preserves major content structure for the sample slides.
6. Imported PPTX structure is visibly better than plain text fallback for supported text, image, table, and icon-card cases.

## Known Limits

The build is still `V1`, so these are expected:

1. NotebookLM login and generation are not end-to-end automated.
2. Reconstruction is strongest on structured text, tables, and simple icon-card layouts.
3. Complex freeform layouts may still fall back to simpler text/image reconstruction.
4. Generic third-party `.pptx` files are best-effort in this phase and may degrade more than internal or NotebookLM-related PPTX.
5. Imported PPTX quality is structure-first, not full visual parity with the original deck.
