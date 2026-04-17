import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface Memory {
  id: string;
  content: string;
  layer: 'episodic' | 'semantic' | 'procedural';
  timestamp: string;
  relevance?: number;
}

export interface RecallOptions {
  query?: string;
  topK?: number;
  mode?: 'keyword' | 'bm25' | 'hybrid' | 'enhanced_smart';
}

export interface StoreOptions {
  content: string;
  layer?: 'episodic' | 'semantic' | 'procedural';
  metadata?: Record<string, any>;
}

export interface SearchResult {
  memories: Memory[];
  total: number;
}

export class ClawMemBridge {
  private pythonPath: string;
  private workspaceDir: string;

  constructor(options?: { pythonPath?: string; workspaceDir?: string }) {
    this.pythonPath = options?.pythonPath || process.env.CLAW_MEM_PYTHON || 'python3';
    this.workspaceDir = options?.workspaceDir || process.env.CLAW_MEM_WORKSPACE || '~/.claude-mem';
  }

  /**
   * Recall memories (search-based retrieval)
   */
  async recall(options: RecallOptions = {}): Promise<Memory[]> {
    const { query = '', topK = 10 } = options;
    
    const scriptPath = require.resolve('../scripts/bridge.py');
    
    try {
      const { stdout } = await execAsync(
        `${this.pythonPath} -c "
import sys
import os
import json
os.environ['CLAW_MEM_SILENT'] = '1'
sys.path.insert(0, '${this.workspaceDir}')

from claw_mem.memory_manager import MemoryManager
manager = MemoryManager(workspace='${this.workspaceDir}')
results = manager.search('${query.replace(/'/g, "\\'")}', limit=${topK})
output = [{'id': m.get('id', ''), 'content': m.get('content', ''), 'layer': m.get('type', 'semantic'), 'timestamp': m.get('timestamp', ''), 'relevance': m.get('score', 0)} for m in results]
print(json.dumps(output))
"`,
        { maxBuffer: 1024 * 1024 * 10, timeout: 30000 }
      );
      return JSON.parse(stdout);
    } catch (error: any) {
      console.error('Recall failed:', error.message);
      return [];
    }
  }

  /**
   * Store a memory
   */
  async store(options: StoreOptions): Promise<{ id: string; success: boolean }> {
    const { content, layer = 'semantic', metadata = {} } = options;
    
    try {
      const { stdout } = await execAsync(
        `${this.pythonPath} -c "
import sys
import os
import json
os.environ['CLAW_MEM_SILENT'] = '1'
sys.path.insert(0, '${this.workspaceDir}')

from claw_mem.memory_manager import MemoryManager
manager = MemoryManager(workspace='${this.workspaceDir}')
success = manager.store('${content.replace(/'/g, "\\'")}', memory_type='${layer}')
print(json.dumps({'id': 'stored', 'success': success}))
"`,
        { timeout: 30000 }
      );
      return JSON.parse(stdout);
    } catch (error: any) {
      console.error('Store failed:', error.message);
      return { id: '', success: false };
    }
  }

  /**
   * Check if claw-mem is installed
   */
  async checkInstallation(): Promise<{ installed: boolean; version?: string; error?: string }> {
    try {
      const { stdout } = await execAsync(
        `${this.pythonPath} -c "import claw_mem; print(getattr(claw_mem, '__version__', 'unknown'))"`,
        { timeout: 5000 }
      );
      return { installed: true, version: stdout.trim() };
    } catch (error: any) {
      return {
        installed: false,
        error: 'claw-mem Python package not found. Run: pip install git+https://github.com/opensourceclaw/claw-mem.git'
      };
    }
  }

  /**
   * Get memory statistics
   */
  async getStats(): Promise<{
    episodic: number;
    semantic: number;
    procedural: number;
    total: number;
  }> {
    try {
      const { stdout } = await execAsync(
        `${this.pythonPath} -c "
import sys
import os
import json
os.environ['CLAW_MEM_SILENT'] = '1'
sys.path.insert(0, '${this.workspaceDir}')

from claw_mem.memory_manager import MemoryManager
manager = MemoryManager(workspace='${this.workspaceDir}')
stats = manager.get_stats()
print(json.dumps({'episodic': stats.get('episodic_count', 0), 'semantic': stats.get('semantic_count', 0), 'procedural': stats.get('procedural_count', 0), 'total': stats.get('episodic_count', 0) + stats.get('semantic_count', 0) + stats.get('procedural_count', 0)}))
"`,
        { timeout: 10000 }
      );
      return JSON.parse(stdout);
    } catch (error) {
      return { episodic: 0, semantic: 0, procedural: 0, total: 0 };
    }
  }
}
