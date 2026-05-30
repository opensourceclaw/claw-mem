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
import { WriteTimeGating, SalienceScorer, VersionChain } from "../../src/gating";

describe("WriteTimeGating", () => {
  it("should store high-salience items to active memory and low-salience to cold storage", () => {
    const gating = new WriteTimeGating(0.6);

    // High salience item (user source, verified, has context)
    const highSalience = gating.write({
      content: "Important decision about tech stack",
      source: "user",
      context: { topic: "tech stack selection" },
      verified: true,
    });
    expect(highSalience.stored).toBe(true);
    expect(highSalience.tier).toBe("active");
    expect(highSalience.salience_score).toBeGreaterThanOrEqual(0.6);

    // Low salience item (external source, no context, not verified)
    // external=0.4*0.4(0.16) + novelty=1.0*0.3(0.3) + reliability=0.5*0.3(0.15) = 0.61
    // Use threshold=0.7 so this goes to cold
    const gatingHigh = new WriteTimeGating(0.7);
    gatingHigh.write({
      content: "Important decision about tech stack",
      source: "user",
      context: { topic: "tech stack selection" },
      verified: true,
    });
    const lowSalience = gatingHigh.write({
      content: "Random noise",
      source: "external",
      verified: false,
    });
    expect(lowSalience.stored).toBe(true);
    expect(lowSalience.tier).toBe("cold");
    expect(lowSalience.salience_score).toBeLessThan(0.7);

    // Verify version chain grew
    const stats = gatingHigh.get_stats();
    expect(stats.version_chain_length).toBe(2);
    expect(stats.active_count).toBe(1);
    expect(stats.cold_count).toBe(1);
  });
});

describe("SalienceScorer", () => {
  it("should compute salience scores based on source, novelty, and reliability", () => {
    const scorer = new SalienceScorer();

    // User source with verified status
    const userItem = scorer.compute({
      content: "First important memory",
      source: "user",
      verified: true,
      context: { topic: "test" },
    });
    expect(userItem).toBeGreaterThanOrEqual(0);
    expect(userItem).toBeLessThanOrEqual(1);
    // user=1.0*0.4 + novelty=1.0*0.3 + reliability=(0.5+0.2+0.2+0.1=1.0)*0.3 = 0.4+0.3+0.3 = 1.0
    expect(userItem).toBeCloseTo(1.0, 1);

    // External source with no context
    const externalItem = scorer.compute({
      content: "Second memory",
      source: "external",
      verified: false,
    });
    expect(externalItem).toBeLessThan(userItem);
    // external=0.4*0.4 + novelty=(some)*0.3 + reliability=0.5*0.3 = 0.16+novelty+0.15
    expect(externalItem).toBeGreaterThanOrEqual(0);
  });
});

describe("VersionChain", () => {
  it("should track version history and retrieve by index", () => {
    const chain = new VersionChain();

    expect(chain.length).toBe(0);
    expect(chain.latest()).toBeUndefined();

    chain.append({ id: "v1", content: "first" });
    chain.append({ id: "v2", content: "second" });
    chain.append({ id: "v3", content: "third" });

    expect(chain.length).toBe(3);

    const first = chain.get(0);
    expect(first).toBeDefined();
    expect(first!._version).toBe(0);
    expect(first!.content).toBe("first");

    const last = chain.latest();
    expect(last).toBeDefined();
    expect(last!._version).toBe(2);
    expect(last!.content).toBe("third");

    // Out of bounds
    expect(chain.get(10)).toBeUndefined();
    expect(chain.get(-1)).toBeUndefined();
  });
});
