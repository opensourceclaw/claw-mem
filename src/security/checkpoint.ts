// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Checkpoint Manager (MVP Version)
 *
 * Creates regular memory snapshots with rollback support.
 */

import * as fs from "fs";
import * as path from "path";

export interface CheckpointData {
  checkpoint_id: string;
  session_id: string;
  timestamp: string;
  status: string;
}

export class CheckpointManager {
  private workspace: string;
  private checkpointDir: string;

  /**
   * @param workspace - Workspace directory path
   */
  constructor(workspace: string) {
    this.workspace = workspace;
    this.checkpointDir = path.join(workspace, ".checkpoints");
    fs.mkdirSync(this.checkpointDir, { recursive: true });
  }

  /**
   * Create a checkpoint for a session.
   *
   * @param sessionId - Session ID
   * @returns The checkpoint ID
   */
  create(sessionId: string): string {
    const now = new Date();
    const ts = now
      .toISOString()
      .replace(/[-:]/g, "")
      .replace(/\.\d{3}/, "")
      .replace("T", "_")
      .slice(0, 15);
    const checkpointId = `${sessionId}_${ts}`;

    const data: CheckpointData = {
      checkpoint_id: checkpointId,
      session_id: sessionId,
      timestamp: now.toISOString(),
      status: "created",
    };

    const filePath = path.join(this.checkpointDir, `${checkpointId}.json`);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
    return checkpointId;
  }

  /**
   * Save a session checkpoint.
   *
   * @param sessionId - Session ID
   * @returns Success status
   */
  save(sessionId: string): boolean {
    const now = new Date();
    const ts = now
      .toISOString()
      .replace(/[-:]/g, "")
      .replace(/\.\d{3}/, "")
      .replace("T", "_")
      .slice(0, 15);
    const checkpointId = `${sessionId}_${ts}`;

    const data: CheckpointData = {
      checkpoint_id: checkpointId,
      session_id: sessionId,
      timestamp: now.toISOString(),
      status: "saved",
    };

    const filePath = path.join(this.checkpointDir, `${checkpointId}.json`);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf-8");
    return true;
  }

  /**
   * Rollback to a specific checkpoint.
   *
   * MVP version: not implemented.
   *
   * @param checkpointId - Checkpoint ID
   * @returns Success status (always false in MVP)
   */
  rollback(checkpointId: string): boolean {
    console.warn(`Rollback feature not implemented yet: ${checkpointId}`);
    return false;
  }

  /**
   * List all checkpoints, optionally filtered by session ID.
   *
   * @param sessionId - Optional session ID filter
   * @returns Sorted list of checkpoint data (newest first)
   */
  listCheckpoints(sessionId?: string): CheckpointData[] {
    const checkpoints: CheckpointData[] = [];

    if (!fs.existsSync(this.checkpointDir)) {
      return checkpoints;
    }

    const files = fs.readdirSync(this.checkpointDir);
    for (const file of files) {
      if (!file.endsWith(".json")) continue;
      const filePath = path.join(this.checkpointDir, file);
      try {
        const raw = fs.readFileSync(filePath, "utf-8");
        const data: CheckpointData = JSON.parse(raw);
        if (sessionId === undefined || data.session_id === sessionId) {
          checkpoints.push(data);
        }
      } catch {
        // skip malformed files
      }
    }

    checkpoints.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    );
    return checkpoints;
  }
}
