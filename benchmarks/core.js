"use strict";
// BenchmarkCore - Shared harness for all benchmarks (v6.32.0)
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
exports.BenchmarkCore = exports.DEFAULT_CONFIG = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const memory_manager_js_1 = require("../src/memory_manager.js");
const random_js_1 = require("./random.js");
const data_generator_js_1 = require("./data-generator.js");
/** Default configuration values */
exports.DEFAULT_CONFIG = {
    factCount: 100,
    queryCount: 20,
    distractionCount: 50,
    seed: 42,
    memoryTypes: ["fact", "episodic", "preference"],
    timeoutMs: 60000,
    workspace: "",
    cleanup: true,
};
/**
 * Abstract base class for all benchmarks.
 * Provides lifecycle: init → generateData → loadFacts → runQueries → score → cleanup
 */
class BenchmarkCore {
    manager = null;
    config;
    rng;
    generator;
    workspaceDir;
    constructor(config) {
        this.config = { ...exports.DEFAULT_CONFIG, ...config };
        this.rng = new random_js_1.SeededRandom(this.config.seed);
        this.generator = new data_generator_js_1.DataGenerator(this.config.seed);
        this.workspaceDir = this.config.workspace || `/tmp/claw-mem-bench-${this.config.name}-${Date.now()}`;
    }
    /**
     * Main entry point: run the complete benchmark.
     * Lifecycle: init → generateData → loadFacts → runQueries → score → cleanup
     */
    async run() {
        const startTime = performance.now();
        const timestamp = new Date().toISOString();
        try {
            // 1. Initialize MemoryManager
            await this.init();
            // 2. Generate synthetic test data
            const data = this.generateData();
            // 3. Load facts into memory
            await this.loadFacts(data);
            // 4. Run queries
            const details = await this.runQueries(data);
            // 5. Score results
            const metrics = this.score(details);
            // 6. Determine pass/fail
            const passed = this.checkPassFail(metrics);
            const durationMs = Math.round(performance.now() - startTime);
            return {
                name: this.config.name,
                config: this.config,
                metrics,
                details,
                timestamp,
                version: this.getVersion(),
                durationMs,
                passed,
            };
        }
        finally {
            // 7. Cleanup
            if (this.config.cleanup) {
                this.cleanup();
            }
        }
    }
    /**
     * Initialize MemoryManager with isolated workspace.
     */
    async init() {
        // Create workspace directory
        fs.mkdirSync(this.workspaceDir, { recursive: true });
        fs.writeFileSync(path.join(this.workspaceDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
        // Create MemoryManager
        this.manager = new memory_manager_js_1.MemoryManager({
            workspace: this.workspaceDir,
            autoDetect: false,
            enableGating: false,
            enableDecay: false,
        });
    }
    /**
     * Clean up workspace directory.
     */
    cleanup() {
        if (!this.manager)
            return;
        try {
            // Remove workspace directory recursively
            fs.rmSync(this.workspaceDir, { recursive: true, force: true });
        }
        catch {
            // Ignore cleanup errors
        }
    }
    // Scoring Helpers
    /**
     * Exact match scoring: 1.0 if strings are identical, 0.0 otherwise.
     */
    exactMatch(expected, actual) {
        return expected.toLowerCase().trim() === actual.toLowerCase().trim() ? 1.0 : 0.0;
    }
    /**
     * Semantic match scoring using token overlap (Jaccard similarity).
     * Formula: |tokens(expected) ∩ tokens(actual)| / |tokens(expected) ∪ tokens(actual)|
     */
    semanticMatch(expected, actual) {
        const expectedTokens = new Set(this.tokenize(expected));
        const actualTokens = new Set(this.tokenize(actual));
        if (expectedTokens.size === 0)
            return 0.0;
        const intersection = [...expectedTokens].filter(t => actualTokens.has(t));
        const union = new Set([...expectedTokens, ...actualTokens]);
        return union.size > 0 ? intersection.length / union.size : 0.0;
    }
    /**
     * Contains match: 1.0 if actual contains expected (case-insensitive), 0.0 otherwise.
     */
    containsMatch(expected, actual) {
        return actual.toLowerCase().includes(expected.toLowerCase()) ? 1.0 : 0.0;
    }
    /**
     * Temporal ordering scoring: percentage of correctly ordered pairs.
     * Formula: correct_pairs / total_pairs
     */
    temporalOrder(events, expectedOrder) {
        if (events.length < 2 || expectedOrder.length < 2)
            return 1.0;
        let correctPairs = 0;
        let totalPairs = 0;
        // Check all pairs in expectedOrder
        for (let i = 0; i < expectedOrder.length - 1; i++) {
            for (let j = i + 1; j < expectedOrder.length; j++) {
                const idxI = events.findIndex(e => e.content.includes(expectedOrder[i]));
                const idxJ = events.findIndex(e => e.content.includes(expectedOrder[j]));
                if (idxI !== -1 && idxJ !== -1) {
                    totalPairs++;
                    if (idxI < idxJ)
                        correctPairs++;
                }
            }
        }
        return totalPairs > 0 ? correctPairs / totalPairs : 0.0;
    }
    /**
     * Completeness score: percentage of expected items found in retrieved.
     * Formula: |expected ∩ retrieved| / |expected|
     */
    completenessScore(retrieved, expected) {
        if (expected.length === 0)
            return 1.0;
        const retrievedSet = new Set(retrieved.map(r => r.toLowerCase()));
        const found = expected.filter(e => retrievedSet.has(e.toLowerCase()));
        return found.length / expected.length;
    }
    /**
     * Recall@K: percentage of queries where expected was in top K results.
     * Formula: queries_with_match / total_queries
     */
    recallAtK(details, k) {
        if (details.length === 0)
            return 0.0;
        const hits = details.filter(d => {
            const topK = d.retrievedResults?.slice(0, k) || [d.actual];
            return topK.some(r => this.semanticMatch(d.expected, r) >= 0.5);
        });
        return hits.length / details.length;
    }
    // Utility Methods
    /**
     * Tokenize string into lowercase words.
     */
    tokenize(text) {
        if (typeof text !== "string")
            return [];
        return text.toLowerCase()
            .replace(/[^\w\s]/g, " ")
            .split(/\s+/)
            .filter(t => t.length > 0);
    }
    /**
     * Get claw-mem version from package.json.
     */
    getVersion() {
        try {
            const pkgPath = path.resolve(__dirname, "..", "package.json");
            const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf-8"));
            return pkg.version || "unknown";
        }
        catch {
            return "unknown";
        }
    }
    /**
     * Calculate statistics (avg, p50, p95, p99) from array of numbers.
     */
    stats(values) {
        if (values.length === 0) {
            return { avg: 0, p50: 0, p95: 0, p99: 0, min: 0, max: 0 };
        }
        const sorted = [...values].sort((a, b) => a - b);
        const sum = values.reduce((s, v) => s + v, 0);
        return {
            avg: sum / values.length,
            p50: sorted[Math.floor(sorted.length * 0.5)],
            p95: sorted[Math.floor(sorted.length * 0.95)],
            p99: sorted[Math.floor(sorted.length * 0.99)],
            min: sorted[0],
            max: sorted[sorted.length - 1],
        };
    }
    /**
     * Calculate average score from details.
     */
    avgScore(details) {
        if (details.length === 0)
            return 0;
        return details.reduce((sum, d) => sum + d.score, 0) / details.length;
    }
}
exports.BenchmarkCore = BenchmarkCore;
//# sourceMappingURL=core.js.map