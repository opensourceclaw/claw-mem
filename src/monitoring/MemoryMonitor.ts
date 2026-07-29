/**
 * claw-mem v6.44.0 — Memory Monitor
 * Unified monitoring for memory context overflow prevention.
 */

import * as fs from "fs";

export interface MemoryMetrics {
  // File size
  memory_file_size_bytes: number;
  memory_file_token_estimate: number;
  memory_entry_count: number;
  
  // Compression
  memory_compression_events: number;
  memory_compression_saved_tokens: number;
  
  // Risk
  context_overflow_risk: number;  // 0-1
  mecw_utilization_ratio: number;  // 0-1
  
  // Task
  task_type_distribution: Record<string, number>;
}

export interface MemoryMonitorConfig {
  mecwLimits: Record<string, number>;  // Task type -> token limit
  warningThreshold: number;  // 0.8 = 80%
  criticalThreshold: number;  // 0.95 = 95%
}

const DEFAULT_CONFIG: MemoryMonitorConfig = {
  mecwLimits: {
    'simple-lookup': 10000,
    'multi-lookup': 5000,
    'summarization': 3000,
    'complex-reasoning': 2000,
  },
  warningThreshold: 0.8,
  criticalThreshold: 0.95,
};

export class MemoryMonitor {
  private config: MemoryMonitorConfig;
  private metrics: MemoryMetrics;
  private compressionHistory: Array<{ timestamp: number; savedTokens: number }> = [];

  constructor(config: Partial<MemoryMonitorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.metrics = this.initMetrics();
  }

  private initMetrics(): MemoryMetrics {
    return {
      memory_file_size_bytes: 0,
      memory_file_token_estimate: 0,
      memory_entry_count: 0,
      memory_compression_events: 0,
      memory_compression_saved_tokens: 0,
      context_overflow_risk: 0,
      mecw_utilization_ratio: 0,
      task_type_distribution: {},
    };
  }

  /**
   * Scan memory file and collect metrics.
   */
  scanMemory(filePath: string, taskType: string = 'simple-lookup'): MemoryMetrics {
    if (!fs.existsSync(filePath)) {
      return this.metrics;
    }

    const stats = fs.statSync(filePath);
    const content = fs.readFileSync(filePath, "utf-8");
    
    // Basic metrics
    this.metrics.memory_file_size_bytes = stats.size;
    this.metrics.memory_file_token_estimate = this.estimateTokens(content);
    this.metrics.memory_entry_count = (content.match(/\*\*User\*\*|\*\*Assistant\*\*/g) || []).length;
    
    // MECW utilization
    const mecwLimit = this.config.mecwLimits[taskType] || 5000;
    this.metrics.mecw_utilization_ratio = Math.min(
      this.metrics.memory_file_token_estimate / mecwLimit,
      1.0
    );
    
    // Risk calculation
    this.metrics.context_overflow_risk = this.calculateRisk(taskType);
    
    // Task distribution
    this.metrics.task_type_distribution[taskType] = 
      (this.metrics.task_type_distribution[taskType] || 0) + 1;

    return this.metrics;
  }

  /**
   * Record a compression event.
   */
  recordCompression(savedTokens: number): void {
    this.metrics.memory_compression_events++;
    this.metrics.memory_compression_saved_tokens += savedTokens;
    this.compressionHistory.push({
      timestamp: Date.now(),
      savedTokens,
    });
    
    // Keep only last 100 events
    if (this.compressionHistory.length > 100) {
      this.compressionHistory.shift();
    }
  }

  /**
   * Get current risk level.
   */
  getRiskLevel(): 'safe' | 'warning' | 'critical' {
    if (this.metrics.context_overflow_risk >= this.config.criticalThreshold) {
      return 'critical';
    }
    if (this.metrics.context_overflow_risk >= this.config.warningThreshold) {
      return 'warning';
    }
    return 'safe';
  }

  /**
   * Get status report.
   */
  getStatus(): {
    riskLevel: 'safe' | 'warning' | 'critical';
    metrics: MemoryMetrics;
    recommendations: string[];
  } {
    const riskLevel = this.getRiskLevel();
    const recommendations: string[] = [];

    if (riskLevel === 'critical') {
      recommendations.push('IMMEDIATE ACTION: Memory file approaching limit');
      recommendations.push('Trigger compression or flush');
    } else if (riskLevel === 'warning') {
      recommendations.push('Consider proactive compression soon');
    }

    return {
      riskLevel,
      metrics: this.metrics,
      recommendations,
    };
  }

  private estimateTokens(content: string): number {
    // Rough estimate: 4 chars ≈ 1 token
    return Math.ceil(content.length / 4);
  }

  private calculateRisk(taskType: string): number {
    const mecwLimit = this.config.mecwLimits[taskType] || 5000;
    const ratio = this.metrics.memory_file_token_estimate / mecwLimit;
    
    // Add compression history factor
    const recentCompressions = this.compressionHistory.filter(
      e => Date.now() - e.timestamp < 3600000  // Last hour
    ).length;
    
    const compressionFactor = Math.min(recentCompressions / 10, 0.3);
    
    return Math.min(ratio + compressionFactor, 1.0);
  }
}

export const DEFAULT_MEMORY_MONITOR_CONFIG = DEFAULT_CONFIG;
