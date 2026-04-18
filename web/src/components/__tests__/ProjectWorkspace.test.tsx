import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ProjectWorkspace } from "../ProjectWorkspace";

describe("ProjectWorkspace", () => {
  it("shows the manual NotebookLM handoff steps", () => {
    render(<ProjectWorkspace projectId={null} />);

    expect(screen.getByText("半自动模式")).toBeInTheDocument();
    expect(
      screen.getByText("这个工作台负责准备提示词并重建导出的 deck，而生成与导出仍在 NotebookLM 中完成。"),
    ).toBeInTheDocument();
    expect(screen.getByText("继续到 NotebookLM")).toBeInTheDocument();
    expect(screen.getByText("把提示词粘贴到 NotebookLM 里，在那里生成 deck。")).toBeInTheDocument();
    expect(screen.getByText("从 NotebookLM 导出 deck 后，再回到这里做重建和下载。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "打开 NotebookLM" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "标记导出已就绪" })).toBeInTheDocument();
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
      if (url.includes("/imports")) {
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

    const slideInput = screen.getByLabelText("导出的 slide 图片");
    const file = new File(["slide"], "slide-1.png", { type: "image/png" });

    await user.upload(slideInput, file);
    await user.click(screen.getByRole("button", { name: "标记导出已就绪" }));

    expect(fetchMock).toHaveBeenCalledTimes(5);
    const displayLinks = await screen.findAllByRole("link", { name: "展示版 clone" });
    const editableLinks = screen.getAllByRole("link", { name: "可编辑重建版" });

    expect(displayLinks).toHaveLength(2);
    expect(editableLinks).toHaveLength(2);
    expect(displayLinks[0]).toHaveAttribute("href", "http://127.0.0.1:8000/artifacts/1/rebuild-001/display-clone.pptx");
    expect(editableLinks[0]).toHaveAttribute("href", "http://127.0.0.1:8000/artifacts/1/rebuild-001/editable-rebuild.pptx");

    vi.unstubAllGlobals();
  });

  it("uploads a pptx import and lists imported revisions", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.includes("/sources/history")) {
        return { json: async () => [] };
      }
      if (url.includes("/projects/7/imports") && init?.method === "POST") {
        return {
          json: async () => ({
            id: 11,
            project_id: 7,
            source_type: "internal_generated",
            filename: "demo.pptx",
            status: "ready",
            page_count: 1,
            error_message: "",
            object_summary: {
              imported_text: 2,
              imported_image: 1,
              imported_table: 0,
              imported_icon_card: 0,
            },
            slide_assets: [
              {
                id: 1,
                slide_index: 1,
                preview_image_path: "/artifacts/7/imports/import-11/slide-1.png",
                text_dump: "Editable rebuild",
                structure_json_path: "",
                object_summary: {
                  imported_text: 2,
                  imported_image: 1,
                  imported_table: 0,
                  imported_icon_card: 0,
                },
              },
              {
                id: 2,
                slide_index: 2,
                preview_image_path: "/artifacts/7/imports/import-11/slide-2.png",
                text_dump: "NotebookLM export",
                structure_json_path: "",
                object_summary: {
                  imported_text: 1,
                  imported_image: 0,
                  imported_table: 1,
                  imported_icon_card: 0,
                },
              },
            ],
          }),
        };
      }
      if (url.includes("/projects/7/imports")) {
        return { json: async () => [] };
      }
      if (url.endsWith("/projects/7")) {
        return {
          json: async () => ({
            id: 7,
            title: "Import deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Import brief",
            prompt_draft: "Import prompt",
            source_manifest: { urls: [] },
            insight_summary: "",
          }),
        };
      }
      return { json: async () => [] };
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectWorkspace projectId={7} />);

    expect((await screen.findAllByText("导入 PPTX")).length).toBeGreaterThan(0);
    expect(screen.getByText("已导入的 PPTX 版本")).toBeInTheDocument();

    const pptxInput = screen.getByLabelText("本地 PPTX 文件");
    const file = new File(["pptx"], "demo.pptx", {
      type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    });

    await user.upload(pptxInput, file);
    await user.click(screen.getByRole("button", { name: "导入 PPTX" }));

    expect(await screen.findByText("demo.pptx")).toBeInTheDocument();
    expect(screen.getByText("来源类型: internal_generated")).toBeInTheDocument();
    expect(screen.getByText("页数: 1")).toBeInTheDocument();
    expect(screen.getByText("已导入页面")).toBeInTheDocument();
    expect(screen.getByText("当前预览：第 1 页")).toBeInTheDocument();
    expect(screen.getAllByRole("img", { name: "第 1 页预览" }).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Text: 2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Images: 1").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "从导入版本重建" })).toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("defaults to the first imported slide and updates when another slide is selected", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.includes("/sources/history")) {
        return { json: async () => [] };
      }
      if (url.includes("/projects/8/imports")) {
        return {
          json: async () => [
            {
              id: 12,
              project_id: 8,
              source_type: "generic_pptx",
              filename: "preview.pptx",
              status: "ready",
              page_count: 2,
              error_message: "",
              object_summary: {
                imported_text: 3,
                imported_image: 1,
                imported_table: 1,
                imported_icon_card: 0,
              },
              slide_assets: [
                {
                  id: 1,
                  slide_index: 1,
                  preview_image_path: "http://127.0.0.1:8000/artifacts/8/imports/import-12/slide-1.png",
                  text_dump: "Slide 1",
                  structure_json_path: "",
                  object_summary: {
                    imported_text: 2,
                    imported_image: 1,
                    imported_table: 0,
                    imported_icon_card: 0,
                  },
                },
                {
                  id: 2,
                  slide_index: 2,
                  preview_image_path: "http://127.0.0.1:8000/artifacts/8/imports/import-12/slide-2.png",
                  text_dump: "Slide 2",
                  structure_json_path: "",
                  object_summary: {
                    imported_text: 1,
                    imported_image: 0,
                    imported_table: 1,
                    imported_icon_card: 0,
                  },
                },
              ],
            },
          ],
        };
      }
      if (url.endsWith("/projects/8")) {
        return {
          json: async () => ({
            id: 8,
            title: "Preview deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "Preview brief",
            prompt_draft: "Preview prompt",
            source_manifest: { urls: [] },
            insight_summary: "",
          }),
        };
      }
      return { json: async () => [] };
    });

    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectWorkspace projectId={8} />);

    expect(await screen.findByText("第 1 页")).toBeInTheDocument();
    expect(screen.getByText("当前预览：第 1 页")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "第 2 页预览 第 2 页" }));
    expect(screen.getByText("当前预览：第 2 页")).toBeInTheDocument();
    expect(screen.getAllByText("Tables: 1").length).toBeGreaterThan(0);

    vi.unstubAllGlobals();
  });

  it("loads project detail fields from the backend", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.includes("/imports")) {
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
    expect(screen.getByLabelText("来源链接")).toHaveValue("https://example.com/one\nhttps://example.com/two");
    expect(screen.getByLabelText("来源文件路径")).toHaveValue("D:/docs/launch-brief.txt");
    expect(screen.getByLabelText("图片文件路径")).toHaveValue("D:/media/cover.png");
    expect(screen.getByLabelText("音频文件路径")).toHaveValue("D:/media/voice.mp3");
    expect(screen.getByLabelText("视频文件路径")).toHaveValue("D:/media/demo.mp4");
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
      if (url.includes("/imports")) {
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
    const sourceFilesInput = screen.getByLabelText("来源文件路径");
    expect(sourceFilesInput).toHaveValue("D:/docs/original.txt");
    const imagePathsInput = screen.getByLabelText("图片文件路径");
    expect(imagePathsInput).toHaveValue("D:/media/original.png");
    const audioPathsInput = screen.getByLabelText("音频文件路径");
    expect(audioPathsInput).toHaveValue("D:/media/original.mp3");
    const videoPathsInput = screen.getByLabelText("视频文件路径");
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
    await user.click(screen.getByRole("button", { name: "保存项目详情" }));

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
      if (url.includes("/imports")) {
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
    const sourceFilesInput = screen.getByLabelText("来源文件路径");
    expect(sourceFilesInput).toHaveValue("D:/docs/launch.txt");
    const imagePathsInput = screen.getByLabelText("图片文件路径");
    expect(imagePathsInput).toHaveValue("D:/media/launch.png");
    const audioPathsInput = screen.getByLabelText("音频文件路径");
    expect(audioPathsInput).toHaveValue("D:/media/launch.mp3");
    const videoPathsInput = screen.getByLabelText("视频文件路径");
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
    await user.click(screen.getByRole("button", { name: "分析来源" }));

    expect((await screen.findAllByText("2 urls, 2 files, 2 images, 1 audio, 2 videos")).length).toBeGreaterThan(0);
    expect(screen.getByText("最近的来源版本")).toBeInTheDocument();
    expect(screen.getAllByText("版本 2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ 链接: https://example.com/faq").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ 文件: D:/docs/faq.txt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ 图片: D:/media/gallery.png").length).toBeGreaterThan(0);
    expect(screen.getAllByText("+ 视频: D:/media/demo.mp4").length).toBeGreaterThan(0);

    expect(screen.getAllByText("链接").length).toBeGreaterThan(0);
    expect(screen.getAllByText("文件").length).toBeGreaterThan(0);
    expect(screen.getAllByText("图片").length).toBeGreaterThan(0);
    expect(screen.getAllByText("音频").length).toBeGreaterThan(0);
    expect(screen.getAllByText("视频").length).toBeGreaterThan(0);
    expect(screen.getAllByText("https://example.com/launch").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/docs/faq.txt").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/media/gallery.png").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/media/launch.mp3").length).toBeGreaterThan(0);
    expect(screen.getAllByText("D:/media/demo.mp4").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "展开版本 1 全部来源" }));
    expect(screen.getAllByText("链接").length).toBeGreaterThan(0);

    vi.unstubAllGlobals();
  });

  it("compares two source revisions side by side", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/rebuilds")) {
        return { json: async () => [] };
      }
      if (url.includes("/imports")) {
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

    expect(await screen.findByText("比较版本")).toBeInTheDocument();
    const newerSelect = screen.getByLabelText("比较较新版本");
    const olderSelect = screen.getByLabelText("对比版本");

    await user.selectOptions(newerSelect, "3");
    await user.selectOptions(olderSelect, "2");

    const comparePanel = screen.getByText("比较版本").closest(".source-compare-panel") as HTMLElement;
    const compareQueries = within(comparePanel);

    expect(compareQueries.getByText("版本 3 快照")).toBeInTheDocument();
    expect(compareQueries.getByText("版本 2 快照")).toBeInTheDocument();
    expect(compareQueries.getByText("版本 3 新增")).toBeInTheDocument();
    expect(compareQueries.getByText("相对版本 2 移除")).toBeInTheDocument();
    expect(compareQueries.getByText("+ 链接: https://example.com/roadmap")).toBeInTheDocument();
    expect(compareQueries.getByText("这次对比没有移除来源。")).toBeInTheDocument();
    expect(compareQueries.getAllByText("D:/docs/roadmap.txt").length).toBeGreaterThan(0);
    expect(compareQueries.getAllByText("D:/media/demo.mp4").length).toBeGreaterThan(0);
    expect(compareQueries.getAllByText("D:/media/cover.png").length).toBeGreaterThan(0);

    await user.click(compareQueries.getByRole("button", { name: "图片" }));

    expect(compareQueries.queryByText("+ 链接: https://example.com/roadmap")).not.toBeInTheDocument();
    expect(compareQueries.queryByText("D:/docs/roadmap.txt")).not.toBeInTheDocument();
    expect(compareQueries.getByText("这次对比没有新增来源。")).toBeInTheDocument();
    expect(compareQueries.getAllByText("D:/media/cover.png").length).toBeGreaterThan(0);

    await user.click(compareQueries.getByRole("checkbox", { name: "只看变化项" }));

    expect(compareQueries.queryByText("D:/media/cover.png")).not.toBeInTheDocument();
    expect(compareQueries.getByText("这次对比没有新增来源。")).toBeInTheDocument();
    expect(compareQueries.getByText("这次对比没有移除来源。")).toBeInTheDocument();

    await user.click(compareQueries.getByRole("button", { name: "音频" }));
    await user.click(compareQueries.getByRole("button", { name: "将比较摘要加入提示词" }));

    const promptInput = screen.getByLabelText("生成提示词");
    expect((promptInput as HTMLTextAreaElement).value).toContain("Compare prompt");
    expect((promptInput as HTMLTextAreaElement).value).toContain("来源比较摘要");
    expect((promptInput as HTMLTextAreaElement).value).toContain("筛选：音频");
    expect((promptInput as HTMLTextAreaElement).value).toContain("版本 3 新增");
    expect((promptInput as HTMLTextAreaElement).value).toContain("+ 音频: D:/media/voice.mp3");
    expect((promptInput as HTMLTextAreaElement).value).not.toContain("+ 链接: https://example.com/roadmap");

    vi.unstubAllGlobals();
  });
});
