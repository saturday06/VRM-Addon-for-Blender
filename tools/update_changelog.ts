/**
 * Tool to fetch GitHub repository release info and auto-update CHANGELOG.md (TypeScript/Octokit)
 * Uses Deno import map (deno.jsonc) for Octokit
 */
import { Octokit } from "@octokit/rest";
import type { Endpoints } from "@octokit/types";
import git from "isomorphic-git";
import fs from "node:fs";

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

async function getRepoFromGit(): Promise<string> {
  const remotes = await git.listRemotes({ fs, dir: "." });
  const origin = remotes.find((remote) => remote.remote === "origin");
  if (!origin) {
    throw new Error("origin remote not found in git repository.");
  }

  const urlString = origin.url;
  let url: URL;
  try {
    url = new URL(urlString);
  } catch {
    // Handle SSH format: git@github.com:owner/repo.git
    const match = urlString.match(/^git@github\.com:([^/]+\/[^/]+?)(\.git)?$/);
    if (!match || !match[1]) {
      throw new Error(
        `Could not parse owner/repo from origin URL: ${urlString}`,
      );
    }
    return match[1];
  }

  // Handle HTTPS format: https://github.com/owner/repo.git
  return url.pathname.slice(1).replace(/\.git$/, "");
}

if (import.meta.main) {
  const token = Deno.env.get("GITHUB_TOKEN") || Deno.env.get("GH_TOKEN");
  try {
    const repo = await getRepoFromGit();
    const releases = await fetchGithubReleases(repo, token);
    await updateChangelog(releases);
    console.log("CHANGELOG.md updated.");
  } catch (e) {
    console.error("Error:", e instanceof Error ? e.message : e);
    Deno.exit(2);
  }
}
