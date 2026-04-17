import { ClawMemBridge, Memory } from '../bridge.js';

export interface SessionStartContext {
  recentMessages?: Array<{ role: string; content: string }>;
  cwd?: string;
  preferences?: Record<string, any>;
}

export interface SessionStartResult {
  type: 'context_injection';
  content: string;
  memories?: Memory[];
}

/**
 * SessionStartHook: Inject relevant memories at session start
 * 
 * This hook runs when Claude Code starts a new session.
 * It retrieves relevant memories and injects them as context.
 */
export async function SessionStartHook(
  context: SessionStartContext = {}
): Promise<SessionStartResult> {
  const bridge = new ClawMemBridge();
  
  // Check installation
  const installCheck = await bridge.checkInstallation();
  if (!installCheck.installed) {
    console.error(`⚠️  ${installCheck.error}`);
    return {
      type: 'context_injection',
      content: `# claw-mem Warning\n\n${installCheck.error}\n\nInstall with: \`pip install git+https://github.com/opensourceclaw/claw-mem.git\``
    };
  }

  // Build query from context
  const queryParts: string[] = [];
  
  if (context.recentMessages && context.recentMessages.length > 0) {
    const recentText = context.recentMessages
      .slice(-3)
      .map(m => m.content)
      .join(' ');
    queryParts.push(recentText.substring(0, 200));
  }
  
  if (context.cwd) {
    queryParts.push(`working directory: ${context.cwd}`);
  }
  
  if (context.preferences) {
    queryParts.push(`preferences: ${JSON.stringify(context.preferences)}`);
  }

  const query = queryParts.join(' ');

  // Recall relevant memories
  const memories = await bridge.recall({
    query,
    topK: 10,
    mode: 'enhanced_smart'
  });

  if (memories.length === 0) {
    return {
      type: 'context_injection',
      content: '# claw-mem\n\nNo relevant memories found. This is a fresh start!'
    };
  }

  // Format memories for injection
  const formattedMemories = formatMemories(memories);

  return {
    type: 'context_injection',
    content: formattedMemories,
    memories
  };
}

/**
 * Format memories for Claude context
 */
function formatMemories(memories: Memory[]): string {
  const lines: string[] = [
    '# 🧠 Relevant Memories',
    '',
    `Found ${memories.length} relevant memories:`,
    ''
  ];

  // Group by layer
  const byLayer = {
    episodic: memories.filter(m => m.layer === 'episodic'),
    semantic: memories.filter(m => m.layer === 'semantic'),
    procedural: memories.filter(m => m.layer === 'procedural')
  };

  // Episodic (events)
  if (byLayer.episodic.length > 0) {
    lines.push('## Recent Events');
    byLayer.episodic.slice(0, 3).forEach(m => {
      lines.push(`- ${m.content}`);
    });
    lines.push('');
  }

  // Semantic (facts)
  if (byLayer.semantic.length > 0) {
    lines.push('## Known Facts');
    byLayer.semantic.slice(0, 5).forEach(m => {
      lines.push(`- ${m.content}`);
    });
    lines.push('');
  }

  // Procedural (rules)
  if (byLayer.procedural.length > 0) {
    lines.push('## Rules to Follow');
    byLayer.procedural.forEach(m => {
      lines.push(`- ${m.content}`);
    });
    lines.push('');
  }

  lines.push('---');
  lines.push('*These memories were retrieved by claw-mem. They may or may not be relevant to the current task.*');

  return lines.join('\n');
}
