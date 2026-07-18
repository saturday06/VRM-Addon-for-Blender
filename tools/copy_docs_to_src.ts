import { default as vitepressConfig } from "../docs/.vitepress/config.mts";
import { join, relative } from "node:path";

const sourceRoot = "docs";
const destinationRoot = "src/io_scene_vrm/documentation";
const locales = Object.keys(vitepressConfig.locales ?? {});

async function copyMarkdownFilesRecursively(
  sourceDirectory: string,
  destinationDirectory: string,
): Promise<void> {
  await Deno.mkdir(destinationDirectory, { recursive: true });

  for await (const dirEntry of Deno.readDir(sourceDirectory)) {
    const sourcePath = join(sourceDirectory, dirEntry.name);

    if (dirEntry.isDirectory) {
      await copyMarkdownFilesRecursively(
        sourcePath,
        join(destinationDirectory, dirEntry.name),
      );
      continue;
    }

    if (!dirEntry.isFile || !dirEntry.name.endsWith(".md")) {
      continue;
    }

    const destinationPath = join(destinationDirectory, dirEntry.name);
    await Deno.copyFile(sourcePath, destinationPath);
  }
}

for (const locale of locales) {
  const sourceDirectory = join(sourceRoot, locale);
  const destinationDirectory = join(destinationRoot, locale);

  await copyMarkdownFilesRecursively(sourceDirectory, destinationDirectory);
  console.log(
    `Copied markdown files: ${relative(".", sourceDirectory)} -> ${
      relative(".", destinationDirectory)
    }`,
  );
}
