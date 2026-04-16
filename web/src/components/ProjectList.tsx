export function ProjectList() {
  return (
    <aside className="project-rail">
      <div className="project-rail__brand">
        <p className="eyebrow">NotebookLM PPT</p>
        <h1>Projects</h1>
        <p className="project-rail__tagline">Prepare prompts here, generate in NotebookLM, then come back for editable rebuilds.</p>
      </div>
      <button className="primary-action" type="button">
        New project
      </button>
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
