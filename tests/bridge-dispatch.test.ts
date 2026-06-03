import { describe, it, expect } from 'vitest';
import { handleRequest } from '../src/bridge';

function mockManager() {
  const store: any[] = [];
  let idCounter = 0;
  return {
    store: (content: string, _type?: string, tags?: string[], meta?: Record<string, unknown>) => {
      const id = `m_${++idCounter}`;
      const record: any = { id, content, tags: tags || [], metadata: meta || {}, timestamp: Date.now().toString() };
      if (typeof content === 'string') {
        try { Object.assign(record, JSON.parse(content)); } catch {}
      }
      store.push(record);
      return true;
    },
    search: () => [...store],
    getStats: () => ({ memories: store.length }),
    health: () => ({ status: 'ok' }),
    workspace: '/tmp',
    index: null,
    constitutionStore: { getAll: () => [], getStats: () => ({}), scanAndSuggest: () => [], promoteToL2: () => 'id', delete: () => true },
    sessionId: 'test',
    injectConstitution: () => {},
  };
}

describe('Dispatch History (v5.3.0)', () => {
  it('store_dispatch_history creates a record', () => {
    const r = handleRequest({ jsonrpc: '2.0', method: 'store_dispatch_history', params: { agent: 'stark', intent_type: 'tech', task: 'fix', result: 'success', latency_ms: 100, confidence: 0.9 }, id: 1 }, mockManager() as any);
    expect((r.result as any).success).toBe(true);
  });
  it('filters by agent', () => {
    const mm = mockManager();
    handleRequest({ jsonrpc: '2.0', method: 'store_dispatch_history', params: { agent: 'stark', intent_type: 'tech', task: 't', result: 'success', latency_ms: 100, confidence: 0.9 }, id: 1 }, mm as any);
    handleRequest({ jsonrpc: '2.0', method: 'store_dispatch_history', params: { agent: 'pepper', intent_type: 'health', task: 't', result: 'failure', latency_ms: 200, confidence: 0.8 }, id: 2 }, mm as any);
    const r = handleRequest({ jsonrpc: '2.0', method: 'get_dispatch_history', params: { agent: 'stark' }, id: 3 }, mm as any);
    expect((r.result as any).records.length).toBe(1);
  });
  it('classifies timeout as execution_error', () => {
    const r = handleRequest({ jsonrpc: '2.0', method: 'classify_failure_signal', params: { error_message: 'Agent timeout after 30s', context: {} }, id: 1 }, mockManager() as any);
    expect((r.result as any).type).toBe('execution_error');
  });
  it('classifies network error as external_error', () => {
    const r = handleRequest({ jsonrpc: '2.0', method: 'classify_failure_signal', params: { error_message: 'Network error: connection refused', context: {} }, id: 1 }, mockManager() as any);
    expect((r.result as any).type).toBe('external_error');
  });
  it('get_dispatch_stats returns aggregated data', () => {
    const mm = mockManager();
    handleRequest({ jsonrpc: '2.0', method: 'store_dispatch_history', params: { agent: 'stark', intent_type: 'tech', task: 't', result: 'success', latency_ms: 100, confidence: 0.9 }, id: 1 }, mm as any);
    const r = handleRequest({ jsonrpc: '2.0', method: 'get_dispatch_stats', params: {}, id: 2 }, mm as any);
    expect((r.result as any).stats).toBeDefined();
  });
});

describe('Cross Domain Signals (v5.4.0)', () => {
  it('stores a signal', () => {
    const r = handleRequest({ jsonrpc: '2.0', method: 'store_cross_domain_signal', params: { pillar: 'stark', agent: 'tech', signal_type: 'task_complete', summary: 'Fixed bug', impact_score: 0.7 }, id: 1 }, mockManager() as any);
    expect((r.result as any).success).toBe(true);
  });
  it('filters by pillar', () => {
    const mm = mockManager();
    handleRequest({ jsonrpc: '2.0', method: 'store_cross_domain_signal', params: { pillar: 'stark', agent: 'tech', signal_type: 'task', summary: 'Fixed', impact_score: 0.8 }, id: 1 }, mm as any);
    handleRequest({ jsonrpc: '2.0', method: 'store_cross_domain_signal', params: { pillar: 'pepper', agent: 'body', signal_type: 'alert', summary: 'Stress', impact_score: 0.6 }, id: 2 }, mm as any);
    const r = handleRequest({ jsonrpc: '2.0', method: 'get_cross_domain_signals', params: { pillars: ['stark'] }, id: 3 }, mm as any);
    expect((r.result as any).signals.length).toBe(1);
  });
  it('detects stark→pepper correlation', () => {
    const mm = mockManager();
    handleRequest({ jsonrpc: '2.0', method: 'store_cross_domain_signal', params: { pillar: 'stark', agent: 'tech', signal_type: 'task', summary: '紧急修复Django性能问题', impact_score: 0.8 }, id: 1 }, mm as any);
    const r = handleRequest({ jsonrpc: '2.0', method: 'detect_cross_domain_correlation', params: { current_pillar: 'pepper', current_intent: 'health' }, id: 2 }, mm as any);
    expect((r.result as any).correlations.length).toBeGreaterThanOrEqual(1);
  });
  it('generates human-readable summary', () => {
    const r = handleRequest({ jsonrpc: '2.0', method: 'generate_signal_summary', params: { agent: 'tech', task: 'Fix Django N+1', result: 'success' }, id: 1 }, mockManager() as any);
    expect((r.result as any).summary).toContain('Fix Django N+1');
  });
});

describe('Tech Debt (v5.5.0)', () => {
  it('stores with auto-priority', () => {
    const r = handleRequest({ jsonrpc: '2.0', method: 'store_tech_debt', params: { project: 'claw-mem', debt_type: 'code_smell', location: 'x.ts:1', description: 'x', severity: 'medium', impact_score: 0.6 }, id: 1 }, mockManager() as any);
    expect((r.result as any).success).toBe(true);
  });
  it('filters by project', () => {
    const mm = mockManager();
    handleRequest({ jsonrpc: '2.0', method: 'store_tech_debt', params: { project: 'claw-mem', debt_type: 'code_smell', location: 'a', description: 'x', severity: 'low' }, id: 1 }, mm as any);
    handleRequest({ jsonrpc: '2.0', method: 'store_tech_debt', params: { project: 'claw-ctx', debt_type: 'arch', location: 'b', description: 'y', severity: 'high' }, id: 2 }, mm as any);
    const r = handleRequest({ jsonrpc: '2.0', method: 'get_tech_debts', params: { project: 'claw-mem' }, id: 3 }, mm as any);
    expect((r.result as any).debts.length).toBe(1);
  });
  it('updates status to resolved', () => {
    const mm = mockManager();
    const r1 = handleRequest({ jsonrpc: '2.0', method: 'store_tech_debt', params: { project: 'test', debt_type: 'test', location: 'x', description: 'x', severity: 'low' }, id: 1 }, mm as any);
    const id = (r1.result as any).id;
    const r2 = handleRequest({ jsonrpc: '2.0', method: 'update_debt_status', params: { debt_id: id, status: 'resolved', resolution: 'Fixed' }, id: 2 }, mm as any);
    expect((r2.result as any).updated).toBe(true);
    expect((r2.result as any).status).toBe('resolved');
  });
  it('updates priority', () => {
    const mm = mockManager();
    const r1 = handleRequest({ jsonrpc: '2.0', method: 'store_tech_debt', params: { project: 'test', debt_type: 'test', location: 'x', description: 'x', severity: 'low' }, id: 1 }, mm as any);
    const id = (r1.result as any).id;
    const r2 = handleRequest({ jsonrpc: '2.0', method: 'update_debt_priority', params: { debt_id: id, priority: 'urgent', reason: 'Blocking' }, id: 2 }, mm as any);
    expect((r2.result as any).updated).toBe(true);
    expect((r2.result as any).priority).toBe('urgent');
  });
  it('aggregates stats by severity and type', () => {
    const mm = mockManager();
    handleRequest({ jsonrpc: '2.0', method: 'store_tech_debt', params: { project: 'claw-mem', debt_type: 'code_smell', location: 'a', description: 'x', severity: 'high', impact_score: 0.7 }, id: 1 }, mm as any);
    handleRequest({ jsonrpc: '2.0', method: 'store_tech_debt', params: { project: 'claw-mem', debt_type: 'architecture', location: 'b', description: 'y', severity: 'medium', impact_score: 0.5 }, id: 2 }, mm as any);
    const r = handleRequest({ jsonrpc: '2.0', method: 'get_debt_stats', params: { project: 'claw-mem' }, id: 3 }, mm as any);
    const s = r.result as any;
    expect(s.total).toBe(2);
    expect(s.by_severity.high).toBe(1);
    expect(s.by_severity.medium).toBe(1);
  });
});
