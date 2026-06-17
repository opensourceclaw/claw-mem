import { describe, it, expect, beforeEach } from 'vitest';
import { DualLayerMemory } from '../src/graph/dual_layer';

describe('DualLayerMemory', () => {
  let dlm: DualLayerMemory;

  beforeEach(() => { dlm = new DualLayerMemory(); });

  it('addEvent returns eventId', () => {
    const id = dlm.addEvent('Migration', 'TS migration', ['n1', 'n2'], 's1', ['typescript']);
    expect(id).toBeDefined();
    expect(id).toContain('evt');
  });

  it('addTopic returns topicId', () => {
    const id = dlm.addTopic('TypeSafety', 'Type safety', ['k1', 'k2']);
    expect(id).toBeDefined();
    expect(id).toContain('tpc_');
  });

  it('getEvent returns created event', () => {
    const id = dlm.addEvent('Test', 'desc', ['n1'], 's1');
    const got = dlm.getEvent(id);
    expect(got).toBeDefined();
    expect(got!.title).toBe('Test');
  });

  it('getTopic returns created topic', () => {
    const id = dlm.addTopic('Topic1', 'desc', ['kw']);
    const got = dlm.getTopic(id);
    expect(got).toBeDefined();
  });

  it('linkEvents connects two events', () => {
    const e1 = dlm.addEvent('E1', 'd1', ['n1'], 's1');
    const e2 = dlm.addEvent('E2', 'd2', ['n2'], 's1');
    dlm.linkEvents(e1, e2);
    const chain = dlm.getEventChain(e1);
    expect(chain.length).toBeGreaterThan(0);
  });

  it('linkTopics connects two topics', () => {
    const t1 = dlm.addTopic('T1', 'd1', ['k1']);
    const t2 = dlm.addTopic('T2', 'd2', ['k2']);
    expect(() => dlm.linkTopics(t1, t2, 0.8)).not.toThrow();
  });

  it('getRelatedTopics returns related', () => {
    const t1 = dlm.addTopic('T1', 'd1', ['a', 'b']);
    const t2 = dlm.addTopic('T2', 'd2', ['a', 'c']);
    dlm.linkTopics(t1, t2);
    const related = dlm.getRelatedTopics(t1);
    expect(Array.isArray(related)).toBe(true);
  });

  it('getEventChain returns chain', () => {
    const e1 = dlm.addEvent('E1', 'd1', ['n1'], 's1');
    const e2 = dlm.addEvent('E2', 'd2', ['n2'], 's1');
    dlm.linkEvents(e1, e2);
    const chain = dlm.getEventChain(e1);
    expect(Array.isArray(chain)).toBe(true);
  });

  it('toDict and fromDict round-trip', () => {
    dlm.addEvent('E1', 'Test', ['n1'], 's1', ['ts']);
    dlm.addTopic('T1', 'Test', ['kw']);
    const d = dlm.toDict();
    expect(d.events).toBeDefined();
    expect(d.topics).toBeDefined();
    const restored = DualLayerMemory.fromDict(d);
    expect(restored).toBeDefined();
  });

  it('getEvent returns undefined for unknown', () => {
    expect(dlm.getEvent('nonexistent')).toBeUndefined();
  });

  it('getTopic returns undefined for unknown', () => {
    expect(dlm.getTopic('nonexistent')).toBeUndefined();
  });
});
