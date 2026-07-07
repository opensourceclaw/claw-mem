"use strict";
// UpdateRobustnessBenchmark - Update correctness test (v6.32.0)
Object.defineProperty(exports, "__esModule", { value: true });
exports.UpdateRobustnessBenchmark = void 0;
const core_js_1 = require("./core.js");
/** Pass/fail thresholds */
const THRESHOLDS = {
    override_accuracy: { min: 0.90 },
    version_chain_accuracy: { min: 0.80 },
    staleness_rate: { max: 0.10 },
    avg_latency_ms: { min: 0 },
};
class UpdateRobustnessBenchmark extends core_js_1.BenchmarkCore {
    latencies = [];
    originalPrefs = [];
    updatedPrefs = [];
    constructor(config) {
        super({ name: "update-robustness", ...config });
    }
    generateData() {
        // Generate preference pairs
        const { original, updated } = this.generator.generatePreferences(this.config.factCount);
        this.originalPrefs = original;
        this.updatedPrefs = updated;
        return {
            facts: [...original, ...updated],
            queries: this.generateUpdateQueries(),
        };
    }
    async loadFacts(data) {
        if (!this.manager)
            return;
        // Store original preferences first
        for (const pref of this.originalPrefs) {
            this.manager.store(pref.content, "preference", pref.tags || [], pref.metadata || {});
        }
        // Then store updated preferences (should override)
        for (const pref of this.updatedPrefs) {
            this.manager.store(pref.content, "preference", pref.tags || [], pref.metadata || {});
        }
    }
    async runQueries(data) {
        if (!this.manager)
            return [];
        const details = [];
        for (const query of data.queries) {
            const start = performance.now();
            let result;
            let actualContent = "";
            if (query.queryType === "latest") {
                result = this.manager.getPreference?.(query.query);
                actualContent = result?.content || "";
            }
            else if (query.queryType === "history") {
                result = this.manager.getPreferenceHistory?.(query.query);
                actualContent = JSON.stringify(result);
            }
            else {
                result = this.manager.search(query.query, "preference", 5);
                const typedResult = result;
                actualContent = typedResult.map(r => r.content || "").join(" | ");
            }
            const latency = performance.now() - start;
            this.latencies.push(latency);
            const score = this.scoreUpdateQuery(query, result);
            details.push({
                query: query.query,
                expected: query.expectedAnswer,
                actual: actualContent,
                score,
                metadata: { queryType: query.queryType },
            });
        }
        return details;
    }
    score(details) {
        const stats = this.stats(this.latencies);
        // Group by query type
        const latestQueries = details.filter(d => d.metadata?.queryType === "latest");
        const historyQueries = details.filter(d => d.metadata?.queryType === "history");
        // Calculate metrics
        const override_accuracy = this.avgScore(latestQueries);
        let versionChainHits = 0;
        for (const q of historyQueries) {
            try {
                const history = JSON.parse(q.actual);
                if (Array.isArray(history) && history.length >= 2) {
                    versionChainHits++;
                }
            }
            catch {
                // Ignore parse errors
            }
        }
        const version_chain_accuracy = historyQueries.length > 0
            ? versionChainHits / historyQueries.length
            : 0;
        // Staleness rate: queries that returned old value instead of new
        let staleCount = 0;
        for (let i = 0; i < Math.min(latestQueries.length, this.updatedPrefs.length); i++) {
            const updated = this.updatedPrefs[i]?.content || "";
            const original = this.originalPrefs[i]?.content || "";
            const actual = latestQueries[i].actual;
            // Stale if actual matches original more than updated
            if (this.semanticMatch(original, actual) > this.semanticMatch(updated, actual)) {
                staleCount++;
            }
        }
        const staleness_rate = latestQueries.length > 0 ? staleCount / latestQueries.length : 0;
        return {
            override_accuracy,
            version_chain_accuracy,
            staleness_rate,
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
    generateUpdateQueries() {
        const queries = [];
        // Type 1: Latest value queries
        for (let i = 0; i < this.updatedPrefs.length; i++) {
            const pref = this.updatedPrefs[i];
            queries.push({
                query: pref.prefKey || "",
                expectedAnswer: pref.content,
                relatedFactIndices: [this.originalPrefs.length + i],
                queryType: "latest",
            });
        }
        // Type 2: Version history queries
        for (let i = 0; i < Math.min(5, this.originalPrefs.length); i++) {
            const pref = this.originalPrefs[i];
            queries.push({
                query: pref.prefKey || "",
                expectedAnswer: "version_history",
                relatedFactIndices: [i],
                queryType: "history",
            });
        }
        return queries;
    }
    scoreUpdateQuery(query, result) {
        if (query.queryType === "latest") {
            return this.semanticMatch(query.expectedAnswer, result?.content || result || "");
        }
        else if (query.queryType === "history") {
            try {
                const history = JSON.parse(result);
                return Array.isArray(history) && history.length >= 2 ? 1.0 : 0.0;
            }
            catch {
                return 0.0;
            }
        }
        return 0.0;
    }
}
exports.UpdateRobustnessBenchmark = UpdateRobustnessBenchmark;
//# sourceMappingURL=update-robustness.js.map