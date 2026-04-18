import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "../../App";

describe("App shell", () => {
  it("renders Chinese by default and can switch to English", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects")) {
        return {
          json: async () => [{ id: 7, title: "History deck", preferred_language: "zh-CN" }],
        };
      }
      if (url.endsWith("/projects/7")) {
        return {
          json: async () => ({
            id: 7,
            title: "History deck",
            preferred_language: "zh-CN",
            preferred_style: "default",
            brief: "History brief",
            prompt_draft: "History prompt",
            source_manifest: { urls: [] },
          }),
        };
      }
      if (url.includes("/rebuilds")) {
        return {
          json: async () => [],
        };
      }
      return {
        json: async () => [],
      };
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    expect(screen.getByText("项目")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "English" })).toBeInTheDocument();
    expect(await screen.findByText("History deck")).toBeInTheDocument();
    expect(screen.getAllByText("工作台").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "English" }));

    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getAllByText("Workspace").length).toBeGreaterThan(0);

    vi.unstubAllGlobals();
  });
});
