type Artifact = { id: string; label: string; href: string };
type RebuildVersion = { id: string | number; version_number: number; artifacts: Artifact[] };

export function ArtifactGallery({ artifacts, rebuilds = [] }: { artifacts: Artifact[]; rebuilds?: RebuildVersion[] }) {
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
      {rebuilds.length > 0 ? (
        <div className="rebuild-history">
          <h4>Recent versions</h4>
          <ul>
            {rebuilds.map((rebuild) => (
              <li key={rebuild.id}>
                <span>{`Version ${rebuild.version_number}`}</span>
                {rebuild.artifacts.map((artifact) => (
                  <a key={artifact.id} href={artifact.href}>
                    {artifact.label}
                  </a>
                ))}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
