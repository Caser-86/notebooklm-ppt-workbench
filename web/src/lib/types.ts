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
    file_paths?: string[];
    image_paths?: string[];
    audio_paths?: string[];
    video_paths?: string[];
    notes?: string;
  };
  insight_summary: string;
};

export type LaunchJobResponse = {
  project_id: number;
  status: "ready_to_generate";
  prompt: string;
};

export type JobEnqueueResponse = {
  job_id: number;
  status: string;
};

export type JobRead = {
  id: number;
  project_id: number;
  job_type: string;
  status: string;
  result_json: Record<string, unknown>;
  error_message: string;
  created_at: string;
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

export type SourceRevision = {
  id: number;
  revision_number: number;
  source_manifest: {
    urls?: string[];
    file_paths?: string[];
    image_paths?: string[];
    audio_paths?: string[];
    video_paths?: string[];
  };
  insight_summary: string;
};

export type ImportedSlideAsset = {
  id: number;
  slide_index: number;
  preview_image_path: string;
  text_dump: string;
  structure_json_path: string;
  object_summary: Record<string, number>;
};

export type ImportedPresentation = {
  id: number;
  project_id: number;
  source_type: string;
  filename: string;
  status: string;
  page_count: number;
  error_message: string;
  object_summary: Record<string, number>;
  slide_assets: ImportedSlideAsset[];
};
