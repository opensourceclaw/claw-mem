// push-dispatch gate (Peter ruling 2026-11-06): every main push must carry an
// inbox/inbox-release/ record with Peter APPROVED + a Dispatcher/To/Assignee
// line naming the CURRENT ReleaseAgent persona (resolved from
// configs/role-mapping.json — seat-based since v11.1.0; fail-closed, no
// literal fallback). Checked before the PUBLIC-only publish-scope rule.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { spawnSync } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const REPO_ROOT = path.resolve(import.meta.dirname, "../..");
const HOOK = path.join(REPO_ROOT, "scripts/git-hooks/pre-push");
const ZERO = "0".repeat(40);

// Fixtures follow the config, never a literal persona name.
const ROLE_CONFIG = JSON.parse(
  fs.readFileSync(path.join(REPO_ROOT, "configs/role-mapping.json"), "utf-8"),
) as { agents: Record<string, string> };
const personaFor = (role: string): string =>
  Object.keys(ROLE_CONFIG.agents).find((name) => ROLE_CONFIG.agents[name] === role)!;
const RELEASE_PERSONA = personaFor("ReleaseAgent");
const TEST_PERSONA = personaFor("TestAgent");

describe("push-dispatch gate (claw-mem repo pre-push)", () => {
  let dir: string;
  let head: string;
  let env: NodeJS.ProcessEnv;

  beforeEach(() => {
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-dispatch-"));
    // isolate from the developer's global hooks/config; stub gh so the
    // publish-scope rule resolves to "unknown visibility" and skips.
    const bin = path.join(dir, "bin");
    fs.mkdirSync(bin);
    fs.writeFileSync(path.join(bin, "gh"), "#!/bin/sh\nexit 1\n", { mode: 0o755 });
    env = {
      ...process.env,
      PATH: `${bin}:${process.env.PATH ?? ""}`,
      GIT_CONFIG_GLOBAL: "/dev/null",
      GIT_CONFIG_SYSTEM: "/dev/null",
    };
    const git = (args: string[]) =>
      spawnSync("git", ["-c", "user.email=t@t", "-c", "user.name=t", ...args], {
        cwd: dir,
        env,
        encoding: "utf-8",
      });
    git(["init", "-q"]);
    fs.writeFileSync(path.join(dir, "README.md"), "base\n");
    git(["add", "README.md"]);
    git(["commit", "-qm", "init"]);
    head = git(["rev-parse", "HEAD"]).stdout.trim();
    // The gate resolves the ReleaseAgent persona from the repo config.
    fs.mkdirSync(path.join(dir, "configs"), { recursive: true });
    fs.copyFileSync(
      path.join(REPO_ROOT, "configs/role-mapping.json"),
      path.join(dir, "configs/role-mapping.json"),
    );
  });

  afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

  function writeRelease(body: string) {
    fs.mkdirSync(path.join(dir, "inbox/inbox-release"), { recursive: true });
    fs.writeFileSync(path.join(dir, "inbox/inbox-release/peter-approval.md"), body);
  }

  function run() {
    const r = spawnSync("sh", [HOOK], {
      cwd: dir,
      env,
      encoding: "utf-8",
      input: `refs/heads/main ${head} refs/heads/main ${ZERO}\n`,
    });
    return { code: r.status, out: `${r.stdout ?? ""}${r.stderr ?? ""}` };
  }

  it(`APPROVED + Dispatcher: ${RELEASE_PERSONA} → push allowed`, () => {
    writeRelease(
      `# Release approval\n\n**Approver**: Peter\n**Decision**: APPROVED\n**Dispatcher**: ${RELEASE_PERSONA}\n`,
    );
    const r = run();
    expect(r.code).toBe(0);
    expect(r.out).not.toContain("push-dispatch");
  });

  it(`APPROVED + To: ${RELEASE_PERSONA} → push allowed`, () => {
    writeRelease(
      `# Release approval\n\n**Approver**: Peter\n**Decision**: APPROVED\n**To**: ${RELEASE_PERSONA}\n`,
    );
    const r = run();
    expect(r.code).toBe(0);
  });

  it(`legacy Dispatcher: ${TEST_PERSONA} → rejected (only the current ReleaseAgent resolves)`, () => {
    writeRelease(
      `# Release approval\n\n**Approver**: Peter\n**Decision**: APPROVED\n**Dispatcher**: ${TEST_PERSONA}\n`,
    );
    const r = run();
    expect(r.code).toBe(1);
    expect(r.out).toContain("[push-dispatch] PUSH REJECTED");
    expect(r.out).toContain(`owned by ${RELEASE_PERSONA}`);
  });

  it("APPROVED without a dispatcher line → rejected, naming the current persona", () => {
    writeRelease("# Release approval\n\n**Approver**: Peter\n**Decision**: APPROVED\n");
    const r = run();
    expect(r.code).toBe(1);
    expect(r.out).toContain("[push-dispatch] PUSH REJECTED");
    expect(r.out).toContain(`Dispatcher: ${RELEASE_PERSONA}`);
  });

  it("no release record → rejected", () => {
    const r = run();
    expect(r.code).toBe(1);
    expect(r.out).toContain("[push-dispatch] PUSH REJECTED");
  });

  it("unreadable role-mapping → fail-closed reject (no literal fallback)", () => {
    fs.rmSync(path.join(dir, "configs/role-mapping.json"));
    writeRelease(
      `# Release approval\n\n**Approver**: Peter\n**Decision**: APPROVED\n**Dispatcher**: ${RELEASE_PERSONA}\n`,
    );
    const r = run();
    expect(r.code).toBe(1);
    expect(r.out).toContain("cannot resolve current ReleaseAgent persona");
    expect(r.out).not.toContain("owned by Karen");
  });
});
