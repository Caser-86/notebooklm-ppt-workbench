type SourceIntakePanelProps = {
  prompt: string;
  onPromptChange: (value: string) => void;
};

export function SourceIntakePanel({ prompt, onPromptChange }: SourceIntakePanelProps) {
  return (
    <section>
      <label>
        Project brief
        <textarea value={prompt} onChange={(event) => onPromptChange(event.target.value)} />
      </label>
    </section>
  );
}
