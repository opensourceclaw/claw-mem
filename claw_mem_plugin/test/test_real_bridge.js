#!/usr/bin/env node
/**
 * Test claw-mem Bridge with real MemoryManager
 * 
 * Prerequisites:
 * - Python 3.9+
 * - claw-mem package installed
 * - claw_mem.bridge module available
 */

import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class BridgeClient {
  constructor() {
    this.process = null;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.buffer = '';
  }
  
  async start(pythonPath = 'python3', bridgeModule = 'claw_mem.bridge') {
    return new Promise((resolve, reject) => {
      console.log('[test] Starting Python Bridge with real MemoryManager...');
      
      // Use venv Python if available
      const venvPython = path.resolve(__dirname, '..', '..', 'venv', 'bin', 'python3');
      const actualPython = existsSync(venvPython) ? venvPython : pythonPath;
      
      // Set PYTHONPATH to include src directory
      const env = {
        ...process.env,
        PYTHONPATH: path.resolve(__dirname, '..', '..', 'src')
      };
      
      console.log(`[test] Using Python: ${actualPython}`);
      console.log(`[test] PYTHONPATH: ${env.PYTHONPATH}`);
      console.log(`[test] Bridge module: ${bridgeModule}`);
      console.log(`[test] CWD: ${path.resolve(__dirname, '..', '..')}`);
      
      // Spawn with separate arguments: python -m claw_mem.bridge
      this.process = spawn(actualPython, ['-m', bridgeModule], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.resolve(__dirname, '..', '..'),
        env: env,
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

async function testRealBridge() {
  console.log('========================================');
  console.log('Phase 1: Real claw-mem Integration Test');
  console.log('========================================\n');
  
  const client = new BridgeClient();
  const latencies = [];
  
  try {
    // Start bridge
    await client.start();
    
    // Initialize with real MemoryManager
    console.log('[test] Initializing with real MemoryManager...');
    const initResult = await client.call('initialize', {
      workspace_dir: path.resolve(__dirname, '..', '..'),
      config: {}
    });
    
    if (initResult.result && initResult.result.status === 'initialized') {
      console.log('  ✅ MemoryManager initialized');
      console.log(`  Workspace: ${initResult.result.workspace}`);
      console.log(`  Latency: ${initResult.result.latency_ms.toFixed(3)}ms\n`);
      latencies.push(initResult.result.latency_ms);
    } else {
      console.log('  ❌ Initialization failed:', initResult);
      return;
    }
    
    // Test 1: Store memories
    console.log('[test] Storing 10 memories...');
    const storeLatencies = [];
    for (let i = 0; i < 10; i++) {
      const start = Date.now();
      const result = await client.call('store', {
        text: `Test memory ${i}: This is important fact ${i}`,
        metadata: { test: true, index: i },
        user_id: 'test_user',
        layer: 'episodic'
      });
      const latency = Date.now() - start;
      storeLatencies.push(latency);
      
      if (i === 0 || i === 9) {
        console.log(`  Memory ${i + 1}: ${result.result.id}, latency=${latency}ms`);
      }
    }
    const avgStoreLatency = storeLatencies.reduce((a, b) => a + b, 0) / storeLatencies.length;
    console.log(`  ✅ Store test completed, avg latency: ${avgStoreLatency.toFixed(3)}ms\n`);
    
    // Test 2: Search memories
    console.log('[test] Searching memories (10 queries)...');
    const searchLatencies = [];
    for (let i = 0; i < 10; i++) {
      const start = Date.now();
      const result = await client.call('search', {
        query: `important fact ${i}`,
        limit: 5,
        user_id: 'test_user'
      });
      const latency = Date.now() - start;
      searchLatencies.push(latency);
      
      if (i === 0 || i === 9) {
        console.log(`  Query ${i + 1}: ${result.result.count} results, latency=${latency}ms`);
      }
    }
    const avgSearchLatency = searchLatencies.reduce((a, b) => a + b, 0) / searchLatencies.length;
    console.log(`  ✅ Search test completed, avg latency: ${avgSearchLatency.toFixed(3)}ms\n`);
    
    // Test 3: Get memory
    console.log('[test] Getting a specific memory...');
    const start = Date.now();
    const getResult = await client.call('get', {
      id: 'test-memory-id' // This will fail but we test the path
    });
    const getLatency = Date.now() - start;
    console.log(`  Latency: ${getLatency}ms`);
    console.log(`  Result: ${getResult.result.error || 'success'}\n`);
    
    // Test 4: Delete memory
    console.log('[test] Deleting a memory...');
    const start2 = Date.now();
    const deleteResult = await client.call('delete', {
      id: 'test-memory-id'
    });
    const deleteLatency = Date.now() - start2;
    console.log(`  Latency: ${deleteLatency}ms`);
    console.log(`  Success: ${deleteResult.result.success}\n`);
    
    // Test 5: Get stats
    console.log('[test] Getting bridge statistics...');
    const statsResult = await client.call('stats', {});
    console.log(`  Request count: ${statsResult.result.request_count}`);
    console.log(`  Total latency: ${statsResult.result.total_latency_ms.toFixed(3)}ms`);
    console.log(`  Average latency: ${statsResult.result.avg_latency_ms.toFixed(3)}ms\n`);
    
    // Calculate overall statistics
    const allLatencies = [...storeLatencies, ...searchLatencies];
    const avg = allLatencies.reduce((a, b) => a + b, 0) / allLatencies.length;
    const min = Math.min(...allLatencies);
    const max = Math.max(...allLatencies);
    const sorted = [...allLatencies].sort((a, b) => a - b);
    const p50 = sorted[Math.floor(sorted.length * 0.5)];
    const p90 = sorted[Math.floor(sorted.length * 0.9)];
    const p95 = sorted[Math.floor(sorted.length * 0.95)];
    
    console.log('========================================');
    console.log('Performance Statistics');
    console.log('========================================');
    console.log(`Request Count: ${allLatencies.length}`);
    console.log(`Average Latency: ${avg.toFixed(3)}ms`);
    console.log(`Min Latency: ${min}ms`);
    console.log(`Max Latency: ${max}ms`);
    console.log('\nPercentiles:');
    console.log(`  P50: ${p50}ms`);
    console.log(`  P90: ${p90}ms`);
    console.log(`  P95: ${p95}ms`);
    console.log('========================================\n');
    
    // Performance evaluation
    console.log('Performance Evaluation:');
    console.log('----------------------');
    
    if (avg < 5) {
      console.log('✅ EXCELLENT: Average latency < 5ms');
      console.log('   → Ready for production use!');
    } else if (avg < 10) {
      console.log('✅ GOOD: Average latency < 10ms');
      console.log('   → Acceptable for production use');
    } else if (avg < 20) {
      console.log('⚠️  ACCEPTABLE: Average latency < 20ms');
      console.log('   → Consider optimizations');
    } else {
      console.log('❌ SLOW: Average latency > 20ms');
      console.log('   → Needs optimization');
    }
    
    console.log('\n✅ Phase 1 integration test completed successfully!');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    throw error;
  } finally {
    await client.stop();
  }
}

testRealBridge()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
