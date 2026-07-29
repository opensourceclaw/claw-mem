/**
 * claw-mem v6.43.0 — Memory Bridge Configuration
 */

export interface MemoryBridgeConfig {
  enabled: boolean;
  reportingInterval: number;    // ms, default: 30000
  autoCompact: boolean;
  strategies: {
    truncate: { enabled: boolean };
    summarize: { enabled: boolean; method: "simple" | "llm" };
    compress: { enabled: boolean };
  };
}

export const DEFAULT_MEMORY_BRIDGE_CONFIG: MemoryBridgeConfig = {
  enabled: true,
  reportingInterval: 30000,
  autoCompact: true,
  strategies: {
    truncate: { enabled: true },
    summarize: { enabled: true, method: "simple" },
    compress: { enabled: false },
  },
};
