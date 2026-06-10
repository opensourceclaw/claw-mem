// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/** claw-mem v5.0.0 — Importance Scoring (TS) */

export interface ImportanceResult {
  score: number;
  factors: Record<string, number>;
}

export class ImportanceScorer {
  score(content: string, metadata?: Record<string, unknown>): ImportanceResult {
    const factors: Record<string, number> = {};

    // 1. Length factor (longer content = potentially more important)
    factors.length = Math.min(content.length / 500, 1.0) * 0.2;

    // 2. Keyword density (technical terms suggest importance)
    const techKeywords = [
      "critical", "important", "urgent", "security", "bug", "fix",
      "deploy", "production", "breaking", "migration", "incident",
      "必须", "重 to ", "紧急", "安全", "生产", "故障",
    ];
    const keywordHits = techKeywords.filter((kw) => content.toLowerCase().includes(kw)).length;
    factors.keywords = Math.min(keywordHits / 5, 1.0) * 0.3;

    // 3. Metadata boost (tagged memories are more relevant)
    const tags = (metadata?.tags as string[]) ?? [];
    factors.metadata = Math.min(tags.length / 3, 1.0) * 0.2;

    // 4. Recency factor (from timestamp)
    const ts = metadata?.timestamp as string | undefined;
    factors.recency = ts ? this._recencyScore(ts) * 0.3 : 0.2;

    const score = Object.values(factors).reduce((s, v) => s + v, 0);
    return { score: Math.max(0, Math.min(1, score)), factors };
  }

  private _recencyScore(timestamp: string): number {
    try {
      const ageHrs = (Date.now() - new Date(timestamp).getTime()) / 3600000;
      return Math.exp(-ageHrs / 24);
    } catch { return 0.5; }
  }
}
