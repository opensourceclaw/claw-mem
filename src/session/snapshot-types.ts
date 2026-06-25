// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/** Session Snapshot — Type Definitions */
export const SNAPSHOT_TAG = "session_snapshot";

export interface SessionSnapshot {
  sessionId: string;
  startedAt: number;
  lastActiveAt: number;
  turnCount: number;
  currentTopic: string;
  activeTask?: {
    description: string;
    progress: string;
  };
  recentDecisions: string[];
  pendingItems: string[];
  keyEntities: string[];
  isClosed: boolean;
}

export interface SnapshotStoreOptions {
  maxSnapshotsPerSession?: number;
  maxAgeHours?: number;
}

export interface SnapshotStoreResult {
  stored: boolean;
  id: string;
}
