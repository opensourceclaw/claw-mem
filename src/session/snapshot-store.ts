// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

import { SessionSnapshot, SnapshotStoreOptions, SnapshotStoreResult, SNAPSHOT_TAG } from "./snapshot-types.js";
import type { MemoryManager } from "../memory_manager.js";

const DEFAULT_MAX_AGE_HOURS = 48;
const MAX_SNAPSHOT_BYTES = 2048;

export class SnapshotStore {
  constructor(
    private manager: MemoryManager,
    private options: SnapshotStoreOptions = {},
  ) {}

  store(snapshot: SessionSnapshot): SnapshotStoreResult {
    const safe = this.enforceSizeLimit(snapshot);
    const content = `[${SNAPSHOT_TAG}] ${JSON.stringify(safe)}`;
    const tags = [SNAPSHOT_TAG, `session:${safe.sessionId}`];
    const ok = this.manager.store(content, "episodic", tags, {
      sessionId: safe.sessionId,
      lastActiveAt: safe.lastActiveAt,
      isClosed: safe.isClosed,
    });
    return { stored: ok, id: `snap_${Date.now()}` };
  }

  getLatest(sessionId?: string): SessionSnapshot | null {
    const all = this.loadAll();
    const filtered = sessionId
      ? all.filter((s) => s.sessionId === sessionId)
      : all;
    if (filtered.length === 0) return null;
    return filtered.reduce((a, b) => (b.lastActiveAt > a.lastActiveAt ? b : a));
  }

  close(sessionId: string): { closed: boolean } {
    const latest = this.getLatest(sessionId);
    if (!latest) return { closed: false };
    // Monotonic lastActiveAt: same-ms writes would otherwise keep the
    // unclosed snapshot as "latest" (getLatest picks strictly greater).
    this.store({ ...latest, isClosed: true, lastActiveAt: Math.max(Date.now(), latest.lastActiveAt + 1) });
    return { closed: true };
  }

  getUnclosed(): SessionSnapshot[] {
    const latestPerSession = this.groupLatestBySession(this.loadAll());
    const cutoff = Date.now() - this.maxAgeMs();
    return latestPerSession.filter(
      (s) => !s.isClosed && s.lastActiveAt >= cutoff,
    );
  }

  private loadAll(): SessionSnapshot[] {
    const all = this.manager.episodic.getAll();
    return all
      .filter((r) => r.tags.includes(SNAPSHOT_TAG))
      .map((r) => {
        try {
          const content = r.content.replace(`[${SNAPSHOT_TAG}] `, "");
          return JSON.parse(content) as SessionSnapshot;
        }
        catch { return null; }
      })
      .filter((s): s is SessionSnapshot => s !== null);
  }

  private groupLatestBySession(all: SessionSnapshot[]): SessionSnapshot[] {
    const map = new Map<string, SessionSnapshot>();
    for (const s of all) {
      const cur = map.get(s.sessionId);
      if (!cur || s.lastActiveAt > cur.lastActiveAt) map.set(s.sessionId, s);
    }
    return [...map.values()];
  }

  private maxAgeMs(): number {
    return (this.options.maxAgeHours ?? DEFAULT_MAX_AGE_HOURS) * 3600_000;
  }

  private enforceSizeLimit(snapshot: SessionSnapshot): SessionSnapshot {
    let s = { ...snapshot };
    const size = () => Buffer.byteLength(JSON.stringify(s), "utf-8");
    if (size() <= MAX_SNAPSHOT_BYTES) return s;

    // Truncate arrays
    s = { ...s, pendingItems: s.pendingItems.slice(0, 3) };
    if (size() <= MAX_SNAPSHOT_BYTES) return s;
    s = { ...s, recentDecisions: s.recentDecisions.slice(0, 3) };
    if (size() <= MAX_SNAPSHOT_BYTES) return s;
    s = { ...s, keyEntities: s.keyEntities.slice(0, 5) };
    if (size() <= MAX_SNAPSHOT_BYTES) return s;

    // Truncate string lengths
    s = {
      ...s,
      pendingItems: s.pendingItems.map((v) => v.slice(0, 100)),
      recentDecisions: s.recentDecisions.map((v) => v.slice(0, 100)),
      keyEntities: s.keyEntities.map((v) => v.slice(0, 100)),
    };
    if (size() <= MAX_SNAPSHOT_BYTES) return s;

    // Truncate activeTask progress
    if (s.activeTask) {
      s = { ...s, activeTask: { ...s.activeTask, progress: s.activeTask.progress.slice(0, 120) } };
    }
    return s;
  }
}
