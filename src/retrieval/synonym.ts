// claw-mem v5.0.0 — Synonym Expander (TypeScript)
//
// Expands search queries with synonym terms to improve recall.
// Pure TypeScript with built-in bilingual (Chinese/English) synonym dictionary.
// Zero external dependencies.
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
 * Built-in bilingual synonym dictionary.
 * Maps keywords to lists of synonym terms (including the original term).
 */
export const BUILTIN_SYNONYMS: Record<string, string[]> = {
  // AI / Machine Learning
  "ai": ["人工智能", "ai", "machine learning", "ml", "深度学习", "deep learning"],
  "人工智能": ["人工智能", "ai", "machine learning", "ml", "深度学习", "deep learning"],
  "machine learning": ["machine learning", "ml", "人工智能", "ai", "深度学习"],
  "ml": ["ml", "machine learning", "人工智能", "ai", "深度学习"],
  "deep learning": ["deep learning", "深度学习", "dl", "neural network", "神经网络"],
  "深度学习": ["深度学习", "deep learning", "dl", "neural network", "神经网络"],

  // Model / Framework
  "模型": ["模型", "model", "框架", "framework"],
  "model": ["model", "模型", "framework", "框架"],
  "框架": ["框架", "framework", "架构", "architecture"],
  "framework": ["framework", "框架", "architecture", "架构"],

  // Natural Language Processing
  "nlp": ["nlp", "natural language processing", "自然语言处理", "文本处理"],
  "自然语言处理": ["自然语言处理", "nlp", "natural language processing", "文本处理"],

  // Agent / Assistant
  "agent": ["agent", "代理", "助手", "assistant", "智能体"],
  "代理": ["代理", "agent", "助手", "assistant"],
  "助手": ["助手", "assistant", "agent", "代理"],
  "assistant": ["assistant", "助手", "agent", "代理"],

  // Memory / Storage
  "memory": ["memory", "记忆", "存储", "storage", "缓存", "cache"],
  "记忆": ["记忆", "memory", "存储", "storage"],
  "存储": ["存储", "storage", "memory", "记忆", "保存", "持久化"],
  "storage": ["storage", "存储", "memory", "持久化"],

  // Search / Retrieval
  "搜索": ["搜索", "search", "检索", "retrieval", "查询", "query"],
  "search": ["search", "搜索", "检索", "retrieval", "查询"],
  "检索": ["检索", "retrieval", "search", "搜索", "查询"],
  "retrieval": ["retrieval", "检索", "search", "搜索"],

  // Performance / Optimization
  "性能": ["性能", "performance", "优化", "optimization", "速度", "speed"],
  "performance": ["performance", "性能", "优化", "optimization", "速度"],
  "优化": ["优化", "optimization", "改进", "improvement", "性能"],
  "optimization": ["optimization", "优化", "改进", "improvement"],

  // Error / Bug
  "错误": ["错误", "error", "bug", "问题", "issue", "缺陷"],
  "error": ["error", "错误", "bug", "问题", "issue"],
  "bug": ["bug", "缺陷", "错误", "error", "issue"],

  // Deployment / Release
  "部署": ["部署", "deploy", "发布", "release", "上线"],
  "deploy": ["deploy", "部署", "发布", "release"],
  "发布": ["发布", "release", "部署", "deploy", "上线"],

  // Configuration / Settings
  "配置": ["配置", "config", "设置", "settings", "参数"],
  "config": ["config", "配置", "设置", "settings"],
  "settings": ["settings", "设置", "配置", "config"],

  // Code / Development
  "代码": ["代码", "code", "编程", "开发", "development"],
  "code": ["code", "代码", "编程", "开发"],
  "开发": ["开发", "development", "编程", "coding", "代码"],

  // Testing
  "测试": ["测试", "test", "验证", "verify", "检查"],
  "test": ["test", "测试", "验证", "verify", "检查"],

  // Data
  "数据": ["数据", "data", "信息", "information", "资料"],
  "data": ["data", "数据", "信息", "information"],

  // API
  "api": ["api", "接口", "interface", "端点", "endpoint"],
  "接口": ["接口", "api", "interface", "端点"],

  // OpenClaw specific
  "openclaw": ["openclaw", "open claw", "openc law", "openclaw"],
  "neoclaw": ["neoclaw", "neo claw", "neoc law"],
  "claw-mem": ["claw-mem", "claw mem", "clawmem", "memory system"],
  "claw-rl": ["claw-rl", "claw rl", "clawrl", "learning system"],

  // Common Technology
  "python": ["python", "py", "python3"],
  "javascript": ["javascript", "js", "typescript", "ts"],
  "typescript": ["typescript", "ts", "javascript", "js"],
  "docker": ["docker", "容器", "container"],
  "容器": ["容器", "container", "docker"],

  // Project Neo
  "project neo": ["project neo", "neo project", "neo"],
  "harness": ["harness", "harness engineering"],
};

/**
 * SynonymExpander for query expansion.
 *
 * Expands query terms using a built-in bilingual synonym dictionary,
 * with support for custom user-defined mappings.
 *
 * Usage:
 *   const expander = new SynonymExpander();
 *   const expanded = expander.expand("AI search");
 *   // -> "AI search 人工智能 machine learning 搜索 retrieval"
 */
export class SynonymExpander {
  private synonyms: Map<string, string[]>;
  private enabled: boolean;
  private maxExpansions: number;

  constructor(
    customSynonyms?: Record<string, string[]>,
    enabled: boolean = true,
    maxExpansions: number = 5,
  ) {
    this.synonyms = new Map();
    this.enabled = enabled;
    this.maxExpansions = maxExpansions;

    // Load built-in synonyms (lowercased keys)
    for (const [key, terms] of Object.entries(BUILTIN_SYNONYMS)) {
      this.synonyms.set(key.toLowerCase(), terms.map((t) => t.toLowerCase()));
    }

    // Merge custom synonyms
    if (customSynonyms) {
      for (const [key, terms] of Object.entries(customSynonyms)) {
        const keyLower = key.toLowerCase();
        const existing = this.synonyms.get(keyLower);
        if (existing) {
          const existingSet = new Set(existing);
          for (const t of terms) existingSet.add(t.toLowerCase());
          this.synonyms.set(keyLower, [...existingSet]);
        } else {
          this.synonyms.set(keyLower, terms.map((t) => t.toLowerCase()));
        }
      }
    }
  }

  /**
   * Add or extend synonym mappings for a keyword.
   *
   * @param keyword - The base keyword to map from.
   * @param terms - Synonym terms to add.
   */
  addSynonyms(keyword: string, terms: string[]): void {
    const keyLower = keyword.toLowerCase();
    const existing = this.synonyms.get(keyLower);
    if (existing) {
      const existingSet = new Set(existing);
      for (const t of terms) {
        const tLower = t.toLowerCase();
        if (tLower !== keyLower) existingSet.add(tLower);
      }
      this.synonyms.set(keyLower, [...existingSet]);
    } else {
      this.synonyms.set(
        keyLower,
        terms.map((t) => t.toLowerCase()).filter((t) => t !== keyLower),
      );
    }
  }

  /**
   * Expand query with relevant synonyms.
   *
   * @param query - Original search query.
   * @returns Expanded query string with synonyms appended.
   */
  expand(query: string): string {
    if (!this.enabled || !query) return query;

    const queryLower = query.toLowerCase();
    const expandedTerms = new Set<string>();

    // Check each keyword in the synonym dictionary
    for (const [keyword, synonyms] of this.synonyms.entries()) {
      if (queryLower.includes(keyword)) {
        for (const syn of synonyms) {
          if (syn !== keyword && !queryLower.includes(syn)) {
            expandedTerms.add(syn);
            if (expandedTerms.size >= this.maxExpansions) break;
          }
        }
        if (expandedTerms.size >= this.maxExpansions) break;
      }
    }

    if (expandedTerms.size > 0) {
      const expansionTerms = [...expandedTerms].slice(0, this.maxExpansions);
      return `${query} ${expansionTerms.join(" ")}`;
    }

    return query;
  }

  /**
   * Get synonyms for a specific keyword.
   *
   * @param keyword - Keyword to look up.
   * @returns Array of synonym terms, or empty array if not found.
   */
  getSynonyms(keyword: string): string[] {
    return this.synonyms.get(keyword.toLowerCase()) ?? [];
  }
}
