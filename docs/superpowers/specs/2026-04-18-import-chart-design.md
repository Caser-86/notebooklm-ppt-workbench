# Imported Chart Handling Design

## Summary

This spec adds the next object type to the PPTX import quality pipeline:

- `chart`

The goal is not to deliver full editable PowerPoint chart parity in this phase.

The goal is to ensure imported charts are:

1. recognized explicitly
2. surfaced in imported-slide review
3. preserved through a stable downgrade path
4. never silently lost during rebuild

This is a `chart-first` design. Grouped shapes are noted but intentionally deferred.

## Product Goal

When a user imports a local `.pptx` that contains charts, the system should no longer treat those slides as if the chart were invisible or indistinguishable from generic text.

Instead, the workbench should:

- detect chart presence
- show chart counts in import summaries
- preserve chart information during rebuild through a predictable fallback strategy

## Scope

This phase covers only imported charts.

It does not attempt:

- full editable chart reconstruction
- group shape preservation
- arbitrary composite object editing

## Object Model

Add a new normalized imported block type:

- `imported_chart`

### Minimum fields

- `slide_index`
- `content_type: "imported_chart"`
- `chart_type`
- `title`
- `categories`
- `series`
- `x`
- `y`
- `width`
- `height`
- `snapshot_path` optional
- `fallback_mode`

These fields are enough to support both:

- immediate review in the workbench
- future upgrades toward stronger chart reconstruction

## Recommended Fallback Strategy

This phase should prioritize safe, explicit fallback over ambitious chart editing.

### Best case

If a chart snapshot can be produced reliably:

- preserve the chart as an image-like object in the rebuilt slide

This keeps chart visibility intact even if editability is limited.

### Mid-level fallback

If a chart image cannot be preserved but chart data can be extracted:

- render:
  - a title text block
  - a structured table derived from category/series data

This keeps the chart content understandable and partially editable.

### Lowest safe fallback

If neither image nor reliable chart data is available:

- keep chart metadata
- record the fallback reason
- surface the chart in the workbench summary

This avoids silent loss and makes the limitation visible.

## Why This Approach

The current system is already strong at:

- text
- image
- table

That makes chart handling safer if it leans on those strengths:

- preserve chart as image when possible
- degrade to table when possible

This is much more stable than trying to invent a full editable chart renderer in the same phase.

## Import Flow

The imported chart path should be:

1. detect chart shapes in the PPTX
2. extract chart metadata
3. attempt to create a snapshot or equivalent preserved representation
4. normalize chart into `imported_chart`
5. include chart in slide-level object summaries
6. during rebuild:
   - use snapshot if available
   - otherwise degrade to structured content

## Workbench Behavior

The workbench should show chart information in two places:

### Import summary

The imported presentation summary should include a chart count.

### Per-slide summary

The selected-slide summary should include chart count if that slide contains charts.

This means users can tell immediately:

- whether charts were detected
- on which slides they appear

## Rebuild Behavior

The rebuild engine must not silently drop chart blocks.

For this phase, acceptable output behavior is:

- preserve as an image object
- or preserve as a structured table plus text

What is not acceptable:

- chart is missing with no trace
- chart is counted during import but absent during rebuild with no explanation

## Group Shape Position

Grouped shapes are explicitly out of scope for this phase.

However, the importer should be prepared to:

- detect that a grouped/composite object exists
- mark it as unsupported or deferred metadata

This keeps the door open for future group-shape work without forcing it into the chart phase.

## Success Criteria

This phase is successful when:

1. imported charts are detected as `imported_chart`
2. chart counts appear in import summaries
3. chart counts appear in per-slide summaries
4. rebuild output preserves chart presence through image or structured fallback
5. charts are never silently dropped
6. existing imported text/image/table/icon-card flows remain stable

## Testing Strategy

This phase should add three layers of tests.

### 1. Import extraction tests

Verify that a PPTX with a chart produces at least one `imported_chart` block.

### 2. API summary tests

Verify that chart counts appear in:

- imported presentation summary
- imported slide summary

### 3. Rebuild tests

Verify that a chart-containing PPTX produces rebuild output where the chart remains represented by:

- an image object
- or a structured fallback object

## Out Of Scope

This phase does not include:

- fully editable chart recreation in PowerPoint native chart objects
- series styling parity
- legend fidelity
- axis fidelity
- theme-aware chart reconstruction
- grouped shape restoration

## Risk Management

The main risks are:

1. trying to over-build chart editability too early
2. introducing chart handling that breaks the current imported object pipeline
3. hiding failed chart recovery instead of reporting it clearly

This design avoids those risks by:

- making downgrade behavior explicit
- preserving chart visibility first
- keeping group shape work deferred

## Recommendation

Proceed with a chart-first phase that:

- adds `imported_chart`
- exposes chart counts in summaries
- preserves charts through image or structured fallback

This is the highest-value next step after text/image/table/icon-card and imported-slide preview support.
