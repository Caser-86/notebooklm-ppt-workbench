import { useEffect, useState, useTransition } from "react";

import { ProjectList } from "./components/ProjectList";
import { ProjectWorkspace } from "./components/ProjectWorkspace";
import { createProject, fetchProjects } from "./lib/api";
import type { ProjectSummary } from "./lib/types";

export default function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [, startTransition] = useTransition();

  useEffect(() => {
    let isMounted = true;
    void fetchProjects().then((loadedProjects) => {
      if (!isMounted) {
        return;
      }
      startTransition(() => {
        setProjects(loadedProjects);
        setSelectedProjectId((current) => current ?? loadedProjects[0]?.id ?? null);
      });
    });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <ProjectList
        projects={projects}
        selectedProjectId={selectedProjectId}
        onSelectProject={setSelectedProjectId}
        onCreateProject={async () => {
          const newProject = await createProject(`Project ${projects.length + 1}`);
          startTransition(() => {
            setProjects((current) => [newProject, ...current]);
            setSelectedProjectId(newProject.id);
          });
        }}
      />
      <ProjectWorkspace projectId={selectedProjectId} />
    </div>
  );
}
