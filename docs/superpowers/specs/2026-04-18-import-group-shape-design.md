# Imported Group Shape Handling Design

## Summary

This spec adds the next import-quality upgrade after text, image, table, icon-card, chart, and imported-slide preview support:

- shallow group-shape expansion with explicit fallback

The goal is not full group hierarchy recovery.

The goal is to make sure grouped content is:

1. recognized
2. partially expanded when safe
3. summarized clearly in the workbench
4. never silently lost

## Product Goal

When a local `.pptx` contains grouped shapes, the import pipeline should no longer treat the entire group as an opaque object that either disappears or gets flattened without explanation.

Instead, the system should:

- expand supported child objects into existing block types
- record unsupported parts explicitly
- preserve visible fallback behavior when full recovery is not possible

## Scope

This phase covers:

- shallow expansion of group shapes
- supported child extraction
- unsupported-group metadata and fallback

This phase does not cover:

- full recursive group hierarchy recovery
- editing group membership in the browser
- preserving original nested grouping semantics

## Recommended Strategy

Use **one-level group expansion**.

The importer should:

1. detect a group shape
2. inspect its direct children only
3. classify those children as:
   - supported
   - unsupported

Supported children should be converted into existing imported block types.

Unsupported children should not disappear. They should be represented by a new marker block:

- `unsupported_group`

## Supported Child Types

In this phase, only these child types should be promoted into the existing import pipeline:

- `imported_text`
- `imported_image`
- `imported_table`
- `imported_chart`
- elements that can form `imported_icon_card`

This keeps the implementation aligned with the current object set the renderer already knows how to handle.

## New Fallback Block

Add a new normalized block type:

- `unsupported_group`

### Minimum fields

- `slide_index`
- `content_type: "unsupported_group"`
- `x`
- `y`
- `width`
- `height`
- `supported_child_count`
- `unsupported_child_count`
- `unsupported_types`
- `fallback_mode`
- `snapshot_path` optional

## Import Flow

For each group shape:

1. identify its direct child objects
2. convert supported children into existing block types
3. collect unsupported child object type names
4. if unsupported children exist, emit an `unsupported_group` marker block
5. continue normal block grouping and rebuild flow

This means a single imported slide can contain both:

- real extracted child blocks
- one or more `unsupported_group` markers

## Why This Is Better

This design avoids two bad outcomes:

### Bad outcome 1

The whole group is dropped because one child type is unsupported.

### Bad outcome 2

The importer pretends the group was fully understood when it was not.

By separating supported child extraction from unsupported-group signaling, the system becomes:

- more useful
- more honest
- easier to extend later

## Fallback Strategy

### Best case

All direct children are supported.

Result:

- no `unsupported_group`
- the group is effectively expanded into existing blocks

### Mixed case

Some direct children are supported, some are not.

Result:

- supported children become real blocks
- unsupported remainder becomes `unsupported_group`

### Lowest safe fallback

No children can be meaningfully promoted.

Result:

- emit `unsupported_group`
- preserve snapshot if available
- otherwise preserve metadata and visible fallback only

## Rebuild Behavior

`unsupported_group` must not silently vanish during rebuild.

In this phase, acceptable fallback behavior is:

- if `snapshot_path` exists, preserve as an image-like object
- otherwise preserve as a compact text note describing unsupported grouped content

The important rule is:

- grouped content must remain visible as a limitation, not disappear as if it never existed

## Workbench Behavior

The workbench should surface grouped-object information in two places:

### Import summary

Imported presentation summaries should show:

- `unsupported_group` count

### Selected-slide summary

Selected imported slide summaries should show:

- grouped-object count
- unsupported-group count

This keeps the UI lightweight while still making grouped-content limitations visible.

## Success Criteria

This phase is successful when:

1. group shapes are detected
2. supported direct child objects are promoted into existing imported block types
3. unsupported grouped content is represented by `unsupported_group`
4. import summaries show grouped-content counts
5. rebuild output does not silently lose grouped content
6. current text/image/table/chart/icon-card flows remain stable

## Testing Strategy

This phase should add three layers of tests.

### 1. Import extraction tests

Verify that a grouped PPTX slide produces:

- promoted supported child blocks
- `unsupported_group` when needed

### 2. Summary tests

Verify that grouped-content counts appear in:

- imported presentation summary
- imported slide summary

### 3. Rebuild fallback tests

Verify that unsupported grouped content is still represented after rebuild through:

- snapshot-based image fallback
- or text fallback

## Out Of Scope

This phase does not include:

- recursive nested group recovery
- editable reconstruction of arbitrary group hierarchies
- preserving original group containers as editable group objects
- full shape graph reconstruction

## Risk Management

Main risks:

1. over-promoting child objects when coordinate context is ambiguous
2. under-reporting unsupported grouped content
3. making grouped-content behavior too opaque for the user

This design mitigates those risks by:

- limiting expansion to one level
- explicitly recording unsupported children
- surfacing grouped-content counts in the workbench

## Recommendation

Proceed with shallow group-shape expansion that:

- extracts supported direct children
- emits `unsupported_group` for the rest
- preserves grouped content through explicit fallback

This is the safest high-value next step before any future attempt at full group hierarchy recovery.
