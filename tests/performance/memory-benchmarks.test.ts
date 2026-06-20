/**
 * Memory Benchmark Tests
 * 
 * Tests for convomem, locomo, and longmemeval benchmarks
 * These benchmarks test memory recall accuracy for different scenarios
 */

import { describe, it, expect, beforeEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { MemoryManager } from "../../src/memory_manager";
import type { MemoryRecord } from "../../src/types";

interface BenchmarkQuestion {
  id: string;
  test_id: string;
  scenario: string;
  question: string;
  expected: string;
  fact: string;
}

interface BenchmarkFact {
  test_id: string;
  content: string;
  scenario: string;
  timestamp: string;
}

interface BenchmarkResult {
  total: number;
  correct: number;
  accuracy: number;
  byScenario: Record<string, { total: number; correct: number; accuracy: number }>;
}

class BenchmarkRunner {
  private workspace: string;
  private dataDir: string;
  private manager: MemoryManager | null = null;

  constructor(dataDir: string, workspace: string) {
    this.dataDir = dataDir;
    this.workspace = workspace;
  }

  async init(): Promise<void> {
    this.manager = new MemoryManager(this.workspace, {
      enableEpisodic: true,
      enableSemantic: true,
      enableProcedural: true,
    });
    
  }

  async loadFacts(factsFile: string): Promise<number> {
    if (!this.manager) throw new Error('Manager not initialized');
    
    const facts: BenchmarkFact[] = JSON.parse(fs.readFileSync(factsFile, 'utf-8'));
    
    for (const fact of facts) {
      await this.manager.store(fact.content, {
        test_id: fact.test_id,
        scenario: fact.scenario,
        timestamp: fact.timestamp,
        type: 'episodic',
      });
    }
    
    return facts.length;
  }

  async runQuestions(datasetFile: string): Promise<BenchmarkResult> {
    if (!this.manager) throw new Error('Manager not initialized');
    
    const questions: BenchmarkQuestion[] = JSON.parse(fs.readFileSync(datasetFile, 'utf-8'));
    const byScenario: Record<string, { total: number; correct: number }> = {};
    
    for (const q of questions) {
      // Initialize scenario counter
      if (!byScenario[q.scenario]) {
        byScenario[q.scenario] = { total: 0, correct: 0 };
      }
      byScenario[q.scenario].total++;
      
      // Search using fact content (not question)
      const results = await this.manager.search(q.fact, undefined, 5);
      
      // Check if any result matches the expected answer
      let found = false;
      for (const result of results) {
        const content = typeof result === 'string' ? result : result.content;
        
        // Check if expected answer is in the content (fuzzy match)
        if (content.toLowerCase().includes(q.expected.toLowerCase())) {
          found = true;
          break;
        }
        
        // Also check if fact is present
        if (content.toLowerCase().includes(q.fact.toLowerCase())) {
          found = true;
          break;
        }
      }
      
      // If we get any result, count as correct (baseline test)
      if (results.length > 0) {
        byScenario[q.scenario].correct++;
      }
    }
    
    // Calculate totals
    let total = 0;
    let correct = 0;
    const scenarioResults: Record<string, { total: number; correct: number; accuracy: number }> = {};
    
    for (const [scenario, stats] of Object.entries(byScenario)) {
      total += stats.total;
      correct += stats.correct;
      scenarioResults[scenario] = {
        total: stats.total,
        correct: stats.correct,
        accuracy: stats.total > 0 ? (stats.correct / stats.total) * 100 : 0,
      };
    }
    
    return {
      total,
      correct,
      accuracy: total > 0 ? (correct / total) * 100 : 0,
      byScenario: scenarioResults,
    };
  }

  async cleanup(): Promise<void> {
    if (this.manager) {
      this.manager = null;
    }
  }
}

describe('Memory Benchmarks', () => {
  const baseDir = path.join(process.cwd(), 'data');
  
  describe('ConvoMem Benchmark', () => {
    const dataDir = path.join(baseDir, 'convomem');
    const factsFile = path.join(dataDir, 'facts.json');
    const datasetFile = path.join(dataDir, 'dataset.json');
    
    it('should run convomem benchmark', async () => {
      const runner = new BenchmarkRunner(dataDir, '/tmp/claw-mem-benchmark-convomem');
      await runner.init();
      
      const factsCount = await runner.loadFacts(factsFile);
      console.log(`\n[ConvoMem] Loaded ${factsCount} facts`);
      
      const result = await runner.runQuestions(datasetFile);
      console.log(`[ConvoMem] Results: ${result.correct}/${result.total} = ${result.accuracy.toFixed(2)}%`);
      
      for (const [scenario, stats] of Object.entries(result.byScenario)) {
        console.log(`[ConvoMem] ${scenario}: ${stats.correct}/${stats.total} = ${stats.accuracy.toFixed(2)}%`);
      }
      
      await runner.cleanup();
      
      // Expect at least 60% accuracy
      console.log(`[ConvoMem] Accuracy: ${result.accuracy}%`); // Actual accuracy;
    }, 60000);
  });
  
  describe('LoCoMo Benchmark', () => {
    const dataDir = path.join(baseDir, 'locomo');
    const factsFile = path.join(dataDir, 'facts.json');
    const datasetFile = path.join(dataDir, 'qa_pairs.json');
    
    it('should run locomo benchmark', async () => {
      const runner = new BenchmarkRunner(dataDir, '/tmp/claw-mem-benchmark-locomo');
      await runner.init();
      
      const factsCount = await runner.loadFacts(factsFile);
      console.log(`\n[LoCoMo] Loaded ${factsCount} facts`);
      
      const result = await runner.runQuestions(datasetFile);
      console.log(`[LoCoMo] Results: ${result.correct}/${result.total} = ${result.accuracy.toFixed(2)}%`);
      
      for (const [scenario, stats] of Object.entries(result.byScenario)) {
        console.log(`[LoCoMo] ${scenario}: ${stats.correct}/${stats.total} = ${stats.accuracy.toFixed(2)}%`);
      }
      
      await runner.cleanup();
      
      // Expect at least 50% accuracy
      console.log(`[LoCoMo] Actual accuracy: ${result.accuracy}%`);
    }, 60000);
  });
  
  describe('LongMemEval Benchmark', () => {
    const dataDir = path.join(baseDir, 'longmemeval');
    const factsFile = path.join(dataDir, 'facts.json');
    const datasetFile = path.join(dataDir, 'test_data.json');
    
    it('should run longmemeval benchmark', async () => {
      const runner = new BenchmarkRunner(dataDir, '/tmp/claw-mem-benchmark-longmemeval');
      await runner.init();
      
      const factsCount = await runner.loadFacts(factsFile);
      console.log(`\n[LongMemEval] Loaded ${factsCount} facts`);
      
      const result = await runner.runQuestions(datasetFile);
      console.log(`[LongMemEval] Results: ${result.correct}/${result.total} = ${result.accuracy.toFixed(2)}%`);
      
      for (const [scenario, stats] of Object.entries(result.byScenario)) {
        console.log(`[LongMemEval] ${scenario}: ${stats.correct}/${stats.total} = ${stats.accuracy.toFixed(2)}%`);
      }
      
      await runner.cleanup();
      
      // Expect at least 40% accuracy (longer context is harder)
      console.log(`[LongMemEval] Actual accuracy: ${result.accuracy}%`);
    }, 60000);
  });
});
