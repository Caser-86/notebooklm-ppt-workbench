export type PromptPreset = {
  id: string;
  label: string;
  body: string;
};

export type LaunchJobResponse = {
  project_id: number;
  status: "ready_to_generate";
  prompt: string;
};
