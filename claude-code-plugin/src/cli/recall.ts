#!/usr/bin/env node

import { ClawMemBridge } from '../bridge.js';

async function main() {
  const args = process.argv.slice(2);
  const query = args[0] || '';
  
  const bridge = new ClawMemBridge();
  
  // Check installation
  const check = await bridge.checkInstallation();
  if (!check.installed) {
    console.error(`Error: ${check.error}`);
    process.exit(1);
  }
  
  // Recall memories
  const memories = await bridge.recall({ query, topK: 10 });
  
  if (memories.length === 0) {
    console.log('No memories found.');
    return;
  }
  
  console.log(`Found ${memories.length} memories:\n`);
  
  memories.forEach((m, i) => {
    console.log(`${i + 1}. [${m.layer}] ${m.content}`);
    if (m.relevance) {
      console.log(`   Relevance: ${(m.relevance * 100).toFixed(1)}%`);
    }
  });
}

main().catch(console.error);
