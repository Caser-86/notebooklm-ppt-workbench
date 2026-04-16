import { useState, useTransition } from "react";

import { ArtifactGallery } from "./ArtifactGallery";
import { JobTimeline } from "./JobTimeline";
import { PromptStudio } from "./PromptStudio";
import { SourceIntakePanel } from "./SourceIntakePanel";
import { submitManualExportRebuild } from "../lib/api";
import type { DownloadArtifact } from "../lib/types";

export function ProjectWorkspace() {
  const [brief, setBrief] = useState("Create a launch deck");
  const [presetId, setPresetId] = useState("default");
  const [value, setValue] = useState("Start here");
  const [slideFiles, setSlideFiles] = useState<File[]>([]);
  const [ocrFile, setOcrFile] = useState<File | null>(null);
  const [artifacts, setArtifacts] = useState<DownloadArtifact[]>([]);
  const [isPending, startTransition] = useTransition();

  return (
    <main className="workspace">
      <header className="workspace-hero">
        <p className="eyebrow">Workspace</p>
        <h2>Workspace</h2>
        <p>No project selected</p>
      </header>
      <section className="workspace-section workspace-section--intro">
        <h3>Semi-automatic mode</h3>
        <p>This workspace prepares the prompt and rebuilds the exported deck, while you generate and export inside NotebookLM.</p>
      </section>
      <SourceIntakePanel prompt={brief} onPromptChange={setBrief} />
      <PromptStudio
        presets={[{ id: "default", label: "Default", body: "Start here" }]}
        selectedPresetId={presetId}
        value={value}
        onPresetChange={setPresetId}
        onValueChange={setValue}
      />
      <section className="workspace-section workspace-section--handoff">
        <div className="section-copy">
          <p className="eyebrow">NotebookLM handoff</p>
          <h3>Continue in NotebookLM</h3>
          <p>Paste the prompt into NotebookLM and generate the deck there.</p>
          <p>Export the deck from NotebookLM, then return here for rebuild and download.</p>
        </div>
        <label>
          Exported slide images
          <input
            type="file"
            multiple
            accept=".png,.jpg,.jpeg"
            onChange={(event) => setSlideFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        <label>
          OCR JSON (optional)
          <input
            type="file"
            accept=".json,application/json"
            onChange={(event) => setOcrFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <div className="handoff-actions">
          <button
            className="primary-action"
            type="button"
            onClick={() => window.open("https://notebooklm.google.com/", "_blank", "noopener")}
          >
            Open NotebookLM
          </button>
          <button
            className="secondary-action"
            type="button"
            disabled={slideFiles.length === 0 || isPending}
            onClick={async () => {
              const formData = new FormData();
              slideFiles.forEach((file) => formData.append("slide_images", file));
              if (ocrFile) {
                formData.append("ocr_json", ocrFile);
              }
              const payload = await submitManualExportRebuild(1, formData);
              startTransition(() => {
                setArtifacts(payload.artifacts);
              });
            }}
          >
            {isPending ? "Rebuilding..." : "Mark export ready"}
          </button>
        </div>
      </section>
      <JobTimeline status="needs_attention" attentionReason="browser_login_required" />
      <ArtifactGallery artifacts={artifacts} />
    </main>
  );
}
