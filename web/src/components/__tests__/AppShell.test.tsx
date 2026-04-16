import { render, screen } from "@testing-library/react";
import App from "../../App";

describe("App shell", () => {
  it("renders the project list and empty workspace state", () => {
    render(<App />);

    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("No project selected")).toBeInTheDocument();
  });
});
