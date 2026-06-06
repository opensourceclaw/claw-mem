import OpenAI from 'openai';

const DEFAULT_CONFIG = {
  baseUrl: 'https://zhenze-huhehaote.cmecloud.cn/api/coding/v1',
  apiKey: 'rNI5Iin7Kp4uG0tvVgp4-8I6uU8IS6EpFlyRHJ-Zs5I',
  model: 'MiniMax-M2.5',
};

let _client: OpenAI | null = null;

function getClient(): OpenAI {
  if (!_client) {
    _client = new OpenAI({
      baseURL: DEFAULT_CONFIG.baseUrl,
      apiKey: DEFAULT_CONFIG.apiKey,
    });
  }
  return _client;
}

export interface EvalResult {
  score: number;
  reasoning: string;
}

function extractJSON(text: string): string {
  // Try to extract JSON from markdown code blocks
  let cleaned = text.trim();
  
  // Remove markdown code fences
  if (cleaned.startsWith('```json')) {
    cleaned = cleaned.slice(7);
  } else if (cleaned.startsWith('```')) {
    cleaned = cleaned.slice(3);
  }
  
  if (cleaned.endsWith('```')) {
    cleaned = cleaned.slice(0, -3);
  }
  
  return cleaned.trim();
}

export async function evaluateRetrieval(
  query: string,
  retrievedContext: string[],
  expectedAnswer: string,
): Promise<EvalResult> {
  const client = getClient();
  const context = retrievedContext.join("\n---\n");

  const prompt = `You are evaluating a memory retrieval system.

Context retrieved:
${context}

Query: ${query}
Expected answer: ${expectedAnswer}

Evaluate whether the retrieved context can answer the query.
Respond with ONLY a JSON object (no markdown), format:
{"score": 0-100, "reasoning": "brief explanation"}`;

  try {
    const response = await client.chat.completions.create({
      model: DEFAULT_CONFIG.model,
      messages: [{ role: "user", content: prompt }],
      temperature: 0,
      max_tokens: 200,
    });

    const content = response?.choices?.[0]?.message?.content || "{}";
    const cleaned = extractJSON(content);
    
    try {
      const parsed = JSON.parse(cleaned);
      return {
        score: Math.min(100, Math.max(0, parsed.score || 0)),
        reasoning: parsed.reasoning || "",
      };
    } catch (parseError) {
      console.log("JSON parse failed, content:", cleaned.slice(0, 100));
      // Fallback: try rule-based
      return { 
        score: ruleBasedScore(retrievedContext, expectedAnswer) * 100, 
        reasoning: "fallback to rule-based" 
      };
    }
  } catch (e) {
    console.log("LLM eval error:", e);
    // Fallback to rule-based
    return { 
      score: ruleBasedScore(retrievedContext, expectedAnswer) * 100, 
      reasoning: "LLM failed, fallback to rule-based" 
    };
  }
}

// Rule-based fallback
export function ruleBasedScore(
  retrievedContext: string[],
  expectedAnswer: string,
): number {
  if (!retrievedContext.length) return 0;
  const combined = retrievedContext.join(" ").toLowerCase();
  const expected = expectedAnswer.toLowerCase();
  
  const keywords = expected.split(/\s+/).filter(k => k.length > 2);
  const matches = keywords.filter(k => combined.includes(k)).length;
  
  return keywords.length > 0 ? matches / keywords.length : 0;
}

export async function evaluateAccuracy(
  query: string,
  retrievedContext: string[],
  expectedAnswer: string,
): Promise<number> {
  const result = await evaluateRetrieval(query, retrievedContext, expectedAnswer);
  return result.score / 100;
}

export async function evaluatePrecision(
  query: string,
  retrievedContext: string[],
  expectedAnswers: string[],
): Promise<number> {
  if (expectedAnswers.length === 0) return 0;
  
  const results = await Promise.all(
    expectedAnswers.map(async (exp) => 
      evaluateRetrieval(query, retrievedContext, exp)
    )
  );
  
  const avgScore = results.reduce((sum, r) => sum + r.score, 0) / results.length;
  return avgScore / 100;
}

export async function evaluateRecall(
  query: string,
  retrievedContext: string[],
  facts: string[],
): Promise<number> {
  if (facts.length === 0) return 0;
  
  const results = await Promise.all(
    facts.map(async (fact) => 
      evaluateRetrieval(query, retrievedContext, fact)
    )
  );
  
  const avgScore = results.reduce((sum, r) => sum + r.score, 0) / facts.length;
  return avgScore / 100;
}
