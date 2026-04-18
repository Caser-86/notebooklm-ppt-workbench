type Artifact = { id: string; label: string; href: string };
type RebuildVersion = { id: string | number; version_number: number; artifacts: Artifact[] };

import { useI18n } from "../lib/i18n";

export function ArtifactGallery({ artifacts, rebuilds = [] }: { artifacts: Artifact[]; rebuilds?: RebuildVersion[] }) {
  const { messages } = useI18n();
  const getLabel = (artifact: Artifact) =>
    messages.artifactGallery.artifactLabels[artifact.id]
    ?? messages.artifactGallery.artifactLabels[artifact.label.toLowerCase().replace(/\s+/g, "-")]
    ?? artifact.label;

  return (
    <section className="workspace-section">
      <div className="section-copy">
        <p className="eyebrow">{messages.artifactGallery.eyebrow}</p>
        <h3>{messages.artifactGallery.title}</h3>
        <p>{messages.artifactGallery.description}</p>
      </div>
      {artifacts.length > 0 ? (
        <ul>
          {artifacts.map((artifact) => (
            <li key={artifact.id}>
              <a href={artifact.href}>{getLabel(artifact)}</a>
            </li>
          ))}
        </ul>
      ) : (
        <p>{messages.artifactGallery.empty}</p>
      )}
      {rebuilds.length > 0 ? (
        <div className="rebuild-history">
          <h4>{messages.artifactGallery.recentVersions}</h4>
          <ul>
            {rebuilds.map((rebuild) => (
              <li key={rebuild.id}>
                <span>{messages.artifactGallery.versionLabel(rebuild.version_number)}</span>
                {rebuild.artifacts.map((artifact) => (
                  <a key={artifact.id} href={artifact.href}>
                    {getLabel(artifact)}
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
