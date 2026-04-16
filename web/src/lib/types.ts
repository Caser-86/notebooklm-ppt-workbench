export type PromptPreset = {
  id: string;
  label: string;
  body: string;
};

export type DownloadArtifact = {
  id: string;
  label: string;
  href: string;
};

export type ProjectSummary = {
  id: number;
  title: string;
  preferred_language: string;
};

export type ProjectDetail = {
  id: number;
  title: string;
  preferred_language: string;
  preferred_style: string;
  brief: string;
  prompt_draft: string;
  source_manifest: {
    urls?: string[];
    notes?: string;
  };
};

export type LaunchJobResponse = {
  project_id: number;
  status: "ready_to_generate";
  prompt: string;
};

export type ManualExportRebuildResponse = {
  project_id: number;
  version_number: number;
  artifacts: DownloadArtifact[];
};

export type RebuildVersion = {
  id: number;
  version_number: number;
  slide_count: number;
  artifacts: DownloadArtifact[];
};
