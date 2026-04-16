type Artifact = { id: string; label: string; href: string };

export function ArtifactGallery({ artifacts }: { artifacts: Artifact[] }) {
  return (
    <section>
      <h3>Artifacts</h3>
      <ul>
        {artifacts.map((artifact) => (
          <li key={artifact.id}>
            <a href={artifact.href}>{artifact.label}</a>
          </li>
        ))}
      </ul>
    </section>
  );
}
