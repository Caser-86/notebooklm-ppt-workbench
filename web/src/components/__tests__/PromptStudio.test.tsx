import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PromptStudio } from "../PromptStudio";

describe("PromptStudio", () => {
  it("lets the user switch preset and edit the prompt body", async () => {
    const user = userEvent.setup();
    render(
      <PromptStudio
        presets={[{ id: "default", label: "Default", body: "Start here" }]}
        selectedPresetId="default"
        value="Start here"
        onPresetChange={() => {}}
        onValueChange={() => {}}
      />,
    );

    const textarea = screen.getByLabelText("Generation prompt");
    await user.type(textarea, " updated");

    expect(textarea).toHaveValue("Start here updated");
  });
});
