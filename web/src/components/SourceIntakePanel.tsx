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
      <label>
        Source links
        <textarea value={sourceLinks} onChange={(event) => onSourceLinksChange(event.target.value)} />
      </label>
      <label>
        Source file paths
        <textarea value={sourceFilePaths} onChange={(event) => onSourceFilePathsChange(event.target.value)} />
      </label>
      <label>
        Image file paths
        <textarea value={imageFilePaths} onChange={(event) => onImageFilePathsChange(event.target.value)} />
      </label>
      <label>
        Audio file paths
        <textarea value={audioFilePaths} onChange={(event) => onAudioFilePathsChange(event.target.value)} />
      </label>
      <label>
        Video file paths
        <textarea value={videoFilePaths} onChange={(event) => onVideoFilePathsChange(event.target.value)} />
      </label>
    </section>
  );
}
