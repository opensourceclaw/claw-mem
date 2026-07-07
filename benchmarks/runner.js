"use strict";
// CLI Runner - Benchmark execution entry point (v6.32.0)
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
exports.getLastBenchmarkResults = getLastBenchmarkResults;
exports.runAll = runAll;
exports.main = main;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const factual_recall_js_1 = require("./factual-recall.js");
const temporal_reasoning_js_1 = require("./temporal-reasoning.js");
const long_horizon_js_1 = require("./long-horizon.js");
const update_robustness_js_1 = require("./update-robustness.js");
const retrieval_fidelity_js_1 = require("./retrieval-fidelity.js");
const operational_cost_js_1 = require("./operational-cost.js");
const reporter_js_1 = require("./reporter.js");
/**
 * Get version from package.json.
 */
function getVersion() {
    try {
        // Try two levels up first (compiled: dist/benchmarks/ -> project root)
        let pkgPath = path.resolve(__dirname, "..", "..", "package.json");
        if (!fs.existsSync(pkgPath)) {
            // Fallback to one level up (source: benchmarks/ -> project root)
            pkgPath = path.resolve(__dirname, "..", "package.json");
        }
        return JSON.parse(fs.readFileSync(pkgPath, "utf-8")).version || "unknown";
    }
    catch {
        return "unknown";
    }
}
// Cache for last benchmark results (used by bridge RPC)
let lastBenchmarkResults = null;
let lastBenchmarkTimestamp = null;
/**
 * Get last cached benchmark results.
 */
function getLastBenchmarkResults() {
    return { results: lastBenchmarkResults, timestamp: lastBenchmarkTimestamp };
}
/**
 * Run all benchmarks or a specific one.
 */
async function runAll(options = {}) {
    const results = [];
    const errors = [];
    const benchmarkFactories = [
        () => new factual_recall_js_1.FactualRecallBenchmark(options),
        () => new temporal_reasoning_js_1.TemporalReasoningBenchmark(options),
        () => new long_horizon_js_1.LongHorizonBenchmark(options),
        () => new update_robustness_js_1.UpdateRobustnessBenchmark(options),
        () => new retrieval_fidelity_js_1.RetrievalFidelityBenchmark(options),
        () => new operational_cost_js_1.OperationalCostBenchmark(options),
    ];
    const benchmarkNames = [
        "factual-recall",
        "temporal-reasoning",
        "long-horizon",
        "update-robustness",
        "retrieval-fidelity",
        "operational-cost",
    ];
    for (let i = 0; i < benchmarkFactories.length; i++) {
        const benchmarkName = benchmarkNames[i];
        // Skip if running specific benchmark
        if (options.name && options.name !== benchmarkName) {
            continue;
        }
        try {
            console.log(`Running ${benchmarkName}...`);
            const benchmark = benchmarkFactories[i]();
            const result = await benchmark.run();
            results.push(result);
            console.log(`  ✓ ${result.name}: ${result.passed ? "PASS" : "FAIL"} (${result.durationMs}ms)`);
            if (!result.passed) {
                console.log(`  Metrics: ${JSON.stringify(result.metrics, null, 2).split('\n').join('\n  ')}`);
            }
        }
        catch (err) {
            const error = err instanceof Error ? err : new Error(String(err));
            errors.push(error);
            console.error(`  ✗ ${benchmarkName}: ${error.message}`);
        }
    }
    // Cache results
    lastBenchmarkResults = results;
    lastBenchmarkTimestamp = new Date().toISOString();
    // Generate report
    if (results.length > 0) {
        const reportOptions = {
            outputDir: options.outputDir || "./results",
            format: options.format || "both",
            baseline: options.baseline,
        };
        reporter_js_1.ResultReporter.generate(results, reportOptions);
    }
    // Report errors
    if (errors.length > 0) {
        console.error(`\n${errors.length} benchmark(s) failed with errors.`);
    }
    return results;
}
/**
 * CLI entry point.
 */
async function main() {
    const args = process.argv.slice(2);
    const options = {};
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        if (arg === "--name" && args[i + 1]) {
            options.name = args[++i];
        }
        else if (arg === "--seed" && args[i + 1]) {
            options.seed = parseInt(args[++i], 10);
        }
        else if (arg === "--format" && args[i + 1]) {
            options.format = args[++i];
        }
        else if (arg === "--baseline" && args[i + 1]) {
            options.baseline = args[++i];
        }
        else if (arg === "--output" && args[i + 1]) {
            options.outputDir = args[++i];
        }
        else if (arg === "--fact-count" && args[i + 1]) {
            options.factCount = parseInt(args[++i], 10);
        }
        else if (arg === "--query-count" && args[i + 1]) {
            options.queryCount = parseInt(args[++i], 10);
        }
        else if (arg === "--help") {
            console.log(`
claw-mem Benchmark Suite v${getVersion()}

Usage: npm run benchmark [options]

Options:
  --name <benchmark>     Run specific benchmark only
  --seed <number>        Random seed for reproducibility (default: 42)
  --format <format>      Output format: json, markdown, both (default: both)
  --baseline <file>      Compare against baseline JSON file
  --output <dir>         Output directory (default: ./results)
  --fact-count <n>       Number of facts to generate (default: 100)
  --query-count <n>      Number of queries to run (default: 20)
  --help                 Show this help message
      `);
            process.exit(0);
        }
    }
    console.log(`claw-mem Benchmark Suite v${getVersion()}`);
    console.log(`Seed: ${options.seed || 42}`);
    console.log("");
    const startTime = Date.now();
    const results = await runAll(options);
    const totalDuration = Date.now() - startTime;
    console.log("");
    console.log(`Total: ${results.length} benchmarks, ${totalDuration}ms`);
    console.log(`Passed: ${results.filter(r => r.passed).length}/${results.length}`);
}
// Run main if executed directly
if (require.main === module) {
    main().catch(err => {
        console.error(err);
        process.exit(1);
    });
}
//# sourceMappingURL=runner.js.map