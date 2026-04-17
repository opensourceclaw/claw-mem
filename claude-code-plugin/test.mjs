#!/usr/bin/env node

import { ClawMemBridge } from './dist/bridge.js';

async function main() {
  console.log('🧪 Testing claw-mem Claude Code Plugin\n');
  
  const bridge = new ClawMemBridge();
  
  // Test 1: Check installation
  console.log('Test 1: Check installation');
  const check = await bridge.checkInstallation();
  console.log(`  Installed: ${check.installed}`);
  if (check.version) console.log(`  Version: ${check.version}`);
  console.log();
  
  // Test 2: Store memory
  console.log('Test 2: Store memory');
  const storeResult = await bridge.store({
    content: 'Test from Claude Code plugin',
    layer: 'semantic'
  });
  console.log(`  Success: ${storeResult.success}`);
  console.log();
  
  // Test 3: Get stats
  console.log('Test 3: Get stats');
  const stats = await bridge.getStats();
  console.log(`  Episodic: ${stats.episodic}`);
  console.log(`  Semantic: ${stats.semantic}`);
  console.log(`  Procedural: ${stats.procedural}`);
  console.log(`  Total: ${stats.total}`);
  console.log();
  
  console.log('✅ Tests completed');
}

main().catch(console.error);
