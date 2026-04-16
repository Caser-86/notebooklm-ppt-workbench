import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import App from "../../App";

describe("App shell", () => {
  it("renders the project list and empty workspace state", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/projects")) {
        return {
          json: async () => [{ id: 7, title: "History deck", preferred_language: "zh-CN" }],
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

    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(await screen.findByText("History deck")).toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
