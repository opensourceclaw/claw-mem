/** claw-mem v7.0.0 — MemoryCapability Tests */
import { describe, it, expect, beforeEach } from "vitest";
import { MemoryCapability } from "../../src/capability/memory-capability";

describe("MemoryCapability", () => {
  let cap: MemoryCapability;

  beforeEach(() => {
    cap = new MemoryCapability();
  });

  it("should have name 'memory'", () => {
    expect(cap.name).toBe("memory");
  });

  it("should have version '7.0.0'", () => {
    expect(cap.version).toBe("7.0.0");
  });

  it("should store a memory", async () => {
    const result = await cap.store("test memory content");
    expect(result).toHaveProperty("id");
    expect(result.stored).toBe(true);
  });

  it("should store with memory type and tags", async () => {
    const result = await cap.store("important fact", "semantic", ["important", "fact"]);
    expect(result.stored).toBe(true);
  });

  it("should search memories", async () => {
    await cap.store("hello world", "episodic");
    const result = await cap.search("hello");
    expect(result).toHaveProperty("items");
    expect(result).toHaveProperty("total");
    expect(Array.isArray(result.items)).toBe(true);
  });

  it("should get context", async () => {
    await cap.store("remember this", "episodic");
    const result = await cap.getContext({ limit: 5 });
    expect(result).toHaveProperty("context");
  });

  it("should get stats", async () => {
    await cap.store("test", "episodic");
    const stats = await cap.getStats();
    expect(stats).toHaveProperty("total");
  });

  it("should dispose cleanly", async () => {
    await cap.dispose();
    await expect(cap.store("test")).rejects.toThrow("disposed");
  });
});
