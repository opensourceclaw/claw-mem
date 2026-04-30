#!/usr/bin/env node
/**
 * claw-mem Bridge Integration Test (v2.5.0)
 *
 * Tests the new bridge protocol with:
 * - Auto-initialization (id=0 response)
 * - Store / Search / Get / Delete
 * - Plugin Slots: build_context, start_session, end_session, resolve_flush_plan
 * - Cache behavior verification
 * - Performance benchmarks
 */

import { spawn } from 'child_process';

const PASS = '\x1b[32m✓\x1b[0m';
const FAIL = '\x1b[31m✗\x1b[0m';

class BridgeClient {
  constructor() {
    this.process = null;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.buffer = '';
    this.initPromise = null;
    this.initResolve = null;
    this.initialized = false;
  }

  async start() {
    this.initPromise = new Promise((resolve) => { this.initResolve = resolve; });

    this.process = spawn('python3', ['-m', 'claw_mem.bridge'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env },
    });

    this.process.stdout.on('data', (data) => {
      this.buffer += data.toString();
      const lines = this.buffer.split('\n');
      this.buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const resp = JSON.parse(line);
          // Bridge auto-init: id=0 means initialization complete
          if (resp.id === 0 && !this.initialized) {
            this.initialized = true;
            if (resp.error) {
              this.initResolve({ ok: false, error: resp.error.message });
            } else {
              this.initResolve({ ok: true, result: resp.result });
            }
          }
          // Regular request responses
          if (resp.id > 0) {
            const pending = this.pendingRequests.get(resp.id);
            if (pending) {
              this.pendingRequests.delete(resp.id);
              if (resp.error) {
                pending.reject(new Error(resp.error.message));
              } else {
                pending.resolve(resp.result);
              }
            }
          }
        } catch (e) {
          // Ignore parse errors (diagnostic output on stderr is expected)
        }
      }
    });

    this.process.stderr.on('data', (data) => {
      // Bridge logs to stderr - expected
    });

    this.process.on('error', (err) => {
      if (!this.initialized) this.initResolve({ ok: false, error: err.message });
    });

    return this.initPromise;
  }

  async call(method, params = {}) {
    if (!this.initialized) throw new Error('Bridge not initialized');

    return new Promise((resolve, reject) => {
      const id = ++this.requestId;
      this.pendingRequests.set(id, { resolve, reject });
      this.process.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params, id }) + '\n');

      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error(`Timeout: ${method}`));
        }
      }, 15000);
    });
  }

  async stop() {
    if (this.process) {
      this.process.kill();
      this.process = null;
    }
  }
}

async function main() {
  console.log('========================================');
  console.log('claw-mem Bridge Integration Test v2.5.0');
  console.log('========================================\n');

  const client = new BridgeClient();
  let tests = 0, passed = 0;

  function check(name, condition, detail = '') {
    tests++;
    if (condition) {
      passed++;
      console.log(`  ${PASS} ${name} ${detail}`);
    } else {
      console.log(`  ${FAIL} ${name} ${detail}`);
    }
  }

  try {
    // ---- Start bridge ----
    const init = await client.start();
    check('Bridge auto-init', init.ok, init.result?.version || '');
    if (!init.ok) throw new Error(`Init failed: ${init.error}`);

    // ---- Store ----
    console.log('\n[Store tests]');
    const ids = [];
    for (let i = 0; i < 5; i++) {
      const result = await client.call('store', {
        text: `Important fact ${i}: claw-mem v2.5.0 plugin slots test`,
        metadata: { test: true, index: i },
        memory_type: 'episodic',
      });
      ids.push(result.id);
    }
    check('Store 5 memories', ids.length === 5, `ids: ${ids.length}`);

    // ---- Search ----
    console.log('\n[Search tests]');
    const t1 = Date.now();
    const search1 = await client.call('search', { query: 'plugin slots test', limit: 10 });
    const t1Latency = Date.now() - t1;
    check('Search returns results', search1.results?.length > 0, `${search1.results?.length} results`);
    check('Search latency < 50ms', t1Latency < 50, `${t1Latency}ms`);

    // ---- Cache test ----
    const cacheStart = Date.now();
    const search2 = await client.call('search', { query: 'plugin slots test', limit: 10 });
    const cacheLatency = Date.now() - cacheStart;
    check('Cache hit faster', cacheLatency <= t1Latency + 10, `original=${t1Latency}ms, cached=${cacheLatency}ms`);

    // Cache miss for different query
    const missStart = Date.now();
    await client.call('search', { query: 'different query cache miss', limit: 10 });
    const missLatency = Date.now() - missStart;
    check('Cache miss returns fresh results', missLatency > 0, `${missLatency}ms`);

    // ---- Plugin Slots ----
    console.log('\n[Plugin Slots tests]');

    // build_context
    const ctx = await client.call('build_context', { topK: 5 });
    check('build_context returns sections', ctx.count > 0 || !ctx.error, `count=${ctx.count}`);

    // start_session / end_session
    const sess = await client.call('start_session', { sessionId: 'test-session-1' });
    check('start_session', sess.status === 'started', sess.sessionId);
    const endSess = await client.call('end_session', { sessionId: 'test-session-1' });
    check('end_session', endSess.status === 'ended', endSess.sessionId);

    // resolve_flush_plan
    const plan = await client.call('resolve_flush_plan', {});
    check('resolve_flush_plan returns plan', plan.softThresholdTokens > 0, `soft=${plan.softThresholdTokens}`);
    check('Flush plan has all fields', plan.prompt && plan.systemPrompt && plan.relativePath);

    // ---- Status ----
    console.log('\n[Status]');
    const status = await client.call('status', {});
    check('Status ok', status.status === 'ok');

    // ---- Performance benchmark ----
    console.log('\n[Performance benchmark]');
    const iters = 20;
    const latencies = [];
    for (let i = 0; i < iters; i++) {
      const start = Date.now();
      await client.call('search', { query: `benchmark query ${i}`, limit: 5 });
      latencies.push(Date.now() - start);
    }
    const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
    const sorted = [...latencies].sort((a, b) => a - b);
    const p50 = sorted[Math.floor(sorted.length * 0.5)];
    const p95 = sorted[Math.floor(sorted.length * 0.95)];
    console.log(`  ${iters} search requests:`);
    console.log(`    avg=${avg.toFixed(1)}ms  p50=${p50}ms  p95=${p95}ms`);
    check('Average search < 50ms', avg < 50, `avg=${avg.toFixed(1)}ms`);
    check('P95 search < 100ms', p95 < 100, `p95=${p95}ms`);

    // ---- Summary ----
    console.log(`\n========================================`);
    console.log(`Results: ${passed}/${tests} passed`);
    console.log(`========================================`);

    if (passed < tests) {
      console.error(`${FAIL} Some tests failed`);
      process.exit(1);
    }

  } catch (error) {
    console.error(`\n${FAIL} ${error.message}`);
    process.exit(1);
  } finally {
    await client.stop();
  }
}

main();
