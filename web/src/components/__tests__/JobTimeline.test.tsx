import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { JobTimeline } from "../JobTimeline";

describe("JobTimeline", () => {
  it("shows a resume action when the job needs attention", () => {
    render(<JobTimeline status="needs_attention" attentionReason="browser_login_required" />);

    expect(screen.getByText("需要你处理")).toBeInTheDocument();
    expect(screen.getByText("请登录 Google，并在 NotebookLM 中完成这一步。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "我已在 NotebookLM 中完成" })).toBeInTheDocument();
  });

  it("shows recent jobs when provided", () => {
    render(
      <JobTimeline
        status="running"
        jobs={[
          { id: 1, job_type: "import_pptx", status: "succeeded", created_at: "2026-04-19T01:00:00Z", error_message: "" },
          { id: 2, job_type: "analyze_sources", status: "running", created_at: "2026-04-19T01:01:00Z", error_message: "" },
        ]}
      />,
    );

    expect(screen.getByText("最近任务")).toBeInTheDocument();
    expect(screen.getByText("import_pptx")).toBeInTheDocument();
    expect(screen.getByText("analyze_sources")).toBeInTheDocument();
  });

  it("shows failed job details and calls retry", async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();

    render(
      <JobTimeline
        status="failed"
        jobs={[
          {
            id: 3,
            job_type: "rebuild_import",
            status: "failed",
            created_at: "2026-04-19T01:02:00Z",
            error_message: "Import pipeline failed",
          },
        ]}
        onRetry={onRetry}
      />,
    );

    expect(screen.getByText(/Import pipeline failed/, { selector: "p" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(onRetry).toHaveBeenCalledWith(3);
  });
});
