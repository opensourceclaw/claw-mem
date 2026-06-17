import { describe, it, expect } from 'vitest';
import { Node, EpisodeNode, FactNode, ReflectionNode, ConceptNode, createNode } from '../src/graph/nodes';

describe('Graph Nodes', () => {
  it('Node creates with id, type, content', () => {
    const node = new Node('n1', 'episode' as any, 'test content');
    expect(node.id).toBe('n1');
    expect(node.type).toBe('episode');
    expect(node.content).toBe('test content');
  });

  it('Node toDict and fromDict round-trip', () => {
    const node = new Node('n1', 'concept' as any, 'test', null, { key: 'val' });
    const d = node.toDict();
    expect(d.id).toBe('n1');
    expect(d.metadata.key).toBe('val');
    const restored = Node.fromDict(d);
    expect(restored.id).toBe('n1');
    expect(restored.content).toBe('test');
  });

  it('EpisodeNode creates with content and timestamp', () => {
    const ts = new Date();
    const ep = new EpisodeNode('ep1', 'test content', 1, 'user', ts, 's1');
    expect(ep.id).toBe('ep1');
    expect(ep.content).toBe('test content');
    expect(ep.sequence_id).toBe(1);
    expect(ep.speaker).toBe('user');
  });

  it('FactNode creates with required fields', () => {
    const fn = new FactNode('f1', 'test fact', 0.9, 'ep1', false);
    expect(fn.id).toBe('f1');
    expect(fn.content).toBe('test fact');
    expect(fn.confidence).toBe(0.9);
    expect(fn.verified).toBe(false);
  });

  it('ReflectionNode creates', () => {
    const rn = new ReflectionNode('r1', 'summary', 'insight', ['f1'], 0.8, 's1');
    expect(rn.id).toBe('r1');
    expect(rn.content).toBe('summary');
    expect(rn.summary_type).toBe('insight');
  });

  it('ConceptNode creates', () => {
    const cn = new ConceptNode('c1', 'TypeScript', 'language', 3, ['ts']);
    expect(cn.id).toBe('c1');
    expect(cn.content).toBe('TypeScript');
    expect(cn.category).toBe('language');
    expect(cn.frequency).toBe(3);
  });

  it('createNode dispatches to correct types', () => {
    const ep = createNode('episode', 'e1', { content: 'test', timestamp: new Date().toISOString() });
    expect(ep).toBeInstanceOf(EpisodeNode);
    const fn = createNode('fact', 'f1', { content: 'fact', confidence: 0.8 });
    expect(fn).toBeInstanceOf(FactNode);
    const cn = createNode('concept', 'c1', { content: 'TS', category: 'tool' });
    expect(cn).toBeInstanceOf(ConceptNode);
  });

  it('createNode throws on unknown type', () => {
    expect(() => createNode('bogus' as any, 'x', {})).toThrow();
  });
});
