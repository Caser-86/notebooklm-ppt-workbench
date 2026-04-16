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
      />,
    );

    expect(screen.getByRole("link", { name: "Display clone" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Editable rebuild" })).toBeInTheDocument();
  });
});
