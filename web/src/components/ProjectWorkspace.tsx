import { useState } from "react";

import { PromptStudio } from "./PromptStudio";
import { SourceIntakePanel } from "./SourceIntakePanel";

export function ProjectWorkspace() {
  const [brief, setBrief] = useState("Create a launch deck");
  const [presetId, setPresetId] = useState("default");
  const [value, setValue] = useState("Start here");

  return (
    <main>
      <h2>Workspace</h2>
      <SourceIntakePanel prompt={brief} onPromptChange={setBrief} />
      <PromptStudio
        presets={[{ id: "default", label: "Default", body: "Start here" }]}
        selectedPresetId={presetId}
        value={value}
        onPresetChange={setPresetId}
        onValueChange={setValue}
      />
    </main>
  );
}
