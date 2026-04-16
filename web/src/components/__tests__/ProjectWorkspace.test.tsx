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
      if (url.endsWith("/projects/1")) {
        return {
          json: async () => ({
            id: 1,
            title: "Project 1",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Create a launch deck",
            prompt_draft: "Start here",
            source_manifest: { urls: [] },
          }),
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

    expect(fetchMock).toHaveBeenCalledTimes(3);
    const displayLinks = await screen.findAllByRole("link", { name: "Display clone" });
    const editableLinks = screen.getAllByRole("link", { name: "Editable rebuild" });

    expect(displayLinks).toHaveLength(2);
    expect(editableLinks).toHaveLength(2);
    expect(displayLinks[0]).toHaveAttribute("href", "http://127.0.0.1:8000/artifacts/1/rebuild-001/display-clone.pptx");
    expect(editableLinks[0]).toHaveAttribute("href", "http://127.0.0.1:8000/artifacts/1/rebuild-001/editable-rebuild.pptx");

    vi.unstubAllGlobals();
  });

  it("loads project detail fields from the backend", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.endsWith("/projects/3")) {
        return {
          json: async () => ({
            id: 3,
            title: "Growth deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Loaded brief",
            prompt_draft: "Loaded prompt",
            source_manifest: { urls: ["https://example.com/one", "https://example.com/two"] },
          }),
        };
      }
      return { json: async () => [] };
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectWorkspace projectId={3} />);

    expect(await screen.findByDisplayValue("Loaded brief")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Loaded prompt")).toBeInTheDocument();
    expect(screen.getByLabelText("Source links")).toHaveValue("https://example.com/one\nhttps://example.com/two");

    vi.unstubAllGlobals();
  });

  it("saves project detail fields back to the backend", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.endsWith("/projects/4") && (!init || init.method === undefined)) {
        return {
          json: async () => ({
            id: 4,
            title: "Ops deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Original brief",
            prompt_draft: "Original prompt",
            source_manifest: { urls: ["https://example.com/start"] },
          }),
        };
      }
      if (url.endsWith("/projects/4") && init?.method === "PUT") {
        return {
          json: async () => ({
            id: 4,
            title: "Ops deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Updated brief",
            prompt_draft: "Updated prompt",
            source_manifest: { urls: ["https://example.com/updated"] },
          }),
        };
      }
      return { json: async () => [] };
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectWorkspace projectId={4} />);

    const briefInput = await screen.findByDisplayValue("Original brief");
    const promptInput = screen.getByDisplayValue("Original prompt");
    const sourceLinksInput = screen.getByDisplayValue("https://example.com/start");

    await user.clear(briefInput);
    await user.type(briefInput, "Updated brief");
    await user.clear(promptInput);
    await user.type(promptInput, "Updated prompt");
    await user.clear(sourceLinksInput);
    await user.type(sourceLinksInput, "https://example.com/updated");
    await user.click(screen.getByRole("button", { name: "Save project details" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/projects/4",
      expect.objectContaining({
        method: "PUT",
      }),
    );

    vi.unstubAllGlobals();
  });
});
