// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Checkpoint Manager (TS)
 *
 * Manages session checkpoints with in-memory storage and disk persistence.
 * Supports save, restore, rollback, and FIFO eviction.
 */

import * as fs from "fs";
import * as path from "path";
import type { CheckpointData, CheckpointOptions, SessionMessage, SessionState } from "./types.js";

let checkpointCounter = 0;

export class CheckpointManager {
  private checkpoints: Map<string, CheckpointData[]>;
  private options: Required<CheckpointOptions>;

  constructor(options?: CheckpointOptions) {
    this.checkpoints = new Map();
    this.options = {
      maxMessages: options?.maxMessages ?? 100,
      intervalMinutes: options?.intervalMinutes ?? 30,
      maxCheckpoints: options?.maxCheckpoints ?? 10,
      storageDir: options?.storageDir ?? "./checkpoints",
    };
  }

  /** Create a checkpoint in memory. */
  create(sessionId: string, data: Partial<CheckpointData>): CheckpointData {
    if (!sessionId) throw new TypeError("sessionId cannot be empty");

    const now = new Date().toISOString();
    checkpointCounter++;
    const existing = this.checkpoints.get(sessionId) ?? [];

    const checkpoint: CheckpointData = {
      checkpointId: `cp_${sessionId}_${Date.now()}_${checkpointCounter}`,
      sessionId,
      timestamp: now,
      status: "created",
      messages: data.messages ?? [],
      sessionState: data.sessionState ?? this.defaultSessionState(sessionId),
      summary: data.summary ?? "",
      metadata: {
        messageCount: data.messages?.length ?? 0,
        tokenCount: data.metadata?.tokenCount ?? 0,
        lastTopic: data.metadata?.lastTopic ?? data.sessionState?.topic ?? "",
      },
    };

    existing.push(checkpoint);

    // FIFO eviction if over maxCheckpoints
    while (existing.length > this.options.maxCheckpoints) {
      existing.shift();
    }

    this.checkpoints.set(sessionId, existing);
    return checkpoint;
  }

  /** Save a checkpoint to disk. */
  save(sessionId: string): boolean {
    const existing = this.checkpoints.get(sessionId);
    if (!existing || existing.length === 0) return false;

    const latest = existing[existing.length - 1];
    const dir = path.join(this.options.storageDir, sessionId);

    try {
      fs.mkdirSync(dir, { recursive: true });
      const filename = `checkpoint-${Date.now()}-${existing.length - 1}.json`;
      const filePath = path.join(dir, filename);
      fs.writeFileSync(filePath, JSON.stringify(latest, null, 2), "utf-8");
      latest.status = "saved";
      return true;
    } catch {
      return false;
    }
  }

  /** Restore a checkpoint from disk. */
  restore(checkpointId: string): CheckpointData | null {
    // Search all sessions
    for (const [, cps] of this.checkpoints.entries()) {
      const found = cps.find((cp) => cp.checkpointId === checkpointId);
      if (found) {
        found.status = "restored";
        return found;
      }
    }

    // Try disk
    try {
      const storageDir = this.options.storageDir;
      if (!fs.existsSync(storageDir)) return null;

      const sessionDirs = fs.readdirSync(storageDir);
      for (const sessionDir of sessionDirs) {
        const dirPath = path.join(storageDir, sessionDir);
        if (!fs.statSync(dirPath).isDirectory()) continue;

        const files = fs.readdirSync(dirPath).filter((f) => f.endsWith(".json"));
        for (const file of files) {
          const filePath = path.join(dirPath, file);
          const raw = fs.readFileSync(filePath, "utf-8");
          const data = JSON.parse(raw) as CheckpointData;
          if (data.checkpointId === checkpointId) {
            data.status = "restored";
            return data;
          }
        }
      }
    } catch {
      return null;
    }

    return null;
  }

  /** Rollback to a specific checkpoint. */
  rollback(checkpointId: string): boolean {
    const checkpoint = this.restore(checkpointId);
    if (!checkpoint) return false;

    // Clear subsequent checkpoints for this session
    const existing = this.checkpoints.get(checkpoint.sessionId);
    if (existing) {
      const idx = existing.findIndex((cp) => cp.checkpointId === checkpointId);
      if (idx >= 0) {
        this.checkpoints.set(checkpoint.sessionId, existing.slice(0, idx + 1));
      }
    }

    return true;
  }

  /** List checkpoints, optionally filtered by session. */
  listCheckpoints(sessionId?: string): CheckpointData[] {
    if (sessionId) {
      return this.checkpoints.get(sessionId) ?? [];
    }

    const all: CheckpointData[] = [];
    for (const cps of this.checkpoints.values()) {
      all.push(...cps);
    }
    return all;
  }

  /** Clean up old checkpoints. */
  cleanup(maxAgeHours: number): number {
    const cutoff = Date.now() - maxAgeHours * 60 * 60 * 1000;
    let removed = 0;

    for (const [sessionId, cps] of this.checkpoints.entries()) {
      const before = cps.length;
      this.checkpoints.set(
        sessionId,
        cps.filter((cp) => new Date(cp.timestamp).getTime() >= cutoff),
      );
      removed += before - this.checkpoints.get(sessionId)!.length;
    }

    // Clean disk
    try {
      const storageDir = this.options.storageDir;
      if (fs.existsSync(storageDir)) {
        const sessionDirs = fs.readdirSync(storageDir);
        for (const sessionDir of sessionDirs) {
          const dirPath = path.join(storageDir, sessionDir);
          if (!fs.statSync(dirPath).isDirectory()) continue;

          const files = fs.readdirSync(dirPath).filter((f) => f.endsWith(".json"));
          for (const file of files) {
            const filePath = path.join(dirPath, file);
            try {
              const raw = fs.readFileSync(filePath, "utf-8");
              const data = JSON.parse(raw) as CheckpointData;
              if (new Date(data.timestamp).getTime() < cutoff) {
                fs.unlinkSync(filePath);
                removed++;
              }
            } catch {
              // Skip unreadable files
            }
          }
        }
      }
    } catch {
      // Disk cleanup errors are non-fatal
    }

    return removed;
  }

  private defaultSessionState(sessionId: string): SessionState {
    return {
      sessionId,
      status: "active",
      lastActivity: new Date().toISOString(),
      topic: "",
      tags: [],
      metadata: {},
    };
  }
}
