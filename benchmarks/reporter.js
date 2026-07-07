"use strict";
// ResultReporter - JSON and Markdown report generation (v6.32.0)
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
exports.ResultReporter = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class ResultReporter {
    /**
     * Generate reports for all benchmark results.
     */
    static generate(results, options) {
        fs.mkdirSync(options.outputDir, { recursive: true });
        if (options.format === "json" || options.format === "both") {
            const jsonPath = path.join(options.outputDir, "latest.json");
            fs.writeFileSync(jsonPath, this.toJSON(results), "utf-8");
        }
        if (options.format === "markdown" || options.format === "both") {
            const mdPath = path.join(options.outputDir, "report.md");
            fs.writeFileSync(mdPath, this.toMarkdown(results, options), "utf-8");
        }
    }
    /**
     * Compare current results against baseline.
     */
    static compare(current, baseline) {
        const reports = [];
        for (const curr of current) {
            const base = baseline.find(b => b.name === curr.name);
            if (!base)
                continue;
            for (const [metric, value] of Object.entries(curr.metrics)) {
                const baseValue = base.metrics[metric];
                if (baseValue === undefined)
                    continue;
                const change = value - baseValue;
                const changePercent = baseValue !== 0 ? (change / Math.abs(baseValue)) * 100 : 0;
                // Determine if improvement (lower is better for latency, higher is better for accuracy)
                const lowerIsBetter = metric.includes("latency") || metric.includes("rate") || metric.includes("cost");
                const improved = lowerIsBetter ? change < 0 : change > 0;
                reports.push({
                    benchmark: curr.name,
                    metric,
                    current: value,
                    baseline: baseValue,
                    change,
                    changePercent,
                    improved,
                });
            }
        }
        return reports;
    }
    /**
     * Get version from package.json.
     */
    static getVersion() {
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
    /**
     * Format as JSON.
     */
    static toJSON(results) {
        return JSON.stringify({
            version: this.getVersion(),
            timestamp: new Date().toISOString(),
            results,
        }, null, 2);
    }
    /**
     * Format as Markdown.
     */
    static toMarkdown(results, options) {
        const version = this.getVersion();
        const lines = [
            `# claw-mem v${version} Benchmark Report`,
            `**Date**: ${new Date().toISOString()}`,
            `**Version**: ${version}`,
            "",
        ];
        for (const result of results) {
            lines.push(`## ${result.name}`);
            lines.push("");
            lines.push("| Metric | Value | Status |");
            lines.push("|--------|-------|:------:|");
            for (const [metric, value] of Object.entries(result.metrics)) {
                // Skip nested objects (strategy breakdown)
                if (typeof value === "object")
                    continue;
                const formatted = typeof value === "number" && value < 10
                    ? value.toFixed(4)
                    : typeof value === "number"
                        ? value.toFixed(2)
                        : String(value);
                const status = this.checkThreshold(result.name, metric, value, options.thresholds);
                const statusIcon = status === "pass" ? "✅" : status === "fail" ? "❌" : "➖";
                lines.push(`| ${metric} | ${formatted} | ${statusIcon} |`);
            }
            lines.push("");
            lines.push(`**Duration**: ${result.durationMs}ms`);
            lines.push(`**Passed**: ${result.passed ? "✅" : "❌"}`);
            lines.push("");
        }
        return lines.join("\n");
    }
    /**
     * Check if metric passes threshold.
     */
    static checkThreshold(benchmark, metric, value, thresholds) {
        if (!thresholds)
            return "unknown";
        const benchmarkThresholds = thresholds[benchmark];
        if (!benchmarkThresholds)
            return "unknown";
        const threshold = benchmarkThresholds[metric];
        if (!threshold)
            return "unknown";
        if (threshold.min !== undefined && value < threshold.min)
            return "fail";
        if (threshold.max !== undefined && value > threshold.max)
            return "fail";
        return "pass";
    }
}
exports.ResultReporter = ResultReporter;
//# sourceMappingURL=reporter.js.map