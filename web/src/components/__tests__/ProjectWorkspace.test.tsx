import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ProjectWorkspace } from "../ProjectWorkspace";

describe("ProjectWorkspace", () => {
  it("shows the manual NotebookLM handoff steps", () => {
    render(<ProjectWorkspace projectId={null} />);

    expect(screen.getByText("Semi-automatic mode")).toBeInTheDocument();
    expect(
      screen.getByText("This workspace prepares the prompt and rebuilds the exported deck, while you generate and export inside NotebookLM."),
    ).toBeInTheDocument();
    expect(screen.getByText("Continue in NotebookLM")).toBeInTheDocument();
    expect(screen.getByText("Paste the prompt into NotebookLM and generate the deck there.")).toBeInTheDocument();
    expect(screen.getByText("Export the deck from NotebookLM, then return here for rebuild and download.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open NotebookLM" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark export ready" })).toBeInTheDocument();
  });

  it("uploads exported files and shows rebuilt downloads from the agent response", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return {
          json: async () => [],
        };
      }
      return {
        json: async () => ({
          version_number: 1,
          artifacts: [
            { id: "display-clone", label: "Display clone", href: "/artifacts/1/rebuild-001/display-clone.pptx" },
            { id: "editable-rebuild", label: "Editable rebuild", href: "/artifacts/1/rebuild-001/editable-rebuild.pptx" },
          ],
        }),
      };
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectWorkspace projectId={1} />);

    const slideInput = screen.getByLabelText("Exported slide images");
    const file = new File(["slide"], "slide-1.png", { type: "image/png" });

    await user.upload(slideInput, file);
    await user.click(screen.getByRole("button", { name: "Mark export ready" }));

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const displayLinks = await screen.findAllByRole("link", { name: "Display clone" });
    const editableLinks = screen.getAllByRole("link", { name: "Editable rebuild" });

    expect(displayLinks).toHaveLength(2);
    expect(editableLinks).toHaveLength(2);
    expect(displayLinks[0]).toHaveAttribute("href", "http://127.0.0.1:8000/artifacts/1/rebuild-001/display-clone.pptx");
    expect(editableLinks[0]).toHaveAttribute("href", "http://127.0.0.1:8000/artifacts/1/rebuild-001/editable-rebuild.pptx");

    vi.unstubAllGlobals();
  });
});
