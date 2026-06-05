import { describe, it, expect, beforeEach } from 'vitest';
import { LLMCompressorV2 } from '../src/compression/llm-compressor-v2';

describe('LLMCompressorV2', () => {
  let compressor: LLMCompressorV2;

  beforeEach(() => {
    compressor = new LLMCompressorV2();
  });

  const makeMemory = (text: string) => ({
    id: 'test-1',
    text,
    memory_type: 'episodic' as const,
    timestamp: new Date().toISOString(),
    importance: 0.5,
  });

  it('compressWithQualityEvaluation returns quality metrics', () => {
    const mem = makeMemory(
      '第一步，我们分析了代码库的结构。然后，我们发现了性能瓶颈。因为数据库查询没有索引，所以响应时间很慢。因此，我们决定添加索引优化。',
    );
    const result = compressor.compressWithQualityEvaluation(mem);

    expect(result.summary.length).toBeGreaterThan(0);
    expect(result.quality.semanticRetention).toBeGreaterThan(0);
    expect(result.quality.keyInformationPreserved).toBeGreaterThan(0);
    expect(result.quality.reasoningChainIntegrity).toBeGreaterThan(0);
    expect(result.quality.overallQuality).toBeGreaterThan(0);
    expect(result.quality.compressionRatio).toBeLessThan(1);
  });

  it('adaptiveCompress respects target token count', () => {
    const mem = makeMemory(
      '这是一个很长的记忆文本，包含了大量的信息。首先，我们讨论了架构设计。然后，我们实现了核心功能。因为时间紧迫，所以我们需要快速行动。最终，我们决定采用渐进式的方案来解决这个问题。这个决定是基于之前的经验教训。',
    );
    const result = compressor.adaptiveCompress(mem, 20);

    expect(result.method).toBe('adaptive');
    expect(result.quality.compressedTokens).toBeLessThanOrEqual(30);
  });

  it('adaptiveCompress returns base when already within target', () => {
    const mem = makeMemory('short text');
    const result = compressor.adaptiveCompress(mem, 1000);
    expect(result.summary).toBeDefined();
  });

  it('preserveReasoningChain detects reasoning keywords', () => {
    const withReasoning = makeMemory(
      '因为数据库连接池耗尽，所以API响应超时。因此需要增加连接池大小。',
    );
    expect(compressor.preserveReasoningChain(withReasoning)).toBe(true);

    const withoutReasoning = makeMemory('今天天气不错。');
    expect(compressor.preserveReasoningChain(withoutReasoning)).toBe(false);
  });

  it('batchCompressWithQuality processes multiple memories', () => {
    const memories = [
      makeMemory('第一个记忆：关于TypeScript migration的讨论。'),
      makeMemory('第二个记忆：因为迁移导致了CI失败，所以需要修复。'),
      makeMemory('第三个记忆：最终决定采用渐进迁移方案。'),
    ];
    const results = compressor.batchCompressWithQuality(memories);
    expect(results).toHaveLength(3);
    expect(results[0].summary).toBeDefined();
  });

  it('getQualityStats returns valid statistics', () => {
    compressor.compressWithQualityEvaluation(makeMemory('test memory content here'));
    compressor.compressWithQualityEvaluation(makeMemory('another memory'));

    const stats = compressor.getQualityStats();
    expect(stats.totalCompressions).toBe(2);
    expect(stats.avgOverallQuality).toBeGreaterThan(0);
  });

  it('updateConfig changes behavior', () => {
    const result1 = compressor.preserveReasoningChain(
      makeMemory('because of something'),
    );
    expect(result1).toBe(true);

    compressor.updateConfig({ preserveReasoning: false });
    const result2 = compressor.preserveReasoningChain(
      makeMemory('because of something'),
    );
    expect(result2).toBe(false);
  });

  it('reset clears history', () => {
    compressor.compressWithQualityEvaluation(makeMemory('test'));
    compressor.reset();
    const stats = compressor.getQualityStats();
    expect(stats.totalCompressions).toBe(0);
  });

  it('handles empty text gracefully', () => {
    const mem = makeMemory('');
    const result = compressor.compressWithQualityEvaluation(mem);
    expect(result.summary).toBeDefined();
  });
});
