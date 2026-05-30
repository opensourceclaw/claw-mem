// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Performance monitor with latency histogram and hit-rate tracking.
 *
 * Tracks search latency, cache performance, and memory usage.
 * Uses process.memoryUsage() instead of psutil for simplicity.
 */

export interface PerformanceStats {
  search_count: number;
  avg_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  uptime_seconds: number;
  memory_mb: number;
}

export class PerformanceMonitor {
  private _latencies: number[];
  private _cacheHits: number;
  private _cacheMisses: number;
  private _searchCount: number;
  private _totalLatency: number;
  private _minLatency: number;
  private _maxLatency: number;
  private _startTime: number;

  constructor() {
    this._latencies = [];
    this._cacheHits = 0;
    this._cacheMisses = 0;
    this._searchCount = 0;
    this._totalLatency = 0.0;
    this._minLatency = Infinity;
    this._maxLatency = 0.0;
    this._startTime = Date.now();
  }

  /**
   * Record a search operation with its latency.
   *
   * @param latencyMs - Latency in milliseconds
   */
  recordSearch(latencyMs: number): void {
    this._searchCount++;
    this._latencies.push(latencyMs);
    this._totalLatency += latencyMs;
    if (latencyMs < this._minLatency) {
      this._minLatency = latencyMs;
    }
    if (latencyMs > this._maxLatency) {
      this._maxLatency = latencyMs;
    }
  }

  /**
   * Record a cache hit.
   */
  recordCacheHit(): void {
    this._cacheHits++;
  }

  /**
   * Record a cache miss.
   */
  recordCacheMiss(): void {
    this._cacheMisses++;
  }

  /**
   * Get current performance statistics.
   *
   * @returns PerformanceStats object
   */
  getStats(): PerformanceStats {
    const latencies = this._latencies.length > 0
      ? [...this._latencies].sort((a, b) => a - b)
      : [0];
    const n = latencies.length;

    const percentile = (p: number): number => {
      const idx = Math.floor((n * p) / 100);
      return latencies[Math.min(idx, n - 1)];
    };

    const totalCalls = this._cacheHits + this._cacheMisses;

    return {
      search_count: this._searchCount,
      avg_latency_ms: Math.round((this._totalLatency / Math.max(1, n)) * 1000) / 1000,
      min_latency_ms: Math.round((this._minLatency === Infinity ? 0 : this._minLatency) * 1000) / 1000,
      max_latency_ms: Math.round(this._maxLatency * 1000) / 1000,
      p50_latency_ms: Math.round(percentile(50) * 1000) / 1000,
      p95_latency_ms: Math.round(percentile(95) * 1000) / 1000,
      p99_latency_ms: Math.round(percentile(99) * 1000) / 1000,
      cache_hits: this._cacheHits,
      cache_misses: this._cacheMisses,
      cache_hit_rate: this._cacheHits / Math.max(1, totalCalls),
      uptime_seconds: Math.round((Date.now() - this._startTime) / 1000 * 10) / 10,
      memory_mb: Math.round(this._memoryUsageMb() * 100) / 100,
    };
  }

  /**
   * Get current process memory usage in MB.
   * Uses Node.js process.memoryUsage() instead of psutil.
   */
  private _memoryUsageMb(): number {
    try {
      const mem = process.memoryUsage();
      return mem.rss / 1024 / 1024;
    } catch {
      return 0.0;
    }
  }

  /**
   * Reset all collected metrics.
   */
  reset(): void {
    this._latencies = [];
    this._cacheHits = 0;
    this._cacheMisses = 0;
    this._searchCount = 0;
    this._totalLatency = 0.0;
    this._minLatency = Infinity;
    this._maxLatency = 0.0;
    this._startTime = Date.now();
  }
}
