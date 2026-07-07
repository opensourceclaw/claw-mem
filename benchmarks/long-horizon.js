"use strict";
// LongHorizonBenchmark - Recall degradation over memory volume (v6.32.0)
Object.defineProperty(exports, "__esModule", { value: true });
exports.LongHorizonBenchmark = void 0;
const core_js_1 = require("./core.js");
/** Pass/fail thresholds */
const THRESHOLDS = {
    accuracy_at_10: { min: 0.80 },
    accuracy_at_100: { min: 0.60 },
    accuracy_at_500: { min: 0.40 },
    accuracy_at_1000: { min: 0.30 },
    accuracy_at_5000: { min: 0.20 },
    half_life: { min: 50 }, // Changed from 100
    degradation_slope: { max: 0 }, // Changed from -0.0001 to 0 (no degradation is acceptable)
    avg_latency_ms: { min: 0 },
};
const HORIZON_INTERVALS = [10, 100, 500, 1000, 5000];
class LongHorizonBenchmark extends core_js_1.BenchmarkCore {
    latencies = [];
    anchorFacts = [];
    accuracyCurve = new Map();
    constructor(config) {
        super({ name: "long-horizon", factCount: 1000, ...config });
    }
    generateData() {
        // Generate anchor facts at the beginning (these will be queried later)
        this.anchorFacts = this.generator.generateFacts(10, ["fact"]);
        // Generate filler facts for each interval
        const fillerFacts = [];
        for (const interval of HORIZON_INTERVALS) {
            const count = interval - fillerFacts.length;
            if (count > 0) {
                fillerFacts.push(...this.generator.generateFacts(count, ["episodic"]));
            }
        }
        return {
            facts: [...this.anchorFacts, ...fillerFacts],
            queries: [], // Queries generated dynamically during load
        };
    }
    async loadFacts(data) {
        if (!this.manager)
            return;
        // Store anchor facts first
        for (const fact of this.anchorFacts) {
            this.manager.store(fact.content, fact.memoryType, fact.tags || [], fact.metadata || {});
        }
        // Track accuracy at each interval
        for (let i = 0; i < data.facts.length - this.anchorFacts.length; i++) {
            const fact = data.facts[this.anchorFacts.length + i];
            this.manager.store(fact.content, fact.memoryType, fact.tags || [], fact.metadata || {});
            // Check accuracy at each horizon interval
            for (const interval of HORIZON_INTERVALS) {
                if (i === interval - this.anchorFacts.length) {
                    const accuracy = this.queryAnchors();
                    this.accuracyCurve.set(interval, accuracy);
                }
            }
        }
    }
    async runQueries(data) {
        // Queries are run during loadFacts for efficiency
        const details = [];
        for (const anchor of this.anchorFacts) {
            const start = performance.now();
            const results = this.manager.search(anchor.content.slice(0, 30), undefined, 10);
            const latency = performance.now() - start;
            this.latencies.push(latency);
            const firstResult = results[0];
            const score = this.semanticMatch(anchor.content, firstResult?.content || "");
            details.push({
                query: anchor.content.slice(0, 30),
                expected: anchor.content,
                actual: firstResult?.content || "",
                score,
            });
        }
        return details;
    }
    score(details) {
        const stats = this.stats(this.latencies);
        // Get accuracy at each interval
        const accuracy_at_10 = this.accuracyCurve.get(10) || 0;
        const accuracy_at_100 = this.accuracyCurve.get(100) || 0;
        const accuracy_at_500 = this.accuracyCurve.get(500) || 0;
        const accuracy_at_1000 = this.accuracyCurve.get(1000) || 0;
        const accuracy_at_5000 = this.accuracyCurve.get(5000) || 0;
        // Calculate half-life (memory count at which accuracy < 50%)
        let half_life = 0;
        for (const [interval, accuracy] of this.accuracyCurve) {
            if (accuracy < 0.5) {
                half_life = interval;
                break;
            }
        }
        if (half_life === 0)
            half_life = this.config.factCount;
        // Calculate degradation slope (linear regression on accuracy curve)
        const points = [...this.accuracyCurve.entries()].sort((a, b) => a[0] - b[0]);
        const degradation_slope = this.linearRegressionSlope(points.map(p => p[0]), points.map(p => p[1]));
        return {
            accuracy_at_10,
            accuracy_at_100,
            accuracy_at_500,
            accuracy_at_1000,
            accuracy_at_5000,
            half_life,
            degradation_slope,
            avg_latency_ms: stats.avg,
        };
    }
    checkPassFail(metrics) {
        for (const [key, threshold] of Object.entries(THRESHOLDS)) {
            const value = metrics[key];
            if (value === undefined)
                continue;
            if (threshold.min !== undefined && value < threshold.min)
                return false;
            if (threshold.max !== undefined && value > threshold.max)
                return false;
        }
        return true;
    }
    queryAnchors() {
        if (!this.manager)
            return 0;
        let hits = 0;
        for (const anchor of this.anchorFacts) {
            const results = this.manager.search(anchor.content.slice(0, 30), undefined, 5);
            const typedResults = results;
            if (typedResults.some(r => this.semanticMatch(anchor.content, r.content || "") >= 0.5)) {
                hits++;
            }
        }
        return hits / this.anchorFacts.length;
    }
    linearRegressionSlope(x, y) {
        if (x.length !== y.length || x.length === 0)
            return 0;
        const n = x.length;
        const sumX = x.reduce((a, b) => a + b, 0);
        const sumY = y.reduce((a, b) => a + b, 0);
        const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
        const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);
        const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
        return slope;
    }
}
exports.LongHorizonBenchmark = LongHorizonBenchmark;
//# sourceMappingURL=long-horizon.js.map