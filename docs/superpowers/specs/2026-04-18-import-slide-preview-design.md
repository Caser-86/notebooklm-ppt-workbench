# Imported Slide Preview Design

## Summary

This spec adds a preview-focused review surface for imported PPTX revisions inside the existing workbench.

The goal is to make imported presentations easier to inspect before rebuild by showing:

- a left-side filmstrip of imported slides
- a main preview area for the selected slide
- a per-slide object summary for the selected slide

This feature is intentionally review-oriented. It improves confidence and usability after import without introducing in-browser editing of imported slides.

## Product Goal

After a user imports a local `.pptx`, they should be able to quickly answer:

1. how many slides were imported
2. what each slide roughly looks like
3. what kinds of editable objects were detected on each slide

The feature should help the user decide whether to rebuild immediately or inspect the import more closely.

## UX Direction

The UI should follow an editor-like layout:

- **left:** imported slide filmstrip
- **right:** selected-slide preview and summary

This is closer to how people expect deck review to feel than a flat list or a generic asset gallery.

## Chosen Interaction Model

### Left side: Filmstrip

The filmstrip should show:

- slide thumbnail
- slide number
- a compact per-slide object count

It should support:

- vertical scrolling
- selecting a slide
- defaulting to the first slide

It does not need:

- drag-and-drop reordering
- inline rename
- per-slide action menus

### Right side: Selected Slide Detail

When a slide is selected, the right side should show:

1. a large preview image
2. a compact object summary

The summary should include counts for:

- text
- images
- tables
- cards

This side is intentionally simple. It is a review pane, not an editor.

## Data Model Changes

This feature should use the existing import model and extend per-slide asset payloads rather than introducing a new API shape.

### Imported Slide Asset

Add a per-slide `object_summary` field to `ImportedSlideAsset`.

Minimum shape:

- `slide_index`
- `preview_image_path`
- `text_dump`
- `structure_json_path`
- `object_summary`

Where `object_summary` contains per-slide counts such as:

- `imported_text`
- `imported_image`
- `imported_table`
- `imported_icon_card`

## API Strategy

Do not create new endpoints for this feature.

Instead, enrich the existing imported presentation payload so each slide asset already includes the data needed by the UI.

That keeps the flow simple:

- fetch project imports
- render filmstrip
- render selected slide detail

No additional detail request is required for the first version.

## Backend Responsibilities

The backend should:

1. continue generating `preview_image_path`
2. compute per-slide `object_summary` during import serialization
3. return that summary inside each imported slide asset

The backend should not add:

- slide preview caching strategy changes
- image processing pipelines
- additional import job states

for this phase.

## Frontend Responsibilities

The frontend should:

1. render a filmstrip when an imported presentation exists
2. select the first slide by default
3. update the right-side preview when the selection changes
4. show a readable object summary for the selected slide

The frontend should not add:

- object highlighting inside the preview
- slide diff mode
- object inspector panels

for this phase.

## Layout Behavior

### Empty State

If no imported PPTX exists:

- keep the current “no imported PPTX yet” message
- do not render an empty preview frame

### Single Slide

If the import contains one slide:

- the filmstrip still appears
- the preview opens on that slide

### Multi-Slide

If the import contains multiple slides:

- the filmstrip should scroll
- the selected slide should remain visually distinct

## Visual Priority

This feature is about clarity, not flair.

The visual hierarchy should be:

1. selected slide image
2. slide number and filename context
3. object summary
4. filmstrip navigation

The design should feel like a lightweight review workspace, not a marketing card layout.

## Success Criteria

This feature is successful when:

1. imported PPTX revisions show a filmstrip of slide thumbnails
2. the first slide is selected automatically
3. selecting another thumbnail changes the main preview
4. the selected slide shows a per-slide object summary
5. the feature works with both single-slide and multi-slide imports

## Out Of Scope

This feature does not include:

- slide editing
- object-level hover overlays
- object bounding boxes on preview images
- compare mode between imported slides
- rebuilding from a single selected slide only

## Risks

The main risks are:

1. overloading the workspace with too much detail
2. accidentally making the preview panel feel like a second editor
3. exposing summary data at the import level but not the slide level

This design avoids those risks by:

- keeping the right side to preview plus summary only
- using per-slide summaries
- reusing the current import flow and payloads

## Recommendation

Implement this as a small extension of the current imported revision area:

- enrich imported slide assets with `object_summary`
- add a filmstrip on the left
- add a selected-slide preview and summary on the right

This is the highest-value next UX improvement for imported PPTX review without opening a larger editing project.
