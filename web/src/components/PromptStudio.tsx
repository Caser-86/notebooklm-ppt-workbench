import { useEffect, useState } from "react";

type Preset = { id: string; label: string; body: string };

type PromptStudioProps = {
  presets: Preset[];
  selectedPresetId: string;
  value: string;
  onPresetChange: (presetId: string) => void;
  onValueChange: (value: string) => void;
};

export function PromptStudio(props: PromptStudioProps) {
  const [draftValue, setDraftValue] = useState(props.value);

  useEffect(() => {
    setDraftValue(props.value);
  }, [props.value]);

  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">Prompt studio</p>
        <h3>Shape the deck before handoff</h3>
        <p>Use presets to get a strong first draft, then tighten tone and structure before opening NotebookLM.</p>
      </div>
      <label>
        Preset
        <select value={props.selectedPresetId} onChange={(event) => props.onPresetChange(event.target.value)}>
          {props.presets.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Generation prompt
        <textarea
          value={draftValue}
          onChange={(event) => {
            setDraftValue(event.target.value);
            props.onValueChange(event.target.value);
          }}
        />
      </label>
    </section>
  );
}
