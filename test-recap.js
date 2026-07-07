#!/usr/bin/env node
// Manual recap test script
// Run: node test-recap.js

import { TranscriptStorage } from './dist/transcript/storage.js';
import { RecapGenerator } from './dist/transcript/recap-generator.js';
import { MemoryManager } from './dist/memory_manager.js';
import * as fs from 'fs';
import * as path from 'path';

const workspace = process.env.HOME + '/.openclaw';
const transcriptDir = path.join(workspace, 'transcripts', '2026-07-05');

// Find the latest transcript file
const files = fs.readdirSync(transcriptDir)
  .filter(f => f.startsWith('session-') && f.endsWith('.md'))
  .sort()
  .reverse();

if (files.length === 0) {
  console.log('No transcript files found');
  process.exit(1);
}

const transcriptFile = path.join(transcriptDir, files[0]);
console.log('Testing with transcript:', transcriptFile);

// Parse transcript
const content = fs.readFileSync(transcriptFile, 'utf-8');

// Extract session ID from header
const sessionMatch = content.match(/session:\s*(\S+)/);
const sessionId = sessionMatch ? sessionMatch[1] : 'unknown';

console.log('Session ID:', sessionId);

// Create storage and generator
const storage = new TranscriptStorage(workspace);
const generator = new RecapGenerator();

// Load transcript entries (simulate from file)
const entries = [];
const lines = content.split('\n');
let currentRole = 'assistant';
for (const line of lines) {
  if (line.includes('[User]')) currentRole = 'user';
  else if (line.includes('[Assistant]')) currentRole = 'assistant';
  else if (line.trim() && !line.startsWith('##') && !line.startsWith('<!--')) {
    entries.push({
      role: currentRole,
      content: line.trim(),
      timestamp: Date.now()
    });
  }
}

console.log('Parsed entries:', entries.length);

// Generate recap
const recap = generator.generateSync(sessionId, entries);
console.log('\n=== Generated Recap ===');
console.log('What were we doing:', recap.whatWereWeDoing);
console.log('What is next:', recap.whatIsNext);

// Store recap using MemoryManager
const manager = new MemoryManager({ workspace, logger: console });

const storeResult = manager.store(
  `Session Recap: ${recap.whatWereWeDoing}\n\nNext: ${recap.whatIsNext}`,
  'session_recap',
  ['session_recap', 'test'],
  { session_id: sessionId }
);

console.log('\n=== Storage Result ===');
console.log('Stored:', storeResult);

// Verify storage
const recaps = manager.retrieve('session_recap', { limit: 5 });
console.log('\n=== Retrieved Recaps ===');
console.log('Found:', recaps.length, 'recaps');
recaps.forEach((r, i) => {
  console.log(`\n--- Recap ${i + 1} ---`);
  console.log('ID:', r.id);
  console.log('Text:', r.text.substring(0, 100) + '...');
  console.log('Tags:', r.tags);
});
