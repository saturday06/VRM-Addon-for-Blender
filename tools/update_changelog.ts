/**
 * Tool to fetch GitHub repository release info and auto-update CHANGELOG.md (TypeScript/Octokit)
 * Uses Deno import map (deno.jsonc) for Octokit
 */
import { Octokit } from "@octokit/rest";
import type { Endpoints } from "@octokit/types";

interface Release {
  tag_name: string;
  name: string | null;
  body: string | null | undefined;
  published_at: string | null;
}

type ListReleasesResponse =
  Endpoints["GET /repos/{owner}/{repo}/releases"]["response"]["data"];

async function fetchGithubReleases(
  repo: string,
  token?: string,
): Promise<Release[]> {
  const [owner, repoName] = repo.split("/");
  const octokit = new Octokit({ auth: token });
  // Get all releases with pagination
  const releases: ListReleasesResponse = await octokit.paginate(
    octokit.repos.listReleases,
    { owner, repo: repoName },
  );
  return releases.map((release) => ({
    tag_name: release.tag_name,
    name: release.name,
    body: release.body,
    published_at: release.published_at,
  }));
}

async function updateChangelog(
  releases: Release[],
  changelogPath = "CHANGELOG.md",
): Promise<void> {
  let newContent = "# Changelog\n\n";
  for (const release of releases) {
    if (!release.tag_name.startsWith("v")) {
      break;
    }
    newContent += `${release.body}\n\n`;
  }
  await Deno.writeTextFile(changelogPath, newContent.trimEnd() + "\n");
}

if (import.meta.main) {
  const [repo, tokenArg] = Deno.args;
  if (!repo) {
    console.error(
      "Usage: update_changelog_from_github.ts <owner/repo> [github_token]",
    );
    Deno.exit(1);
  }
  const token = tokenArg || Deno.env.get("GITHUB_TOKEN");
  try {
    const releases = await fetchGithubReleases(repo, token);
    await updateChangelog(releases);
    console.log("CHANGELOG.md updated.");
  } catch (e) {
    console.error("Error:", e instanceof Error ? e.message : e);
    Deno.exit(2);
  }
}
