import { useEffect, useState } from "react";
import { useI18n } from "../lib/i18n";

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
  const { messages } = useI18n();

  useEffect(() => {
    setDraftValue(props.value);
  }, [props.value]);

  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">{messages.promptStudio.eyebrow}</p>
        <h3>{messages.promptStudio.title}</h3>
        <p>{messages.promptStudio.description}</p>
      </div>
      <label>
        {messages.promptStudio.preset}
        <select value={props.selectedPresetId} onChange={(event) => props.onPresetChange(event.target.value)}>
          {props.presets.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        {messages.promptStudio.prompt}
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
