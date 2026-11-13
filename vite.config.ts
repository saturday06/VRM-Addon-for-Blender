import { defineConfig } from "vite-plus";

export default defineConfig({
  staged: {
    "*": "vp check --fix",
  },
  fmt: {
    ignorePatterns: [
      ".local/**",
      "tests/resources/unity/*/ProjectSettings/*.json",
      "CHANGELOG.md",
      "pnpm-lock.yaml",
    ],
  },
  lint: {
    ignorePatterns: [".local/**", "tests/resources/unity/**"],
  },
});
