#!/usr/bin/env node
/**
 * Simple Node.js Test for Bridge Prototype
 * 
 * Tests basic stdio JSON-RPC communication
 */

const { spawn } = require('child_process');

class SimpleBridgeClient {
  constructor() {
    this.process = null;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.buffer = '';
  }
  
  async start() {
    return new Promise((resolve, reject) => {
      console.log('[test] Starting Python Bridge...');
      
      this.process = spawn('python3', ['prototype/bridge_prototype.py'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      this.process.stdout.on('data', (data) => {
        this.buffer += data.toString();
        const lines = this.buffer.split('\n');
        this.buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.trim()) {
            try {
              const response = JSON.parse(line);
              this.handleResponse(response);
            } catch (e) {
              console.error('[test] Parse error:', e.message);
            }
          }
        }
      });
      
      this.process.stderr.on('data', (data) => {
        console.log('[python]', data.toString().trim());
      });
      
      this.process.on('error', reject);
      
      // Wait for process to start
      setTimeout(resolve, 100);
    });
  }
  
  handleResponse(response) {
    const pending = this.pendingRequests.get(response.id);
    if (pending) {
      this.pendingRequests.delete(response.id);
      if (response.error) {
        pending.reject(new Error(response.error.message));
      } else {
        pending.resolve(response);
      }
    }
  }
  
  async call(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.requestId;
      const request = {
        jsonrpc: '2.0',
        method,
        params,
        id
      };
      
      this.pendingRequests.set(id, { resolve, reject });
      this.process.stdin.write(JSON.stringify(request) + '\n');
      
      // Timeout
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('Timeout'));
        }
      }, 30000);
    });
  }
  
  async stop() {
    if (this.process) {
      await this.call('shutdown');
      this.process.kill();
      this.process = null;
    }
  }
}

async function test() {
  console.log('========================================');
  console.log('Phase 0: Basic stdio JSON-RPC Test');
  console.log('========================================\n');
  
  const client = new SimpleBridgeClient();
  const latencies = [];
  
  try {
    await client.start();
    
    // Test initialize
    console.log('[test] Testing initialize...');
    const initResult = await client.call('initialize');
    console.log(`  ✅ Initialized: ${initResult.result.status}`);
    console.log(`  Latency: ${initResult.latency_ms.toFixed(3)}ms\n`);
    latencies.push(initResult.latency_ms);
    
    // Test search (100 times)
    console.log('[test] Testing search (100 requests)...');
    for (let i = 0; i < 100; i++) {
      const start = Date.now();
      const result = await client.call('search', { query: `test ${i}`, limit: 5 });
      const latency = Date.now() - start;
      latencies.push(latency);
      
      if (i === 0 || i === 99) {
        console.log(`  Request ${i + 1}: client=${latency.toFixed(3)}ms, server=${result.latency_ms.toFixed(3)}ms`);
      }
    }
    console.log('  ✅ Search test completed\n');
    
    // Test store (50 times)
    console.log('[test] Testing store (50 requests)...');
    for (let i = 0; i < 50; i++) {
      const start = Date.now();
      const result = await client.call('store', { text: `Memory ${i}` });
      const latency = Date.now() - start;
      latencies.push(latency);
      
      if (i === 0 || i === 49) {
        console.log(`  Request ${i + 1}: client=${latency.toFixed(3)}ms, server=${result.latency_ms.toFixed(3)}ms`);
      }
    }
    console.log('  ✅ Store test completed\n');
    
    // Calculate statistics
    const stats = client => {
      const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      const min = Math.min(...latencies);
      const max = Math.max(...latencies);
      const sorted = [...latencies].sort((a, b) => a - b);
      const p50 = sorted[Math.floor(sorted.length * 0.5)];
      const p90 = sorted[Math.floor(sorted.length * 0.9)];
      const p95 = sorted[Math.floor(sorted.length * 0.95)];
      const p99 = sorted[Math.floor(sorted.length * 0.99)];
      
      return { avg, min, max, p50, p90, p95, p99 };
    };
    
    const s = stats();
    
    console.log('========================================');
    console.log('Performance Statistics');
    console.log('========================================');
    console.log(`Request Count: ${latencies.length}`);
    console.log(`Average Latency: ${s.avg.toFixed(3)}ms`);
    console.log(`Min Latency: ${s.min.toFixed(3)}ms`);
    console.log(`Max Latency: ${s.max.toFixed(3)}ms`);
    console.log('\nPercentiles:');
    console.log(`  P50: ${s.p50.toFixed(3)}ms`);
    console.log(`  P90: ${s.p90.toFixed(3)}ms`);
    console.log(`  P95: ${s.p95.toFixed(3)}ms`);
    console.log(`  P99: ${s.p99.toFixed(3)}ms`);
    console.log('========================================\n');
    
    // Performance evaluation
    console.log('Performance Evaluation:');
    console.log('----------------------');
    
    if (s.avg < 5) {
      console.log('✅ EXCELLENT: Average latency < 5ms');
      console.log('   → stdio JSON-RPC is a viable approach');
    } else if (s.avg < 10) {
      console.log('✅ GOOD: Average latency < 10ms');
      console.log('   → stdio JSON-RPC is acceptable');
    } else if (s.avg < 20) {
      console.log('⚠️  ACCEPTABLE: Average latency < 20ms');
      console.log('   → Consider optimizations');
    } else {
      console.log('❌ SLOW: Average latency > 20ms');
      console.log('   → Consider alternative approaches');
    }
    
    console.log('\n✅ All tests passed!');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    throw error;
  } finally {
    await client.stop();
  }
}

test()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
