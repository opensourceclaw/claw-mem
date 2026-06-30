// Entity Module - Barrel export (v6.30.0)

export { EntityExtractor } from "./entity-extractor.js";
export type { EntityExtractorOptions } from "./entity-extractor.js";

export { EntityResolver } from "./entity-resolver.js";
export type { EntityResolverOptions } from "./entity-resolver.js";

export { EntityIndex } from "./entity-index.js";
export type { EntityIndexOptions } from "./entity-index.js";

// Re-export types
export type {
  Entity,
  EntityType,
  ExtractionRule,
  EntityRecord,
  CoocEntry,
  EntitySearchResult,
  ResolutionResult,
  EntityConfig,
  DEFAULT_ENTITY_CONFIG,
} from "../types.js";
