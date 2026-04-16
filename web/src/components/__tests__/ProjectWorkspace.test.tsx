import { render, screen } from "@testing-library/react";
import { ProjectWorkspace } from "../ProjectWorkspace";

describe("ProjectWorkspace", () => {
  it("shows the manual NotebookLM handoff steps", () => {
    render(<ProjectWorkspace />);

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
});
