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

    expect(screen.getByText("重建下载")).toBeInTheDocument();
    expect(
      screen.getByText("这些文件会在你从 NotebookLM 导出 deck 并返回这里重建之后出现。"),
    ).toBeInTheDocument();
    expect(screen.getByText("最近版本")).toBeInTheDocument();
    expect(screen.getByText("版本 1")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "展示版 clone" })).toHaveLength(2);
    expect(screen.getAllByRole("link", { name: "可编辑重建版" })).toHaveLength(2);
  });
});
