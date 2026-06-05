import { describe, it, expect, beforeEach } from 'vitest';
import { SemanticMergeScheduler } from '../src/merge/semantic_merger';
import { MultiGraphMemory } from '../src/graph/multi_graph';
import { GraphReasoner } from '../src/graph/graph_reasoner';
import { EdgeType } from '../src/graph/edges';

// ── Mocks ──────────────────────────────────────────────────────────

class MockStorage {
  filePath = '/tmp/test-memory.md';
  private mems: Record<string, unknown>[] = [];
  constructor(mems?: Record<string, unknown>[]) { this.mems = mems ?? []; }
  getAll() { return [...this.mems]; }
  _formatMemory(m: Record<string, unknown>) { return `- [${m.id}] ${m.content}\n`; }
}

class MockLLM {
  private responses: Record<string, string> = {};
  setResponse(keyword: string, response: string) { this.responses[keyword] = response; }
  generate(prompt: string, _opts?: any): string {
    for (const [kw, resp] of Object.entries(this.responses)) {
      if (prompt.includes(kw)) return resp;
    }
    return 'merged response';
  }
}

class MockEmbedding {
  encode(texts: string[]): number[][] {
    return texts.map((_, i) => {
      const v = new Array(128).fill(0);
      v[i % 128] = 1;
      return v;
    });
  }
}

class MockManager {
  semantic = new MockStorage();
  stored: Array<{ content: string; type: string; tags: string[]; meta: Record<string, string> }> = [];
  store(content: string, type: string, tags?: string[], meta?: Record<string, string>) {
    this.stored.push({ content, type, tags: tags ?? [], meta: meta ?? {} });
  }
}

function makeMem(id: string, content: string, meta?: Record<string, string>, tags?: string[]) {
  return { id, content, metadata: meta ?? {}, tags: tags ?? [] };
}

// ── SemanticMergeScheduler ─────────────────────────────────────────

describe('SemanticMergeScheduler', () => {
  let manager: MockManager;
  let llm: MockLLM;
  let embed: MockEmbedding;

  beforeEach(() => {
    manager = new MockManager();
    llm = new MockLLM();
    embed = new MockEmbedding();
  });

  it('shouldRun returns true at interval boundary', () => {
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any, 10);
    expect(s.shouldRun(10)).toBe(true);
    expect(s.shouldRun(20)).toBe(true);
  });

  it('shouldRun returns false below interval', () => {
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any, 10);
    expect(s.shouldRun(5)).toBe(false);
    expect(s.shouldRun(15)).toBe(false);
  });

  it('findMergeCandidates returns empty when < 2 memories', () => {
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any);
    expect(s.findMergeCandidates()).toEqual([]);
  });

  it('findMergeCandidates finds similar memories', () => {
    manager.semantic = new MockStorage([
      makeMem('m1', 'TypeScript migration to strict mode'),
      makeMem('m2', 'Migrating codebase to TypeScript strict'),
      makeMem('m3', 'Setting up CI pipeline for tests'),
    ]);
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any, 10, 'auto', 0.85, 0.6);
    const candidates = s.findMergeCandidates();
    expect(Array.isArray(candidates)).toBe(true);
  });

  it('findMergeCandidates skips deprecated memories', () => {
    manager.semantic = new MockStorage([
      makeMem('m1', 'Active memory', {}),
      makeMem('m2', 'Deprecated memory', { deprecated: 'true' }),
      makeMem('m3', 'Another active', {}),
    ]);
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any, 10, 'auto', 0.85, 0.6);
    const candidates = s.findMergeCandidates();
    candidates.forEach(c => {
      expect(c.id1).not.toBe('m2');
      expect(c.id2).not.toBe('m2');
    });
  });

  it('mergePair returns merged memory', () => {
    manager.semantic = new MockStorage([makeMem('m1', 'A'), makeMem('m2', 'B')]);
    llm.setResponse('Memory A:', 'merged result text');
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any);
    const result = s.mergePair(makeMem('m1', 'A'), makeMem('m2', 'B'), 0.9);
    expect(result).not.toBeNull();
    expect(result!.content).toBe('merged result text');
  });

  it('mergePair returns null for empty content', () => {
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any);
    expect(s.mergePair(makeMem('m1', ''), makeMem('m2', 'B'), 0.9)).toBeNull();
  });

  it('runMergeCycle processes candidates', () => {
    manager.semantic = new MockStorage([
      makeMem('m1', 'First memory about testing'),
      makeMem('m2', 'Second memory about test frameworks'),
      makeMem('m3', 'Completely unrelated topic here'),
    ]);
    llm.setResponse('Memory A:', 'merged');
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any, 10, 'auto', 0.85, 0.1);
    const stats = s.runMergeCycle();
    expect(typeof stats.mergedCount).toBe('number');
    expect(typeof stats.candidatesFound).toBe('number');
  });

  it('toString returns summary', () => {
    const s = new SemanticMergeScheduler(manager as any, llm as any, embed as any, 50);
    expect(s.toString()).toContain('SemanticMergeScheduler');
    expect(s.toString()).toContain('50');
  });
});

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
