import { render, screen } from "@testing-library/react";
import { ArtifactGallery } from "../ArtifactGallery";

describe("ArtifactGallery", () => {
  it("shows both the display clone and editable rebuild downloads", () => {
    render(
      <ArtifactGallery
        artifacts={[
          { id: "1", label: "Display clone", href: "/display-clone.pptx" },
          { id: "2", label: "Editable rebuild", href: "/editable-rebuild.pptx" },
        ]}
        rebuilds={[
          {
            id: "history-1",
            version_number: 1,
            artifacts: [
              { id: "1", label: "Display clone", href: "/display-clone.pptx" },
              { id: "2", label: "Editable rebuild", href: "/editable-rebuild.pptx" },
            ],
          },
        ]}
      />,
    );

    expect(screen.getByText("Rebuilt downloads")).toBeInTheDocument();
    expect(
      screen.getByText("These files appear after you export the deck from NotebookLM and return here for rebuild."),
    ).toBeInTheDocument();
    expect(screen.getByText("Recent versions")).toBeInTheDocument();
    expect(screen.getByText("Version 1")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Display clone" })).toHaveLength(2);
    expect(screen.getAllByRole("link", { name: "Editable rebuild" })).toHaveLength(2);
  });
});
