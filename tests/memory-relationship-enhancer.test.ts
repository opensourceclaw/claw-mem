import { describe, it, expect, beforeEach } from 'vitest';
import {
  EntityChaining,
  DecisionLineage,
  CausalGraph,
  MemoryRelationshipEnhancer,
} from '../src/memory-relationship-enhancer';

describe('EntityChaining', () => {
  let ec: EntityChaining;

  beforeEach(() => { ec = new EntityChaining(); });

  it('linkEntities creates bidirectional links', () => {
    ec.linkEntities('TypeScript', 'JavaScript', 's1');
    const chain = ec.getEntityChain('TypeScript');
    expect(chain.length).toBe(2);
    expect(chain.some((n) => n.name === 'JavaScript')).toBe(true);
  });

  it('linkEntities increments weight for repeated links', () => {
    ec.linkEntities('A', 'B', 's1');
    ec.linkEntities('A', 'B', 's2');
    const links = ec.getEntityLinks('A');
    expect(links).toHaveLength(1);
    expect(links[0].weight).toBe(2);
  });

  it('getEntityChain returns connected component', () => {
    ec.linkEntities('A', 'B', 's1');
    ec.linkEntities('B', 'C', 's1');
    ec.linkEntities('D', 'E', 's1'); // separate component

    const chain = ec.getEntityChain('A');
    expect(chain.length).toBe(3); // A, B, C
  });

  it('getCrossSessionRelated finds cross-session entities', () => {
    ec.linkEntities('shared', 'in_s1', 's1');
    ec.linkEntities('shared', 'in_s2', 's2');
    // 'in_s3' only in s3, which shared has NOT been seen in
    ec.linkEntities('in_s2', 'in_s3', 's3');
    const cross = ec.getCrossSessionRelated('shared');
    expect(cross.length).toBeGreaterThan(0);
  });

  it('getEntityLinks returns empty for unknown entity', () => {
    expect(ec.getEntityLinks('unknown')).toEqual([]);
  });

  it('getStats returns counts', () => {
    ec.linkEntities('A', 'B', 's1');
    ec.linkEntities('B', 'C', 's1');
    const stats = ec.getStats();
    expect(stats.entityCount).toBeGreaterThanOrEqual(3);
    expect(stats.linkCount).toBeGreaterThanOrEqual(2);
  });

  it('reset clears all data', () => {
    ec.linkEntities('A', 'B', 's1');
    ec.reset();
    expect(ec.getStats().entityCount).toBe(0);
  });
});

describe('DecisionLineage', () => {
  let dl: DecisionLineage;

  beforeEach(() => { dl = new DecisionLineage(); });

  it('trackDecision stores decisions', () => {
    dl.trackDecision({
      id: 'd1',
      description: 'Adopt TypeScript',
      sessionId: 's1',
      timestamp: Date.now(),
      context: '',
      entitiesInvolved: ['TypeScript', 'project'],
    }, 'Decided to migrate to TypeScript');

    const history = dl.getDecisionHistory();
    expect(history).toHaveLength(1);
    expect(history[0].description).toBe('Adopt TypeScript');
  });

  it('trackDecision builds lineage chain', () => {
    dl.trackDecision({
      id: 'root',
      description: 'Root decision',
      sessionId: 's1',
      timestamp: Date.now(),
      context: '',
      entitiesInvolved: ['A'],
    }, 'Root context');

    dl.trackDecision({
      id: 'child',
      description: 'Child decision',
      sessionId: 's1',
      timestamp: Date.now(),
      context: '',
      entitiesInvolved: ['A', 'B'],
      parentDecision: 'root',
    }, 'Child context');

    const chain = dl.getLineage('root');
    expect(chain).toBeDefined();
    expect(chain!.depth).toBe(2);
    expect(chain!.decisions).toHaveLength(2);
  });

  it('getDecisionsByEntity filters by entity', () => {
    dl.trackDecision({
      id: 'd1', description: 'D1', sessionId: 's1',
      timestamp: Date.now(), context: '', entitiesInvolved: ['TypeScript'],
    }, 'ctx1');
    dl.trackDecision({
      id: 'd2', description: 'D2', sessionId: 's1',
      timestamp: Date.now(), context: '', entitiesInvolved: ['Python'],
    }, 'ctx2');

    expect(dl.getDecisionsByEntity('TypeScript')).toHaveLength(1);
    expect(dl.getDecisionsByEntity('Python')).toHaveLength(1);
    expect(dl.getDecisionsByEntity('Rust')).toHaveLength(0);
  });

  it('reset clears decisions', () => {
    dl.trackDecision({
      id: 'd1', description: 'D1', sessionId: 's1',
      timestamp: Date.now(), context: '', entitiesInvolved: [],
    }, 'ctx');
    dl.reset();
    expect(dl.getDecisionHistory()).toHaveLength(0);
  });
});

describe('CausalGraph', () => {
  let cg: CausalGraph;

  beforeEach(() => { cg = new CausalGraph(); });

  it('addCausalLink creates causal relationship', () => {
    cg.addCausalLink(
      { id: 'e1', description: 'Bug introduced', sessionId: 's1', timestamp: 1, type: 'cause' },
      { id: 'e2', description: 'CI failed', sessionId: 's1', timestamp: 2, type: 'effect' },
      's1',
    );

    const causality = cg.queryCausality('e1');
    expect(causality).toHaveLength(1);
    expect(causality[0].effect.id).toBe('e2');
  });

  it('getCausalChain returns transitive closure', () => {
    cg.addCausalLink(
      { id: 'root', description: 'Root', sessionId: 's1', timestamp: 1, type: 'cause' },
      { id: 'mid', description: 'Middle', sessionId: 's1', timestamp: 2, type: 'both' },
      's1',
    );
    cg.addCausalLink(
      { id: 'mid', description: 'Middle', sessionId: 's1', timestamp: 2, type: 'both' },
      { id: 'leaf', description: 'Leaf', sessionId: 's1', timestamp: 3, type: 'effect' },
      's1',
    );

    const chain = cg.getCausalChain('root');
    expect(chain.length).toBeGreaterThanOrEqual(2);
  });

  it('getRootCauses finds events with no incoming links', () => {
    cg.addCausalLink(
      { id: 'root', description: 'R', sessionId: 's1', timestamp: 1, type: 'cause' },
      { id: 'child', description: 'C', sessionId: 's1', timestamp: 2, type: 'effect' },
      's1',
    );

    const roots = cg.getRootCauses();
    expect(roots).toHaveLength(1);
    expect(roots[0].id).toBe('root');
  });

  it('reset clears all', () => {
    cg.addCausalLink(
      { id: 'e1', description: 'E1', sessionId: 's1', timestamp: 1, type: 'cause' },
      { id: 'e2', description: 'E2', sessionId: 's1', timestamp: 2, type: 'effect' },
    );
    cg.reset();
    expect(cg.queryCausality('e1')).toHaveLength(0);
  });
});

describe('MemoryRelationshipEnhancer', () => {
  it('enhance links entities from memory tags', () => {
    const enhancer = new MemoryRelationshipEnhancer();
    enhancer.enhance([
      { id: '1', text: 'Working on TypeScript migration', tags: ['TypeScript', 'migration'] },
      { id: '2', text: 'Fixing CI pipeline', tags: ['CI', 'TypeScript'] },
    ]);

    const chain = enhancer.entityChaining.getEntityChain('TypeScript');
    expect(chain.length).toBeGreaterThanOrEqual(2);
  });

  it('enhance handles empty input', () => {
    const enhancer = new MemoryRelationshipEnhancer();
    expect(() => enhancer.enhance([])).not.toThrow();
  });

  it('reset clears all subsystems', () => {
    const enhancer = new MemoryRelationshipEnhancer();
    enhancer.enhance([
      { id: '1', text: 'test', tags: ['A', 'B'] },
    ]);
    enhancer.reset();
    expect(enhancer.entityChaining.getStats().entityCount).toBe(0);
  });
});
