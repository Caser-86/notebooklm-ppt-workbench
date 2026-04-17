# Demo Script

## Goal

Use this script for a short `3 minute` walkthrough of the current `V1`.

## One-line Positioning

This is a semi-automatic NotebookLM PPT workbench that prepares source material, hands generation off to NotebookLM, and then rebuilds exported slides into editable PowerPoint outputs.

## Suggested Demo Order

### 1. Open the workbench

Show:

- project rail
- source intake
- prompt studio
- source history and compare
- NotebookLM handoff
- rebuilt outputs

Say:

This product is intentionally split in two. The first part prepares sources and prompt flow for NotebookLM. The second part takes exported assets and rebuilds them into editable slides.

### 2. Show project and source workflow

Open a project and show:

- brief
- source links
- media paths
- source insight
- source compare

Say:

The user can keep iterating on inputs before going into NotebookLM. We store revision history, compare source versions, and even push compare summaries back into Prompt Studio.

### 3. Explain the semi-automatic handoff

Point to the NotebookLM handoff area.

Say:

We do not fully automate Google sign-in or generation inside NotebookLM. Instead, the user logs in and exports there, and this workbench handles preparation, tracking, and post-export rebuild.

### 4. Show the reconstruction story

Use the generated demo artifacts or rebuilt outputs.

Say:

After export, the local agent produces two outputs:

- a display-faithful clone
- a more editable rebuilt PowerPoint

The rebuild engine already handles structured text, merged tables, grouped headers, and repeated icon-card layouts.

### 5. Show proof of capability

Mention the strongest currently supported structures:

- grouped tables
- row and column spans
- multi-level headers
- icon plus title plus description cards

Say:

We focused on practical slide structures first, so the current build is strongest on business-style content rather than arbitrary decorative layouts.

### 6. Close with honest boundaries

Say:

This is already closed-loop for a semi-automatic workflow, but it is still honest about its limits. NotebookLM generation remains manual, and very freeform visual layouts may still reconstruct more simply than the original.

## Short Script

You can read this version almost verbatim:

This project solves a very specific problem. NotebookLM can generate rich slides, but those exports are often not editable enough for downstream work. So we built a semi-automatic workbench around it.

First, the user prepares a project here: sources, links, media paths, prompt draft, and source comparisons. Then they continue into NotebookLM, generate the deck there, and export it manually.

After export, our local reconstruction engine takes over. It can generate a display-faithful clone and a more editable rebuilt PPT. At this point, the system already supports structured text pages, complex business tables, merged headers, row spans, and repeated icon-card layouts.

So the value of the product is not just generation. It is the full bridge from source preparation to editable downstream PowerPoint output.

## Likely Questions

### Why not fully automate NotebookLM?

Because Google sign-in automation is not stable or reliable enough for a good product path right now. We chose a semi-automatic workflow so the system is honest and usable today.

### What is strongest right now?

Structured text slides, table-heavy slides, and repeated icon-card feature slides.

### What is still weaker?

Highly decorative freeform layouts and generalized arbitrary visual compositions.

### Is this already usable?

Yes, for the intended `V1` semi-automatic workflow. The branch already includes documentation, acceptance scaffolding, sample assets, and a passing acceptance run.
