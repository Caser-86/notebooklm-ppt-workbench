import { useEffect, useState, useTransition } from "react";

import { ProjectList } from "./components/ProjectList";
import { ProjectWorkspace } from "./components/ProjectWorkspace";
import { I18nProvider, useI18n } from "./lib/i18n";
import { createProject, fetchProjects } from "./lib/api";
import type { ProjectSummary } from "./lib/types";

function AppContent() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [, startTransition] = useTransition();
  const { locale } = useI18n();

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
          const prefix = locale === "zh-CN" ? "项目" : "Project";
          const newProject = await createProject(`${prefix} ${projects.length + 1}`);
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

export default function App() {
  return (
    <I18nProvider>
      <AppContent />
    </I18nProvider>
  );
}
