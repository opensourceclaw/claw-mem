import { describe, it, expect } from 'vitest';
import { DummyExtractor, LLMExtractor } from '../src/graph/extractors';
import { OpenIEExtractor } from '../src/extraction/openie_extractor';
import { InMemoryGraphStorage } from '../src/graph/storage';
import { Edge, EdgeType } from '../src/graph/edges';
import { Node } from '../src/graph/nodes';
import { CompressionSpectrum } from '../src/compression/spectrum';

// ── extractors.ts ─────────────────────────────────────────────────

describe('DummyExtractor', () => {
  it('extractFacts returns empty', () => {
    expect(new DummyExtractor().extractFacts('any text')).toEqual([]);
  });
  it('extractConcepts returns empty', () => {
    expect(new DummyExtractor().extractConcepts('any text')).toEqual([]);
  });
});

describe('LLMExtractor', () => {
  it('falls back to rule-based when no LLM', () => {
    const ex = new LLMExtractor(null);
    expect(Array.isArray(ex.extractFacts('Peter likes TypeScript'))).toBe(true);
    expect(Array.isArray(ex.extractConcepts('Docker and Kubernetes'))).toBe(true);
  });

  it('uses mock LLM for facts', () => {
    const facts = new LLMExtractor({ generate: () => 'fact one\nfact two' }).extractFacts('test');
    expect(facts).toEqual(['fact one', 'fact two']);
  });

  it('uses mock LLM for concepts', () => {
    const c = new LLMExtractor({ generate: () => 'c1\nc2\nc3' }).extractConcepts('test');
    expect(c).toHaveLength(3);
  });

  it('falls back on LLM error', () => {
    const bad = { generate: () => { throw new Error('fail'); } };
    expect(Array.isArray(new LLMExtractor(bad).extractFacts('Peter uses TS'))).toBe(true);
    expect(Array.isArray(new LLMExtractor(bad).extractConcepts('Docker'))).toBe(true);
  });
});

// ── openie_extractor.ts ────────────────────────────────────────────

describe('OpenIEExtractor', () => {
  it('extracts from text', () => {
    const t = new OpenIEExtractor().extract('Peter uses TypeScript for development');
    expect(Array.isArray(t)).toBe(true);
  });
  it('handles empty', () => { expect(new OpenIEExtractor().extract('')).toEqual([]); });
  it('handles short', () => { expect(new OpenIEExtractor().extract('hi')).toEqual([]); });
  it('handles CJK', () => {
    expect(Array.isArray(new OpenIEExtractor().extract('Peter喜欢TypeScript'))).toBe(true);
  });
});

// ── storage.ts ─────────────────────────────────────────────────────

describe('InMemoryGraphStorage', () => {
  it('saveNode and getNode', () => {
    const gs = new InMemoryGraphStorage();
    gs.saveNode(new Node('n1', 'concept' as any, 'Test'));
    expect(gs.getNode('n1')!.content).toBe('Test');
  });

  it('deleteNode', () => {
    const gs = new InMemoryGraphStorage();
    gs.saveNode(new Node('x1', 'concept' as any, 'X'));
    expect(gs.deleteNode('x1')).toBe(true);
    expect(gs.deleteNode('none')).toBe(false);
  });

  it('saveEdge and getEdge', () => {
    const gs = new InMemoryGraphStorage();
    gs.saveEdge(new Edge('a', 'b', EdgeType.RELATED_TO, 0.8));
    expect(gs.getEdge('a', 'b')!.weight).toBe(0.8);
  });

  it('getEdgesFrom', () => {
    const gs = new InMemoryGraphStorage();
    gs.saveEdge(new Edge('a', 'b', EdgeType.RELATED_TO, 0.5));
    expect(gs.getEdgesFrom('a').length).toBe(1);
  });

  it('getNeighbors', () => {
    const gs = new InMemoryGraphStorage();
    gs.saveEdge(new Edge('src', 'dst', EdgeType.RELATED_TO, 1));
    expect(gs.getNeighbors('src').has('dst')).toBe(true);
  });

  it('getAllNodes', () => {
    const gs = new InMemoryGraphStorage();
    gs.saveNode(new Node('n1', 'fact' as any, 'F1'));
    expect(gs.getAllNodes().length).toBeGreaterThanOrEqual(1);
  });

  it('getStats returns object', () => {
    const gs = new InMemoryGraphStorage();
    const stats = gs.getStats();
    expect(typeof stats).toBe('object');
  });

  it('clear', () => {
    const gs = new InMemoryGraphStorage();
    gs.saveNode(new Node('x', 'concept' as any, 'X'));
    gs.clear();
    expect(gs.getNode('x')).toBeUndefined();
  });
});

// ── spectrum.ts ────────────────────────────────────────────────────

describe('CompressionSpectrum', () => {
  it('creates', () => { expect(new CompressionSpectrum()).toBeDefined(); });
  it('recordAccess returns undefined for unknown', () => {
    expect(new CompressionSpectrum().recordAccess('nonexistent')).toBeUndefined();
  });
  it('recordApply returns undefined for unknown', () => {
    expect(new CompressionSpectrum().recordApply('nonexistent')).toBeUndefined();
  });
  it('recordVerify returns undefined for unknown', () => {
    expect(new CompressionSpectrum().recordVerify('nonexistent')).toBeUndefined();
  });
  it('getCompressed returns array', () => {
    expect(Array.isArray(new CompressionSpectrum().getCompressed('skill'))).toBe(true);
  });
});
