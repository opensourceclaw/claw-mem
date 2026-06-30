// Version Chain - Preference version history storage (v6.31.0)

import type { MemoryRecord } from "../types.js";
import type { SemanticStorage } from "./semantic.js";
import * as fs from "fs";
import * as path from "path";

/** Version entry in the chain */
export interface VersionEntry {
  version: number;
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

/** Version chain file format */
interface VersionChainFile {
  pref_key: string;
  versions: VersionEntry[];
}

/** Version chain store for preferences */
export class VersionChain {
  private preferencesDir: string;

  constructor(workspace: string) {
    this.preferencesDir = path.join(workspace, "memory", "preferences");
    fs.mkdirSync(this.preferencesDir, { recursive: true });
  }

  /** Archive an old version of a preference */
  archive(prefKey: string, record: MemoryRecord): number {
    const filePath = this.getFilePath(prefKey);

    // Load existing chain or create new
    let chain: VersionChainFile;
    if (fs.existsSync(filePath)) {
      try {
        chain = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      } catch {
        chain = { pref_key: prefKey, versions: [] };
      }
    } else {
      chain = { pref_key: prefKey, versions: [] };
    }

    // Add new version
    const newVersion: VersionEntry = {
      version: chain.versions.length + 1,
      content: record.text,
      timestamp: record.created_at || new Date().toISOString(),
      metadata: record.metadata,
    };

    chain.versions.push(newVersion);

    // Atomic write
    this.writeAtomic(filePath, JSON.stringify(chain, null, 2));

    return newVersion.version;
  }

  /** Get all versions of a preference */
  getHistory(prefKey: string): VersionEntry[] {
    const filePath = this.getFilePath(prefKey);
    if (!fs.existsSync(filePath)) return [];

    try {
      const chain: VersionChainFile = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      return chain.versions || [];
    } catch {
      return [];
    }
  }

  /** Get a specific version */
  getVersion(prefKey: string, version: number): VersionEntry | undefined {
    const history = this.getHistory(prefKey);
    return history.find(v => v.version === version);
  }

  /** Get latest version number */
  getLatestVersion(prefKey: string): number {
    const history = this.getHistory(prefKey);
    return history.length > 0 ? history[history.length - 1].version : 0;
  }

  /** Rollback to a previous version (creates a new version with old content) */
  rollback(prefKey: string, version: number, context: { semantic: SemanticStorage }): VersionEntry {
    const targetVersion = this.getVersion(prefKey, version);

    if (!targetVersion) {
      throw new Error(`Version ${version} not found for preference ${prefKey}`);
    }

    // Create new version with old content
    const newVersionEntry: VersionEntry = {
      version: this.getLatestVersion(prefKey) + 1,
      content: targetVersion.content,
      timestamp: new Date().toISOString(),
      metadata: {
        ...targetVersion.metadata,
        rollback_from: version,
      },
    };

    // Add to chain
    const filePath = this.getFilePath(prefKey);
    let chain: VersionChainFile;
    try {
      chain = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    } catch {
      chain = { pref_key: prefKey, versions: [] };
    }
    chain.versions.push(newVersionEntry);
    this.writeAtomic(filePath, JSON.stringify(chain, null, 2));

    // Update semantic storage with rolled-back content
    const existingPrefs = context.semantic.searchByTag(`pref:${prefKey}`);
    if (existingPrefs.length > 0) {
      const prefId = existingPrefs[0].id;
      if (prefId) {
        context.semantic.update(prefId, targetVersion.content);
      }
    }

    return newVersionEntry;
  }

  /** Clear version history for a preference */
  clearHistory(prefKey: string): void {
    const filePath = this.getFilePath(prefKey);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  }

  /** Get file path for a preference key (sanitized) */
  private getFilePath(prefKey: string): string {
    // Sanitize pref_key to prevent path traversal
    const sanitized = prefKey.replace(/[^a-zA-Z0-9_-]/g, "_");
    return path.join(this.preferencesDir, `${sanitized}.json`);
  }

  /** Atomic write using temp + rename */
  private writeAtomic(filePath: string, content: string): void {
    const tmpPath = filePath + ".tmp." + Date.now();
    fs.writeFileSync(tmpPath, content, "utf-8");
    fs.renameSync(tmpPath, filePath);
  }
}
