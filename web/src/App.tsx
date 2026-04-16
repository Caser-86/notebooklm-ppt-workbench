import { ProjectList } from "./components/ProjectList";
import { ProjectWorkspace } from "./components/ProjectWorkspace";

export default function App() {
  return (
    <div className="app-shell">
      <ProjectList />
      <ProjectWorkspace />
    </div>
  );
}
