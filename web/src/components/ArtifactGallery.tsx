type Artifact = { id: string; label: string; href: string };

export function ArtifactGallery({ artifacts }: { artifacts: Artifact[] }) {
  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">Outputs</p>
        <h3>Rebuilt downloads</h3>
        <p>These files appear after you export the deck from NotebookLM and return here for rebuild.</p>
      </div>
      {artifacts.length > 0 ? (
        <ul>
          {artifacts.map((artifact) => (
            <li key={artifact.id}>
              <a href={artifact.href}>{artifact.label}</a>
            </li>
          ))}
        </ul>
      ) : (
        <p>No rebuilt files yet. Upload the exported NotebookLM slides and mark the export as ready.</p>
      )}
    </section>
  );
}
