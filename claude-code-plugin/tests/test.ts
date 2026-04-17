import { ClawMemBridge } from '../src/bridge.js';
import { SessionStartHook } from '../src/hooks/SessionStartHook.js';
import { PostToolUseHook } from '../src/hooks/PostToolUseHook.js';
import { SessionEndHook } from '../src/hooks/SessionEndHook.js';

async function runTests() {
  console.log('🧪 Testing claw-mem Claude Code Plugin\n');
  
  const bridge = new ClawMemBridge();
  
  // Test 1: Check installation
  console.log('Test 1: Check installation');
  const installCheck = await bridge.checkInstallation();
  console.log(`  Installed: ${installCheck.installed}`);
  if (installCheck.version) {
    console.log(`  Version: ${installCheck.version}`);
  }
  if (installCheck.error) {
    console.log(`  Error: ${installCheck.error}`);
  }
  console.log();
  
  // Test 2: SessionStartHook
  console.log('Test 2: SessionStartHook');
  const sessionStart = await SessionStartHook({
    cwd: '/test/project'
  });
  console.log(`  Type: ${sessionStart.type}`);
  console.log(`  Content length: ${sessionStart.content.length} chars`);
  console.log(`  Memories: ${sessionStart.memories?.length || 0}`);
  console.log();
  
  // Test 3: PostToolUseHook (write)
  console.log('Test 3: PostToolUseHook (write)');
  const postToolWrite = await PostToolUseHook({
    tool: 'write',
    input: { path: '/test/file.txt' },
    output: { success: true },
    success: true
  });
  console.log(`  Captured: ${postToolWrite.captured}`);
  if (postToolWrite.memory) {
    console.log(`  Memory: ${postToolWrite.memory.content}`);
  }
  console.log();
  
  // Test 4: PostToolUseHook (failed)
  console.log('Test 4: PostToolUseHook (failed operation)');
  const postToolFailed = await PostToolUseHook({
    tool: 'exec',
    input: { command: 'false' },
    output: { stderr: 'Error' },
    success: false
  });
  console.log(`  Captured: ${postToolFailed.captured}`);
  console.log(`  Reason: ${postToolFailed.reason}`);
  console.log();
  
  // Test 5: SessionEndHook
  console.log('Test 5: SessionEndHook');
  const sessionEnd = await SessionEndHook({
    duration: 60000,
    messageCount: 10,
    toolUseCount: 5
  });
  console.log(`  Summarized: ${sessionEnd.summarized}`);
  console.log(`  Memories created: ${sessionEnd.memoriesCreated}`);
  console.log();
  
  // Test 6: Bridge recall
  console.log('Test 6: Bridge recall');
  const memories = await bridge.recall({ topK: 5 });
  console.log(`  Memories found: ${memories.length}`);
  console.log();
  
  // Test 7: Bridge store
  console.log('Test 7: Bridge store');
  const storeResult = await bridge.store({
    content: 'Test memory from Claude Code plugin',
    layer: 'semantic'
  });
  console.log(`  Success: ${storeResult.success}`);
  console.log(`  ID: ${storeResult.id}`);
  console.log();
  
  console.log('✅ All tests completed');
}

runTests().catch(console.error);
