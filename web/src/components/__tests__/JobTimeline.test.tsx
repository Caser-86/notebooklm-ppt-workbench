import { render, screen } from "@testing-library/react";
import { JobTimeline } from "../JobTimeline";

describe("JobTimeline", () => {
  it("shows a resume action when the job needs attention", () => {
    render(<JobTimeline status="needs_attention" attentionReason="browser_login_required" />);

    expect(screen.getByText("Needs your action")).toBeInTheDocument();
    expect(screen.getByText("Sign in to Google and finish this step in NotebookLM.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "I finished this in NotebookLM" })).toBeInTheDocument();
  });
});
