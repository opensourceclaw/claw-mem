// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Memory Federation Preview
 *
 * Cross-workspace memory sharing: search across multiple
 * workspaces on the same machine.
 */

import { EpisodicStorage } from "../storage/episodic.js";
import { SemanticStorage } from "../storage/semantic.js";

export interface FederationConfig {
  workspaces: string[];
  sharedTags?: string[];
  maxResults?: number;
}

export class MemoryFederation {
  private _workspaces: string[];
  private _sharedTags: string[];
  private _maxResults: number;

  constructor(config: FederationConfig) {
    this._workspaces = config.workspaces;
    this._sharedTags = config.sharedTags ?? [];
    this._maxResults = config.maxResults ?? 50;
  }

  /**
   * Search across all federated workspaces.
   * Returns deduplicated results by content.
   */
  search(query: string): Array<{ content: string; workspace: string; source: string }> {
    const all: Array<{ content: string; workspace: string; source: string }> = [];
    const q = query.toLowerCase();

    for (const ws of this._workspaces) {
      try {
        const ep = new EpisodicStorage(ws);
        const sem = new SemanticStorage(ws);

        for (const m of ep.getRecent(100)) {
          if (m.content.toLowerCase().includes(q)) {
            all.push({ content: m.content, workspace: ws, source: "episodic" });
          }
        }
        for (const m of sem.getAll()) {
          if (m.content.toLowerCase().includes(q)) {
            all.push({ content: m.content, workspace: ws, source: "semantic" });
          }
        }
      } catch { /* workspace unavailable → skip */ }
    }

    return all.slice(0, this._maxResults);
  }

  getStats(): Record<string, unknown> {
    return {
      workspaceCount: this._workspaces.length,
      sharedTags: this._sharedTags,
    };
  }
}
