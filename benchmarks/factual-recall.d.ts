import { BenchmarkCore, BenchmarkConfig, BenchmarkDetail } from "./core.js";
import { BenchmarkData } from "./data-generator.js";
export declare class FactualRecallBenchmark extends BenchmarkCore {
    private latencies;
    private factsByIndex;
    constructor(config?: Partial<BenchmarkConfig>);
    protected generateData(): BenchmarkData;
    protected loadFacts(data: BenchmarkData): Promise<void>;
    protected runQueries(data: BenchmarkData): Promise<BenchmarkDetail[]>;
    private getFactMemoryType;
    protected score(details: BenchmarkDetail[]): Record<string, number>;
    protected checkPassFail(metrics: Record<string, number>): boolean;
}
