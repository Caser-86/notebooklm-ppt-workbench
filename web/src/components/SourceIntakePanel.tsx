type SourceIntakePanelProps = {
  prompt: string;
  onPromptChange: (value: string) => void;
  sourceLinks: string;
  onSourceLinksChange: (value: string) => void;
  sourceFilePaths: string;
  onSourceFilePathsChange: (value: string) => void;
  imageFilePaths: string;
  onImageFilePathsChange: (value: string) => void;
  audioFilePaths: string;
  onAudioFilePathsChange: (value: string) => void;
  videoFilePaths: string;
  onVideoFilePathsChange: (value: string) => void;
};

import { useI18n } from "../lib/i18n";

export function SourceIntakePanel({
  prompt,
  onPromptChange,
  sourceLinks,
  onSourceLinksChange,
  sourceFilePaths,
  onSourceFilePathsChange,
  imageFilePaths,
  onImageFilePathsChange,
  audioFilePaths,
  onAudioFilePathsChange,
  videoFilePaths,
  onVideoFilePathsChange,
}: SourceIntakePanelProps) {
  const { messages } = useI18n();

  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">{messages.sourceIntake.eyebrow}</p>
        <h3>{messages.sourceIntake.title}</h3>
        <p>{messages.sourceIntake.description}</p>
      </div>
      <label>
        {messages.sourceIntake.projectBrief}
        <textarea value={prompt} onChange={(event) => onPromptChange(event.target.value)} />
      </label>
      <label>
        {messages.sourceIntake.sourceLinks}
        <textarea value={sourceLinks} onChange={(event) => onSourceLinksChange(event.target.value)} />
      </label>
      <label>
        {messages.sourceIntake.sourceFilePaths}
        <textarea value={sourceFilePaths} onChange={(event) => onSourceFilePathsChange(event.target.value)} />
      </label>
      <label>
        {messages.sourceIntake.imageFilePaths}
        <textarea value={imageFilePaths} onChange={(event) => onImageFilePathsChange(event.target.value)} />
      </label>
      <label>
        {messages.sourceIntake.audioFilePaths}
        <textarea value={audioFilePaths} onChange={(event) => onAudioFilePathsChange(event.target.value)} />
      </label>
      <label>
        {messages.sourceIntake.videoFilePaths}
        <textarea value={videoFilePaths} onChange={(event) => onVideoFilePathsChange(event.target.value)} />
      </label>
    </section>
  );
}
