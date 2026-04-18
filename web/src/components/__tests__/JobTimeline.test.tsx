import { render, screen } from "@testing-library/react";
import { JobTimeline } from "../JobTimeline";

describe("JobTimeline", () => {
  it("shows a resume action when the job needs attention", () => {
    render(<JobTimeline status="needs_attention" attentionReason="browser_login_required" />);

    expect(screen.getByText("需要你处理")).toBeInTheDocument();
    expect(screen.getByText("请登录 Google，并在 NotebookLM 中完成这一步。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "我已在 NotebookLM 中完成" })).toBeInTheDocument();
  });
});
