// Strategy Registry Unit Tests (v6.31.0)

import { describe, it, expect, beforeEach } from "vitest";
import { StrategyRegistry } from "../../src/storage/strategy-registry.js";
import type { StorageStrategy, StrategyContext, StoreResult } from "../../src/storage/strategy-registry.js";

// Mock strategy for testing
class MockStrategy implements StorageStrategy {
  name: string;
  memoryTypes: string[];

  constructor(name: string, types: string[]) {
    this.name = name;
    this.memoryTypes = types;
  }

  store(): StoreResult {
    return { id: "test", strategy: this.name };
  }

  retrieve() {
    return [];
  }
}

describe("StrategyRegistry", () => {
  let registry: StrategyRegistry;
  let defaultStrategy: MockStrategy;

  beforeEach(() => {
    defaultStrategy = new MockStrategy("default", ["*"]);
    registry = new StrategyRegistry(defaultStrategy);
  });

  it("resolves registered strategy", () => {
    const strategy = new MockStrategy("custom", ["custom_type"]);
    registry.register(strategy);

    const resolved = registry.resolve("custom_type");
    expect(resolved.name).toBe("custom");
  });

  it("falls back to default for unknown type", () => {
    const resolved = registry.resolve("unknown_type");
    expect(resolved.name).toBe("default");
  });

  it("lists all strategies", () => {
    const strategy1 = new MockStrategy("strat1", ["type1"]);
    const strategy2 = new MockStrategy("strat2", ["type2", "type3"]);

    registry.register(strategy1);
    registry.register(strategy2);

    const list = registry.list();
    expect(list.length).toBe(3); // strat1, strat2, default
    expect(list.find(s => s.name === "strat1")).toBeDefined();
    expect(list.find(s => s.name === "strat2")).toBeDefined();
  });

  it("checks if type has custom strategy", () => {
    const strategy = new MockStrategy("custom", ["custom_type"]);
    registry.register(strategy);

    expect(registry.hasStrategy("custom_type")).toBe(true);
    expect(registry.hasStrategy("unknown_type")).toBe(false);
  });

  it("handles multiple types per strategy", () => {
    const strategy = new MockStrategy("multi", ["type1", "type2", "type3"]);
    registry.register(strategy);

    expect(registry.resolve("type1").name).toBe("multi");
    expect(registry.resolve("type2").name).toBe("multi");
    expect(registry.resolve("type3").name).toBe("multi");
  });
});
