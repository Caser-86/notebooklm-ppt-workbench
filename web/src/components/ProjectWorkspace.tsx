import { useEffect, useState, useTransition } from "react";

import { ArtifactGallery } from "./ArtifactGallery";
import { JobDrawer } from "./JobDrawer";
import { JobTimeline } from "./JobTimeline";
import { PromptStudio } from "./PromptStudio";
import { SourceIntakePanel } from "./SourceIntakePanel";
import {
  analyzeProjectSources,
  fetchJob,
  fetchProjectDetail,
  fetchProjectImports,
  fetchProjectJobs,
  fetchProjectRebuilds,
  fetchProjectSourceHistory,
  rebuildProjectImport,
  cancelJob,
  deleteJob,
  retryJob,
  submitManualExportRebuild,
  uploadProjectPptx,
  updateProjectDetail,
} from "../lib/api";
import { useI18n } from "../lib/i18n";
import type { DownloadArtifact, ImportedPresentation, JobRead, RebuildVersion, SourceRevision } from "../lib/types";

const sourceCategories = [
  { key: "urls", diffLabel: "URL" },
  { key: "file_paths", diffLabel: "File" },
  { key: "image_paths", diffLabel: "Image" },
  { key: "audio_paths", diffLabel: "Audio" },
  { key: "video_paths", diffLabel: "Video" },
] as const;

type SourceCategoryKey = (typeof sourceCategories)[number]["key"];
type CompareCategoryFilter = "all" | SourceCategoryKey;

function buildSourceRevisionDiffs(
  current: SourceRevision,
  previous: SourceRevision | undefined,
  categoryLabels: Record<string, string>,
) {
  return sourceCategories.flatMap(({ key, diffLabel }) => {
    const previousValues = new Set(previous?.source_manifest?.[key] ?? []);
    return (current.source_manifest?.[key] ?? [])
      .filter((value) => !previousValues.has(value))
      .map((value) => `+ ${categoryLabels[key] ?? diffLabel}: ${value}`);
  });
}

function buildSourceCompareDiffs(
  newer: SourceRevision | undefined,
  older: SourceRevision | undefined,
  categoryLabels: Record<string, string>,
  categoryFilter: CompareCategoryFilter = "all",
) {
  const emptyGroups = { added: [] as string[], removed: [] as string[] };
  if (!newer || !older) {
    return emptyGroups;
  }

  return sourceCategories.reduce(
    (groups, { key, diffLabel }) => {
      if (categoryFilter !== "all" && key !== categoryFilter) {
        return groups;
      }

      const newerValues = newer.source_manifest?.[key] ?? [];
      const olderValues = older.source_manifest?.[key] ?? [];
      const olderSet = new Set(olderValues);
      const newerSet = new Set(newerValues);

      groups.added.push(
        ...newerValues.filter((value) => !olderSet.has(value)).map((value) => `+ ${categoryLabels[key] ?? diffLabel}: ${value}`),
      );
      groups.removed.push(
        ...olderValues.filter((value) => !newerSet.has(value)).map((value) => `- ${categoryLabels[key] ?? diffLabel}: ${value}`),
      );

      return groups;
    },
    { added: [] as string[], removed: [] as string[] },
  );
}

function buildSourceCompareSummary({
  newer,
  older,
  categoryLabels,
  categoryFilter,
  changesOnly,
}: {
  newer?: SourceRevision;
  older?: SourceRevision;
  categoryLabels: Record<string, string>;
  categoryFilter: CompareCategoryFilter;
  changesOnly: boolean;
}) {
  if (!newer || !older) {
    return "";
  }

  const compareDiffs = buildSourceCompareDiffs(newer, older, categoryLabels, categoryFilter);
  const filterLabel = categoryFilter === "all"
    ? categoryLabels.all ?? "All"
    : categoryLabels[categoryFilter] ?? "All";

  const addedSection = compareDiffs.added.length > 0
    ? compareDiffs.added.join("\n")
    : "No added sources in this compare.";
  const removedSection = compareDiffs.removed.length > 0
    ? compareDiffs.removed.join("\n")
    : "No removed sources in this compare.";

  return [
    categoryLabels.summaryTitle ?? "Source compare summary",
    categoryLabels.newerRevisionLabel?.replace("{revision}", String(newer.revision_number)) ?? `Newer revision: ${newer.revision_number}`,
    categoryLabels.olderRevisionLabel?.replace("{revision}", String(older.revision_number)) ?? `Against revision: ${older.revision_number}`,
    (categoryLabels.filterPrefix ?? "Filter: ") + filterLabel,
    (categoryLabels.changesOnlyPrefix ?? "Changes only: ") + (changesOnly ? categoryLabels.enabled ?? "On" : categoryLabels.disabled ?? "Off"),
    (categoryLabels.addedPrefix ?? "Added in Revision ").replace("{revision}", String(newer.revision_number)),
    addedSection,
    (categoryLabels.removedPrefix ?? "Removed from Revision ").replace("{revision}", String(older.revision_number)),
    removedSection,
  ].join("\n");
}

function filterSourceManifest(
  revision: SourceRevision,
  counterpart?: SourceRevision,
  changesOnly = false,
  categoryFilter: CompareCategoryFilter = "all",
) {
  if (!changesOnly || !counterpart) {
    if (categoryFilter === "all") {
      return revision.source_manifest;
    }

    return {
      [categoryFilter]: revision.source_manifest?.[categoryFilter] ?? [],
    } as SourceRevision["source_manifest"];
  }

  const manifest = Object.fromEntries(
    sourceCategories.map(({ key }) => {
      if (categoryFilter !== "all" && key !== categoryFilter) {
        return [key, []];
      }
      const counterpartValues = new Set(counterpart.source_manifest?.[key] ?? []);
      return [key, (revision.source_manifest?.[key] ?? []).filter((item) => !counterpartValues.has(item))];
    }),
  );

  return manifest as SourceRevision["source_manifest"];
}

function SourceManifestPanel({
  revision,
  manifest,
}: {
  revision: SourceRevision;
  manifest?: SourceRevision["source_manifest"];
}) {
  const sourceManifest = manifest ?? revision.source_manifest;
  const { messages } = useI18n();

  return (
    <div className="source-detail-panel">
      {sourceCategories.map(({ key }) => (
        <div key={`${revision.id}-${key}`} className="source-manifest-group">
          <h5>{messages.sourceCategories[key]}</h5>
          <ul>
            {(sourceManifest[key] ?? []).map((item) => (
              <li key={`${revision.id}-${key}-${item}`}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export function ProjectWorkspace({ projectId }: { projectId: number | null }) {
  const { locale, messages } = useI18n();
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
  const [expandedRevisionId, setExpandedRevisionId] = useState<number | null>(null);
  const [compareNewerRevisionId, setCompareNewerRevisionId] = useState<number | null>(null);
  const [compareOlderRevisionId, setCompareOlderRevisionId] = useState<number | null>(null);
  const [showCompareChangesOnly, setShowCompareChangesOnly] = useState(false);
  const [compareCategoryFilter, setCompareCategoryFilter] = useState<CompareCategoryFilter>("all");
  const [slideFiles, setSlideFiles] = useState<File[]>([]);
  const [selectedPptx, setSelectedPptx] = useState<File | null>(null);
  const [ocrFile, setOcrFile] = useState<File | null>(null);
  const [artifacts, setArtifacts] = useState<DownloadArtifact[]>([]);
  const [rebuilds, setRebuilds] = useState<RebuildVersion[]>([]);
  const [imports, setImports] = useState<ImportedPresentation[]>([]);
  const [selectedImportId, setSelectedImportId] = useState<number | null>(null);
  const [selectedImportedSlideIndex, setSelectedImportedSlideIndex] = useState<number | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("needs_attention");
  const [jobError, setJobError] = useState<string>("");
  const [jobs, setJobs] = useState<JobRead[]>([]);
  const [isJobDrawerOpen, setIsJobDrawerOpen] = useState(false);
  const [showFailedJobsOnly, setShowFailedJobsOnly] = useState(false);
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
      setExpandedRevisionId(null);
      setCompareNewerRevisionId(null);
      setCompareOlderRevisionId(null);
      setShowCompareChangesOnly(false);
      setCompareCategoryFilter("all");
      setSelectedPptx(null);
      setImports([]);
      setSelectedImportId(null);
      setSelectedImportedSlideIndex(null);
      setJobStatus("needs_attention");
      setJobError("");
      setJobs([]);
      setIsJobDrawerOpen(false);
      setShowFailedJobsOnly(false);
      return;
    }

    let isMounted = true;
    void Promise.all([
      fetchProjectDetail(projectId),
      fetchProjectRebuilds(projectId),
      fetchProjectSourceHistory(projectId),
      fetchProjectImports(projectId),
      fetchProjectJobs(projectId),
    ]).then(
      ([detail, history, sourceRevisions, importedPresentations, projectJobs]) => {
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
        setExpandedRevisionId(sourceRevisions[0]?.id ?? null);
        setCompareNewerRevisionId(sourceRevisions[0]?.id ?? null);
        setCompareOlderRevisionId(sourceRevisions[1]?.id ?? null);
        setShowCompareChangesOnly(false);
        setCompareCategoryFilter("all");
        setRebuilds(history);
        setArtifacts(history[0]?.artifacts ?? []);
        setImports(importedPresentations);
        setSelectedImportId(importedPresentations[0]?.id ?? null);
        setSelectedImportedSlideIndex(importedPresentations[0]?.slide_assets[0]?.slide_index ?? null);
        setJobs(projectJobs);
      });
    });

    return () => {
      isMounted = false;
    };
  }, [projectId]);

  const activeImport = imports.find((entry) => entry.id === selectedImportId) ?? imports[0] ?? null;
  const selectedSlide = activeImport?.slide_assets.find((slide) => slide.slide_index === selectedImportedSlideIndex)
    ?? activeImport?.slide_assets[0]
    ?? null;

  async function pollJobUntilFinished(jobId: number) {
    for (let attempt = 0; attempt < 20; attempt += 1) {
      const job = await fetchJob(jobId);
      setJobStatus(job.status);
      setJobError(job.error_message);
      if (job.status === "succeeded" || job.status === "failed") {
        return job;
      }
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    return await fetchJob(jobId);
  }

  async function handleRetryJob(jobId: number) {
    if (!projectId) {
      return;
    }

    const originalJob = jobs.find((job) => job.id === jobId);
    if (!originalJob) {
      return;
    }

    setJobStatus("queued");
    setJobError("");
    const queued = await retryJob(jobId);
    const job = await pollJobUntilFinished(queued.job_id);

    if (originalJob.job_type === "analyze_sources") {
      const [detail, sourceRevisions, projectJobs] = await Promise.all([
        fetchProjectDetail(projectId),
        fetchProjectSourceHistory(projectId),
        fetchProjectJobs(projectId),
      ]);
      startTransition(() => {
        setInsightSummary(detail.insight_summary || "");
        setSourceHistory(sourceRevisions);
        setExpandedRevisionId(sourceRevisions[0]?.id ?? null);
        setCompareNewerRevisionId(sourceRevisions[0]?.id ?? null);
        setCompareOlderRevisionId(sourceRevisions[1]?.id ?? null);
        setJobStatus(job.status);
        setJobError(job.error_message);
        setJobs(projectJobs);
      });
      return;
    }

    if (originalJob.job_type === "import_pptx") {
      const [refreshedImports, projectJobs] = await Promise.all([
        fetchProjectImports(projectId),
        fetchProjectJobs(projectId),
      ]);
      startTransition(() => {
        setImports(refreshedImports);
        setSelectedImportId(refreshedImports[0]?.id ?? null);
        setSelectedImportedSlideIndex(refreshedImports[0]?.slide_assets[0]?.slide_index ?? null);
        setJobStatus(job.status);
        setJobError(job.error_message);
        setJobs(projectJobs);
      });
      return;
    }

    if (originalJob.job_type === "rebuild_import") {
      const [refreshedRebuilds, projectJobs] = await Promise.all([
        fetchProjectRebuilds(projectId),
        fetchProjectJobs(projectId),
      ]);
      startTransition(() => {
        setRebuilds(refreshedRebuilds);
        setArtifacts(refreshedRebuilds[0]?.artifacts ?? []);
        setJobStatus(job.status);
        setJobError(job.error_message);
        setJobs(projectJobs);
      });
      return;
    }

    const projectJobs = await fetchProjectJobs(projectId);
    startTransition(() => {
      setJobStatus(job.status);
      setJobError(job.error_message);
      setJobs(projectJobs);
    });
  }

  async function handleCancelJob(jobId: number) {
    if (!projectId) {
      return;
    }

    const cancelledJob = await cancelJob(jobId);
    const projectJobs = await fetchProjectJobs(projectId);
    startTransition(() => {
      setJobStatus(cancelledJob.status);
      setJobError(cancelledJob.error_message);
      setJobs(projectJobs);
    });
  }

  async function handleDeleteJob(jobId: number) {
    if (!projectId) {
      return;
    }

    await deleteJob(jobId);
    const projectJobs = await fetchProjectJobs(projectId);
    startTransition(() => {
      setJobs(projectJobs);
    });
  }

  return (
    <main className="workspace">
      <header className="workspace-hero">
        <p className="eyebrow">{messages.workspace.eyebrow}</p>
        <h2>{messages.workspace.title}</h2>
        <p>{projectId ? messages.workspace.projectLabel(projectId) : messages.workspace.noProjectSelected}</p>
      </header>
      <section className="workspace-section workspace-section--intro">
        <h3>{messages.workspace.introTitle}</h3>
        <p>{messages.workspace.introDescription}</p>
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
        presets={[{ id: "default", label: messages.promptStudio.defaultPreset, body: messages.promptStudio.defaultBody }]}
        selectedPresetId={presetId}
        value={value}
        onPresetChange={setPresetId}
        onValueChange={setValue}
      />
      <section className="workspace-section">
        <div className="section-copy">
          <p className="eyebrow">{messages.workspace.projectDraftEyebrow}</p>
          <h3>{messages.workspace.projectDraftTitle}</h3>
          <p>{messages.workspace.projectDraftDescription}</p>
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
            {messages.workspace.saveProjectDetails}
          </button>
        </div>
      </section>
      <section className="workspace-section">
        <div className="section-copy">
          <p className="eyebrow">{messages.workspace.sourceInsightEyebrow}</p>
          <h3>{messages.workspace.sourceInsightTitle}</h3>
          <p>{messages.workspace.sourceInsightDescription}</p>
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
              setJobStatus("queued");
              const payload = await analyzeProjectSources(projectId, {
                prompt: brief,
                urls: sourceLinks.split("\n").map((item) => item.trim()).filter(Boolean),
                file_paths: sourceFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
                image_paths: imageFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
                audio_paths: audioFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
                video_paths: videoFilePaths.split("\n").map((item) => item.trim()).filter(Boolean),
              });
              const job = await pollJobUntilFinished(payload.job_id);
              const [detail, sourceRevisions, projectJobs] = await Promise.all([
                fetchProjectDetail(projectId),
                fetchProjectSourceHistory(projectId),
                fetchProjectJobs(projectId),
              ]);
              startTransition(() => {
                setInsightSummary(detail.insight_summary || "");
                setSourceHistory(sourceRevisions);
                setExpandedRevisionId(sourceRevisions[0]?.id ?? null);
                setCompareNewerRevisionId(sourceRevisions[0]?.id ?? null);
                setCompareOlderRevisionId(sourceRevisions[1]?.id ?? null);
                setJobStatus(job.status);
                setJobError(job.error_message);
                setJobs(projectJobs);
              });
            }}
          >
            {messages.workspace.analyzeSources}
          </button>
        </div>
        {insightSummary ? <p>{insightSummary}</p> : <p>{messages.workspace.noSourceInsight}</p>}
        {sourceHistory.length > 0 ? (
          <div className="rebuild-history">
            <h4>{messages.workspace.recentSourceVersions}</h4>
            {sourceHistory.length > 1 ? (
              <div className="source-compare-panel">
                <div className="section-copy">
                  <p className="eyebrow">{messages.workspace.compareEyebrow}</p>
                  <h4>{messages.workspace.compareTitle}</h4>
                  <p>{messages.workspace.compareDescription}</p>
                </div>
                <div className="source-compare-controls">
                  <label>
                    {messages.workspace.compareNewerRevision}
                    <select
                      value={compareNewerRevisionId ?? ""}
                      onChange={(event) => setCompareNewerRevisionId(Number(event.target.value))}
                    >
                      {sourceHistory.map((revision) => (
                        <option key={`newer-${revision.id}`} value={revision.id}>
                          {messages.workspace.revisionLabel(revision.revision_number)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    {messages.workspace.againstRevision}
                    <select
                      value={compareOlderRevisionId ?? ""}
                      onChange={(event) => setCompareOlderRevisionId(Number(event.target.value))}
                    >
                      {sourceHistory.map((revision) => (
                        <option key={`older-${revision.id}`} value={revision.id}>
                          {messages.workspace.revisionLabel(revision.revision_number)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="source-compare-toggle">
                    <input
                      type="checkbox"
                      checked={showCompareChangesOnly}
                      onChange={(event) => setShowCompareChangesOnly(event.target.checked)}
                    />
                    {messages.workspace.showChangesOnly}
                  </label>
                </div>
                <div className="source-filter-chips">
                  <button
                    type="button"
                    className={compareCategoryFilter === "all" ? "primary-action source-filter-chip" : "secondary-action source-filter-chip"}
                    onClick={() => setCompareCategoryFilter("all")}
                  >
                    {messages.workspace.all}
                  </button>
                  {sourceCategories.map(({ key }) => (
                    <button
                      key={`filter-${key}`}
                      type="button"
                      className={compareCategoryFilter === key ? "primary-action source-filter-chip" : "secondary-action source-filter-chip"}
                      onClick={() => setCompareCategoryFilter(key)}
                    >
                      {messages.sourceCategories[key]}
                    </button>
                  ))}
                </div>
                {(() => {
                  const newerRevision = sourceHistory.find((revision) => revision.id === compareNewerRevisionId);
                  const olderRevision = sourceHistory.find((revision) => revision.id === compareOlderRevisionId);
                  const compareLabels = {
                    ...messages.sourceCategories,
                    all: messages.workspace.all,
                    summaryTitle: messages.compareSummary.title,
                    newerRevisionLabel: locale === "zh-CN" ? "较新版本：{revision}" : "Newer revision: {revision}",
                    olderRevisionLabel: locale === "zh-CN" ? "对比版本：{revision}" : "Against revision: {revision}",
                    filterPrefix: locale === "zh-CN" ? "筛选：" : "Filter: ",
                    changesOnlyPrefix: locale === "zh-CN" ? "仅变化项：" : "Changes only: ",
                    enabled: locale === "zh-CN" ? "开" : "On",
                    disabled: locale === "zh-CN" ? "关" : "Off",
                    addedPrefix: locale === "zh-CN" ? "版本 {revision} 新增" : "Added in Revision {revision}",
                    removedPrefix: locale === "zh-CN" ? "相对版本 {revision} 移除" : "Removed from Revision {revision}",
                  } as Record<string, string>;
                  const compareDiffs = buildSourceCompareDiffs(newerRevision, olderRevision, compareLabels, compareCategoryFilter);
                  const compareSummary = buildSourceCompareSummary({
                    newer: newerRevision,
                    older: olderRevision,
                    categoryLabels: compareLabels,
                    categoryFilter: compareCategoryFilter,
                    changesOnly: showCompareChangesOnly,
                  });

                  if (!newerRevision || !olderRevision) {
                    return null;
                  }

                  return (
                    <>
                      <div className="handoff-actions">
                        <button
                          className="secondary-action"
                          type="button"
                          onClick={() => {
                            setValue((currentValue) =>
                              currentValue.trim()
                                ? `${currentValue}\n\n${compareSummary}`
                                : compareSummary,
                            );
                          }}
                        >
                          {messages.workspace.useCompareSummaryInPrompt}
                        </button>
                      </div>
                      <div className="source-compare-groups">
                        <div className="source-compare-group">
                          <h5>{messages.workspace.addedInRevision(newerRevision.revision_number)}</h5>
                          {compareDiffs.added.length > 0 ? (
                            <ul className="source-compare-diffs">
                              {compareDiffs.added.map((diff) => (
                                <li key={`compare-added-${newerRevision.id}-${olderRevision.id}-${diff}`}>{diff}</li>
                              ))}
                            </ul>
                          ) : (
                            <p>{messages.workspace.noAddedSources}</p>
                          )}
                        </div>
                        <div className="source-compare-group">
                          <h5>{messages.workspace.removedFromRevision(olderRevision.revision_number)}</h5>
                          {compareDiffs.removed.length > 0 ? (
                            <ul className="source-compare-diffs">
                              {compareDiffs.removed.map((diff) => (
                                <li key={`compare-removed-${newerRevision.id}-${olderRevision.id}-${diff}`}>{diff}</li>
                              ))}
                            </ul>
                          ) : (
                            <p>{messages.workspace.noRemovedSources}</p>
                          )}
                        </div>
                      </div>
                      <div className="source-compare-grid">
                        <div className="source-compare-column">
                          <h5>{messages.workspace.revisionSnapshot(newerRevision.revision_number)}</h5>
                          <p>{newerRevision.insight_summary}</p>
                          <SourceManifestPanel
                            revision={newerRevision}
                            manifest={filterSourceManifest(newerRevision, olderRevision, showCompareChangesOnly, compareCategoryFilter)}
                          />
                        </div>
                        <div className="source-compare-column">
                          <h5>{messages.workspace.revisionSnapshot(olderRevision.revision_number)}</h5>
                          <p>{olderRevision.insight_summary}</p>
                          <SourceManifestPanel
                            revision={olderRevision}
                            manifest={filterSourceManifest(olderRevision, newerRevision, showCompareChangesOnly, compareCategoryFilter)}
                          />
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
            ) : null}
            <ul>
              {sourceHistory.map((revision, index) => {
                const diffs = buildSourceRevisionDiffs(revision, sourceHistory[index + 1], messages.sourceCategories);
                return (
                <li key={revision.id}>
                  <span>{messages.workspace.revisionLabel(revision.revision_number)}</span>
                  <span>{revision.insight_summary}</span>
                  <button
                    className="secondary-action"
                    type="button"
                    onClick={() => setExpandedRevisionId((current) => (current === revision.id ? null : revision.id))}
                  >
                    {expandedRevisionId === revision.id
                      ? messages.workspace.hideFullSources(revision.revision_number)
                      : messages.workspace.showFullSources(revision.revision_number)}
                  </button>
                  {diffs.length > 0 ? (
                    <ul>
                      {diffs.map((diff) => (
                        <li key={`${revision.id}-${diff}`}>{diff}</li>
                      ))}
                    </ul>
                  ) : null}
                  {expandedRevisionId === revision.id ? (
                    <SourceManifestPanel revision={revision} />
                  ) : null}
                </li>
                );
              })}
            </ul>
          </div>
        ) : null}
      </section>
      <section className="workspace-section">
        <div className="section-copy">
          <p className="eyebrow">{messages.workspace.importPptxEyebrow}</p>
          <h3>{messages.workspace.importPptxTitle}</h3>
          <p>{messages.workspace.importPptxDescription}</p>
        </div>
        <label>
          {messages.workspace.importPptxFile}
          <input
            type="file"
            accept=".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation"
            onChange={(event) => setSelectedPptx(event.target.files?.[0] ?? null)}
          />
        </label>
        <div className="handoff-actions">
          <button
            className="secondary-action"
            type="button"
            disabled={!projectId || !selectedPptx || isPending}
            onClick={async () => {
              if (!projectId || !selectedPptx) {
                return;
              }
              setJobStatus("queued");
              const queued = await uploadProjectPptx(projectId, selectedPptx);
              const job = await pollJobUntilFinished(queued.job_id);
              const [refreshedImports, refreshedJobs] = await Promise.all([
                fetchProjectImports(projectId),
                fetchProjectJobs(projectId),
              ]);
              startTransition(() => {
                setImports(refreshedImports);
                setSelectedImportId(refreshedImports[0]?.id ?? null);
                setSelectedImportedSlideIndex(refreshedImports[0]?.slide_assets[0]?.slide_index ?? null);
                setJobStatus(job.status);
                setJobError(job.error_message);
                setJobs(refreshedJobs);
                setSelectedPptx(null);
              });
            }}
          >
            {messages.workspace.importPptxAction}
          </button>
        </div>
        <div className="rebuild-history">
          <h4>{messages.workspace.importedPptxRevisions}</h4>
          {imports.length > 0 ? (
            <ul>
              {imports.map((entry) => (
                <li key={entry.id}>
                  <button
                    className="secondary-action"
                    type="button"
                    onClick={() => {
                      setSelectedImportId(entry.id);
                      setSelectedImportedSlideIndex(entry.slide_assets[0]?.slide_index ?? null);
                    }}
                  >
                    {entry.filename}
                  </button>
                  <span>{messages.workspace.importSourceType}: {entry.source_type}</span>
                  <span>{messages.workspace.importPageCount}: {entry.page_count}</span>
                  <span>{entry.status}</span>
                  <span>Text: {entry.object_summary?.imported_text ?? 0}</span>
                  <span>Images: {entry.object_summary?.imported_image ?? 0}</span>
                  <span>Tables: {entry.object_summary?.imported_table ?? 0}</span>
                  <span>Charts: {entry.object_summary?.imported_chart ?? 0}</span>
                  <span>Groups: {entry.object_summary?.unsupported_group ?? 0}</span>
                  <span>Cards: {entry.object_summary?.imported_icon_card ?? 0}</span>
                  <button
                    className="secondary-action"
                    type="button"
                    disabled={isPending}
                    onClick={async () => {
                      setJobStatus("queued");
                      const queued = await rebuildProjectImport(entry.id);
                      const job = await pollJobUntilFinished(queued.job_id);
                      const [refreshedRebuilds, refreshedJobs] = projectId
                        ? await Promise.all([fetchProjectRebuilds(projectId), fetchProjectJobs(projectId)])
                        : [[], []];
                      startTransition(() => {
                        setRebuilds(refreshedRebuilds);
                        setArtifacts(refreshedRebuilds[0]?.artifacts ?? []);
                        setJobStatus(job.status);
                        setJobError(job.error_message);
                        setJobs(refreshedJobs as JobRead[]);
                      });
                    }}
                  >
                    {messages.workspace.rebuildFromImport}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p>{messages.workspace.noImportedPptx}</p>
          )}
          {activeImport && selectedSlide ? (
            <div className="import-review-shell">
              <aside className="import-filmstrip">
                <h5>{messages.workspace.importedSlidesTitle}</h5>
                {activeImport.slide_assets.map((slide) => (
                  <button
                    key={slide.id}
                    type="button"
                    className={slide.slide_index === selectedSlide.slide_index ? "filmstrip-slide is-active" : "filmstrip-slide"}
                    onClick={() => setSelectedImportedSlideIndex(slide.slide_index)}
                  >
                    <img
                      src={slide.preview_image_path}
                      alt={messages.workspace.importedSlidePreviewAlt(slide.slide_index)}
                    />
                    <span>{messages.workspace.importedSlideLabel(slide.slide_index)}</span>
                  </button>
                ))}
              </aside>
              <section className="import-preview-detail">
                <h5>{messages.workspace.selectedImportedSlide(selectedSlide.slide_index)}</h5>
                <img
                  className="import-preview-image"
                  src={selectedSlide.preview_image_path}
                  alt={messages.workspace.importedSlidePreviewAlt(selectedSlide.slide_index)}
                />
                <div className="import-slide-summary">
                  <span>Text: {selectedSlide.object_summary?.imported_text ?? 0}</span>
                  <span>Images: {selectedSlide.object_summary?.imported_image ?? 0}</span>
                  <span>Tables: {selectedSlide.object_summary?.imported_table ?? 0}</span>
                  <span>Charts: {selectedSlide.object_summary?.imported_chart ?? 0}</span>
                  <span>Groups: {selectedSlide.object_summary?.unsupported_group ?? 0}</span>
                  <span>Cards: {selectedSlide.object_summary?.imported_icon_card ?? 0}</span>
                </div>
              </section>
            </div>
          ) : null}
        </div>
      </section>
      <section className="workspace-section workspace-section--handoff">
        <div className="section-copy">
          <p className="eyebrow">{messages.workspace.notebooklmEyebrow}</p>
          <h3>{messages.workspace.notebooklmTitle}</h3>
          <p>{messages.workspace.notebooklmDescription1}</p>
          <p>{messages.workspace.notebooklmDescription2}</p>
        </div>
        <label>
          {messages.workspace.exportedSlideImages}
          <input
            type="file"
            multiple
            accept=".png,.jpg,.jpeg"
            onChange={(event) => setSlideFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        <label>
          {messages.workspace.ocrJsonOptional}
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
            {messages.workspace.openNotebooklm}
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
            {isPending ? messages.workspace.rebuilding : messages.workspace.markExportReady}
          </button>
        </div>
      </section>
      <JobTimeline
        status={jobStatus}
        attentionReason={jobStatus === "needs_attention" ? "browser_login_required" : jobError}
        jobs={jobs}
        onRetry={handleRetryJob}
        onViewAllJobs={() => setIsJobDrawerOpen(true)}
      />
      <JobDrawer
        open={isJobDrawerOpen}
        jobs={jobs}
        failedOnly={showFailedJobsOnly}
        onClose={() => setIsJobDrawerOpen(false)}
        onToggleFailedOnly={() => setShowFailedJobsOnly((current) => !current)}
        onRetry={handleRetryJob}
        onCancel={handleCancelJob}
        onDelete={handleDeleteJob}
      />
      <ArtifactGallery artifacts={artifacts} rebuilds={rebuilds} />
    </main>
  );
}
