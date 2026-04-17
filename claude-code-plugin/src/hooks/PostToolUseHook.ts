import { ClawMemBridge } from '../bridge.js';

export interface ToolUseResult {
  tool: string;
  input: Record<string, any>;
  output: any;
  success: boolean;
  duration?: number;
}

export interface PostToolUseResult {
  captured: boolean;
  memory?: { id: string; content: string };
  reason?: string;
}

/**
 * PostToolUseHook: Capture important facts from tool usage
 * 
 * This hook runs after each tool use.
 * It extracts and stores important observations.
 */
export async function PostToolUseHook(
  result: ToolUseResult
): Promise<PostToolUseResult> {
  const bridge = new ClawMemBridge();

  // Extract fact from tool result
  const fact = extractFact(result);
  
  if (!fact) {
    return { captured: false, reason: 'No significant fact extracted' };
  }

  // Determine layer based on tool type
  const layer = determineLayer(result.tool);

  // Store the fact
  const storeResult = await bridge.store({
    content: fact,
    layer,
    metadata: {
      tool: result.tool,
      timestamp: new Date().toISOString(),
      success: result.success
    }
  });

  return {
    captured: true,
    memory: { id: storeResult.id, content: fact }
  };
}

/**
 * Extract a fact from tool result
 */
function extractFact(result: ToolUseResult): string | null {
  const { tool, input, output, success } = result;

  // Skip failed operations
  if (!success) return null;

  // Tool-specific extraction
  switch (tool) {
    case 'read':
      if (input.path && output) {
        const lineCount = typeof output === 'string' 
          ? output.split('\n').length 
          : 0;
        return `Read file ${input.path} (${lineCount} lines)`;
      }
      break;

    case 'write':
      if (input.path) {
        return `Created/modified file: ${input.path}`;
      }
      break;

    case 'edit':
      if (input.path) {
        return `Edited file: ${input.path}`;
      }
      break;

    case 'exec':
      if (input.command) {
        const cmd = input.command.substring(0, 50);
        return `Executed command: ${cmd}${input.command.length > 50 ? '...' : ''}`;
      }
      break;

    case 'web_fetch':
      if (input.url) {
        return `Fetched content from ${input.url}`;
      }
      break;

    case 'browser':
      if (input.url || input.action) {
        return `Browser action: ${input.action || 'navigate'} ${input.url || ''}`;
      }
      break;

    default:
      // Skip unknown tools
      return null;
  }

  return null;
}

/**
 * Determine memory layer based on tool type
 */
function determineLayer(tool: string): 'episodic' | 'semantic' | 'procedural' {
  // Procedural: tools that establish patterns
  if (['exec', 'write', 'edit'].includes(tool)) {
    return 'procedural';
  }
  
  // Episodic: tools that record events
  if (['read', 'web_fetch', 'browser'].includes(tool)) {
    return 'episodic';
  }
  
  // Semantic: default for facts
  return 'semantic';
}
