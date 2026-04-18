import { render, screen } from "@testing-library/react";
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
          { id: 1, job_type: "import_pptx", status: "succeeded" },
          { id: 2, job_type: "analyze_sources", status: "running" },
        ]}
      />,
    );

    expect(screen.getByText("最近任务")).toBeInTheDocument();
    expect(screen.getByText("import_pptx")).toBeInTheDocument();
    expect(screen.getByText("analyze_sources")).toBeInTheDocument();
  });
});
