// SeededRandom - Reproducible random number generator (v6.32.0)

/**
 * Seeded random number generator for reproducibility.
 * Uses mulberry32 algorithm for fast, high-quality randomness.
 */
export class SeededRandom {
  private state: number;

  constructor(seed: number) {
    this.state = seed >>> 0;
  }

  /**
   * Next random float in range [0, 1).
   * Uses mulberry32 algorithm.
   */
  next(): number {
    let t = (this.state += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /**
   * Random integer in range [min, max] (inclusive).
   */
  nextInt(min: number, max: number): number {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  /**
   * Pick random element from array.
   */
  pick<T>(arr: T[]): T {
    if (arr.length === 0) {
      throw new Error("Cannot pick from empty array");
    }
    return arr[this.nextInt(0, arr.length - 1)];
  }

  /**
   * Shuffle array in place using Fisher-Yates algorithm with seed.
   */
  shuffle<T>(arr: T[]): T[] {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = this.nextInt(0, i);
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  /**
   * Generate random string of given length.
   */
  randomString(length: number): string {
    const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    let result = "";
    for (let i = 0; i < length; i++) {
      result += chars[this.nextInt(0, chars.length - 1)];
    }
    return result;
  }
}
