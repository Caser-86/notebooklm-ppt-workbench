import { render, screen } from "@testing-library/react";
import { JobTimeline } from "../JobTimeline";

describe("JobTimeline", () => {
  it("shows a resume action when the job needs attention", () => {
    render(<JobTimeline status="needs_attention" attentionReason="browser_login_required" />);

    expect(screen.getByText("browser_login_required")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resume job" })).toBeInTheDocument();
  });
});
