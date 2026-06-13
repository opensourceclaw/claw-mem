import type { MemoryRecord } from "../types.js";

export abstract class BaseStorage {
  abstract store(record: MemoryRecord): string;
  abstract retrieve(id: string): MemoryRecord | undefined;
  abstract delete(id: string): boolean;
  abstract listAll(memoryType?: string, limit?: number): MemoryRecord[];

  count(memoryType?: string): number {
    return this.listAll(memoryType, 1_000_000).length;
  }
}

export { MemoryRecord };
