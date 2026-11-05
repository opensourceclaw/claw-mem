// claw-mem — repo-local commit role validator tests (2026-11-05)
//
// Verifies the file the shared ~/.git-hooks/commit-msg hook requires exists and
// enforces the claw-mem collaboration surface (deny-by-default).

import { describe, it, expect } from "vitest";
import { spawnSync } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const SCRIPT = path.resolve(__dirname, "../../scripts/validate-commit.ts");
const TS_NODE = path.resolve(__dirname, "../../node_modules/.bin/ts-node");

function setup(files: string[]): string {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-vc-"));
  const env = { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_SYSTEM: "/dev/null" };
  const run = (args: string[]) => {
    const result = spawnSync("git", args, { cwd: repo, env, encoding: "utf-8" });
    if (result.status !== 0) throw new Error(`git ${args.join(" ")}: ${result.stderr}`);
  };
  run(["init", "-q"]);
  for (const rel of files) {
    const abs = path.join(repo, rel);
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, "x\n", "utf-8");
  }
  run(["add", "."]);
  return repo;
}

function validate(repo: string, role: string): { status: number | null; out: string } {
  const result = spawnSync(
    TS_NODE,
    ["--transpile-only", SCRIPT, `--role=${role}`, "--commit-msg=/dev/null"],
    {
      cwd: repo,
      encoding: "utf-8",
      env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_SYSTEM: "/dev/null" },
      timeout: 30_000,
    },
  );
  return { status: result.status, out: `${result.stdout ?? ""}${result.stderr ?? ""}` };
}

describe("claw-mem validate-commit (role matrix)", () => {
  it("ArchitectAgent can commit the release/docs surface", () => {
    const repo = setup(["RELEASE_NOTES_v7.7.0.md", "docs/architecture/a.html"]);
    try {
      const result = validate(repo, "ArchitectAgent");
      expect(result.status, result.out).toBe(0);
    } finally {
      fs.rmSync(repo, { recursive: true, force: true });
    }
  });

  it("CodeAgent can commit src/tests but not release files", () => {
    const okRepo = setup(["src/a.ts", "tests/a.test.ts"]);
    try {
      expect(validate(okRepo, "CodeAgent").status).toBe(0);
    } finally {
      fs.rmSync(okRepo, { recursive: true, force: true });
    }

    const badRepo = setup(["package.json"]);
    try {
      const result = validate(badRepo, "CodeAgent");
      expect(result.status).not.toBe(0);
      expect(result.out).toContain("package.json");
    } finally {
      fs.rmSync(badRepo, { recursive: true, force: true });
    }
  });

  it("TestAgent is limited to tests/reports and denied src", () => {
    const okRepo = setup(["tests/a.test.ts", "reports/r.md"]);
    try {
      expect(validate(okRepo, "TestAgent").status).toBe(0);
    } finally {
      fs.rmSync(okRepo, { recursive: true, force: true });
    }

    const badRepo = setup(["src/a.ts"]);
    try {
      const result = validate(badRepo, "TestAgent");
      expect(result.status).not.toBe(0);
      expect(result.out).toContain("src/a.ts");
    } finally {
      fs.rmSync(badRepo, { recursive: true, force: true });
    }
  });

  it("ReleaseAgent can commit release notes but not src", () => {
    const okRepo = setup(["RELEASE_NOTES_v7.8.0.md", "CHANGELOG.md"]);
    try {
      expect(validate(okRepo, "ReleaseAgent").status).toBe(0);
    } finally {
      fs.rmSync(okRepo, { recursive: true, force: true });
    }

    const badRepo = setup(["src/a.ts"]);
    try {
      expect(validate(badRepo, "ReleaseAgent").status).not.toBe(0);
    } finally {
      fs.rmSync(badRepo, { recursive: true, force: true });
    }
  });

  it("rejects unknown roles and accepts canonical aliases", () => {
    const repo = setup(["src/a.ts"]);
    try {
      expect(validate(repo, "Contractor").status).not.toBe(0);
      expect(validate(repo, "Coder").status).toBe(0);
    } finally {
      fs.rmSync(repo, { recursive: true, force: true });
    }
  });

  it("passes when nothing is staged", () => {
    const repo = setup([]);
    try {
      expect(validate(repo, "CodeAgent").status).toBe(0);
    } finally {
      fs.rmSync(repo, { recursive: true, force: true });
    }
  });
});
