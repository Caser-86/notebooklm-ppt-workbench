import type {
  LaunchJobResponse,
  ManualExportRebuildResponse,
  ProjectDetail,
  ProjectSummary,
  PromptPreset,
  RebuildVersion,
} from "./types";

const API_BASE = "http://127.0.0.1:8000";

export async function fetchPromptPresets(): Promise<PromptPreset[]> {
  const response = await fetch(`${API_BASE}/prompt-presets`);
  return response.json();
}

export async function fetchProjects(): Promise<ProjectSummary[]> {
  const response = await fetch(`${API_BASE}/projects`);
  return response.json();
}

export async function createProject(title: string): Promise<ProjectSummary> {
  const response = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, preferred_language: "zh-CN" }),
  });
  return response.json();
}

export async function fetchProjectDetail(projectId: number): Promise<ProjectDetail> {
  const response = await fetch(`${API_BASE}/projects/${projectId}`);
  return response.json();
}

export async function updateProjectDetail(
  projectId: number,
  payload: { brief: string; prompt_draft: string; source_manifest: { urls: string[] } },
): Promise<ProjectDetail> {
  const response = await fetch(`${API_BASE}/projects/${projectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function fetchProjectRebuilds(projectId: number): Promise<RebuildVersion[]> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/rebuilds`);
  const payload = (await response.json()) as RebuildVersion[];
  return payload.map((version) => ({
    ...version,
    artifacts: version.artifacts.map((artifact) => ({
      ...artifact,
      href: artifact.href.startsWith("http") ? artifact.href : `${API_BASE}${artifact.href}`,
    })),
  }));
}

export async function launchGenerateJob(
  projectId: number,
  payload: { preset_id: string; user_prompt: string; source_summary: string },
): Promise<LaunchJobResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/jobs/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function submitManualExportRebuild(projectId: number, formData: FormData): Promise<ManualExportRebuildResponse> {
  const response = await fetch(`${API_BASE}/projects/${projectId}/rebuild/manual-export`, {
    method: "POST",
    body: formData,
  });
  const payload = (await response.json()) as ManualExportRebuildResponse;
  return {
    ...payload,
    artifacts: payload.artifacts.map((artifact) => ({
      ...artifact,
      href: artifact.href.startsWith("http") ? artifact.href : `${API_BASE}${artifact.href}`,
    })),
  };
}
