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
import {
  OpenIEExtractor,
  SkillExtractor,
  SkillStore,
} from "../../src/extraction";

import type { Triplet } from "../../src/extraction";

describe("OpenIEExtractor", () => {
  it("should extract triplets using rule mode for Chinese text", () => {
    const extractor = new OpenIEExtractor(undefined, "rule");
    const text = "张三负责电商项目。";

    const triplets = extractor.extract(text);
    expect(triplets.length).toBeGreaterThanOrEqual(1);

    const t = triplets[0];
    expect(t.subject).toBe("张三");
    expect(t.predicate).toBe("负责");
    expect(t.object).toBe("电商项目。");
    expect(t.source).toBe("rule");
  });

  it("should extract triplets using rule mode for English text", () => {
    const extractor = new OpenIEExtractor(undefined, "rule");
    const text = "Alice is developer";

    const triplets = extractor.extract(text);
    expect(triplets.length).toBeGreaterThanOrEqual(1);

    const t = triplets[0];
    expect(t.subject).toBe("Alice");
    expect(t.predicate).toBe("is");
    expect(t.confidence).toBeGreaterThan(0);
    expect(t.source).toBe("rule");
  });
});

describe("SkillExtractor", () => {
  it("should extract skills from triplets using rule mode", () => {
    const extractor = new SkillExtractor(undefined, "rule");

    const triplets: Triplet[] = [
      { subject: "张三", predicate: "负责", object: "需求分析", confidence: 0.9, source: "rule" },
      { subject: "张三", predicate: "负责", object: "系统设计", confidence: 0.85, source: "rule" },
      { subject: "张三", predicate: "负责", object: "编码实现", confidence: 0.8, source: "rule" },
    ];

    const skills = extractor.extract(triplets);
    expect(skills.length).toBe(1);

    const skill = skills[0];
    expect(skill.name).toBe("责任制工作");
    expect(skill.steps.length).toBeGreaterThan(0);
    expect(skill.confidence).toBeGreaterThan(0);
    expect(skill.source_triplets).toBe(3);
    expect(skill.compression_ratio).toBeGreaterThanOrEqual(3);
    expect(skill.source).toBe("rule");
  });

  it("should return empty list when not enough triplets", () => {
    const extractor = new SkillExtractor(undefined, "rule");
    const triplets: Triplet[] = [
      { subject: "Alice", predicate: "likes", object: "coffee", confidence: 0.8, source: "rule" },
    ];

    const skills = extractor.extract(triplets);
    expect(skills.length).toBe(0);
  });
});

describe("SkillStore", () => {
  it("should store, search, and merge skills", () => {
    const store = new SkillStore();

    const skill1 = {
      name: "责任制工作",
      steps: ["确认责任范围", "规划执行路径"],
      applicability: "当需要明确责任分工时",
      confidence: 0.85,
      compression_ratio: 3.0,
      source_triplets: 3,
      created_at: Date.now() / 1000,
      source: "rule" as const,
    };

    const skill2 = {
      name: "责任制工作",
      steps: ["推进交付", "汇报进展"],
      applicability: "当需要推进任务交付时",
      confidence: 0.7,
      compression_ratio: 2.0,
      source_triplets: 2,
      created_at: Date.now() / 1000,
      source: "rule" as const,
    };

    // Store first skill
    const id1 = store.store(skill1);
    expect(id1).toBeTruthy();
    expect(store.count()).toBe(1);

    // Store second skill (same name → merge)
    const id2 = store.store(skill2);
    expect(id2).toBe(id1); // Same ID returned

    // Merged skill should have combined steps and weighted confidence
    const merged = store.get(id1);
    expect(merged).toBeDefined();
    expect(merged!.steps.length).toBeGreaterThanOrEqual(3);
    expect(merged!.source).toBe("merged");
    expect(merged!.source_triplets).toBe(5);

    // Search
    const results = store.search("责任");
    expect(results.length).toBe(1);

    // List all
    expect(store.list_all().length).toBe(1);

    // Clear
    store.clear();
    expect(store.count()).toBe(0);
  });
});
