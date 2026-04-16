type SourceIntakePanelProps = {
  prompt: string;
  onPromptChange: (value: string) => void;
};

export function SourceIntakePanel({ prompt, onPromptChange }: SourceIntakePanelProps) {
  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">Inputs</p>
        <h3>Source intake</h3>
        <p>Drop in the brief, links, and supporting material you want this deck to follow.</p>
      </div>
      <label>
        Project brief
        <textarea value={prompt} onChange={(event) => onPromptChange(event.target.value)} />
      </label>
    </section>
  );
}
