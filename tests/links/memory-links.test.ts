// Comprehensive tests for MemoryLink, MemoryTags, and parsers
import { describe, it, expect } from "vitest";
import {
  MemoryLink,
  MemoryTags,
  MemoryLinkParser,
  MemoryTagParser,
  MemoryLinkManager,
} from "../../src/links/memory_links";

describe("MemoryLink", () => {
  it("creates a link with default values", () => {
    const link = new MemoryLink("src1", "tgt1");
    expect(link.sourceId).toBe("src1");
    expect(link.targetId).toBe("tgt1");
    expect(link.linkType).toBe("reference");
    expect(link.createdAt).toBeTruthy();
  });

  it("creates a link with custom type and timestamp", () => {
    const link = new MemoryLink("src1", "tgt1", "depends_on", "2026-01-01");
    expect(link.linkType).toBe("depends_on");
    expect(link.createdAt).toBe("2026-01-01");
  });

  it("toDict returns correct structure", () => {
    const link = new MemoryLink("src1", "tgt1");
    const dict = link.toDict();
    expect(dict.source_id).toBe("src1");
    expect(dict.target_id).toBe("tgt1");
    expect(dict.link_type).toBe("reference");
  });
});

describe("MemoryTags", () => {
  it("creates empty tags by default", () => {
    const tags = new MemoryTags("mem1");
    expect(tags.memoryId).toBe("mem1");
    expect(tags.tags.size).toBe(0);
  });

  it("creates tags with initial set", () => {
    const tags = new MemoryTags("mem1", new Set(["tag1", "tag2"]));
    expect(tags.tags.size).toBe(2);
    expect(tags.tags.has("tag1")).toBe(true);
  });

  it("toDict exports tags as array", () => {
    const tags = new MemoryTags("mem1", new Set(["a", "b"]));
    const dict = tags.toDict();
    expect(dict.memory_id).toBe("mem1");
    expect(dict.tags).toEqual(["a", "b"]);
  });
});

describe("MemoryLinkParser", () => {
  it("parses simple wiki-style links", () => {
    const parser = new MemoryLinkParser();
    const links = parser.parseLinks("See [[mem_001]]", "source");
    expect(links).toHaveLength(1);
    expect(links[0].targetId).toBe("mem_001");
    expect(links[0].sourceId).toBe("source");
  });

  it("parses date#title format links", () => {
    const parser = new MemoryLinkParser();
    const links = parser.parseLinks("[[2026-03-25#investment-decision]]", "s");
    expect(links).toHaveLength(1);
    expect(links[0].targetId).toBe("2026-03-25#investment-decision");
  });

  it("parses multiple links", () => {
    const parser = new MemoryLinkParser();
    const links = parser.parseLinks("[[a]] and [[b]] and [[c]]", "s");
    expect(links).toHaveLength(3);
  });

  it("returns empty array when no links", () => {
    const parser = new MemoryLinkParser();
    const links = parser.parseLinks("No links here", "s");
    expect(links).toHaveLength(0);
  });

  it("removeLinks strips link syntax", () => {
    const parser = new MemoryLinkParser();
    const result = parser.removeLinks("See [[mem_001]] for more");
    expect(result).not.toContain("[[");
    expect(result).toContain("mem_001");
  });

  it("extractLinkTargets returns target strings", () => {
    const parser = new MemoryLinkParser();
    const targets = parser.extractLinkTargets("[[a]] [[b#c]]");
    expect(targets).toEqual(["a", "b#c"]);
  });

  it("resets regex state between calls", () => {
    const parser = new MemoryLinkParser();
    const r1 = parser.extractLinkTargets("[[a]] [[b]]");
    expect(r1).toHaveLength(2);
    const r2 = parser.parseLinks("[[c]]", "s");
    expect(r2).toHaveLength(1);
    expect(r2[0].targetId).toBe("c");
  });
});

describe("MemoryTagParser", () => {
  it("parses English tags", () => {
    const parser = new MemoryTagParser();
    const tags = parser.parseTags("This is #important and #urgent");
    expect(tags.has("important")).toBe(true);
    expect(tags.has("urgent")).toBe(true);
  });

  it("parses Chinese tags", () => {
    const parser = new MemoryTagParser();
    const tags = parser.parseTags("参考 #设计模式 和 #最佳实践");
    expect(tags.has("设计模式")).toBe(true);
    expect(tags.has("最佳实践")).toBe(true);
  });

  it("normalizes to lowercase", () => {
    const parser = new MemoryTagParser();
    const tags = parser.parseTags("#Important #IMPORTANT");
    expect(tags.size).toBe(1);
    expect(tags.has("important")).toBe(true);
  });

  it("returns empty set when no tags", () => {
    const parser = new MemoryTagParser();
    const tags = parser.parseTags("No tags here");
    expect(tags.size).toBe(0);
  });

  it("removeTags strips tag syntax", () => {
    const parser = new MemoryTagParser();
    const result = parser.removeTags("#hello world #test");
    expect(result).not.toContain("#");
  });

  it("extractTags returns tags set", () => {
    const parser = new MemoryTagParser();
    const tags = parser.extractTags("#alpha #beta #gamma");
    expect(tags.size).toBe(3);
  });
});

describe("MemoryLinkManager", () => {
  it("processMemory extracts links and tags", () => {
    const mgr = new MemoryLinkManager();
    const [links, tags] = mgr.processMemory(
      "mem1",
      "See [[mem2]] #urgent",
    );
    expect(links).toHaveLength(1);
    expect(tags.has("urgent")).toBe(true);
  });

  it("getLinkedMemories returns linked IDs", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("mem1", "[[mem2]] [[mem3]]");
    const linked = mgr.getLinkedMemories("mem1");
    expect(linked).toEqual(["mem2", "mem3"]);
  });

  it("getBacklinks finds reverse links", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("mem_A", "[[mem_B]]");
    mgr.processMemory("mem_C", "[[mem_B]]");
    const backlinks = mgr.getBacklinks("mem_B");
    expect(backlinks).toHaveLength(2);
    expect(backlinks).toContain("mem_A");
    expect(backlinks).toContain("mem_C");
  });

  it("searchByTag finds tagged memories", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("m1", "#ai");
    mgr.processMemory("m2", "#ai #ml");
    mgr.processMemory("m3", "#python");
    expect(mgr.searchByTag("ai")).toHaveLength(2);
    expect(mgr.searchByTag("python")).toHaveLength(1);
    expect(mgr.searchByTag("nonexistent")).toHaveLength(0);
  });

  it("getTagsForMemory returns tags", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("m1", "#tag1 #tag2");
    const tags = mgr.getTagsForMemory("m1");
    expect(tags.has("tag1")).toBe(true);
  });

  it("getAllTags returns all known tags", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("m1", "#a #b");
    mgr.processMemory("m2", "#c");
    expect(mgr.getAllTags().size).toBe(3);
  });

  it("getRelatedMemories combines links and shared tags", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("mem1", "[[mem2]] #shared");
    mgr.processMemory("mem2", "[[mem3]] #shared");
    mgr.processMemory("mem3", "#other");
    const related = mgr.getRelatedMemories("mem1");
    expect(related).toContain("mem2"); // linked
    expect(related.length).toBeGreaterThanOrEqual(1);
  });

  it("getRelatedMemories excludes self", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("self", "[[self]] #tag");
    const related = mgr.getRelatedMemories("self");
    expect(related).not.toContain("self");
  });

  it("exportLinks exports complete state", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("m1", "[[m2]] #tag");
    const exported = mgr.exportLinks();
    expect(exported.links).toBeDefined();
    expect(exported.tags).toBeDefined();
    expect(exported.tag_index).toBeDefined();
  });

  it("updating tags for same memory replaces old tags", () => {
    const mgr = new MemoryLinkManager();
    mgr.processMemory("m1", "#old");
    mgr.processMemory("m1", "#new");
    expect(mgr.searchByTag("old")).toHaveLength(0);
    expect(mgr.searchByTag("new")).toHaveLength(1);
  });
});
