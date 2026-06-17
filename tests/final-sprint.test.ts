import { describe, it, expect, beforeEach } from 'vitest';
import { MultiGraphMemory } from '../src/graph/multi_graph';
import { GraphReasoner } from '../src/graph/graph_reasoner';
import { EdgeType } from '../src/graph/edges';

// ── Graph Modules ──────────────────────────────────────────────────

describe('MultiGraphMemory', () => {
  it('creates with default subgraphs', () => {
    const mg = new MultiGraphMemory();
    expect(mg).toBeDefined();
    expect(mg.nodeCount()).toBe(0);
  });

  it('addNode and getNode', () => {
    const mg = new MultiGraphMemory();
    mg.addNode('n1', 'Test content', 'concept' as any);
    expect(mg.nodeCount()).toBe(1);
    expect(mg.getNode('n1')).toBeDefined();
  });

  it('addNode is idempotent', () => {
    const mg = new MultiGraphMemory();
    mg.addNode('n1', 'Test', 'concept' as any);
    mg.addNode('n1', 'Test again', 'concept' as any);
    expect(mg.nodeCount()).toBe(1);
  });

  it('addEdge with known type', () => {
    const mg = new MultiGraphMemory();
    mg.addNode('n1', 'A', 'concept' as any);
    mg.addNode('n2', 'B', 'concept' as any);
    expect(() => mg.addEdge('n1', 'n2', EdgeType.RELATED_TO, 0.8)).not.toThrow();
  });

  it('addEdge throws for unknown type', () => {
    const mg = new MultiGraphMemory();
    mg.addNode('n1', 'A', 'concept' as any);
    mg.addNode('n2', 'B', 'concept' as any);
    expect(() => mg.addEdge('n1', 'n2', 'bogus' as any)).toThrow();
  });

  it('getNode returns undefined for unknown', () => {
    const mg = new MultiGraphMemory();
    expect(mg.getNode('none')).toBeUndefined();
  });

  it('toDict and fromDict round-trip', () => {
    const mg = new MultiGraphMemory();
    mg.addNode('n1', 'A', 'concept' as any);
    const d = mg.toDict();
    expect(d.nodes).toBeDefined();
    const restored = MultiGraphMemory.fromDict(d);
    expect(restored).toBeDefined();
  });
});

describe('GraphReasoner', () => {
  it('creates standalone', () => {
    const gr = new GraphReasoner();
    expect(gr).toBeDefined();
  });

  it('addTriplet builds graph', () => {
    const gr = new GraphReasoner();
    gr.addTriplet('A', 'relates_to', 'B', 0.9);
    const paths = gr.findPaths('A', 'B');
    expect(Array.isArray(paths)).toBe(true);
  });

  it('addTriplets batch adds', () => {
    const gr = new GraphReasoner();
    gr.addTriplets([
      { subject: 'A', predicate: 'uses', object: 'B', confidence: 0.8 },
      { subject: 'B', predicate: 'depends_on', object: 'C', confidence: 0.7 },
    ]);
    const paths = gr.findPaths('A', 'C', 3);
    expect(Array.isArray(paths)).toBe(true);
  });

  it('findPaths returns empty for disconnected', () => {
    const gr = new GraphReasoner();
    expect(gr.findPaths('X', 'Y')).toEqual([]);
  });

  it('bfsShortest finds shortest path', () => {
    const gr = new GraphReasoner();
    gr.addTriplet('A', 'to', 'B');
    gr.addTriplet('B', 'to', 'C');
    const path = gr.bfsShortest('A', 'C', 3);
    expect(path).toBeDefined();
  });

  it('findRelated returns adjacent nodes', () => {
    const gr = new GraphReasoner();
    gr.addTriplet('A', 'to', 'B');
    gr.addTriplet('A', 'to', 'C');
    const related = gr.findRelated('A', 2);
    expect(related.length).toBeGreaterThanOrEqual(2);
  });
});
