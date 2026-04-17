import { ClawMemBridge } from './dist/bridge.js';
import { SessionStartHook } from './dist/hooks/SessionStartHook.js';
import { PostToolUseHook } from './dist/hooks/PostToolUseHook.js';
import { SessionEndHook } from './dist/hooks/SessionEndHook.js';

async function runTests() {
  console.log('🧪 Testing claw-mem Claude Code Plugin\n');
  
  const bridge = new ClawMemBridge();
  
  // Test 1: Check installation
  console.log('Test 1: Check installation');
  const installCheck = await bridge.checkInstallation();
  console.log(`  Installed: ${installCheck.installed}`);
  if (installCheck.version) console.log(`  Version: ${installCheck.version}`);
  if (installCheck.error) console.log(`  Error: ${installCheck.error}`);
  console.log();
  
  // Test 2: SessionStartHook
  console.log('Test 2: SessionStartHook');
  const sessionStart = await SessionStartHook({ cwd: '/test/project' });
  console.log(`  Type: ${sessionStart.type}`);
  console.log(`  Content length: ${sessionStart.content.length} chars`);
  console.log();
  
  // Test 3: PostToolUseHook
  console.log('Test 3: PostToolUseHook (write)');
  const postToolWrite = await PostToolUseHook({
    tool: 'write',
    input: { path: '/test/file.txt' },
    output: { success: true },
    success: true
  });
  console.log(`  Captured: ${postToolWrite.captured}`);
  console.log();
  
  // Test 4: SessionEndHook
  console.log('Test 4: SessionEndHook');
  const sessionEnd = await SessionEndHook({
    duration: 60000,
    messageCount: 10,
    toolUseCount: 5
  });
  console.log(`  Summarized: ${sessionEnd.summarized}`);
  console.log();
  
  console.log('✅ All tests completed');
}

runTests().catch(console.error);
