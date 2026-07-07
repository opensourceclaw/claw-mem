/** Single fact record */
export interface FactRecord {
    /** Unique ID */
    id: string;
    /** Content text */
    content: string;
    /** Memory type: fact, episodic, preference, session_snapshot */
    memoryType: string;
    /** Tags */
    tags?: string[];
    /** Metadata */
    metadata?: Record<string, unknown>;
    /** ISO timestamp */
    timestamp?: string;
    /** Session ID (for session_snapshot) */
    sessionId?: string;
    /** Preference key (for preference type) */
    prefKey?: string;
}
/** Query record */
export interface QueryRecord {
    /** Query string */
    query: string;
    /** Expected answer */
    expectedAnswer: string;
    /** Indices into facts[] for related facts */
    relatedFactIndices: number[];
    /** Query type */
    queryType: "exact" | "semantic" | "temporal" | "update" | "completeness" | "after" | "recent" | "order" | "latest" | "history" | "entity";
}
/** Benchmark data bundle */
export interface BenchmarkData {
    /** Facts to store */
    facts: FactRecord[];
    /** Queries to run */
    queries: QueryRecord[];
    /** Distraction facts (for recall-after-distraction) */
    distractions?: FactRecord[];
}
/**
 * Generate synthetic test data for all benchmarks.
 * No external dependencies - all templates embedded.
 */
export declare class DataGenerator {
    private rng;
    private idCounter;
    constructor(seed: number);
    /**
     * Generate facts of different memory types.
     */
    generateFacts(count: number, types: string[]): FactRecord[];
    /**
     * Generate temporal event sequence with timestamps.
     */
    generateTemporalEvents(count: number): FactRecord[];
    /**
     * Generate preference pairs: original + updated.
     */
    generatePreferences(count: number): {
        original: FactRecord[];
        updated: FactRecord[];
    };
    /**
     * Generate fact-rich conversations (multiple facts per message).
     */
    generateConversations(count: number, factsPerConversation: number): FactRecord[];
    /**
     * Generate queries targeting specific facts.
     */
    generateQueries(facts: FactRecord[], count: number): QueryRecord[];
    /**
     * Generate distraction facts (unrelated to target facts).
     */
    generateDistractions(count: number): FactRecord[];
    private generateFact;
    private fillTemplate;
    private generateQueryForFact;
    private distributeTypes;
    private nextId;
}
