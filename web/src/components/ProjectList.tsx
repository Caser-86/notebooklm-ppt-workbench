import type { ProjectSummary } from "../lib/types";

type ProjectListProps = {
  projects: ProjectSummary[];
  selectedProjectId: number | null;
  onSelectProject: (projectId: number) => void;
  onCreateProject: () => void;
};

export function ProjectList({ projects, selectedProjectId, onSelectProject, onCreateProject }: ProjectListProps) {
  return (
    <aside className="project-rail">
      <div className="project-rail__brand">
        <p className="eyebrow">NotebookLM PPT</p>
        <h1>Projects</h1>
        <p className="project-rail__tagline">Prepare prompts here, generate in NotebookLM, then come back for editable rebuilds.</p>
      </div>
      <button className="primary-action" type="button" onClick={onCreateProject}>
        New project
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
        <p className="eyebrow">Flow</p>
        <ol>
          <li>Collect sources</li>
          <li>Refine the generation prompt</li>
          <li>Generate in NotebookLM</li>
          <li>Return with the export package</li>
        </ol>
      </div>
    </aside>
  );
}
