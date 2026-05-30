// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

import { MemoryLinkManager, MemoryLinkParser, MemoryTagParser } from "../../src/links/memory_links";
import { describe, it, expect } from "vitest";

// ── Link Parser Tests ──────────────────────────────────────────────

function testLinkParsing(): boolean {
  const parser = new MemoryLinkParser();
  const content = `See [[mem_001]] and also [[2026-03-25#investment-decision]] for details.`;

  const links = parser.parseLinks(content, "source_mem");

  if (links.length !== 2) {
    console.error(`FAIL: Expected 2 links, got ${links.length}`);
    return false;
  }
  if (links[0].targetId !== "mem_001") {
    console.error(`FAIL: First link target should be "mem_001", got "${links[0].targetId}"`);
    return false;
  }
  if (links[1].targetId !== "2026-03-25#investment-decision") {
    console.error(`FAIL: Second link target should have date#title format`);
    return false;
  }

  // Test removeLinks
  const cleaned = parser.removeLinks(content);
  if (cleaned.includes("[[")) {
    console.error("FAIL: removeLinks should remove [[ syntax");
    return false;
  }

  console.log("  PASS: Link parsing and removal");
  return true;
}

// ── Tag Parser Tests ───────────────────────────────────────────────

function testTagParsing(): boolean {
  const parser = new MemoryTagParser();
  const content = `This is #important and #urgent plus Chinese #重要标签.`;

  const tags = parser.parseTags(content);

  if (!tags.has("important")) {
    console.error('FAIL: Should find tag "important"');
    return false;
  }
  if (!tags.has("urgent")) {
    console.error('FAIL: Should find tag "urgent"');
    return false;
  }
  if (!tags.has("重要标签")) {
    console.error('FAIL: Should find Chinese tag "重要标签"');
    return false;
  }

  // Test normalize to lowercase
  const mixedContent = `#UpperCase #UPPERCASE`;
  const mixedTags = parser.parseTags(mixedContent);
  if (mixedTags.size !== 1) {
    console.error(`FAIL: Should normalize to lowercase, got ${mixedTags.size} tags`);
    return false;
  }

  console.log("  PASS: Tag parsing and normalization");
  return true;
}

// ── Link Manager Tests ─────────────────────────────────────────────

function testLinkManagerRelationships(): boolean {
  const mgr = new MemoryLinkManager();

  // Process memories with links and tags
  mgr.processMemory(
    "mem_001",
    `First memory about #ai and #machine-learning. See [[mem_002]] for details.`,
  );
  mgr.processMemory(
    "mem_002",
    `Second memory about #ai and #deep-learning. Related to [[mem_001]] and [[mem_003]].`,
  );
  mgr.processMemory(
    "mem_003",
    `Third memory about #python programming.`,
  );

  // Test linked memories
  const linked = mgr.getLinkedMemories("mem_002");
  if (linked.length !== 2) {
    console.error(`FAIL: mem_002 should have 2 linked memories, got ${linked.length}`);
    return false;
  }

  // Test backlinks
  const backlinks = mgr.getBacklinks("mem_001");
  if (backlinks.length !== 1) {
    console.error(`FAIL: mem_001 should have 1 backlink, got ${backlinks.length}`);
    return false;
  }

  // Test tag search
  const aiMemories = mgr.searchByTag("ai");
  if (aiMemories.length !== 2) {
    console.error(`FAIL: Should find 2 memories tagged "ai", got ${aiMemories.length}`);
    return false;
  }

  // Test related memories (links + shared tags)
  const related = mgr.getRelatedMemories("mem_001");
  // mem_001 is linked to mem_002; backlinked from mem_002; shares #ai with mem_002
  // Should contain mem_002 and possibly mem_003 (no direct link/tag overlap, excluded)
  if (related.length < 1) {
    console.error(`FAIL: mem_001 should have at least 1 related memory (mem_002)`);
    return false;
  }

  // Test export
  const exported = mgr.exportLinks();
  if (!exported.links || !exported.tags || !exported.tag_index) {
    console.error("FAIL: export should include links, tags, and tag_index");
    return false;
  }

  console.log("  PASS: Link manager relationships and export");
  return true;
}

// ── Run ────────────────────────────────────────────────────────────


describe("links.test", () => {
  it("Link parsing and removal", () => {    expect(testLinkParsing()).toBe(true);  });
  it("Tag parsing and normalization", () => {    expect(testTagParsing()).toBe(true);  });
  it("Link manager relationships and export", () => {    expect(testLinkManagerRelationships()).toBe(true);  });
});
