import { describe, it, expect } from 'vitest';
import { cosineSimilarity } from '../src/merge/semantic_merger';
import {
  conflictReportToDict,
  conflictResolutionToDict,
} from '../src/merge/conflict_detector';
import { GatingFilter } from '../src/gating/write_time_gating';

describe('SemanticMerger', () => {
  it('cosineSimilarity returns 1 for identical', () => {
    expect(cosineSimilarity([1, 2, 3], [1, 2, 3])).toBeCloseTo(1, 5);
  });

  it('cosineSimilarity returns 0 for orthogonal', () => {
    expect(cosineSimilarity([1, 0], [0, 1])).toBeCloseTo(0, 5);
  });

  it('cosineSimilarity handles negative', () => {
    expect(cosineSimilarity([1, 0], [-1, 0])).toBeCloseTo(-1, 5);
  });

  it('cosineSimilarity returns 0 for zero vector', () => {
    expect(cosineSimilarity([0, 0], [1, 1])).toBe(0);
  });

  it('cosineSimilarity handles different length vectors', () => {
    const sim = cosineSimilarity([1, 2, 3], [1, 2]);
    expect(typeof sim).toBe('number');
  });
});

describe('ConflictDetector', () => {
  it('conflictReportToDict converts', () => {
    const d = conflictReportToDict({
      conflictType: 'semantic',
      memoryIdA: 'a1', memoryIdB: 'b1',
      contentA: 'A', contentB: 'B',
      description: 'conflict',
      similarity: 0.8,
      resolved: false,
      resolution: null,
    });
    expect(d.conflict_type).toBe('semantic');
    expect(d.memory_id_a).toBe('a1');
    expect(d.similarity).toBe(0.8);
    expect(d.resolution).toBeNull();
  });

  it('conflictResolutionToDict converts', () => {
    const d = conflictResolutionToDict({
      action: 'merge',
      winnerId: 'mem-a',
      mergedContent: 'merged text',
      reasoning: 'similar content',
    });
    expect(d.action).toBe('merge');
    expect(d.winner_id).toBe('mem-a');
    expect(d.reasoning).toBe('similar content');
  });
});

describe('GatingFilter', () => {
  it('DEFAULT_THRESHOLD is 1.0', () => {
    expect(GatingFilter.DEFAULT_THRESHOLD).toBe(1.0);
  });

  it('TYPE_WEIGHTS has expected types', () => {
    expect(GatingFilter.TYPE_WEIGHTS.semantic).toBe(0.5);
    expect(GatingFilter.TYPE_WEIGHTS.procedural).toBe(0.3);
  });

  it('should_store returns result', () => {
    const filter = new GatingFilter();
    const result = filter.should_store({
      content: 'test content',
      memory_type: 'semantic',
    });
    expect(result.should_store).toBeDefined();
    expect(typeof result.importance_score).toBe('number');
  });

  it('should_store with high access count scores higher', () => {
    const filter = new GatingFilter(undefined, 0.5);
    const low = filter.should_store({ memory_type: 'episodic', access_count: 0 });
    const high = filter.should_store({ memory_type: 'episodic', access_count: 12, source: 'user' });
    expect(high.importance_score).toBeGreaterThan(low.importance_score);
  });
});
