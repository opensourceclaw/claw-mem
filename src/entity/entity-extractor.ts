// Entity Extractor - Rule-based entity extraction (v6.30.0)

import type { Entity, EntityType, ExtractionRule } from "../types.js";

/** Default English stopwords to filter */
const DEFAULT_STOPWORDS = new Set([
  // Articles
  "The", "A", "An",
  // Prepositions
  "In", "On", "At", "By", "To", "For", "With", "From", "About", "Into", "Through",
  // Conjunctions
  "And", "But", "Or", "So", "Yet", "Nor",
  // Pronouns
  "I", "You", "He", "She", "It", "We", "They", "This", "That", "These", "Those",
  // Common verbs
  "Is", "Are", "Was", "Were", "Be", "Been", "Being", "Have", "Has", "Had", "Do", "Does", "Did",
  // Common sentence starters
  "Fixed", "Working", "Using", "Released", "First", "Then", "Finally", "Also", "Just", "Now",
  // Other common words
  "Not", "No", "Yes", "If", "Then", "Else", "When", "Where", "What", "Which", "Who", "How",
]);

/** Default extraction rules ordered by specificity */
const DEFAULT_RULES: ExtractionRule[] = [
  // 1. @mentions - highest confidence for person
  {
    pattern: /@([A-Za-z][A-Za-z0-9_-]{1,30})\b/g,
    type: "person",
    confidence: 0.95,
    nameTransform: (m) => m.slice(1), // Remove @ prefix
  },

  // 2. Known project names
  {
    pattern: /\b(claw-mem|claw-ctx|claw-cog|openclaw|devclaw|neoclaw)\b/gi,
    type: "project",
    confidence: 0.95,
  },

  // 3. Known tool names
  {
    pattern: /\b(TypeScript|JavaScript|Python|Docker|GitHub|Git|Node\.js|npm|vitest|eslint|prettier|VSCode|VS Code)\b/g,
    type: "tool",
    confidence: 0.9,
  },

  // 4. File paths
  {
    pattern: /\b[\w/\-.]+\.[a-z]{1,6}\b/g,
    type: "file",
    confidence: 0.85,
  },

  // 5. Version tags (v6.30.0, 1.2.3, 1.0.0-beta1)
  {
    pattern: /\bv?\d+\.\d+\.\d+(?:-[a-z]+\d*)?\b/g,
    type: "concept",
    confidence: 0.9,
  },

  // 6. All-caps acronyms (2-6 letters)
  {
    pattern: /\b[A-Z]{2,6}\b/g,
    type: "concept",
    confidence: 0.7,
  },

  // 7. Capitalized consecutive words (names/titles)
  {
    pattern: /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b/g,
    type: "other",
    confidence: 0.6,
  },
];

export interface EntityExtractorOptions {
  customRules?: ExtractionRule[];
  customStopwords?: string[];
}

/**
 * Rule-based entity extractor.
 * Extracts entities from text using regex patterns without LLM.
 */
export class EntityExtractor {
  private rules: ExtractionRule[];
  private stopwords: Set<string>;

  constructor(options?: EntityExtractorOptions) {
    // Start with default rules, prepend custom rules for higher priority
    this.rules = options?.customRules
      ? [...options.customRules, ...DEFAULT_RULES]
      : DEFAULT_RULES;

    // Merge default and custom stopwords
    this.stopwords = new Set(DEFAULT_STOPWORDS);
    if (options?.customStopwords) {
      for (const word of options.customStopwords) {
        this.stopwords.add(word);
      }
    }
  }

  /**
   * Extract entities from text using regex rules.
   * @param text - Input text to extract entities from
   * @returns Array of extracted entities, sorted by position
   */
  extract(text: string): Entity[] {
    if (!text || text.trim().length === 0) return [];

    const entities: Entity[] = [];
    const seen = new Map<string, Entity>(); // Dedup by name

    for (const rule of this.rules) {
      // Reset regex lastIndex for global patterns
      rule.pattern.lastIndex = 0;

      let match;
      while ((match = rule.pattern.exec(text)) !== null) {
        const rawName = match[0];
        const name = rule.nameTransform ? rule.nameTransform(rawName) : rawName;

        // Skip stopwords
        if (this.stopwords.has(name)) continue;

        // Skip short names
        if (name.length < 2) continue;

        const position = match.index;
        const existing = seen.get(name.toLowerCase());

        if (existing) {
          // Keep higher confidence
          if (rule.confidence > existing.confidence) {
            existing.confidence = rule.confidence;
            existing.type = rule.type;
          }
        } else {
          const entity: Entity = {
            name,
            type: rule.type,
            position,
            confidence: rule.confidence,
          };
          entities.push(entity);
          seen.set(name.toLowerCase(), entity);
        }
      }
    }

    // Sort by position
    entities.sort((a, b) => a.position - b.position);

    return entities;
  }

  /**
   * Add a custom extraction rule.
   * @param rule - Extraction rule to add
   */
  addRule(rule: ExtractionRule): void {
    this.rules.unshift(rule); // Add to front for higher priority
  }

  /**
   * Add stopwords to filter.
   * @param words - Words to add to stopword list
   */
  addStopwords(words: string[]): void {
    for (const word of words) {
      this.stopwords.add(word);
    }
  }

  /**
   * Get current rules (read-only).
   */
  getRules(): readonly ExtractionRule[] {
    return this.rules;
  }

  /**
   * Get current stopwords (read-only).
   */
  getStopwords(): ReadonlySet<string> {
    return this.stopwords;
  }
}
