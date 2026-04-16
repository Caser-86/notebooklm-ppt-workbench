import { ProjectList } from "./components/ProjectList";

export default function App() {
  return (
    <div className="app-shell">
      <ProjectList />
      <main>
        <h2>No project selected</h2>
      </main>
    </div>
  );
}
