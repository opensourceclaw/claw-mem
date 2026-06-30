// Entity Index - In-memory entity index with co-occurrence graph (v6.30.0)

import type { Entity, EntityRecord, CoocEntry, EntitySearchResult, ResolutionResult, EntityConfig } from "../types.js";
import { EntityExtractor } from "./entity-extractor.js";
import { EntityResolver } from "./entity-resolver.js";

export interface EntityIndexOptions {
  extractor?: EntityExtractor;
  resolver?: EntityResolver;
  maxEntitiesPerMemory?: number;
}

/**
 * In-memory entity index with co-occurrence tracking.
 * Maps entities to memory IDs and tracks co-occurring entities.
 */
export class EntityIndex {
  private entityMap: Map<string, EntityRecord>;
  private coocGraph: Map<string, CoocEntry>;  // key: "e1||e2" (alphabetically sorted)
  private extractor: EntityExtractor;
  private resolver: EntityResolver;
  private maxEntitiesPerMemory: number;

  constructor(options?: EntityIndexOptions) {
    this.entityMap = new Map();
    this.coocGraph = new Map();
    this.extractor = options?.extractor ?? new EntityExtractor();
    this.resolver = options?.resolver ?? new EntityResolver();
    this.maxEntitiesPerMemory = options?.maxEntitiesPerMemory ?? 50;
  }

  /**
   * Index entities from a memory entry.
   * @param text - Memory text to extract entities from
   * @param memoryId - Memory ID to associate entities with
   */
  index(text: string, memoryId: string): void {
    if (!text) return;

    // 1. Extract entities
    const entities = this.extractor.extract(text);
    if (entities.length === 0) return;

    // 2. Resolve to canonical names
    const canonical = entities.map(e => ({
      ...e,
      name: this.resolver.canonicalize(e.name),
    }));

    // 2.5 Enforce maxEntitiesPerMemory limit
    if (canonical.length > this.maxEntitiesPerMemory) {
      // Sort by confidence descending, keep top N
      canonical.sort((a, b) => b.confidence - a.confidence);
      canonical.length = this.maxEntitiesPerMemory;
    }

    const now = Date.now();
    const uniqueNames = new Set<string>();

    // 3. Update entityMap
    for (const entity of canonical) {
      uniqueNames.add(entity.name);

      const existing = this.entityMap.get(entity.name);
      if (existing) {
        // Update existing record
        if (!existing.memoryIds.includes(memoryId)) {
          existing.memoryIds.push(memoryId);
        }
        existing.lastSeen = now;
        existing.occurrenceCount++;
      } else {
        // Create new record
        this.entityMap.set(entity.name, {
          name: entity.name,
          type: entity.type,
          memoryIds: [memoryId],
          firstSeen: now,
          lastSeen: now,
          occurrenceCount: 1,
        });

        // Register as known entity
        this.resolver.registerKnown(entity.name);
      }
    }

    // 4. Update coocGraph for all pairs
    const names = [...uniqueNames];
    for (let i = 0; i < names.length; i++) {
      for (let j = i + 1; j < names.length; j++) {
        const [a, b] = names[i] < names[j]
          ? [names[i], names[j]]
          : [names[j], names[i]];

        const key = `${a}||${b}`;
        const existing = this.coocGraph.get(key);

        if (existing) {
          existing.count++;
          existing.lastCooc = now;
        } else {
          this.coocGraph.set(key, {
            entityA: a,
            entityB: b,
            count: 1,
            lastCooc: now,
          });
        }
      }
    }
  }

  /**
   * Search by entity name (with resolution).
   * @param name - Entity name to search
   * @returns Entity search result or null if not found
   */
  search(name: string): EntitySearchResult | null {
    // 1. Resolve name to canonical
    const canonical = this.resolver.canonicalize(name);

    // 2. Get entity record
    const entity = this.entityMap.get(canonical);
    if (!entity) return null;

    // 3. Get co-occurring entities
    const related = this.getCooccurrences(canonical);

    return { entity, related };
  }

  /**
   * Resolve name to canonical form and get candidates.
   * @param name - Name to resolve
   * @returns Resolution result
   */
  resolve(name: string): ResolutionResult {
    return this.resolver.resolve(name);
  }

  /**
   * Get all entities.
   * @returns Array of all entity records
   */
  listAll(): EntityRecord[] {
    return [...this.entityMap.values()];
  }

  /**
   * Get co-occurring entities for a given entity.
   * @param name - Entity name
   * @param limit - Maximum number of results (default: 10)
   * @returns Array of co-occurring entity names sorted by count
   */
  getCooccurrences(name: string, limit: number = 10): string[] {
    const canonical = this.resolver.canonicalize(name);
    const related: Array<{ name: string; count: number }> = [];

    for (const [, entry] of this.coocGraph) {
      if (entry.entityA === canonical || entry.entityB === canonical) {
        const other = entry.entityA === canonical ? entry.entityB : entry.entityA;
        related.push({ name: other, count: entry.count });
      }
    }

    // Sort by count descending
    related.sort((a, b) => b.count - a.count);

    return related.slice(0, limit).map(r => r.name);
  }

  /**
   * Remove entity entries for a memory (on memory deletion).
   * @param memoryId - Memory ID to remove
   */
  removeMemory(memoryId: string): void {
    // Collect entities that had this memoryId before removal
    const affectedEntities: string[] = [];
    for (const [name, record] of this.entityMap) {
      if (record.memoryIds.includes(memoryId)) {
        affectedEntities.push(name);
      }
    }

    // Remove memoryId from all entity records
    for (const [name, record] of this.entityMap) {
      const idx = record.memoryIds.indexOf(memoryId);
      if (idx !== -1) {
        record.memoryIds.splice(idx, 1);
        record.occurrenceCount--;
      }

      // Remove entity if no memories left
      if (record.memoryIds.length === 0) {
        this.entityMap.delete(name);
      }
    }

    // Update coocGraph: decrement counts for pairs that involved removed memory
    // For each pair of affected entities, decrement co-occurrence count
    for (let i = 0; i < affectedEntities.length; i++) {
      for (let j = i + 1; j < affectedEntities.length; j++) {
        const [a, b] = affectedEntities[i] < affectedEntities[j]
          ? [affectedEntities[i], affectedEntities[j]]
          : [affectedEntities[j], affectedEntities[i]];

        const key = `${a}||${b}`;
        const entry = this.coocGraph.get(key);
        if (entry) {
          entry.count--;
          // Remove entry if count reaches 0
          if (entry.count <= 0) {
            this.coocGraph.delete(key);
          }
        }
      }
    }
  }

  /**
   * Clear all index data.
   */
  clear(): void {
    this.entityMap.clear();
    this.coocGraph.clear();
  }

  /**
   * Get index statistics.
   */
  getStats(): {
    entityCount: number;
    coocCount: number;
    totalMemoryLinks: number;
    avgCoocPerEntity: number;
  } {
    let totalMemoryLinks = 0;
    for (const record of this.entityMap.values()) {
      totalMemoryLinks += record.memoryIds.length;
    }

    return {
      entityCount: this.entityMap.size,
      coocCount: this.coocGraph.size,
      totalMemoryLinks,
      avgCoocPerEntity: this.entityMap.size > 0
        ? totalMemoryLinks / this.entityMap.size
        : 0,
    };
  }
}
