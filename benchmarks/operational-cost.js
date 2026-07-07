"use strict";
// OperationalCostBenchmark - Performance and cost measurement (v6.32.0)
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.OperationalCostBenchmark = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const core_js_1 = require("./core.js");
/** Pass/fail thresholds */
const THRESHOLDS = {
    store_latency_avg: { max: 50 },
    store_latency_p95: { max: 100 },
    search_latency_avg: { max: 50 },
    search_latency_p95: { max: 100 },
    storage_size_kb_per_1k: { max: 500 },
    estimated_token_cost_per_search: { max: 500 },
};
class OperationalCostBenchmark extends core_js_1.BenchmarkCore {
    storeLatencies = [];
    searchLatencies = [];
    strategyLatencies = new Map();
    initialStorageSize = 0;
    constructor(config) {
        super({ name: "operational-cost", ...config });
    }
    generateData() {
        return {
            facts: this.generator.generateFacts(this.config.factCount, this.config.memoryTypes),
            queries: this.generator.generateQueries([], this.config.queryCount),
        };
    }
    async loadFacts(data) {
        if (!this.manager)
            return;
        // Record initial storage size
        this.initialStorageSize = this.getStorageSize();
        // Store facts and measure latency per strategy
        for (const fact of data.facts) {
            const start = performance.now();
            this.manager.store(fact.content, fact.memoryType, fact.tags || [], fact.metadata || {});
            const latency = performance.now() - start;
            this.storeLatencies.push(latency);
            // Track per-strategy latency
            const strategy = this.manager.getStoreStrategy?.(fact.memoryType);
            if (strategy) {
                if (!this.strategyLatencies.has(strategy)) {
                    this.strategyLatencies.set(strategy, []);
                }
                this.strategyLatencies.get(strategy).push(latency);
            }
        }
    }
    async runQueries(data) {
        if (!this.manager)
            return [];
        const details = [];
        for (const query of data.queries) {
            const start = performance.now();
            const results = this.manager.search(query.query, undefined, 10);
            const latency = performance.now() - start;
            this.searchLatencies.push(latency);
            const typedResults = results;
            // Estimate token cost (rough approximation: chars / 4)
            const tokenCost = typedResults.reduce((sum, r) => sum + Math.ceil((r.content?.length || r.text?.length || 0) / 4), 0);
            const firstResult = typedResults[0];
            details.push({
                query: query.query,
                expected: query.expectedAnswer,
                actual: firstResult?.content || firstResult?.text || "",
                score: 1.0, // Not scoring accuracy here
                metadata: { latency, tokenCost },
            });
        }
        return details;
    }
    score(details) {
        const storeStats = this.stats(this.storeLatencies);
        const searchStats = this.stats(this.searchLatencies);
        // Calculate storage size growth
        const finalStorageSize = this.getStorageSize();
        const storageGrowth = finalStorageSize - this.initialStorageSize;
        const storage_size_kb_per_1k = (storageGrowth / 1024) * (1000 / this.config.factCount);
        // Estimate token cost per search
        const avgTokenCost = details.length > 0
            ? details.reduce((sum, d) => sum + (d.metadata?.tokenCost || 0), 0) / details.length
            : 0;
        // Per-strategy breakdown
        const strategy_breakdown = {};
        for (const [strategy, latencies] of this.strategyLatencies) {
            const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
            strategy_breakdown[strategy] = {
                latency_avg: avg,
                storage_bytes: Math.round(storageGrowth / Math.max(this.strategyLatencies.size, 1)),
            };
        }
        return {
            store_latency_avg: storeStats.avg,
            store_latency_p95: storeStats.p95,
            search_latency_avg: searchStats.avg,
            search_latency_p95: searchStats.p95,
            storage_size_kb_per_1k,
            estimated_token_cost_per_search: avgTokenCost,
            ...strategy_breakdown, // Flatten strategy breakdown into metrics
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
    getStorageSize() {
        if (!this.manager)
            return 0;
        const memoryDir = path.join(this.workspaceDir, "memory");
        if (!fs.existsSync(memoryDir))
            return 0;
        let totalSize = 0;
        const files = fs.readdirSync(memoryDir);
        for (const file of files) {
            const filePath = path.join(memoryDir, file);
            const stat = fs.statSync(filePath);
            totalSize += stat.size;
        }
        return totalSize;
    }
}
exports.OperationalCostBenchmark = OperationalCostBenchmark;
//# sourceMappingURL=operational-cost.js.map