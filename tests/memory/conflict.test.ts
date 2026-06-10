// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { describe, it, expect } from "vitest";
import { ConflictResolver } from "../../src/memory";
import type { MemoryRecord } from "../../src/memory";

function makeRecord(overrides?: Partial<MemoryRecord>): MemoryRecord {
  return {
    id: "rec-1",
    agent_id: "agent-1",
    memory_type: "semantic",
    content: "Project deadline is Friday",
    tags: ["project", "deadline"],
    timestamp: 1000,
    confidence: 1.0,
    source: "local",
    ...overrides,
  };
}

describe("ConflictResolver", () => {
  const resolver = new ConflictResolver();

  it("should detect conflict: same tags + different content", () => {
    const a = makeRecord({ content: "Project deadline is Friday" });
    const b = makeRecord({ id: "rec-2", content: "Project deadline is Monday" });
    const c = resolver.detect(a, b);
    expect(c).not.toBeNull();
    expect(c!.commonTags).toContain("project");
  });

  it("should not detect conflict: same content", () => {
    const a = makeRecord();
    const b = makeRecord({ id: "rec-2" });
    expect(resolver.detect(a, b)).toBeNull();
  });

  it("should not detect conflict: different tags", () => {
    const a = makeRecord({ tags: ["alpha"] });
    const b = makeRecord({ id: "rec-2", tags: ["beta"] });
    expect(resolver.detect(a, b)).toBeNull();
  });

  it("should resolve lww: newer wins", () => {
    const a = makeRecord({ content: "old", timestamp: 100 });
    const b = makeRecord({ id: "rec-2", content: "new", timestamp: 200 });
    const conflict = resolver.detect(a, b)!;
    const resolved = resolver.resolve(conflict, "lww");
    expect(resolved.content).toBe("new");
  });

  it("should resolve merge: content concatenated", () => {
    const a = makeRecord({ content: "Part A", tags: ["shared", "t1"] });
    const b = makeRecord({ id: "rec-2", content: "Part B", tags: ["shared", "t2"] });
    const conflict = resolver.detect(a, b)!;
    const resolved = resolver.resolve(conflict, "merge");
    expect(resolved.content).toContain("Part A");
    expect(resolved.content).toContain("Part B");
    expect(resolved.tags).toContain("t1");
    expect(resolved.tags).toContain("t2");
  });

  it("should resolve keep-both: dual tag added", () => {
    const a = makeRecord();
    const b = makeRecord({ id: "rec-2", content: "different" });
    const conflict = resolver.detect(a, b)!;
    const resolved = resolver.resolve(conflict, "keep-both");
    expect(resolved.tags).toContain("conflict:dual");
  });

  it("should resolve ask-human: pending tag added", () => {
    const a = makeRecord();
    const b = makeRecord({ id: "rec-2", content: "different" });
    const conflict = resolver.detect(a, b)!;
    const resolved = resolver.resolve(conflict, "ask-human");
    expect(resolved.tags).toContain("conflict:pending");
  });
});
