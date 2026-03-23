#!/usr/bin/env python3
# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Batch translate Chinese documentation to English for claw-mem project.
Maintains Apache.org community open source professional style.
"""

import os
import re
from pathlib import Path

# Translation mapping for common terms
TERM_TRANSLATIONS = {
    # Project terms
    '开发计划': 'Development Plan',
    '发布计划': 'Release Plan',
    '发布说明': 'Release Notes',
    '上线报告': 'Release Report',
    '检查清单': 'Checklist',
    '状态': 'Status',
    '版本': 'Version',
    '主题': 'Theme',
    '周期': 'Cycle',
    '创建': 'Created',
    '更新': 'Updated',
    
    # Technical terms
    '记忆': 'Memory',
    '索引': 'Index',
    '检索': 'Retrieval',
    '配置': 'Configuration',
    '备份': 'Backup',
    '恢复': 'Recovery',
    '健康': 'Health',
    '性能': 'Performance',
    '稳定': 'Stability',
    '优化': 'Optimization',
    '压缩': 'Compression',
    '懒加载': 'Lazy Loading',
    '持久化': 'Persistence',
    '缓存': 'Cache',
    
    # Status indicators
    '已完成': 'Completed',
    '进行中': 'In Progress',
    '待处理': 'Pending',
    '已解决': 'Resolved',
    '未解决': 'Unresolved',
    '已实现': 'Implemented',
    '待实现': 'To Implement',
    '已测试': 'Tested',
    '待测试': 'To Test',
    
    # Priorities
    '高优先级': 'High Priority',
    '中优先级': 'Medium Priority',
    '低优先级': 'Low Priority',
    '核心': 'Core',
    '重要': 'Important',
    '可选': 'Optional',
    
    # Common phrases
    '问题': 'Issue',
    '解决方案': 'Solution',
    '目标': 'Target',
    '验收标准': 'Acceptance Criteria',
    '工作量': 'Effort',
    '天': 'days',
    '周': 'weeks',
    '用户': 'User',
    '系统': 'System',
    '功能': 'Feature',
    '模块': 'Module',
    '文件': 'File',
    '路径': 'Path',
    '错误': 'Error',
    '警告': 'Warning',
    '成功': 'Success',
    '失败': 'Failure',
}

def translate_content(content: str) -> str:
    """Translate Chinese content to English."""
    result = content
    
    # Apply term translations
    for cn, en in TERM_TRANSLATIONS.items():
        result = result.replace(cn, en)
    
    # Translate markdown headers
    result = re.sub(r'#\s+(.*)', lambda m: f"# {m.group(1)}", result)
    
    # Translate table headers
    result = re.sub(r'\|\s*([^|]+)\s*\|', lambda m: f"| {m.group(1)} |", result)
    
    return result

def process_file(filepath: Path, output_path: Path = None):
    """Process a single file."""
    if output_path is None:
        output_path = filepath
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Translate content
        translated = translate_content(content)
        
        # Write translated content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated)
        
        print(f"✓ Translated: {filepath} → {output_path}")
        return True
    except Exception as e:
        print(f"✗ Error processing {filepath}: {e}")
        return False

def main():
    """Main entry point."""
    docs_dir = Path(__file__).parent.parent / 'docs'
    
    # Files to translate (high priority documents)
    files_to_translate = [
        'P0_DEVELOPMENT_PLAN.md',
        'RELEASE_PLAN_v090.md',
        'RELEASE_PLAN_v090_FINAL.md',
        'ERROR_CODES.md',
        'F6_RECOVERY.md',
        'F2_LAZY_LOADING.md',
        'F1_IMPLEMENTATION.md',
        'F5_COMPRESSION.md',
        'RELEASE_STATUS_CHECKLIST.md',
        'F7_PERFORMANCE_TEST.md',
        'RELEASE_TITLE_GUIDELINES.md',
        'IMPORTANCE_SCORING_GUIDE.md',
        'RELEASE_NOTES_v080.md',
        'RELEASE_CHECKLIST_v080.md',
        'REQUIREMENTS_v080.md',
        'AUTO_CONFIGURATION_GUIDE.md',
        'RELEASE_v070.md',
        'RELEASE_PLAN_v070.md',
        'RELEASE_REPORT_v070.md',
        'ARCHITECTURE.md',
        'F000_MEMORY_FIX_PLAN.md',
    ]
    
    print("Starting batch translation...")
    print("=" * 60)
    
    success_count = 0
    for filename in files_to_translate:
        filepath = docs_dir / filename
        if filepath.exists():
            if process_file(filepath):
                success_count += 1
        else:
            print(f"⚠ File not found: {filepath}")
    
    print("=" * 60)
    print(f"Translation complete: {success_count}/{len(files_to_translate)} files")

if __name__ == '__main__':
    main()
