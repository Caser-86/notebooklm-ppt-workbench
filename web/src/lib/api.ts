import type { LaunchJobResponse, ManualExportRebuildResponse, PromptPreset } from "./types";

const API_BASE = "http://127.0.0.1:8000";

export async function fetchPromptPresets(): Promise<PromptPreset[]> {
  const response = await fetch(`${API_BASE}/prompt-presets`);
  return response.json();
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
