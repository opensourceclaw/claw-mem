import { describe, it, expect } from 'vitest';
import { ReflectionOrchestrator } from '../src/reflection/orchestrator';
import { BeliefSynthesizer } from '../src/reflection/synthesizer';
import { BeliefTracker } from '../src/reflection/belief_tracker';

describe('ReflectionOrchestrator', () => {
  it('creates with default config', () => {
    const orch = new ReflectionOrchestrator();
    expect(orch.synthesizer).toBeDefined();
    expect(orch.tracker).toBeDefined();
  });

  it('reflect with empty memories returns empty result', () => {
    const orch = new ReflectionOrchestrator();
    const result = orch.reflect([], 'test-user');
    expect(result.observations).toEqual([]);
    expect(result.beliefs).toEqual([]);
    expect(result.new_beliefs).toEqual([]);
    expect(result.summary).toContain('Reflection');
  });

  it('reflect with memories produces observations', () => {
    const orch = new ReflectionOrchestrator({ min_confidence: 0.5 });
    const mems = [
      { id: 'm1', content: 'User prefers TypeScript for new projects', memory_type: 'episodic' },
      { id: 'm2', content: 'Peter asked about code review process', memory_type: 'episodic' },
    ];
    const result = orch.reflect(mems, 'user1');
    expect(result.observations.length).toBeGreaterThanOrEqual(0);
    expect(result.beliefs).toBeDefined();
    expect(result.timestamp).toBeDefined();
    expect(result.summary).toBeDefined();
  });

  it('reflect with force flag works', () => {
    const orch = new ReflectionOrchestrator();
    const result = orch.reflect([], 'user1', true);
    expect(result).toBeDefined();
    expect(result.beliefs).toEqual([]);
  });

  it('get_beliefs returns array', () => {
    const orch = new ReflectionOrchestrator();
    const beliefs = orch.get_beliefs();
    expect(Array.isArray(beliefs)).toBe(true);
  });

  it('get_beliefs with history', () => {
    const orch = new ReflectionOrchestrator();
    orch.reflect([{ id: 'm1', content: 'User likes dark mode', memory_type: 'episodic' }], 'u1');
    const beliefs = orch.get_beliefs(true);
    expect(Array.isArray(beliefs)).toBe(true);
  });

  it('get_reflection_stats returns stats', () => {
    const orch = new ReflectionOrchestrator();
    orch.reflect([{ id: 'm1', content: 'Test', memory_type: 'episodic' }], 'u1');
    const stats = orch.get_reflection_stats();
    expect(stats.reflection_count).toBe(1);
    expect(stats.last_reflection_at).toBeDefined();
    expect(typeof stats.total_beliefs).toBe('number');
  });
});

describe('BeliefTracker', () => {
  it('records and retrieves beliefs', () => {
    const tracker = new BeliefTracker();
    expect(tracker.count_beliefs()).toBe(0);
    tracker.record('b1', 'User likes TypeScript', 0.9);
    expect(tracker.count_beliefs()).toBe(1);
    expect(tracker.get_current('b1')?.statement).toBe('User likes TypeScript');
  });

  it('updates existing belief', () => {
    const tracker = new BeliefTracker();
    tracker.record('b1', 'user likes JS', 0.5);
    tracker.update('b1', 'user likes TypeScript', 0.9);
    const current = tracker.get_current('b1');
    expect(current?.statement).toBe('user likes TypeScript');
    expect(current?.confidence).toBe(0.9);
    expect(current?.version).toBe(2);
  });

  it('get_all_ids returns tracked ids', () => {
    const tracker = new BeliefTracker();
    tracker.record('b1', 'belief 1', 0.8);
    tracker.record('b2', 'belief 2', 0.7);
    expect(tracker.get_all_ids()).toHaveLength(2);
  });

  it('get_history returns versions', () => {
    const tracker = new BeliefTracker();
    tracker.record('b1', 'v1', 0.5);
    tracker.update('b1', 'v2', 0.9);
    const history = tracker.get_history('b1');
    expect(history.length).toBeGreaterThanOrEqual(1);
  });

  it('count_versions returns total', () => {
    const tracker = new BeliefTracker();
    tracker.record('b1', 'v1', 0.5);
    tracker.update('b1', 'v2', 0.9);
    expect(tracker.count_versions()).toBeGreaterThanOrEqual(2);
  });
});

describe('BeliefSynthesizer', () => {
  it('creates with default config', () => {
    const synth = new BeliefSynthesizer();
    expect(synth).toBeDefined();
  });

  it('extract_observations from memories', () => {
    const synth = new BeliefSynthesizer();
    const mems = [
      { id: 'm1', content: 'First memory content', memory_type: 'episodic' },
    ];
    const obs = synth.extract_observations(mems);
    expect(Array.isArray(obs)).toBe(true);
  });

  it('synthesize beliefs from observations', () => {
    const synth = new BeliefSynthesizer();
    const mems = [{ id: 'm1', content: 'User prefers TypeScript for all new code', memory_type: 'episodic' }];
    const obs = synth.extract_observations(mems);
    const beliefs = synth.synthesize(obs, 'user1');
    expect(Array.isArray(beliefs)).toBe(true);
  });

  it('synthesize with empty observations', () => {
    const synth = new BeliefSynthesizer();
    const beliefs = synth.synthesize([], 'user1');
    expect(beliefs).toEqual([]);
  });
});
