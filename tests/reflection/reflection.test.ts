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
import { ReflectionOrchestrator, BeliefSynthesizer, BeliefTracker } from "../../src/reflection";

describe("ReflectionOrchestrator", () => {
  it("should extract observations and synthesize beliefs from memories", () => {
    const orchestrator = new ReflectionOrchestrator();

    const memories = [
      { content: "User prefers dark themes", source: "conversation", id: "m1", timestamp: new Date().toISOString() },
      { content: "User prefers light themes", source: "conversation", id: "m2", timestamp: new Date().toISOString() },
      { content: "User prefers blue themes", source: "conversation", id: "m3", timestamp: new Date().toISOString() },
    ];

    const result = orchestrator.reflect(memories, "user123");

    expect(result.observations.length).toBeGreaterThanOrEqual(2);
    // Each memory matches "User prefers ..." pattern
    // All three share keyword "themes" (longest word) → grouped as one topic with 3 observations → 1 belief
    expect(result.beliefs.length).toBeGreaterThanOrEqual(1);

    expect(result.timestamp).toBeTruthy();
    expect(result.summary).toContain("Reflection #1");
  });
});

describe("BeliefSynthesizer", () => {
  it("should extract observations matching known patterns", () => {
    const synth = new BeliefSynthesizer();

    const memories = [
      { content: "Important: The server runs on Linux", source: "sysadmin", id: "m1" },
      { content: "User prefers dark mode", source: "user", id: "m2" },
      { content: "Random non-matching text", source: "user", id: "m3" },
    ];

    const observations = synth.extract_observations(memories);
    expect(observations.length).toBe(2);
    expect(observations[0].content).toContain("server runs on Linux");
    expect(observations[0].metadata.category).toBe("fact");
    expect(observations[1].content).toContain("dark mode");
    expect(observations[1].metadata.category).toBe("user_preference");
  });
});

describe("BeliefTracker", () => {
  it("should track belief versions and history", () => {
    const tracker = new BeliefTracker();

    // Record initial belief
    tracker.record("BEL_001", "User prefers Python", 0.8);
    expect(tracker.count_beliefs()).toBe(1);
    expect(tracker.count_versions()).toBe(1);

    const current = tracker.get_current("BEL_001");
    expect(current).not.toBeNull();
    expect(current!.statement).toBe("User prefers Python");
    expect(current!.version).toBe(1);

    // Update belief
    tracker.update("BEL_001", "User prefers Python >= 3.10", 0.9);
    expect(tracker.count_versions()).toBe(2);

    const updated = tracker.get_current("BEL_001");
    expect(updated!.version).toBe(2);
    expect(updated!.statement).toBe("User prefers Python >= 3.10");
    expect(updated!.previous_statement).toBe("User prefers Python");

    // History
    const history = tracker.get_history("BEL_001");
    expect(history.length).toBe(2);

    // Get changes since
    const changes = tracker.get_changes_since("2000-01-01T00:00:00.000Z");
    expect(changes.length).toBe(2);

    // All IDs
    const ids = tracker.get_all_ids();
    expect(ids).toEqual(["BEL_001"]);
  });
});
