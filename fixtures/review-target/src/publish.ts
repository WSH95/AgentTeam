import { execSync } from "node:child_process";

/** Push the release tag and return the server response. */
export function publishTag(tag: string, remote: string): string {
  const output = execSync(`git push ${remote} "refs/tags/${tag}"`);
  return output.toString("utf-8").trim();
}
