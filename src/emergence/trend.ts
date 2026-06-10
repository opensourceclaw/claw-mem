// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * TrendAnalyzer — track tag trends over time.
 */

import type { MemoryPool } from "../memory/pool.js";
import type { TrendPoint, TrendLine, TagTrend } from "./types.js";

export class TrendAnalyzer {
  private _pool: MemoryPool;

  constructor(pool: MemoryPool) {
    this._pool = pool;
  }

  track(tag: string, timeWindowMs: number = 3600000): TrendLine {
    const records = this._pool.query({});
    const tagged = records.filter((r) => r.tags.includes(tag));
    if (tagged.length === 0) {
      return { tag, points: [], slope: 0, direction: "stable" };
    }

    const sorted = [...tagged].sort((a, b) => a.timestamp - b.timestamp);
    const minTs = sorted[0].timestamp * 1000;
    const maxTs = sorted[sorted.length - 1].timestamp * 1000;

    const points: TrendPoint[] = [];
    for (let t = minTs; t <= maxTs; t += timeWindowMs) {
      const end = t + timeWindowMs;
      const bucket = sorted.filter(
        (r) => r.timestamp * 1000 >= t && r.timestamp * 1000 < end,
      );
      if (bucket.length > 0) {
        const agents = new Set(bucket.map((r) => r.agent_id));
        points.push({
          timestamp: t / 1000,
          count: bucket.length,
          agentCount: agents.size,
        });
      }
    }

    if (points.length < 2) {
      const direction: "rising" | "falling" | "stable" = "stable";
      return { tag, points, slope: 0, direction };
    }

    // Simple linear regression
    const n = points.length;
    const xMean = points.reduce((s, p) => s + p.timestamp, 0) / n;
    const yMean = points.reduce((s, p) => s + p.count, 0) / n;
    let num = 0;
    let den = 0;
    for (const p of points) {
      num += (p.timestamp - xMean) * (p.count - yMean);
      den += (p.timestamp - xMean) ** 2;
    }
    const slope = den === 0 ? 0 : num / den;

    let direction: "rising" | "falling" | "stable";
    if (slope > 1e-9) direction = "rising";
    else if (slope < -1e-9) direction = "falling";
    else direction = "stable";

    return { tag, points, slope: Math.round(slope * 1e6) / 1e6, direction };
  }

  rising(threshold: number = 0, timeWindowMs: number = 3600000): TagTrend[] {
    const allTags = this._collectAllTags();
    const trends: TagTrend[] = [];

    for (const tag of allTags) {
      const line = this.track(tag, timeWindowMs);
      if (line.direction !== "rising") continue;

      const pts = line.points;
      if (pts.length < 2) continue;

      const half = Math.floor(pts.length / 2);
      const prevCount = pts.slice(0, half).reduce((s, p) => s + p.count, 0);
      const currCount = pts.slice(half).reduce((s, p) => s + p.count, 0);
      const changePercent = prevCount > 0
        ? Math.round(((currCount - prevCount) / prevCount) * 1000) / 10
        : 100;

      if (changePercent > threshold) {
        trends.push({ tag, currentCount: currCount, previousCount: prevCount, changePercent, direction: "rising" });
      }
    }

    return trends.sort((a, b) => b.changePercent - a.changePercent);
  }

  falling(threshold: number = 0, timeWindowMs: number = 3600000): TagTrend[] {
    const allTags = this._collectAllTags();
    const trends: TagTrend[] = [];

    for (const tag of allTags) {
      const line = this.track(tag, timeWindowMs);
      if (line.direction !== "falling") continue;

      const pts = line.points;
      if (pts.length < 2) continue;

      const half = Math.floor(pts.length / 2);
      const prevCount = pts.slice(0, half).reduce((s, p) => s + p.count, 0);
      const currCount = pts.slice(half).reduce((s, p) => s + p.count, 0);
      const changePercent = prevCount > 0
        ? Math.round(((prevCount - currCount) / prevCount) * 1000) / 10
        : 0;

      if (changePercent > threshold) {
        trends.push({ tag, currentCount: currCount, previousCount: prevCount, changePercent, direction: "falling" });
      }
    }

    return trends.sort((a, b) => b.changePercent - a.changePercent);
  }

  private _collectAllTags(): string[] {
    const records = this._pool.query({});
    const tags = new Set<string>();
    for (const r of records) {
      for (const t of r.tags) tags.add(t);
    }
    return [...tags];
  }
}
