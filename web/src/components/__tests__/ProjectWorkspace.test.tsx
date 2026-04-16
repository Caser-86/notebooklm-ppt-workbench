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

    expect(fetchMock).toHaveBeenCalledTimes(4);
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
      if (url.includes("/sources/history")) {
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
            source_manifest: {
              urls: ["https://example.com/one", "https://example.com/two"],
              file_paths: ["D:/docs/launch-brief.txt"],
              image_paths: ["D:/media/cover.png"],
              audio_paths: ["D:/media/voice.mp3"],
              video_paths: ["D:/media/demo.mp4"],
            },
            insight_summary: "2 urls, 1 file, 1 image, 1 audio, 1 video",
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
    expect(screen.getByLabelText("Source file paths")).toHaveValue("D:/docs/launch-brief.txt");
    expect(screen.getByLabelText("Image file paths")).toHaveValue("D:/media/cover.png");
    expect(screen.getByLabelText("Audio file paths")).toHaveValue("D:/media/voice.mp3");
    expect(screen.getByLabelText("Video file paths")).toHaveValue("D:/media/demo.mp4");
    expect(screen.getByText("2 urls, 1 file, 1 image, 1 audio, 1 video")).toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("saves project detail fields back to the backend", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.includes("/sources/history")) {
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
            source_manifest: {
              urls: ["https://example.com/start"],
              file_paths: ["D:/docs/original.txt"],
              image_paths: ["D:/media/original.png"],
              audio_paths: ["D:/media/original.mp3"],
              video_paths: ["D:/media/original.mp4"],
            },
            insight_summary: "",
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
            source_manifest: {
              urls: ["https://example.com/updated"],
              file_paths: ["D:/docs/updated.txt"],
              image_paths: ["D:/media/updated.png"],
              audio_paths: ["D:/media/updated.mp3"],
              video_paths: ["D:/media/updated.mp4"],
            },
            insight_summary: "",
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
    const sourceFilesInput = screen.getByLabelText("Source file paths");
    expect(sourceFilesInput).toHaveValue("D:/docs/original.txt");
    const imagePathsInput = screen.getByLabelText("Image file paths");
    expect(imagePathsInput).toHaveValue("D:/media/original.png");
    const audioPathsInput = screen.getByLabelText("Audio file paths");
    expect(audioPathsInput).toHaveValue("D:/media/original.mp3");
    const videoPathsInput = screen.getByLabelText("Video file paths");
    expect(videoPathsInput).toHaveValue("D:/media/original.mp4");

    await user.clear(briefInput);
    await user.type(briefInput, "Updated brief");
    await user.clear(promptInput);
    await user.type(promptInput, "Updated prompt");
    await user.clear(sourceLinksInput);
    await user.type(sourceLinksInput, "https://example.com/updated");
    await user.clear(sourceFilesInput);
    await user.type(sourceFilesInput, "D:/docs/updated.txt");
    await user.clear(imagePathsInput);
    await user.type(imagePathsInput, "D:/media/updated.png");
    await user.clear(audioPathsInput);
    await user.type(audioPathsInput, "D:/media/updated.mp3");
    await user.clear(videoPathsInput);
    await user.type(videoPathsInput, "D:/media/updated.mp4");
    await user.click(screen.getByRole("button", { name: "Save project details" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/projects/4",
      expect.objectContaining({
        method: "PUT",
      }),
    );

    vi.unstubAllGlobals();
  });

  it("analyzes source inputs and shows source history", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.includes("/sources/history")) {
        return {
          json: async () => [
            {
              id: 1,
              revision_number: 1,
              source_manifest: {
                urls: ["https://example.com/launch"],
                file_paths: ["D:/docs/launch.txt"],
              },
              insight_summary: "1 url, 1 file, 0 images, 0 audio, 0 video",
            },
          ],
        };
      }
      if (url.endsWith("/projects/5") && (!init || init.method === undefined)) {
        return {
          json: async () => ({
            id: 5,
            title: "Insight deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Current brief",
            prompt_draft: "Current prompt",
            source_manifest: {
              urls: ["https://example.com/launch"],
              file_paths: ["D:/docs/launch.txt"],
              image_paths: ["D:/media/launch.png"],
              audio_paths: ["D:/media/launch.mp3"],
              video_paths: ["D:/media/launch.mp4"],
            },
            insight_summary: "1 url, 1 file, 1 image, 1 audio, 1 video",
          }),
        };
      }
      if (url.includes("/sources") && init?.method === "POST") {
        return {
          json: async () => ({
            project_id: 5,
            revision_number: 2,
            source_manifest: {
              urls: ["https://example.com/launch", "https://example.com/faq"],
              file_paths: ["D:/docs/launch.txt", "D:/docs/faq.txt"],
              image_paths: ["D:/media/launch.png", "D:/media/gallery.png"],
              audio_paths: ["D:/media/launch.mp3"],
              video_paths: ["D:/media/launch.mp4", "D:/media/demo.mp4"],
            },
            insight_summary: "2 urls, 2 files, 2 images, 1 audio, 2 videos",
          }),
        };
      }
      return { json: async () => [] };
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectWorkspace projectId={5} />);

    const sourceLinksInput = await screen.findByDisplayValue("https://example.com/launch");
    const sourceFilesInput = screen.getByLabelText("Source file paths");
    expect(sourceFilesInput).toHaveValue("D:/docs/launch.txt");
    const imagePathsInput = screen.getByLabelText("Image file paths");
    expect(imagePathsInput).toHaveValue("D:/media/launch.png");
    const audioPathsInput = screen.getByLabelText("Audio file paths");
    expect(audioPathsInput).toHaveValue("D:/media/launch.mp3");
    const videoPathsInput = screen.getByLabelText("Video file paths");
    expect(videoPathsInput).toHaveValue("D:/media/launch.mp4");

    await user.clear(sourceLinksInput);
    await user.type(sourceLinksInput, "https://example.com/launch\nhttps://example.com/faq");
    await user.clear(sourceFilesInput);
    await user.type(sourceFilesInput, "D:/docs/launch.txt\nD:/docs/faq.txt");
    await user.clear(imagePathsInput);
    await user.type(imagePathsInput, "D:/media/launch.png\nD:/media/gallery.png");
    await user.clear(audioPathsInput);
    await user.type(audioPathsInput, "D:/media/launch.mp3");
    await user.clear(videoPathsInput);
    await user.type(videoPathsInput, "D:/media/launch.mp4\nD:/media/demo.mp4");
    await user.click(screen.getByRole("button", { name: "Analyze sources" }));

    expect((await screen.findAllByText("2 urls, 2 files, 2 images, 1 audio, 2 videos")).length).toBeGreaterThan(0);
    expect(screen.getByText("Recent source versions")).toBeInTheDocument();
    expect(screen.getAllByText("Revision 2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ URL: https://example.com/faq").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ File: D:/docs/faq.txt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ Image: D:/media/gallery.png").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ Video: D:/media/demo.mp4").length).toBeGreaterThan(0);

    expect(screen.getAllByText("URLs").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Files").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Images").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Audio").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Video").length).toBeGreaterThan(0);
    expect(screen.getAllByText("https://example.com/launch").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/docs/faq.txt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/media/gallery.png").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/media/launch.mp3").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/media/demo.mp4").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Show full sources for Revision 1" }));
    expect(screen.getAllByText("URLs").length).toBeGreaterThan(0);

    vi.unstubAllGlobals();
  });

  it("compares two source revisions side by side", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.includes("/sources/history")) {
        return {
          json: async () => [
            {
              id: 3,
              revision_number: 3,
              source_manifest: {
                urls: ["https://example.com/launch", "https://example.com/roadmap"],
                file_paths: ["D:/docs/launch.txt", "D:/docs/roadmap.txt"],
                image_paths: ["D:/media/cover.png"],
                audio_paths: ["D:/media/voice.mp3"],
                video_paths: ["D:/media/demo.mp4"],
              },
              insight_summary: "2 urls, 2 files, 1 image, 1 audio, 1 video",
            },
            {
              id: 2,
              revision_number: 2,
              source_manifest: {
                urls: ["https://example.com/launch"],
                file_paths: ["D:/docs/launch.txt"],
                image_paths: ["D:/media/cover.png"],
                audio_paths: [],
                video_paths: [],
              },
              insight_summary: "1 url, 1 file, 1 image, 0 audio, 0 video",
            },
            {
              id: 1,
              revision_number: 1,
              source_manifest: {
                urls: ["https://example.com/archive"],
                file_paths: ["D:/docs/archive.txt"],
                image_paths: [],
                audio_paths: [],
                video_paths: [],
              },
              insight_summary: "1 url, 1 file, 0 images, 0 audio, 0 video",
            },
          ],
        };
      }
      if (url.endsWith("/projects/6")) {
        return {
          json: async () => ({
            id: 6,
            title: "Compare deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Compare brief",
            prompt_draft: "Compare prompt",
            source_manifest: {
              urls: ["https://example.com/launch"],
              file_paths: ["D:/docs/launch.txt"],
            },
            insight_summary: "1 url, 1 file, 0 images, 0 audio, 0 video",
          }),
        };
      }
      return { json: async () => [] };
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectWorkspace projectId={6} />);

    expect(await screen.findByText("Compare revisions")).toBeInTheDocument();
    const newerSelect = screen.getByLabelText("Compare newer revision");
    const olderSelect = screen.getByLabelText("Against revision");

    await user.selectOptions(newerSelect, "3");
    await user.selectOptions(olderSelect, "1");

    expect(screen.getByText("Revision 3 snapshot")).toBeInTheDocument();
    expect(screen.getByText("Revision 1 snapshot")).toBeInTheDocument();
    expect(screen.getAllByText("+ URL: https://example.com/launch").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ URL: https://example.com/roadmap").length).toBeGreaterThan(0);
    expect(screen.getAllByText("- URL: https://example.com/archive").length).toBeGreaterThan(0);
    expect(screen.getAllByText("- File: D:/docs/archive.txt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/docs/roadmap.txt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/media/demo.mp4").length).toBeGreaterThan(0);

    vi.unstubAllGlobals();
  });
});
