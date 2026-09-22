/**
 * Vendored snapshot byte-lock — claw-mem fixtures (T2a, Friday 2026-09-22).
 *
 * Three cross-repo snapshots vendored into mem's fixtures dir; byte-level sha256
 * locks prevent unilateral edits. Semantic locks (enum/field-name equality) live
 * in error-pattern-injection.test.ts (#15), error-pattern-v780.test.ts (#D4, #E2).
 * Upgrade procedure: devclaw/docs/contracts/VENDORED_CONTRACT_STANDARD.md §(c).
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";

const sha256 = (rel: string): string =>
  createHash("sha256")
    .update(readFileSync(fileURLToPath(new URL(`../fixtures/${rel}`, import.meta.url))))
    .digest("hex");

describe("vendored snapshots — byte sha256 lock (T2a)", () => {
  it("root-cause-categories.snapshot.json (upstream claw-rsi)", () => {
    expect(sha256("root-cause-categories.snapshot.json")).toBe(
      "a498bb8f13c0e814cff602186c82839430bc578c2246553a5540b503c45f86ae"
    );
  });

  it("rsi-mem-lifecycle-alignment.snapshot.json (bidirectional lock)", () => {
    expect(sha256("rsi-mem-lifecycle-alignment.snapshot.json")).toBe(
      "5a98c9f44adb163e5e885af8362350f482d1523c29d9f5449dbf18ea9b07859b"
    );
  });

  it("ctx-task-status-signal.snapshot.json (upstream claw-ctx)", () => {
    expect(sha256("ctx-task-status-signal.snapshot.json")).toBe(
      "3040bcacef5125c334f27cf00b445b9fa56e11b3f7221d19f707e9acd223f4ef"
    );
  });
});
