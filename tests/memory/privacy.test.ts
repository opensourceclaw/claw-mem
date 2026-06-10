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
import { PrivacyFilter } from "../../src/memory";
import type { MemoryRecord } from "../../src/memory";

function makeRecord(content: string): MemoryRecord {
  return {
    id: "rec-1",
    agent_id: "agent-1",
    memory_type: "semantic",
    content,
    tags: [],
    timestamp: Date.now() / 1000,
    confidence: 1.0,
    source: "local",
  };
}

describe("PrivacyFilter", () => {
  const filter = new PrivacyFilter();

  it("should filter email at shared level", () => {
    const r = makeRecord("Contact test@example.com for details");
    const result = filter.filter(r, "shared");
    expect(result.content).toContain("[EMAIL]");
    expect(result.content).not.toContain("test@example.com");
  });

  it("should filter phone at shared level", () => {
    const r = makeRecord("Call 555-123-4567 today");
    const result = filter.filter(r, "shared");
    expect(result.content).toContain("[PHONE]");
    expect(result.content).not.toContain("555-123-4567");
  });

  it("should filter API key at shared level", () => {
    const r = makeRecord("Use api_key: abc123-secret-key");
    const result = filter.filter(r, "shared");
    expect(result.content).toContain("[API_KEY]");
    expect(result.content).not.toContain("abc123-secret-key");
  });

  it("should not redact at local level", () => {
    const r = makeRecord("Email test@example.com");
    const result = filter.filter(r, "local");
    expect(result.content).toContain("test@example.com");
  });

  it("should redact high-sensitivity content at public level", () => {
    const r = makeRecord("The password is hunter2");
    const result = filter.filter(r, "public");
    expect(result.content).toBe("[REDACTED]");
  });

  it("should score high for PII content", () => {
    const r = makeRecord("Email test@example.com for access");
    expect(filter.sensitivity(r)).toBeGreaterThanOrEqual(0.8);
  });

  it("should score high for sensitive keywords", () => {
    const r = makeRecord("Your password is secret123");
    expect(filter.sensitivity(r)).toBeGreaterThanOrEqual(0.6);
  });

  it("should score low for normal content", () => {
    const r = makeRecord("The meeting is at 3pm tomorrow");
    expect(filter.sensitivity(r)).toBeLessThan(0.5);
  });
});
