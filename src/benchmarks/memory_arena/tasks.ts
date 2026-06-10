/**
 * MemoryArena tasks — multi-session cross-domain evaluation tasks.
 *
 * Four task types: web navigation, preference planning,
 * progressive search, and formal reasoning.
 */

export type ArenaTaskType =
  | "web-navigation"
  | "preference-planning"
  | "progressive-search"
  | "formal-reasoning";

export interface ArenaTask {
  id: string;
  type: ArenaTaskType;
  description: string;
  /** Sessions of conversation data for this task */
  sessions: Array<Array<{ role: string; content: string }>>;
  /** Expected knowledge that should be retained across sessions */
  expectedKnowledge: string[];
  /** Minimum score to pass */
  threshold: number;
}

/** Pre-built MemoryArena task definitions. */
export const ARENA_TASKS: ArenaTask[] = [
  // ── Web Navigation ──
  {
    id: "web-nav-001",
    type: "web-navigation",
    description: "Navigate documentation to find API parameters, then recall in next session",
    sessions: [
      [
        { role: "user", content: "Find the max_tokens parameter in the API docs" },
        { role: "assistant", content: "The max_tokens parameter controls the maximum number of tokens in the response. Default is 4096. Set it via the API config." },
      ],
      [
        { role: "user", content: "What was the parameter for controlling response length?" },
        { role: "assistant", content: "max_tokens — maximum tokens in response, default 4096." },
      ],
    ],
    expectedKnowledge: ["max_tokens", "4096", "response length"],
    threshold: 0.5,
  },
  {
    id: "web-nav-002",
    type: "web-navigation",
    description: "Browse deployment guides and recall configuration steps",
    sessions: [
      [
        { role: "user", content: "Show me how to configure the deployment pipeline" },
        { role: "assistant", content: "Configure via .deploy.yaml: set environment to production, branch to main, trigger on push." },
      ],
      [
        { role: "user", content: "How do I set up the deployment?" },
        { role: "assistant", content: "Use .deploy.yaml with environment=production, branch=main, trigger=push." },
      ],
    ],
    expectedKnowledge: [".deploy.yaml", "production", "main", "push"],
    threshold: 0.5,
  },

  // ── Preference Planning ──
  {
    id: "pref-plan-001",
    type: "preference-planning",
    description: "Remember user preferences across sessions for code style",
    sessions: [
      [
        { role: "user", content: "I prefer TypeScript over JavaScript. Use 2-space indentation." },
        { role: "assistant", content: "Noted: TypeScript, 2-space indentation." },
      ],
      [
        { role: "user", content: "Generate a new module for me" },
        { role: "assistant", content: "Generating TypeScript module with 2-space indentation as preferred." },
      ],
    ],
    expectedKnowledge: ["TypeScript", "2-space"],
    threshold: 0.6,
  },
  {
    id: "pref-plan-002",
    type: "preference-planning",
    description: "Track evolving planning constraints across sessions",
    sessions: [
      [
        { role: "user", content: "Budget is $5000. Must use AWS us-east-1. Deadline is Q3." },
        { role: "assistant", content: "Constraints: budget $5000, AWS us-east-1, Q3 deadline." },
      ],
      [
        { role: "user", content: "What are my project constraints?" },
        { role: "assistant", content: "Budget: $5000, Region: AWS us-east-1, Deadline: Q3." },
      ],
    ],
    expectedKnowledge: ["$5000", "us-east-1", "Q3"],
    threshold: 0.5,
  },

  // ── Progressive Search ──
  {
    id: "prog-search-001",
    type: "progressive-search",
    description: "Build knowledge incrementally across search sessions",
    sessions: [
      [
        { role: "user", content: "What is Redis used for?" },
        { role: "assistant", content: "Redis is an in-memory data store used for caching, message brokering, and real-time analytics." },
      ],
      [
        { role: "user", content: "How does Redis handle persistence?" },
        { role: "assistant", content: "Redis persists data via RDB snapshots and AOF (Append-Only File) logs. RDB takes point-in-time snapshots; AOF logs every write." },
      ],
      [
        { role: "user", content: "Compare Redis RDB vs AOF" },
        { role: "assistant", content: "RDB: periodic snapshots, faster restarts, may lose recent data. AOF: logs every write, more durable, larger files. Often used together." },
      ],
    ],
    expectedKnowledge: ["Redis", "RDB", "AOF", "caching", "snapshots"],
    threshold: 0.4,
  },

  // ── Formal Reasoning ──
  {
    id: "formal-reason-001",
    type: "formal-reasoning",
    description: "Track logical reasoning chains across sessions",
    sessions: [
      [
        { role: "user", content: "If A implies B, and B implies C, what does A imply?" },
        { role: "assistant", content: "A implies C (by transitivity: A→B and B→C, therefore A→C)." },
      ],
      [
        { role: "user", content: "Given A is true, what conclusions can we draw?" },
        { role: "assistant", content: "Since A→B and A→C (from previous deduction), both B and C must be true." },
      ],
    ],
    expectedKnowledge: ["A→B", "B→C", "A→C", "transitivity"],
    threshold: 0.5,
  },
];
