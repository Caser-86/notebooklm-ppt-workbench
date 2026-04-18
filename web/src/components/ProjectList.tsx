import type { ProjectSummary } from "../lib/types";
import { useI18n } from "../lib/i18n";

type ProjectListProps = {
  projects: ProjectSummary[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onCreateProject: () => void;
};

export function ProjectList({ projects, selectedProjectId, onSelectProject, onCreateProject }: ProjectListProps) {
  const { locale, setLocale, messages } = useI18n();

  return (
    <aside className="project-rail">
      <div className="project-rail__brand">
        <p className="eyebrow">NotebookLM PPT</p>
        <h1>{messages.projectRail.title}</h1>
        <p className="project-rail__tagline">{messages.projectRail.tagline}</p>
      </div>
      <div className="handoff-actions">
        <button
          className={locale === "zh-CN" ? "primary-action" : "secondary-action"}
          type="button"
          onClick={() => setLocale("zh-CN")}
        >
          中文
        </button>
        <button
          className={locale === "en" ? "primary-action" : "secondary-action"}
          type="button"
          onClick={() => setLocale("en")}
        >
          English
        </button>
      </div>
      <button className="primary-action" type="button" onClick={onCreateProject}>
        {messages.projectRail.newProject}
      </button>
      <div className="project-rail__projects">
        {projects.map((project) => (
          <button
            key={project.id}
            className={project.id == selectedProjectId ? "project-chip project-chip--active" : "project-chip"}
            type="button"
            onClick={() => onSelectProject(project.id)}
          >
            {project.title}
          </button>
        ))}
      </div>
      <div className="project-rail__flow">
        <p className="eyebrow">{messages.projectRail.flow}</p>
        <ol>
          {messages.projectRail.flowSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>
    </aside>
  );
}
