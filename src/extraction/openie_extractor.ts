// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * OpenIE Extractor
 *
 * Dual-mode structured triplet extraction:
 * - LLM mode: high precision via structured prompt
 * - Rule mode: zero-dependency regex matching for Chinese and English text
 */

// ── LLM System Prompt ─────────────────────────────────────────────────

const LLM_SYSTEM_PROMPT = `\
You are a knowledge extraction engine. Extract ALL subject-predicate-object
triplets from the given text. A triplet captures a factual relationship
between two entities.

Output ONLY a JSON array of objects with these fields:
- "s": subject entity (string)
- "p": predicate / relationship (string)
- "o": object entity (string)
- "c": confidence score 0.0-1.0 (float)

Rules:
- Extract EVERY possible relationship, not just the main one
- Use concise entity names (proper nouns preferred)
- Predicates should be short descriptive verbs or phrases
- Set confidence based on how explicit the relationship is in the text
- Return empty array [] if no relationships found

Example:
Text: "\u5f20\u4e09\u662f\u674e\u56db\u7684\u4e0a\u53f8\u3002\u5f20\u4e09\u8d1f\u8d23\u7535\u5546\u9879\u76ee\u3002"
Output: [
  {"s":"\u5f20\u4e09","p":"\u662f...\u7684\u4e0a\u53f8","o":"\u674e\u56db","c":0.9},
  {"s":"\u5f20\u4e09","p":"\u8d1f\u8d23","o":"\u7535\u5546\u9879\u76ee","c":0.9}
]`;

// ── Triplet ───────────────────────────────────────────────────────────

export interface Triplet {
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
  source: "llm" | "rule";
}

// ── OpenIEExtractor ───────────────────────────────────────────────────

export type ExtractionMode = "llm" | "rule" | "auto";

export class OpenIEExtractor {
  private _llm: any;
  private _mode: ExtractionMode;

  constructor(llm_provider?: any, mode: ExtractionMode = "auto") {
    this._llm = llm_provider;
    this._mode = ["llm", "rule", "auto"].includes(mode) ? mode : "auto";
  }

  // ── Public API ────────────────────────────────────────────────────

  /**
   * Extract triplets from text using the configured mode.
   *
   * @param text - Input text (Chinese or English)
   * @returns List of extracted Triplet objects
   */
  extract(text: string): Triplet[] {
    if (!text || !text.trim()) return [];
    text = text.trim();

    if (this._mode === "llm") return this._extract_llm(text);
    if (this._mode === "rule") return this._extract_rule(text);

    // auto mode
    if (this._llm != null) {
      const llmResults = this._extract_llm(text);
      if (llmResults.length > 0) return llmResults;
    }
    return this._extract_rule(text);
  }

  // ── LLM Mode ──────────────────────────────────────────────────────

  private _extract_llm(text: string): Triplet[] {
    if (this._llm == null) return [];

    try {
      const response = this._llm.generate({
        prompt: text,
        system: LLM_SYSTEM_PROMPT,
        max_tokens: 512,
      });
      if (!response) return [];
      return this._parse_llm_response(response);
    } catch {
      return [];
    }
  }

  private _parse_llm_response(response: string): Triplet[] {
    let cleaned = response.trim();

    // Strip markdown code fences
    if (cleaned.startsWith("```")) {
      const lines = cleaned.split("\n");
      if (lines[0].startsWith("```")) lines.shift();
      if (lines.length > 0 && lines[lines.length - 1].trim() === "```") {
        lines.pop();
      }
      cleaned = lines.join("\n");
    }

    let data: any[];
    try {
      data = JSON.parse(cleaned);
      if (!Array.isArray(data)) return [];
    } catch {
      // Try to extract JSON array from within the text
      const match = cleaned.match(/\[.*\]/s);
      if (match) {
        try {
          data = JSON.parse(match[0]);
          if (!Array.isArray(data)) return [];
        } catch {
          return [];
        }
      } else {
        return [];
      }
    }

    const results: Triplet[] = [];
    for (const item of data) {
      if (typeof item !== "object" || item === null) continue;
      const subj = String(item.s ?? item.subject ?? "").trim();
      const pred = String(item.p ?? item.predicate ?? "").trim();
      const obj = String(item.o ?? item.object ?? "").trim();
      if (!subj || !pred || !obj) continue;
      const conf = Number(item.c ?? item.confidence ?? 0.8);
      results.push({
        subject: subj,
        predicate: pred,
        object: obj,
        confidence: Math.max(0.0, Math.min(1.0, conf)),
        source: "llm",
      });
    }
    return results;
  }

  // ── Rule Mode ──────────────────────────────────────────────────────

  // Chinese patterns: [regex, predicate, confidence]
  private static _CN_PATTERNS: Array<[RegExp, string | null, number]> = [
    [/(\S+)负责(\S+)/g, "负责", 0.8],
    [/(\S+) is (\S+)/g, " is ", 0.7],
    [/(\S+) of (\S+)/g, "拥 has ", 0.6],
    [/(\S+) in (\S+)/g, "位于", 0.6],
    [/(\S+)(喜欢|讨厌|管理|开发|拥 has |领导|主管)(\S+)/g, null, 0.5],
  ];

  // English patterns: [regex, predicate, confidence]
  private static _EN_PATTERNS: Array<[RegExp, string, number]> = [
    [/(\w+)\s+is\s+(\w+)/gi, "is", 0.7],
    [/(\w+)\s+has\s+(\w+)/gi, "has", 0.6],
  ];

  private _extract_rule(text: string): Triplet[] {
    const results: Triplet[] = [];
    const seen = new Set<string>();

    // Match Chinese patterns
    if (/[\u4e00-\u9fff]/.test(text)) {
      results.push(...this._match_chinese(text, seen));
    }

    // Match English patterns
    const enSegments = text.match(/[a-zA-Z]+(?:\s+[a-zA-Z]+)*/g);
    const enText = enSegments ? enSegments.join(" ") : "";
    if (enText) {
      results.push(...this._match_english(enText, seen));
    }

    // Fallback if nothing matched
    if (results.length === 0) {
      results.push(...this._fallback_match(text, seen));
    }

    return results;
  }

  private _match_chinese(
    text: string,
    seen: Set<string>,
  ): Triplet[] {
    const results: Triplet[] = [];
    for (const [pattern, predicate, confidence] of OpenIEExtractor._CN_PATTERNS) {
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(text)) !== null) {
        let subj: string, pred: string, obj: string;
        if (predicate === null) {
          subj = match[1];
          pred = match[2];
          obj = match[3];
        } else {
          subj = match[1];
          pred = predicate;
          obj = match[2];
        }
        subj = subj.trim();
        pred = pred.trim();
        obj = obj.trim();

        if (subj.length < 1 || obj.length < 1 || subj.length > 20 || obj.length > 20) {
          continue;
        }
        const key = `${subj}|${pred}|${obj}`;
        if (seen.has(key)) continue;
        seen.add(key);
        results.push({
          subject: subj,
          predicate: pred,
          object: obj,
          confidence,
          source: "rule",
        });
      }
    }
    return results;
  }

  private _match_english(
    text: string,
    seen: Set<string>,
  ): Triplet[] {
    const results: Triplet[] = [];
    for (const [pattern, predicate, confidence] of OpenIEExtractor._EN_PATTERNS) {
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(text)) !== null) {
        const subj = match[1].trim();
        const obj = match[2].trim();
        if (subj.length < 2 || obj.length < 2) continue;
        const key = `${subj}|${predicate}|${obj}`;
        if (seen.has(key)) continue;
        seen.add(key);
        results.push({
          subject: subj,
          predicate,
          object: obj,
          confidence,
          source: "rule",
        });
      }
    }
    return results;
  }

  private _fallback_match(
    text: string,
    seen: Set<string>,
  ): Triplet[] {
    const results: Triplet[] = [];

    // Chinese: character-level tri-gram fallback
    const cnSentences = text.split(/[。！？；\n]/);
    for (const sent of cnSentences) {
      const s = sent.trim();
      if (s.length < 4 || !/[\u4e00-\u9fff]/.test(s)) continue;
      const m = s.match(/(\S{1,6})(\S{1,4})(\S{1,8})/);
      if (m) {
        const subj = m[1];
        const pred = m[2];
        const obj = m[3];
        const key = `${subj}|${pred}|${obj}`;
        if (seen.has(key)) continue;
        seen.add(key);
        results.push({
          subject: subj,
          predicate: pred,
          object: obj,
          confidence: 0.3,
          source: "rule",
        });
      }
    }

    // English fallback: subject verb object
    if (results.length === 0) {
      const enPattern = /(\w{2,})\s+(\w{2,})\s+(\w{2,})/gi;
      const stopwords = new Set([
        "the", "and", "for", "with", "from",
        "that", "this", "then", "when", "where",
      ]);
      let match: RegExpExecArray | null;
      while ((match = enPattern.exec(text)) !== null) {
        const subj = match[1];
        const pred = match[2];
        const obj = match[3];
        if (stopwords.has(pred.toLowerCase())) continue;
        const key = `${subj}|${pred}|${obj}`;
        if (seen.has(key)) continue;
        seen.add(key);
        results.push({
          subject: subj,
          predicate: pred,
          object: obj,
          confidence: 0.3,
          source: "rule",
        });
      }
    }

    return results;
  }
}
