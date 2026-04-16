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

export type LaunchJobResponse = {
  project_id: number;
  status: "ready_to_generate";
  prompt: string;
};

export type ManualExportRebuildResponse = {
  project_id: number;
  artifacts: DownloadArtifact[];
};
