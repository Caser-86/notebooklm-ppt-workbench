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

## Pass Criteria

The build is acceptable for `V1` if all of the following are true:

1. The user can reach NotebookLM from the workbench and complete the manual handoff.
2. The app stores project details and source history.
3. The app rebuilds exported assets into downloadable outputs.
4. Editable rebuild preserves major content structure for the sample slides.

## Known Limits

The build is still `V1`, so these are expected:

1. NotebookLM login and generation are not end-to-end automated.
2. Reconstruction is strongest on structured text, tables, and simple icon-card layouts.
3. Complex freeform layouts may still fall back to simpler text/image reconstruction.
