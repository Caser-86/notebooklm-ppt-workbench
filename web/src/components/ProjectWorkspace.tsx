import { useEffect, useState, useTransition } from "react";

import { ArtifactGallery } from "./ArtifactGallery";
import { JobTimeline } from "./JobTimeline";
import { PromptStudio } from "./PromptStudio";
import { SourceIntakePanel } from "./SourceIntakePanel";
import {
  analyzeProjectSources,
  fetchProjectDetail,
  fetchProjectRebuilds,
  fetchProjectSourceHistory,
  submitManualExportRebuild,
  updateProjectDetail,
} from "../lib/api";
import type { DownloadArtifact, RebuildVersion, SourceRevision } from "../lib/types";

export function ProjectWorkspace({ projectId }: { projectId: number | null }) {
  const [brief, setBrief] = useState("Create a launch deck");
  const [presetId, setPresetId] = useState("default");
  const [value, setValue] = useState("Start here");
  const [sourceLinks, setSourceLinks] = useState("");
  const [sourceFilePaths, setSourceFilePaths] = useState("");
  const [imageFilePaths, setImageFilePaths] = useState("");
  const [audioFilePaths, setAudioFilePaths] = useState("");
  const [videoFilePaths, setVideoFilePaths] = useState("");
  const [insightSummary, setInsightSummary] = useState("");
  const [sourceHistory, setSourceHistory] = useState<SourceRevision[]>([]);
  const [slideFiles, setSlideFiles] = useState<File[]>([]);
  const [ocrFile, setOcrFile] = useState<File | null>(null);
  const [artifacts, setArtifacts] = useState<DownloadArtifact[]>([]);
  const [rebuilds, setRebuilds] = useState<RebuildVersion[]>([]);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!projectId) {
      setArtifacts([]);
      setRebuilds([]);
      setBrief("Create a launch deck");
      setValue("Start here");
      setSourceLinks("");
      setSourceFilePaths("");
      setImageFilePaths("");
      setAudioFilePaths("");
      setVideoFilePaths("");
      setInsightSummary("");
      setSourceHistory([]);
      return;
    }

    let isMounted = true;
    void Promise.all([fetchProjectDetail(projectId), fetchProjectRebuilds(projectId), fetchProjectSourceHistory(projectId)]).then(
      ([detail, history, sourceRevisions]) => {
      if (!isMounted) {
        return;
      }
      startTransition(() => {
        setBrief(detail.brief || "");
        setValue(detail.prompt_draft || "");
        setSourceLinks((detail.source_manifest?.urls ?? []).join("\n"));
        setSourceFilePaths((detail.source_manifest?.file_paths ?? []).join("\n"));
        setImageFilePaths((detail.source_manifest?.image_paths ?? []).join("\n"));
        setAudioFilePaths((detail.source_manifest?.audio_paths ?? []).join("\n"));
        setVideoFilePaths((detail.source_manifest?.video_paths ?? []).join("\n"));
        setInsightSummary(detail.insight_summary || "");
        setSourceHistory(sourceRevisions);
        setRebuilds(history);
        setArtifacts(history[0]?.artifacts ?? []);
      });
    });

    return () => {
      isMounted = false;
    };
  }, [projectId]);

  return (
    <main className="workspace">
      <header className="workspace-hero">
        <p className="eyebrow">Workspace</p>
        <h2>Workspace</h2>
        <p>{projectId ? `Project ${projectId}` : "No project selected"}</p>
      </header>
      <section className="workspace-section workspace-section--intro">
        <h3>Semi-automatic mode</h3>
        <p>This workspace prepares the prompt and rebuilds the exported deck, while you generate and export inside NotebookLM.</p>
      </section>
      <SourceIntakePanel
        prompt={brief}
        onPromptChange={setBrief}
        sourceLinks={sourceLinks}
        onSourceLinksChange={setSourceLinks}
        sourceFilePaths={sourceFilePaths}
        onSourceFilePathsChange={setSourceFilePaths}
        imageFilePaths={imageFilePaths}
        onImageFilePathsChange={setImageFilePaths}
        audioFilePaths={audioFilePaths}
        onAudioFilePathsChange={setAudioFilePaths}
        videoFilePaths={videoFilePaths}
        onVideoFilePathsChange={setVideoFilePaths}
      />
      <PromptStudio
        presets={[{ id: "default", label: "Default", body: "Start here" }]}
        selectedPresetId={presetId}
        value={value}
        onPresetChange={setPresetId}
        onValueChange={setValue}
      />
      <section className="workspace-section">
        <div className="section-copy">
          <p className="eyebrow">Project draft</p>
          <h3>Save project details</h3>
          <p>Store the current brief, prompt draft, and source links with this project before handing off to NotebookLM.</p>
        </div>
        <div className="handoff-actions">
          <button
            className="secondary-action"
            type="button"
            disabled={!projectId}
            onClick={async () => {
              if (!projectId) {
                return;
              }
              const detail = await updateProjectDetail(projectId, {
                brief,
                prompt_draft: value,
                source_manifest: {
                  urls: sourceLinks
                    .split("\n")
                    .map((item) => item.trim())
                    .filter(Boolean),
                  file_paths: sourceFilePaths
                    .split("\n")
                    .map((item) => item.trim())
                    .filter(Boolean),
                  image_paths: imageFilePaths
                    .split("\n")
                    .map((item) => item.trim())
                    .filter(Boolean),
                  audio_paths: audioFilePaths
                    .split("\n")
                    .map((item) => item.trim())
                    .filter(Boolean),
                  video_paths: videoFilePaths
                    .split("\n")
                    .map((item) => item.trim())
                    .filter(Boolean),
                },
              });
              startTransition(() => {
                setBrief(detail.brief);
                setValue(detail.prompt_draft);
                setSourceLinks((detail.source_manifest?.urls ?? []).join("\n"));
                setSourceFilePaths((detail.source_manifest?.file_paths ?? []).join("\n"));
                setImageFilePaths((detail.source_manifest?.image_paths ?? []).join("\n"));
                setAudioFilePaths((detail.source_manifest?.audio_paths ?? []).join("\n"));
                setVideoFilePaths((detail.source_manifest?.video_paths ?? []).join("\n"));
              });
            }}
          >
            Save project details
          </button>
        </div>
      </section>
      <section className="workspace-section">
        <div className="section-copy">
          <p className="eyebrow">Source insight</p>
          <h3>Analyze current sources</h3>
          <p>Persist the current URLs and file paths, then generate a lightweight intake summary for this project.</p>
        </div>
        <div className="handoff-actions">
          <button
            className="secondary-action"
            type="button"
            disabled={!projectId}
            onClick={async () => {
              if (!projectId) {
                return;
              }
              const payload = await analyzeProjectSources(projectId, {
                prompt: brief,
                urls: sourceLinks.split("\n").map((item) => item.trim()).filter(Boolean),
                file_paths: sourceFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
                image_paths: imageFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
                audio_paths: audioFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
                video_paths: videoFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
              });
              startTransition(() => {
                setInsightSummary(payload.insight_summary);
                setSourceHistory((current) => [
                  {
                    id: payload.revision_number,
                    revision_number: payload.revision_number,
                    source_manifest: payload.source_manifest,
                    insight_summary: payload.insight_summary,
                  },
                  ...current,
                ]);
              });
            }}
          >
            Analyze sources
          </button>
        </div>
        {insightSummary ? <p>{insightSummary}</p> : <p>No source insight yet. Analyze the current links and file paths to persist a source snapshot.</p>}
        {sourceHistory.length > 0 ? (
          <div className="rebuild-history">
            <h4>Recent source versions</h4>
            <ul>
              {sourceHistory.map((revision) => (
                <li key={revision.id}>
                  <span>{`Revision ${revision.revision_number}`}</span>
                  <span>{revision.insight_summary}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>
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
              if (!projectId) {
                return;
              }
              const formData = new FormData();
              slideFiles.forEach((file) => formData.append("slide_images", file));
              if (ocrFile) {
                formData.append("ocr_json", ocrFile);
              }
              const payload = await submitManualExportRebuild(projectId, formData);
              startTransition(() => {
                setArtifacts(payload.artifacts);
                setRebuilds((current) => [
                  {
                    id: payload.version_number,
                    version_number: payload.version_number,
                    slide_count: slideFiles.length,
                    artifacts: payload.artifacts,
                  },
                  ...current,
                ]);
              });
            }}
          >
            {isPending ? "Rebuilding..." : "Mark export ready"}
          </button>
        </div>
      </section>
      <JobTimeline status="needs_attention" attentionReason="browser_login_required" />
      <ArtifactGallery artifacts={artifacts} rebuilds={rebuilds} />
    </main>
  );
}
