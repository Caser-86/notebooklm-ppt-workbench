import { useState } from "react";

import { ArtifactGallery } from "./ArtifactGallery";
import { JobTimeline } from "./JobTimeline";
import { PromptStudio } from "./PromptStudio";
import { SourceIntakePanel } from "./SourceIntakePanel";

export function ProjectWorkspace() {
  const [brief, setBrief] = useState("Create a launch deck");
  const [presetId, setPresetId] = useState("default");
  const [value, setValue] = useState("Start here");

  return (
    <main>
      <h2>Workspace</h2>
      <p>No project selected</p>
      <SourceIntakePanel prompt={brief} onPromptChange={setBrief} />
      <PromptStudio
        presets={[{ id: "default", label: "Default", body: "Start here" }]}
        selectedPresetId={presetId}
        value={value}
        onPresetChange={setPresetId}
        onValueChange={setValue}
      />
      <JobTimeline status="needs_attention" attentionReason="browser_login_required" />
      <ArtifactGallery
        artifacts={[
          { id: "1", label: "Display clone", href: "/display-clone.pptx" },
          { id: "2", label: "Editable rebuild", href: "/editable-rebuild.pptx" },
        ]}
      />
    </main>
  );
}
