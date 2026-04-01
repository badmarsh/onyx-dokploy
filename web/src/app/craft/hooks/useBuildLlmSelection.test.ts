import {
  getDefaultLlmSelection,
  isBuildLlmSelectionValid,
} from "@/app/craft/onboarding/constants";

describe("build LLM selection helpers", () => {
  test("uses the first visible model when the preferred model is unavailable", () => {
    const selection = getDefaultLlmSelection([
      {
        name: "NVIDIA NIM",
        provider: "openai",
        model_configurations: [
          { name: "qwen3-coder", is_visible: true },
          { name: "qwen3-next", is_visible: true },
        ],
      },
    ]);

    expect(selection).toEqual({
      providerName: "NVIDIA NIM",
      provider: "openai",
      modelName: "qwen3-coder",
    });
  });

  test("prefers a later provider of the same type when it has the recommended model", () => {
    const selection = getDefaultLlmSelection([
      {
        name: "Provider A",
        provider: "openai",
        model_configurations: [{ name: "qwen3-coder", is_visible: true }],
      },
      {
        name: "Provider B",
        provider: "openai",
        model_configurations: [{ name: "gpt-5.2", is_visible: true }],
      },
    ]);

    expect(selection).toEqual({
      providerName: "Provider B",
      provider: "openai",
      modelName: "gpt-5.2",
    });
  });

  test("requires an exact provider-name and visible-model match for saved selections", () => {
    expect(
      isBuildLlmSelectionValid(
        {
          providerName: "Aliyun DashScope",
          provider: "openai",
          modelName: "qwen3-max-preview",
        },
        [
          {
            name: "Aliyun DashScope",
            provider: "openai",
            model_configurations: [
              { name: "qwen3-max-preview", is_visible: true },
            ],
          },
        ]
      )
    ).toBe(true);

    expect(
      isBuildLlmSelectionValid(
        {
          providerName: "Aliyun DashScope",
          provider: "openai",
          modelName: "gpt-5.2",
        },
        [
          {
            name: "Aliyun DashScope",
            provider: "openai",
            model_configurations: [{ name: "qwen3-max", is_visible: true }],
          },
        ]
      )
    ).toBe(false);
  });
});
