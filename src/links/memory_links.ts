// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * claw-mem Memory Links and Tags
 *
 * Simple markdown-based linking and tagging system.
 * Maintains simplicity while adding association capabilities.
 *
 * Syntax:
 * - Links: [[memory_id]] or [[2026-03-25#investment-decision]]
 * - Tags: #tag or #tagname
 */

export interface MemoryLinkData {
  source_id: string;
  target_id: string;
  link_type: string;
  created_at: string;
}

export class MemoryLink {
  sourceId: string;
  targetId: string;
  linkType: string;
  createdAt: string;

  constructor(
    sourceId: string,
    targetId: string,
    linkType: string = "reference",
    createdAt?: string,
  ) {
    this.sourceId = sourceId;
    this.targetId = targetId;
    this.linkType = linkType;
    this.createdAt = createdAt ?? new Date().toISOString();
  }

  toDict(): MemoryLinkData {
    return {
      source_id: this.sourceId,
      target_id: this.targetId,
      link_type: this.linkType,
      created_at: this.createdAt,
    };
  }
}

export interface MemoryTagsData {
  memory_id: string;
  tags: string[];
  updated_at: string;
}

export class MemoryTags {
  memoryId: string;
  tags: Set<string>;
  updatedAt: string;

  constructor(memoryId: string, tags?: Set<string>, updatedAt?: string) {
    this.memoryId = memoryId;
    this.tags = tags ?? new Set();
    this.updatedAt = updatedAt ?? new Date().toISOString();
  }

  toDict(): MemoryTagsData {
    return {
      memory_id: this.memoryId,
      tags: [...this.tags],
      updated_at: this.updatedAt,
    };
  }
}

/**
 * Memory Link Parser
 *
 * Parses [[memory_id]] syntax from markdown content.
 */
export class MemoryLinkParser {
  // Pattern: [[memory_id]] or [[date#title]]
  private static LINK_RE = /\[\[([^\]]+)\]\]/g;

  /**
   * Parse links from content.
   *
   * @param content  - Markdown content
   * @param sourceId - Source memory ID
   * @returns Parsed MemoryLink instances
   */
  parseLinks(content: string, sourceId: string): MemoryLink[] {
    const links: MemoryLink[] = [];
    let match: RegExpExecArray | null;

    // Reset regex state
    MemoryLinkParser.LINK_RE.lastIndex = 0;

    while ((match = MemoryLinkParser.LINK_RE.exec(content)) !== null) {
      const target = match[1].trim();

      // Parse target (could be memory_id or date#title)
      let targetId: string;
      if (target.includes("#")) {
        const [datePart, titlePart] = target.split("#", 2);
        targetId = `${datePart}#${titlePart}`;
      } else {
        targetId = target;
      }

      links.push(new MemoryLink(sourceId, targetId, "reference"));
    }

    return links;
  }

  /**
   * Remove link syntax from content, leaving just the link text.
   *
   * @param content - Markdown content
   * @returns Content without link syntax
   */
  removeLinks(content: string): string {
    return content.replace(MemoryLinkParser.LINK_RE, "$1");
  }

  /**
   * Extract link targets from content.
   *
   * @param content - Markdown content
   * @returns List of link target strings
   */
  extractLinkTargets(content: string): string[] {
    const targets: string[] = [];
    let match: RegExpExecArray | null;

    MemoryLinkParser.LINK_RE.lastIndex = 0;

    while ((match = MemoryLinkParser.LINK_RE.exec(content)) !== null) {
      targets.push(match[1].trim());
    }

    return targets;
  }
}

/**
 * Memory Tag Parser
 *
 * Parses #tag syntax from markdown content.
 */
export class MemoryTagParser {
  // Pattern: #tag or #tagname (Unicode supported)
  private static TAG_RE = /#([a-zA-Z0-9\u4e00-\u9fa5_]+)/g;

  /**
   * Parse tags from content.
   *
   * @param content - Markdown content
   * @returns Set of parsed tags (lowercased)
   */
  parseTags(content: string): Set<string> {
    const tags = new Set<string>();
    let match: RegExpExecArray | null;

    MemoryTagParser.TAG_RE.lastIndex = 0;

    while ((match = MemoryTagParser.TAG_RE.exec(content)) !== null) {
      const tag = match[1].trim();
      tags.add(tag.toLowerCase());
    }

    return tags;
  }

  /**
   * Remove tag syntax from content.
   *
   * @param content - Markdown content
   * @returns Content without tag syntax
   */
  removeTags(content: string): string {
    return content.replace(MemoryTagParser.TAG_RE, "");
  }

  /**
   * Extract tags from content.
   *
   * @param content - Markdown content
   * @returns Set of tags
   */
  extractTags(content: string): Set<string> {
    return this.parseTags(content);
  }
}

/**
 * Memory Link Manager
 *
 * Manages memory links and tags with in-memory storage.
 */
export class MemoryLinkManager {
  linkParser: MemoryLinkParser;
  tagParser: MemoryTagParser;

  // source_id -> links
  private links: Map<string, MemoryLink[]>;
  // memory_id -> tags
  private tags: Map<string, MemoryTags>;
  // tag -> memory_ids
  private tagIndex: Map<string, Set<string>>;

  constructor() {
    this.linkParser = new MemoryLinkParser();
    this.tagParser = new MemoryTagParser();
    this.links = new Map();
    this.tags = new Map();
    this.tagIndex = new Map();
  }

  /**
   * Process a memory: extract links and tags from content.
   *
   * @param memoryId - Memory ID
   * @param content  - Memory content
   * @returns Tuple of [links, tags]
   */
  processMemory(memoryId: string, content: string): [MemoryLink[], Set<string>] {
    const extractedLinks = this.linkParser.parseLinks(content, memoryId);
    const extractedTags = this.tagParser.parseTags(content);

    // Store links
    this.links.set(memoryId, extractedLinks);

    // Store tags
    this._updateTags(memoryId, extractedTags);

    return [extractedLinks, extractedTags];
  }

  private _updateTags(memoryId: string, newTags: Set<string>): void {
    // Remove from old tag index
    if (this.tags.has(memoryId)) {
      const oldTags = this.tags.get(memoryId)!.tags;
      for (const tag of oldTags) {
        const idx = this.tagIndex.get(tag);
        if (idx) {
          idx.delete(memoryId);
          if (idx.size === 0) {
            this.tagIndex.delete(tag);
          }
        }
      }
    }

    // Update tags
    this.tags.set(
      memoryId,
      new MemoryTags(memoryId, newTags, new Date().toISOString()),
    );

    // Update tag index
    for (const tag of newTags) {
      if (!this.tagIndex.has(tag)) {
        this.tagIndex.set(tag, new Set());
      }
      this.tagIndex.get(tag)!.add(memoryId);
    }
  }

  /**
   * Get memory IDs linked from a memory.
   *
   * @param memoryId - Memory ID
   * @returns List of linked memory IDs
   */
  getLinkedMemories(memoryId: string): string[] {
    const links = this.links.get(memoryId);
    if (!links) return [];
    return links.map((l) => l.targetId);
  }

  /**
   * Get memory IDs that link to this memory (backlinks).
   *
   * @param memoryId - Memory ID
   * @returns List of backlink memory IDs
   */
  getBacklinks(memoryId: string): string[] {
    const backlinks: string[] = [];
    for (const [sourceId, linkList] of this.links) {
      for (const link of linkList) {
        if (link.targetId === memoryId) {
          backlinks.push(sourceId);
        }
      }
    }
    return backlinks;
  }

  /**
   * Search memories by tag.
   *
   * @param tag - Tag name
   * @returns Memory IDs with this tag
   */
  searchByTag(tag: string): string[] {
    const lower = tag.toLowerCase();
    return [...(this.tagIndex.get(lower) ?? new Set())];
  }

  /**
   * Get tags for a memory.
   *
   * @param memoryId - Memory ID
   * @returns Set of tags
   */
  getTagsForMemory(memoryId: string): Set<string> {
    const entry = this.tags.get(memoryId);
    return entry ? new Set(entry.tags) : new Set();
  }

  /**
   * Get all tags in the system.
   *
   * @returns Set of all tag names
   */
  getAllTags(): Set<string> {
    return new Set(this.tagIndex.keys());
  }

  /**
   * Get related memories (links + shared tags).
   *
   * @param memoryId - Memory ID
   * @param limit    - Maximum results (default 10)
   * @returns Related memory IDs
   */
  getRelatedMemories(memoryId: string, limit: number = 10): string[] {
    const related = new Set<string>();

    // Add linked memories
    const linked = this.getLinkedMemories(memoryId);
    for (const id of linked) related.add(id);

    // Add backlinks
    const backlinks = this.getBacklinks(memoryId);
    for (const id of backlinks) related.add(id);

    // Add memories with shared tags
    const myTags = this.getTagsForMemory(memoryId);
    for (const tag of myTags) {
      const tagged = this.searchByTag(tag);
      for (const id of tagged) related.add(id);
    }

    // Remove self
    related.delete(memoryId);

    return [...related].slice(0, limit);
  }

  /**
   * Export all links and tags.
   *
   * @returns Exported data object
   */
  exportLinks(): Record<string, unknown> {
    const linksObj: Record<string, MemoryLinkData[]> = {};
    for (const [source, linkList] of this.links) {
      linksObj[source] = linkList.map((l) => l.toDict());
    }

    const tagsObj: Record<string, MemoryTagsData> = {};
    for (const [memId, tagEntry] of this.tags) {
      tagsObj[memId] = tagEntry.toDict();
    }

    const tagIdxObj: Record<string, string[]> = {};
    for (const [tag, memIds] of this.tagIndex) {
      tagIdxObj[tag] = [...memIds];
    }

    return {
      links: linksObj,
      tags: tagsObj,
      tag_index: tagIdxObj,
    };
  }
}
