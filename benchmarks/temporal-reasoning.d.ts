import { BenchmarkCore, BenchmarkConfig, BenchmarkDetail } from "./core.js";
import { BenchmarkData } from "./data-generator.js";
export declare class TemporalReasoningBenchmark extends BenchmarkCore {
    private latencies;
    private events;
    constructor(config?: Partial<BenchmarkConfig>);
    protected generateData(): BenchmarkData;
    protected loadFacts(data: BenchmarkData): Promise<void>;
    protected runQueries(data: BenchmarkData): Promise<BenchmarkDetail[]>;
    protected score(details: BenchmarkDetail[]): Record<string, number>;
    protected checkPassFail(metrics: Record<string, number>): boolean;
    private generateTemporalQueries;
    private scoreTemporalQuery;
}
