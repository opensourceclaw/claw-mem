import { BenchmarkCore, BenchmarkConfig, BenchmarkDetail } from "./core.js";
import { BenchmarkData } from "./data-generator.js";
export declare class LongHorizonBenchmark extends BenchmarkCore {
    private latencies;
    private anchorFacts;
    private accuracyCurve;
    constructor(config?: Partial<BenchmarkConfig>);
    protected generateData(): BenchmarkData;
    protected loadFacts(data: BenchmarkData): Promise<void>;
    protected runQueries(data: BenchmarkData): Promise<BenchmarkDetail[]>;
    protected score(details: BenchmarkDetail[]): Record<string, number>;
    protected checkPassFail(metrics: Record<string, number>): boolean;
    private queryAnchors;
    private linearRegressionSlope;
}
