# PPTX Import Quality Upgrade Design

## Summary

This spec upgrades the local PPTX import pipeline with a new priority:

- **editable structure recovery over visual similarity**

The current PPTX import pipeline already supports:

- uploading a local `.pptx`
- recording imports at the project level
- rebuilding imported presentations into:
  - display clone
  - editable rebuild

That first phase proved the workflow can close end to end. The next step is to improve what the editable rebuild actually contains.

Instead of treating imported PPTX content mostly as extracted text that gets re-laid out, this upgrade should extract more original object structure from the PPTX and convert those objects into the workbench's normalized editable block model.

The goal is not perfect PPT parity. The goal is to preserve more real editable objects:

- title text boxes
- body text boxes
- pictures
- tables
- recognizable icon-card groups

## Product Goal

When a user imports a local `.pptx`, the editable rebuild should preserve as many meaningful editable objects as possible instead of collapsing the deck into generic text-heavy reconstruction.

In practical terms, the imported editable output should become noticeably better at:

- preserving text boxes as text boxes
- preserving tables as tables
- preserving pictures as picture objects
- preserving simple card-like image-and-text groups as icon-card structures

## Primary Direction

This work is explicitly **structure-first**.

If there is a tradeoff between:

- making the rebuilt deck look slightly closer to the source image
- making the rebuilt deck more editable as native PPT objects

the editability objective wins in this phase.

## Recommended Approach

Use a **hybrid extraction pipeline**.

### Not recommended

Do not continue relying mainly on:

- flat text extraction
- generic OCR-like block synthesis

for imported PPTX content.

That path is good enough for minimal import support, but it caps editability too early.

### Recommended

Add a new object-aware import layer:

1. read PPTX objects directly
2. normalize those objects into a shared internal block model
3. reuse the existing reconstruction renderer wherever possible

This preserves the current architecture while improving the quality of the imported editable output.

## Architecture

The upgraded architecture should have three layers:

1. **PPTX object extraction**
2. **normalized editable blocks**
3. **existing rebuild renderer**

### Layer 1: PPTX Object Extraction

This layer reads object information directly from the imported `.pptx`.

Phase one of the quality upgrade should extract:

- text boxes
- pictures
- tables

Optional grouping logic should then detect:

- icon-card style patterns built from those objects

### Layer 2: Normalized Editable Blocks

This layer converts raw PPTX objects into a stable intermediate model that the renderer can consume.

It should not expose raw `python-pptx` implementation details outside the import layer.

### Layer 3: Existing Rebuild Renderer

The renderer should continue to own the final output behavior:

- slide creation
- text rendering
- image rendering
- table rendering
- icon-card rendering

This avoids creating a second, parallel output pipeline.

## Why This Architecture Is Better

This design has three advantages:

1. it reuses the renderer that already works
2. it improves imported editability without destabilizing the existing OCR path
3. it gives future object-type support a clean expansion point

The current OCR-driven reconstruction path remains valuable for:

- NotebookLM image exports
- mixed asset rebuilds
- fallback behavior

The new PPTX object-aware path should be an addition, not a replacement.

## Object Model

The import pipeline should produce a normalized set of editable blocks.

### Core shared fields

Every imported editable block should include:

- `slide_index`
- `content_type`
- `x`
- `y`
- `width`
- `height`

### Block Type: `imported_text`

Used for title and body text boxes.

Minimum fields:

- `text`
- `text_role`
- `font_size`
- `bold`
- `italic`

### Block Type: `imported_image`

Used for pictures extracted directly from the PPTX.

Minimum fields:

- `image_path`

### Block Type: `imported_table`

Used for PowerPoint tables extracted directly from the PPTX.

Minimum fields:

- `rows`
- `cols`
- `cells`
- `column_widths`
- `header_rows`

### Block Type: `imported_icon_card`

Used when the import layer can confidently detect a simple:

- icon or small image
- short title
- short description

Minimum fields:

- `icon_path`
- `title_text`
- `body_text`
- relative geometry for the icon, title, and body

## Processing Flow

The upgraded import flow should be:

1. user uploads a local `.pptx`
2. import service classifies the source type
3. import service extracts object-level content from the PPTX
4. object extraction is normalized into editable blocks
5. normalized blocks are passed into the existing rebuild renderer
6. display clone and editable rebuild are produced
7. import history and rebuild history are updated

## Source-Type Strategy

The import system should continue to classify imported PPTX files as:

- `internal_generated`
- `notebooklm_export`
- `generic_pptx`

The quality-upgrade path should use that classification internally.

### `internal_generated`

These files should preferentially use the object-aware import path because they are the most structurally predictable.

### `notebooklm_export`

These should also preferentially use the object-aware import path, since improving NotebookLM-related imports is the highest-value product goal.

### `generic_pptx`

These should attempt the object-aware path first, but must degrade gracefully when structure is too irregular or too weak.

## Fallback Rules

The import pipeline must not fail hard just because object extraction is incomplete.

Recommended behavior:

### Best case

- object extraction is strong
- normalized blocks are rich
- editable rebuild uses object-aware structures

### Partial fallback

- some text boxes, pictures, or tables are extracted cleanly
- weak or unknown objects fall back to simpler text-like blocks

### Lowest safe fallback

- the `.pptx` is still accepted and recorded
- display clone still works
- editable rebuild may degrade to simpler text/image reconstruction

The fallback logic should be explicit and safe. It should never pretend high-fidelity object recovery where the importer is not confident.

## First-Phase Scope

This upgrade should first cover four object categories:

1. text boxes
2. pictures
3. tables
4. icon-card style groups

This is enough to create a major improvement in editability without overreaching.

## Out Of Scope

The following remain out of scope for this phase:

- animation recovery
- transition recovery
- SmartArt parity
- complete group-shape hierarchy preservation
- full theme/master fidelity
- arbitrary shape-by-shape reconstruction for every third-party PPTX

## Success Criteria

This quality upgrade is successful when all of the following are true:

1. imported title and body regions are usually preserved as real editable text boxes
2. imported pictures are preserved as picture objects
3. imported PowerPoint tables are preserved as editable tables when table structure is available
4. obvious icon-card layouts are normalized into `icon_card` structures
5. generic PPTX still degrades safely when object extraction is weak
6. the OCR-based rebuild path continues to work unchanged for non-PPTX workflows

## Testing Strategy

This work should add tests at three layers.

### 1. Extraction tests

Verify that PPTX object extraction produces:

- text blocks
- picture blocks
- table blocks

for controlled sample decks.

### 2. Normalization tests

Verify that extracted PPTX objects become the expected normalized block types:

- `imported_text`
- `imported_image`
- `imported_table`
- `imported_icon_card`

### 3. Rebuild tests

Verify that importing a PPTX with these structures produces editable output containing:

- text boxes
- image objects
- table objects
- icon-card output where expected

## Recommended Phase Order

1. add object-aware text extraction
2. add picture extraction
3. add table extraction
4. add icon-card grouping on imported objects
5. wire source-type-aware fallback behavior
6. verify with internal, NotebookLM-related, and generic PPTX examples

## Risks

The main risks are:

1. overfitting to internal PPTX while claiming generic support
2. creating a second renderer by accident
3. mixing raw PPT object semantics directly into rendering code
4. weakening the existing OCR path while improving import quality

The architecture above is designed specifically to avoid those risks.

## Final Recommendation

Proceed with a hybrid object-aware import pipeline that:

- extracts PPTX objects directly
- normalizes them into shared editable blocks
- reuses the current renderer

This is the fastest path to meaningfully better editable imports without turning the project into a full PowerPoint parser/editor.
