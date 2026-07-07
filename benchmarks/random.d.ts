/**
 * Seeded random number generator for reproducibility.
 * Uses mulberry32 algorithm for fast, high-quality randomness.
 */
export declare class SeededRandom {
    private state;
    constructor(seed: number);
    /**
     * Next random float in range [0, 1).
     * Uses mulberry32 algorithm.
     */
    next(): number;
    /**
     * Random integer in range [min, max] (inclusive).
     */
    nextInt(min: number, max: number): number;
    /**
     * Pick random element from array.
     */
    pick<T>(arr: T[]): T;
    /**
     * Shuffle array in place using Fisher-Yates algorithm with seed.
     */
    shuffle<T>(arr: T[]): T[];
    /**
     * Generate random string of given length.
     */
    randomString(length: number): string;
}
