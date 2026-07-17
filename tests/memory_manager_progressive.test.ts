import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager } from "../src/memory_manager";

describe("MemoryManager Progressive Loading (v6.40.0)", () => {
  let tmpDir: string;
  let mm: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-prog-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe("legacy mode (default)", () => {
    it("should initialize storage eagerly by default", () => {
      mm = new MemoryManager({ workspace: tmpDir });

      const state = mm.getLoadState();
      expect(state.episodic).toBe(true);
      expect(state.semantic).toBe(true);
      expect(state.procedural).toBe(true);
    });

    it("should be ready immediately", () => {
      mm = new MemoryManager({ workspace: tmpDir });
      expect(mm.isReady()).toBe(true);
    });
  });

  describe("progressive loading mode", () => {
    it("should not load storage synchronously when progressive loading enabled", () => {
      mm = new MemoryManager({
        workspace: tmpDir,
        enableProgressiveLoading: true
      });

      // Immediately after construction, check state (synchronous)
      // Background prefetch may have started but shouldn't be complete yet
      const state = mm.getLoadState();
      // In progressive mode, semantic and procedural are lazy (not loaded in constructor)
      expect(state.semantic).toBe(false);
      expect(state.procedural).toBe(false);
      // episodic may be loading in background
    });

    it("should load episodic on access", () => {
      mm = new MemoryManager({
        workspace: tmpDir,
        enableProgressiveLoading: true
      });

      // Access episodic triggers load
      const episodic = mm.episodic;
      expect(episodic).toBeDefined();

      const state = mm.getLoadState();
      expect(state.episodic).toBe(true);
    });

    it("should load semantic lazily", () => {
      mm = new MemoryManager({
        workspace: tmpDir,
        enableProgressiveLoading: true
      });

      // Access semantic triggers load
      const semantic = mm.semantic;
      expect(semantic).toBeDefined();

      const state = mm.getLoadState();
      expect(state.semantic).toBe(true);
      // Episodic not loaded yet (background prefetch not complete)
    });

    it("should support waitForReady()", async () => {
      mm = new MemoryManager({
        workspace: tmpDir,
        enableProgressiveLoading: true
      });

      // Not ready immediately
      expect(mm.isReady()).toBe(false);

      // Wait for background prefetch
      await mm.waitForReady();

      // Now ready
      expect(mm.isReady()).toBe(true);
    });

    it("should report isReady() status", () => {
      mm = new MemoryManager({
        workspace: tmpDir,
        enableProgressiveLoading: true
      });

      // Initially not ready
      expect(mm.isReady()).toBe(false);

      // After accessing storage
      mm.episodic;
      // Still not fully ready (index not loaded via background)
    });
  });

  describe("getLoadState()", () => {
    it("should return copy of load state", () => {
      mm = new MemoryManager({ workspace: tmpDir });

      const state1 = mm.getLoadState();
      const state2 = mm.getLoadState();

      expect(state1).not.toBe(state2); // Different objects
      expect(state1).toEqual(state2);  // Same values
    });
  });
});
