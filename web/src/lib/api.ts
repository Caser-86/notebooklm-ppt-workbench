import type { LaunchJobResponse, PromptPreset } from "./types";

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
