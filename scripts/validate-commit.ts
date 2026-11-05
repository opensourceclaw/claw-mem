#!/usr/bin/env npx ts-node
/**
 * claw-mem commit role gate — repo-local validator for the shared
 * ~/.git-hooks/commit-msg hook (which requires $ROOT/scripts/validate-commit.ts).
 *
 * Interface (unchanged from devclaw):
 *   ts-node --transpile-only scripts/validate-commit.ts --role=<role> --commit-msg=<file>
 *
 * Deny-by-default: every staged path must match one of the role's allowed
 * prefixes. `ArchitectAgent`/`Architect` owns the commit/release surface and
 * may commit anything; other roles are restricted to their collaboration area.
 */

import { execFileSync } from "child_process";
import * as path from "path";

type CanonicalRole = "Architect" | "Coder" | "Tester" | "Releaser" | "Owner";

const ROLE_ALIASES: Record<string, CanonicalRole> = {
  architect: "Architect",
  architectagent: "Architect",
  coder: "Coder",
  codeagent: "Coder",
  tester: "Tester",
  testagent: "Tester",
  releaser: "Releaser",
  releaseagent: "Releaser",
  owner: "Owner",
  productowner: "Owner",
};

const COMMON_PATHS = [
  "inbox/",
  "docs/",
  "memory/",
  "transcripts/",
  "reports/",
  "results/",
];

const ROLE_PATHS: Record<CanonicalRole, string[]> = {
  // Commit/release authority: the full repo (role separation is enforced at
  // the pipeline/substage layer, not by withholding file access here).
  Architect: ["*"],
  Coder: [
    "src/",
    "tests/",
    "scripts/",
    "benchmarks/",
    "ci/",
    "pi_plugin/",
    "test_run_validation/",
    "test-recap.js",
    "vitest.config.ts",
    ...COMMON_PATHS,
  ],
  Tester: [
    "tests/",
    "reports/",
    "results/",
    "test_run_validation/",
    ...COMMON_PATHS,
  ],
  Releaser: [
    "package.json",
    "package-lock.json",
    "CHANGELOG.md",
    "RELEASE_NOTES.md",
    "RELEASE_NOTES_v",
    "RELEASE_CHECKLIST.md",
    "RELEASE_PROCESS.md",
    "openclaw.plugin.json",
    "sbom.json",
    "requirements-dev.txt",
    "dist/",
    ...COMMON_PATHS,
  ],
  Owner: [
    "inbox/inbox-release/",
    "inbox/inbox-govern/",
    "docs/",
  ],
};

function fail(message: string): never {
  console.error(message);
  process.exit(1);
}

function normalizeRole(raw: string): CanonicalRole | null {
  return ROLE_ALIASES[raw.trim().toLowerCase()] ?? null;
}

function stagedFiles(root: string): string[] {
  const output = execFileSync(
    "git",
    ["-C", root, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRD"],
    { encoding: "utf-8" },
  );
  return output.split("\0").filter((file) => file.trim() !== "");
}

function isAllowed(role: CanonicalRole, file: string): boolean {
  const normalized = path.posix.normalize(file.replace(/^\.\//, ""));
  return ROLE_PATHS[role].some(
    (rule) => rule === "*" || normalized === rule || normalized.startsWith(rule),
  );
}

function main(): void {
  const roleArg = process.argv.find((arg) => arg.startsWith("--role="));
  const roleRaw = roleArg?.slice("--role=".length).trim();
  // Accepted for interface parity with the shared hook; this repo does not use
  // Acceptance-trailer authorization.
  process.argv.find((arg) => arg.startsWith("--commit-msg="));

  if (!roleRaw) {
    fail("Role not specified. Use: --role=<ArchitectAgent|CodeAgent|TestAgent|ReleaseAgent>");
  }
  const role = normalizeRole(roleRaw);
  if (role === null) {
    fail(
      `Invalid role: ${roleRaw}\n` +
        "   Valid roles: ArchitectAgent, CodeAgent, TestAgent, ReleaseAgent, ProductOwner " +
        "(canonical: Architect, Coder, Tester, Releaser, Owner)",
    );
  }

  let root: string;
  try {
    root = execFileSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf-8" }).trim();
  } catch {
    fail("[claw-mem] commit-msg role check: not a git repository (fail-closed)");
  }
  if (root === "") fail("[claw-mem] commit-msg role check: empty repository root (fail-closed)");

  let files: string[];
  try {
    files = stagedFiles(root);
  } catch (error) {
    fail(
      `[claw-mem] commit-msg role check: cannot read staged files (fail-closed): ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }

  const violations = files.filter((file) => !isAllowed(role, file));
  if (violations.length > 0) {
    console.error("\n❌ Commit rejected: role permission violations detected\n");
    console.error(`Role: ${role} (${roleRaw})\n`);
    for (const file of violations) {
      console.error(`  📄 ${file}`);
      console.error(`     Reason: ${role} cannot modify this path`);
    }
    console.error("\n💡 Ask the owning role to commit this path (or use the release path).\n");
    process.exit(1);
  }

  console.log(`✅ All staged files validated for role: ${role} (${files.length} file(s))`);
}

main();
