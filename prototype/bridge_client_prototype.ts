/**
 * claw-mem Bridge Client Prototype - Phase 0 Verification
 * 
 * Purpose: Verify stdio JSON-RPC performance
 * - Spawn Python Bridge process
 * - Send JSON-RPC requests
 * - Measure latency
 */

import { spawn, ChildProcess } from 'child_process';

interface JSONRPCRequest {
  jsonrpc: '2.0';
  method: string;
  params?: any;
  id: number | string;
}

interface JSONRPCResponse {
  jsonrpc: '2.0';
  result?: any;
  error?: { code: number; message: string };
  id: number | string;
  latency_ms?: number;
}

interface PerformanceStats {
  requestCount: number;
  totalLatency: number;
  avgLatency: number;
  minLatency: number;
  maxLatency: number;
  latencies: number[];
}

class BridgeClientPrototype {
  private process: ChildProcess | null = null;
  private requestId = 0;
  private pendingRequests = new Map<number | string, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
    startTime: number;
  }>();
  
  private stats: PerformanceStats = {
    requestCount: 0,
    totalLatency: 0,
    avgLatency: 0,
    minLatency: Infinity,
    maxLatency: 0,
    latencies: [],
  };
  
  /**
   * Start the Python Bridge process
   */
  async start(pythonPath: string = 'python3', bridgePath: string = 'prototype/bridge_prototype.py'): Promise<void> {
    console.log('[bridge client] Starting Python Bridge...');
    
    // Spawn Python process
    this.process = spawn(pythonPath, [bridgePath], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    
    // Handle stdout (responses)
    let buffer = '';
    this.process.stdout?.on('data', (data) => {
      buffer += data.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer
      
      for (const line of lines) {
        if (line.trim()) {
          try {
            const response: JSONRPCResponse = JSON.parse(line);
            this.handleResponse(response);
          } catch (e) {
            console.error('[bridge client] Failed to parse response:', e);
          }
        }
      }
    });
    
    // Handle stderr (logs)
    this.process.stderr?.on('data', (data) => {
      console.log('[bridge stderr]', data.toString().trim());
    });
    
    // Handle process exit
    this.process.on('exit', (code) => {
      console.log(`[bridge client] Python Bridge exited with code ${code}`);
      this.process = null;
    });
    
    // Handle process error
    this.process.on('error', (err) => {
      console.error('[bridge client] Process error:', err);
    });
    
    // Wait a bit for process to start
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Initialize
    await this.call('initialize', {});
    
    console.log('[bridge client] Python Bridge started successfully');
  }
  
  /**
   * Handle JSON-RPC response
   */
  private handleResponse(response: JSONRPCResponse): void {
    const pending = this.pendingRequests.get(response.id);
    if (!pending) {
      console.warn('[bridge client] No pending request for id:', response.id);
      return;
    }
    
    this.pendingRequests.delete(response.id);
    
    // Calculate latency
    const clientLatency = Date.now() - pending.startTime;
    const serverLatency = response.latency_ms || 0;
    
    // Update stats
    this.stats.requestCount++;
    this.stats.totalLatency += clientLatency;
    this.stats.latencies.push(clientLatency);
    this.stats.minLatency = Math.min(this.stats.minLatency, clientLatency);
    this.stats.maxLatency = Math.max(this.stats.maxLatency, clientLatency);
    this.stats.avgLatency = this.stats.totalLatency / this.stats.requestCount;
    
    // Resolve or reject
    if (response.error) {
      pending.reject(new Error(response.error.message));
    } else {
      pending.resolve({
        ...response.result,
        _clientLatencyMs: clientLatency,
        _serverLatencyMs: serverLatency,
      });
    }
  }
  
  /**
   * Send JSON-RPC request
   */
  async call(method: string, params?: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.process || !this.process.stdin) {
        reject(new Error('Bridge not started'));
        return;
      }
      
      const id = ++this.requestId;
      const request: JSONRPCRequest = {
        jsonrpc: '2.0',
        method,
        params,
        id,
      };
      
      // Store pending request
      this.pendingRequests.set(id, {
        resolve,
        reject,
        startTime: Date.now(),
      });
      
      // Send request
      const requestStr = JSON.stringify(request) + '\n';
      this.process.stdin.write(requestStr);
      
      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error(`Timeout waiting for response to ${method}`));
        }
      }, 30000);
    });
  }
  
  /**
   * Stop the Python Bridge process
   */
  async stop(): Promise<void> {
    if (this.process) {
      console.log('[bridge client] Stopping Python Bridge...');
      
      // Send shutdown command
      try {
        await this.call('shutdown', {});
      } catch (e) {
        // Ignore shutdown errors
      }
      
      // Kill process if still running
      if (this.process) {
        this.process.kill();
        this.process = null;
      }
      
      console.log('[bridge client] Python Bridge stopped');
    }
  }
  
  /**
   * Get performance statistics
   */
  getStats(): PerformanceStats {
    return { ...this.stats };
  }
  
  /**
   * Print performance statistics
   */
  printStats(): void {
    console.log('\n========================================');
    console.log('Performance Statistics');
    console.log('========================================');
    console.log(`Request Count: ${this.stats.requestCount}`);
    console.log(`Total Latency: ${this.stats.totalLatency.toFixed(3)}ms`);
    console.log(`Average Latency: ${this.stats.avgLatency.toFixed(3)}ms`);
    console.log(`Min Latency: ${this.stats.minLatency.toFixed(3)}ms`);
    console.log(`Max Latency: ${this.stats.maxLatency.toFixed(3)}ms`);
    
    if (this.stats.latencies.length > 0) {
      // Calculate percentiles
      const sorted = [...this.stats.latencies].sort((a, b) => a - b);
      const p50 = sorted[Math.floor(sorted.length * 0.5)];
      const p90 = sorted[Math.floor(sorted.length * 0.9)];
      const p95 = sorted[Math.floor(sorted.length * 0.95)];
      const p99 = sorted[Math.floor(sorted.length * 0.99)];
      
      console.log('\nPercentiles:');
      console.log(`  P50: ${p50.toFixed(3)}ms`);
      console.log(`  P90: ${p90.toFixed(3)}ms`);
      console.log(`  P95: ${p95.toFixed(3)}ms`);
      console.log(`  P99: ${p99.toFixed(3)}ms`);
    }
    console.log('========================================\n');
  }
}

/**
 * Performance Test Suite
 */
async function runPerformanceTests() {
  console.log('========================================');
  console.log('Phase 0: stdio JSON-RPC Performance Test');
  console.log('========================================\n');
  
  const client = new BridgeClientPrototype();
  
  try {
    // Start bridge
    await client.start();
    
    // Test 1: Search performance
    console.log('Test 1: Search Performance (100 requests)');
    console.log('----------------------------------------');
    for (let i = 0; i < 100; i++) {
      const result = await client.call('search', {
        query: `test query ${i}`,
        limit: 10
      });
      
      if (i === 0 || i === 99) {
        console.log(`Request ${i + 1}: client=${result._clientLatencyMs.toFixed(3)}ms, server=${result._serverLatencyMs.toFixed(3)}ms`);
      }
    }
    console.log('✅ Search test completed\n');
    
    // Test 2: Store performance
    console.log('Test 2: Store Performance (100 requests)');
    console.log('----------------------------------------');
    for (let i = 0; i < 100; i++) {
      const result = await client.call('store', {
        text: `Test memory ${i}`,
        metadata: { index: i }
      });
      
      if (i === 0 || i === 99) {
        console.log(`Request ${i + 1}: client=${result._clientLatencyMs.toFixed(3)}ms, server=${result._serverLatencyMs.toFixed(3)}ms`);
      }
    }
    console.log('✅ Store test completed\n');
    
    // Test 3: Concurrent requests
    console.log('Test 3: Concurrent Requests (50 concurrent searches)');
    console.log('----------------------------------------');
    const concurrentStart = Date.now();
    const promises = [];
    for (let i = 0; i < 50; i++) {
      promises.push(client.call('search', {
        query: `concurrent test ${i}`,
        limit: 5
      }));
    }
    await Promise.all(promises);
    const concurrentTime = Date.now() - concurrentStart;
    console.log(`✅ 50 concurrent requests completed in ${concurrentTime}ms\n`);
    
    // Test 4: Mixed operations
    console.log('Test 4: Mixed Operations (search/store/get/delete)');
    console.log('----------------------------------------');
    
    // Store
    const storeResult = await client.call('store', {
      text: 'Mixed operation test',
      metadata: { test: 'mixed' }
    });
    console.log(`Store: client=${storeResult._clientLatencyMs.toFixed(3)}ms, server=${storeResult._serverLatencyMs.toFixed(3)}ms`);
    
    // Get
    const getResult = await client.call('get', { id: storeResult.id });
    console.log(`Get: client=${getResult._clientLatencyMs.toFixed(3)}ms, server=${getResult._serverLatencyMs.toFixed(3)}ms`);
    
    // Search
    const searchResult = await client.call('search', {
      query: 'Mixed operation',
      limit: 5
    });
    console.log(`Search: client=${searchResult._clientLatencyMs.toFixed(3)}ms, server=${searchResult._serverLatencyMs.toFixed(3)}ms`);
    
    // Delete
    const deleteResult = await client.call('delete', { id: storeResult.id });
    console.log(`Delete: client=${deleteResult._clientLatencyMs.toFixed(3)}ms, server=${deleteResult._serverLatencyMs.toFixed(3)}ms`);
    
    console.log('✅ Mixed operations test completed\n');
    
    // Print final statistics
    client.printStats();
    
    // Performance evaluation
    const stats = client.getStats();
    console.log('Performance Evaluation:');
    console.log('----------------------');
    
    if (stats.avgLatency < 5) {
      console.log('✅ EXCELLENT: Average latency < 5ms');
      console.log('   → stdio JSON-RPC is a viable approach');
    } else if (stats.avgLatency < 10) {
      console.log('✅ GOOD: Average latency < 10ms');
      console.log('   → stdio JSON-RPC is acceptable');
    } else if (stats.avgLatency < 20) {
      console.log('⚠️  ACCEPTABLE: Average latency < 20ms');
      console.log('   → Consider optimizations');
    } else {
      console.log('❌ SLOW: Average latency > 20ms');
      console.log('   → Consider alternative approaches (HTTP, etc.)');
    }
    
  } catch (error) {
    console.error('[test] Error:', error);
    throw error;
  } finally {
    // Stop bridge
    await client.stop();
  }
}

// Run tests
runPerformanceTests()
  .then(() => {
    console.log('\n✅ All tests completed successfully!');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\n❌ Tests failed:', error);
    process.exit(1);
  });
