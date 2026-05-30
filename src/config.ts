// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Configuration Manager (TypeScript)
 *
 * YAML-based config loading with js-yaml.
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as yaml from "js-yaml";

export interface MemoryConfigOptions {
  workspace?: string;
  autoDetect?: boolean;
  enableGating?: boolean;
  enableGraph?: boolean;
  enableCache?: boolean;
  enableCompression?: boolean;
  enableDecay?: boolean;
  enableGroundTruth?: boolean;
  bm25K1?: number;
  bm25B?: number;
  bm25Weight?: number;
  gatingThreshold?: number;
  maxStaged?: number;
  topK?: number;
  enableSkillExtraction?: boolean;
}

export class MemoryConfig {
  [key: string]: unknown;
  workspace = "";
  autoDetect = true;
  enableGating = false;
  enableGraph = false;
  enableCache = true;
  enableCompression = true;
  enableDecay = false;
  enableGroundTruth = false;
  bm25K1 = 1.5;
  bm25B = 0.75;
  bm25Weight = 0.7;
  keywordWeight = 0.3;
  gatingThreshold = 0.6;
  maxStaged = 500;
  topK = 10;
  enableSkillExtraction = true;

  constructor(opts: Partial<MemoryConfigOptions> = {}) {
    Object.assign(this, opts);
  }

  static default(): MemoryConfig { return new MemoryConfig(); }

  toDict(): Record<string, unknown> {
    return { ...this as unknown as Record<string, unknown> };
  }

  static fromDict(d: Record<string, unknown>): MemoryConfig {
    return new MemoryConfig(d as unknown as MemoryConfigOptions);
  }
}

/** Unified config for YAML persistence. */
export interface UnifiedConfigData {
  version?: string;
  workspace?: string;
  memory?: Record<string, unknown>;
  retrieval?: Record<string, unknown>;
  performance?: Record<string, unknown>;
}

const DEFAULT_CONFIG_PATH = path.join(os.homedir(), ".claw-mem", "config.yml");

export class ConfigManager {
  private configPath: string;
  config: MemoryConfig;

  constructor(customPath?: string) {
    this.configPath = customPath ?? DEFAULT_CONFIG_PATH;
    this.config = new MemoryConfig();
    this.load();
  }

  load(): boolean {
    if (!fs.existsSync(this.configPath)) {
      this.save();
      return true;
    }
    try {
      const raw = fs.readFileSync(this.configPath, "utf-8");
      const data = yaml.load(raw) as Record<string, unknown> | undefined;
      if (data && data.workspace) {
        this.config.workspace = String(data.workspace);
      }
      if (data && data.memory) {
        const m = data.memory as Record<string, unknown>;
        if (m.enableGating !== undefined) this.config.enableGating = !!m.enableGating;
        if (m.enableCompression !== undefined) this.config.enableCompression = !!m.enableCompression;
        if (m.topK !== undefined) this.config.topK = Number(m.topK);
      }
      if (data && data.retrieval) {
        const r = data.retrieval as Record<string, unknown>;
        if (r.maxResults !== undefined) this.config.topK = Number(r.maxResults);
      }
      return true;
    } catch {
      return false;
    }
  }

  save(): void {
    fs.mkdirSync(path.dirname(this.configPath), { recursive: true });
    const data: UnifiedConfigData = {
      version: "5.0.0",
      workspace: this.config.workspace || undefined,
      memory: { topK: this.config.topK, enableGating: this.config.enableGating },
    };
    fs.writeFileSync(this.configPath, yaml.dump(data), "utf-8");
  }

  get(key: string, defaultValue: unknown = undefined): unknown {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (this.config as any)[key] ?? defaultValue;
  }

  set(key: string, value: unknown): void {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (this.config as any)[key] = value;
  }
}

let _globalConfig: ConfigManager | null = null;

export function getConfig(): ConfigManager {
  if (!_globalConfig) _globalConfig = new ConfigManager();
  return _globalConfig;
}
export function reloadConfig(): void {
  _globalConfig = new ConfigManager();
}
