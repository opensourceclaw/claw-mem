/** claw-mem v7.0.0 — IMemoryCapability Contract Tests */
import { describe, it, expect } from "vitest";
import { MemoryCapability } from "../../src/capability/memory-capability";
import type { IMemoryCapability } from "../../src/capability/types";

describe("IMemoryCapability Contract", () => {
  it("MemoryCapability satisfies IMemoryCapability", () => {
    const cap: IMemoryCapability = new MemoryCapability();
    expect(cap.name).toBe("memory");
    expect(cap.version).toBe("7.0.0");
    expect(typeof cap.store).toBe("function");
    expect(typeof cap.search).toBe("function");
    expect(typeof cap.getContext).toBe("function");
    expect(typeof cap.getStats).toBe("function");
    expect(typeof cap.dispose).toBe("function");
  });

  it("all methods return Promises", async () => {
    const cap = new MemoryCapability();
    const p1 = cap.store("test");
    const p2 = cap.search("test");
    const p3 = cap.getContext();
    const p4 = cap.getStats();
    expect(p1).toBeInstanceOf(Promise);
    expect(p2).toBeInstanceOf(Promise);
    expect(p3).toBeInstanceOf(Promise);
    expect(p4).toBeInstanceOf(Promise);
    await Promise.all([p1, p2, p3, p4]);
    await cap.dispose();
  });

  it("search returns items array", async () => {
    const cap = new MemoryCapability();
    const result = await cap.search("test");
    expect(Array.isArray(result.items)).toBe(true);
    expect(typeof result.total).toBe("number");
    await cap.dispose();
  });
});
