#!/usr/bin/env node

import { ClawMemBridge } from '../bridge.js';

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.error('Usage: claw-mem-store <content> [--layer semantic|episodic|procedural]');
    process.exit(1);
  }
  
  // Parse arguments
  let content = '';
  let layer: 'episodic' | 'semantic' | 'procedural' = 'semantic';
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--layer' && args[i + 1]) {
      layer = args[i + 1] as any;
      i++;
    } else if (!args[i].startsWith('--')) {
      content = content ? `${content} ${args[i]}` : args[i];
    }
  }
  
  if (!content) {
    console.error('Error: No content provided');
    process.exit(1);
  }
  
  const bridge = new ClawMemBridge();
  
  // Check installation
  const check = await bridge.checkInstallation();
  if (!check.installed) {
    console.error(`Error: ${check.error}`);
    process.exit(1);
  }
  
  // Store memory
  const result = await bridge.store({ content, layer });
  
  if (result.success) {
    console.log(`✅ Memory stored successfully`);
    console.log(`   ID: ${result.id}`);
    console.log(`   Layer: ${layer}`);
    console.log(`   Content: ${content}`);
  } else {
    console.error('❌ Failed to store memory');
    process.exit(1);
  }
}

main().catch(console.error);
