import { describe, it, expect } from 'vitest';
import { GatingFilter } from '../src/gating/write_time_gating';

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
