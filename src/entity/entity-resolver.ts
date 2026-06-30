// Entity Resolver - Name canonicalization and alias mapping (v6.30.0)

import type { ResolutionResult } from "../types.js";

/** Default alias mappings */
const DEFAULT_ALIASES: Record<string, string[]> = {
  // Projects
  "clawmem": ["claw-mem", "claw_mem", "ClawMem"],
  "clawctx": ["claw-ctx", "claw_ctx", "ClawCtx"],
  "clawcog": ["claw-cog", "claw_cog", "ClawCog"],
  "openclaw": ["OpenClaw"],
  "devclaw": ["DevClaw"],
  "neoclaw": ["NeoClaw"],

  // Tools
  "typescript": ["TypeScript", "TS", "ts"],
  "javascript": ["JavaScript", "JS", "js"],
  "nodejs": ["Node.js", "NodeJS", "node"],
  "npm": ["NPM"],
  "docker": ["Docker"],
  "github": ["GitHub", "GH"],
  "git": ["Git"],
  "vitest": ["Vitest"],
  "eslint": ["ESLint"],
  "prettier": ["Prettier"],
  "vscode": ["VSCode", "VS Code"],

  // Concepts
  "api": ["API", "Api"],
  "sdk": ["SDK", "Sdk"],
  "cli": ["CLI", "Cli"],
  "rpc": ["RPC", "Rpc"],
  "json": ["JSON", "Json"],
  "yaml": ["YAML", "Yaml"],
  "http": ["HTTP", "Http"],
  "url": ["URL", "Url"],
};

export interface EntityResolverOptions {
  customAliases?: Record<string, string[]>;
}

/**
 * Entity resolver for name canonicalization and disambiguation.
 */
export class EntityResolver {
  private aliases: Map<string, string>;       // normalized alias -> canonical
  private aliasOriginals: Map<string, Set<string>>;  // canonical -> set of original aliases
  private knownEntities: Set<string>;          // All known canonical names

  constructor(options?: EntityResolverOptions) {
    this.aliases = new Map();
    this.aliasOriginals = new Map();
    this.knownEntities = new Set();

    // Register default aliases
    for (const [canonical, aliasList] of Object.entries(DEFAULT_ALIASES)) {
      this.addAliases(canonical, aliasList);
    }

    // Register custom aliases
    if (options?.customAliases) {
      for (const [canonical, aliasList] of Object.entries(options.customAliases)) {
        this.addAliases(canonical, aliasList);
      }
    }
  }

  /**
   * Convert name to canonical form.
   * @param name - Name to canonicalize
   * @returns Canonical name
   */
  canonicalize(name: string): string {
    if (!name) return "";

    let result = name;

    // 1. Lowercase
    result = result.toLowerCase();

    // 2. Remove common separators
    result = result.replace(/[-_.\s]/g, "");

    // 3. Remove trailing punctuation
    result = result.replace(/[!?.,;:'"]/g, "");

    // 4. Check alias map
    const mapped = this.aliases.get(result);
    if (mapped) return mapped;

    return result;
  }

  /**
   * Get resolution info for a name.
   * @param name - Name to resolve
   * @returns Resolution result with canonical name and alternatives
   */
  resolve(name: string): ResolutionResult {
    const canonical = this.canonicalize(name);
    const isNew = !this.knownEntities.has(canonical);

    // Get all original aliases for this canonical name
    const alternatives = this.getAliases(canonical);

    return {
      canonical,
      alternatives,
      isNew,
    };
  }

  /**
   * Register a known alias.
   * @param canonical - Canonical name
   * @param alias - Alias to register
   */
  addAlias(canonical: string, alias: string): void {
    const normalizedAlias = alias.toLowerCase().replace(/[-_.\s]/g, "");
    this.aliases.set(normalizedAlias, canonical);

    // Store the original alias for display
    if (!this.aliasOriginals.has(canonical)) {
      this.aliasOriginals.set(canonical, new Set());
    }
    this.aliasOriginals.get(canonical)!.add(alias);

    // Also register the canonical name itself
    this.knownEntities.add(canonical);
  }

  /**
   * Register multiple aliases.
   * @param canonical - Canonical name
   * @param aliases - Aliases to register
   */
  addAliases(canonical: string, aliases: string[]): void {
    for (const alias of aliases) {
      this.addAlias(canonical, alias);
    }
  }

  /**
   * Get all known aliases for a canonical name.
   * @param canonical - Canonical name
   * @returns Array of original aliases (excluding those that are identical to canonical)
   */
  getAliases(canonical: string): string[] {
    const originals = this.aliasOriginals.get(canonical);
    if (!originals) return [];

    // Return aliases that are not exactly equal to canonical
    return [...originals].filter(a => a !== canonical);
  }

  /**
   * Check if entity is known.
   * @param name - Name to check
   * @returns true if known
   */
  isKnown(name: string): boolean {
    const canonical = this.canonicalize(name);
    return this.knownEntities.has(canonical);
  }

  /**
   * Register an entity as known (after indexing).
   * @param canonical - Canonical name to register
   */
  registerKnown(canonical: string): void {
    this.knownEntities.add(canonical);
  }

  /**
   * Fuzzy search for similar names (placeholder for v6.31.0).
   * Currently returns exact matches and aliases only.
   * @param name - Name to search
   * @param threshold - Similarity threshold (unused in v6.30.0)
   * @returns Array of matching names
   */
  fuzzySearch(name: string, _threshold?: number): string[] {
    const canonical = this.canonicalize(name);

    if (this.knownEntities.has(canonical)) {
      return [canonical, ...this.getAliases(canonical)];
    }

    return [];
  }
}
