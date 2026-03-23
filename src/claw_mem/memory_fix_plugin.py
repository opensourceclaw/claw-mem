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
claw-mem Memory System Bug Fix Plugin

Fixes memory retrieval, update, and injection issues without modifying OpenClaw core.

Fixes:
1. Memory retrieval accuracy (exact match priority)
2. Memory deduplication (update vs add)
3. Session start validation
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class MemoryFixPlugin:
    """
    记忆系统修复插件
    
    通过包装和增强 OpenClaw 原生记忆功能，修复已知 Bug
    """
    
    def __init__(self, workspace: str):
        """
        初始化插件
        
        Args:
            workspace: OpenClaw workspace 路径
        """
        self.workspace = Path(workspace).expanduser()
        self.memory_file = self.workspace / "MEMORY.md"
        self.fix_log_file = self.workspace / ".claw-mem" / "memory_fix.log"
        self.fix_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # Fix 1: 改进记忆检索 - 精确匹配优先
    # ========================================================================
    
    def retrieve_with_priority(self, query: str, memories: List[Dict]) -> List[Dict]:
        """
        带优先级的记忆检索
        
        优先级规则：
        1. 精确匹配（URL、路径、名称等）
        2. 最新纠正优先（时间权重）
        3. 置信度评分（用户纠正 = 高置信度）
        
        Args:
            query: 搜索查询
            memories: 记忆列表
        
        Returns:
            list: 排序后的记忆列表（最相关的在前）
        """
        scored_memories = []
        
        for memory in memories:
            score = self._calculate_retrieval_score(query, memory)
            scored_memories.append({
                'memory': memory,
                'score': score
            })
        
        # 按分数降序排序
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回排序后的记忆
        return [item['memory'] for item in scored_memories]
    
    def _calculate_retrieval_score(self, query: str, memory: Dict) -> float:
        """
        计算记忆检索分数
        
        Args:
            query: 搜索查询
            memory: 记忆字典
        
        Returns:
            float: 检索分数（越高越相关）
        """
        score = 0.0
        memory_content = memory.get('content', '')
        
        # 1. 精确匹配（最高优先级）
        if self._is_exact_match(query, memory_content):
            score += 100.0
        
        # 2. 关键信息类型加分（URL、路径等）
        if self._is_critical_info(query):
            if query.lower() in memory_content.lower():
                score += 50.0
        
        # 3. 时间权重（新纠正优先）
        timestamp = memory.get('timestamp')
        if timestamp:
            days_old = self._days_since(timestamp)
            if days_old < 1:  # 当天
                score += 20.0
            elif days_old < 7:  # 7 天内
                score += 10.0
            elif days_old < 30:  # 30 天内
                score += 5.0
        
        # 4. 置信度（用户明确纠正的优先）
        if memory.get('confidence', 0) > 0.8:
            score += 15.0
        
        # 5. 关键词匹配
        query_words = query.lower().split()
        content_lower = memory_content.lower()
        matched_words = sum(1 for word in query_words if word in content_lower)
        score += matched_words * 2.0
        
        return score
    
    def _is_exact_match(self, query: str, content: str) -> bool:
        """检查是否精确匹配"""
        # URL 精确匹配
        url_pattern = r'https?://\S+'
        query_urls = re.findall(url_pattern, query)
        content_urls = re.findall(url_pattern, content)
        
        for url in query_urls:
            if url in content_urls:
                return True
        
        # 路径精确匹配
        path_pattern = r'~?/\S+|\.openclaw/\S+'
        query_paths = re.findall(path_pattern, query)
        content_paths = re.findall(path_pattern, content)
        
        for path in query_paths:
            if path in content_paths:
                return True
        
        # 普通文本精确匹配（忽略大小写）
        return query.lower().strip() in content.lower().strip()
    
    def _is_critical_info(self, text: str) -> bool:
        """检查是否是关键信息（URL、路径、名称等）"""
        critical_patterns = [
            r'https?://',           # URL
            r'~?/\S+',              # 路径
            r'\.openclaw',          # OpenClaw 路径
            r'github\.com',         # GitHub
            r'\.git$',              # Git 仓库
        ]
        
        return any(re.search(pattern, text) for pattern in critical_patterns)
    
    def _days_since(self, timestamp_str: str) -> int:
        """计算距离某天多少天"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return (datetime.now() - timestamp).days
        except:
            return 999
    
    # ========================================================================
    # Fix 2: 记忆更新去重 - 检测并更新而非添加
    # ========================================================================
    
    def store_with_dedup(self, content: str, memory_type: str = "semantic", 
                         tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        带去重的记忆存储
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            tags: 标签列表
        
        Returns:
            tuple: (成功与否，消息)
        """
        if not self.memory_file.exists():
            return self._add_new_memory(content, memory_type, tags)
        
        # 读取现有记忆
        existing_memories = self._read_memories()
        
        # 检测是否有相似条目
        similar = self._find_similar_memory(content, existing_memories)
        
        if similar:
            # 发现相似条目，更新而非添加
            return self._update_memory(similar['index'], content, tags)
        else:
            # 没有相似条目，添加新的
            return self._add_new_memory(content, memory_type, tags)
    
    def _find_similar_memory(self, content: str, memories: List[Dict]) -> Optional[Dict]:
        """
        查找相似的记忆条目
        
        Args:
            content: 新记忆内容
            memories: 现有记忆列表
        
        Returns:
            相似记忆信息（如果有），否则 None
        """
        for i, memory in enumerate(memories):
            similarity = self._calculate_similarity(content, memory['content'])
            if similarity > 0.7:  # 70% 相似度阈值
                return {
                    'index': i,
                    'memory': memory,
                    'similarity': similarity
                }
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本 1
            text2: 文本 2
        
        Returns:
            float: 相似度（0-1）
        """
        # 提取关键信息（URL、路径等）
        key1 = self._extract_key_info(text1)
        key2 = self._extract_key_info(text2)
        
        # 如果关键信息相同，认为高度相似
        if key1 == key2 and len(key1) > 10:  # 避免短字符串误判
            return 1.0
        
        # 检查是否包含相同的关键模式
        if self._has_same_key_pattern(text1, text2):
            return 0.8
        
        # 简单的词语重叠度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 过滤掉常见词
        stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '与', '等'}
        words1 = {w for w in words1 if w not in stop_words and len(w) > 1}
        words2 = {w for w in words2 if w not in stop_words and len(w) > 1}
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _has_same_key_pattern(self, text1: str, text2: str) -> bool:
        """检查是否有相同的关键模式（如相同的 URL 或路径）"""
        # 提取 URL
        urls1 = set(re.findall(r'https?://\S+', text1))
        urls2 = set(re.findall(r'https?://\S+', text2))
        if urls1 and urls2 and urls1 & urls2:
            return True
        
        # 提取路径
        paths1 = set(re.findall(r'~?/\S+|\.openclaw/\S+', text1))
        paths2 = set(re.findall(r'~?/\S+|\.openclaw/\S+', text2))
        if paths1 and paths2 and paths1 & paths2:
            return True
        
        return False
    
    def _extract_key_info(self, text: str) -> str:
        """提取关键信息（URL、路径等）"""
        # URL
        urls = re.findall(r'https?://\S+', text)
        if urls:
            return urls[0]
        
        # 路径
        paths = re.findall(r'~?/\S+|\.openclaw/\S+', text)
        if paths:
            return paths[0]
        
        return text.strip()
    
    def _read_memories(self) -> List[Dict]:
        """读取 MEMORY.md 中的所有记忆"""
        if not self.memory_file.exists():
            return []
        
        memories = []
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析记忆条目
        pattern = r'\[([^\]]+)\]\s*(.+?)\s*(?:<!--\s*tags:\s*([^>]+)\s*-->)?'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        for timestamp, content_str, tags_str in matches:
            memories.append({
                'timestamp': timestamp.strip(),
                'content': content_str.strip(),
                'tags': [t.strip() for t in tags_str.split(',')] if tags_str else [],
                'confidence': 1.0  # 默认高置信度
            })
        
        return memories
    
    def _add_new_memory(self, content: str, memory_type: str, 
                       tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """添加新记忆"""
        try:
            timestamp = datetime.now().isoformat()
            tags_str = f" <!-- tags: {', '.join(tags)} -->" if tags else ""
            
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(f"\n[{timestamp}] {content}{tags_str}\n")
            
            self._log_fix("add", content)
            return True, "记忆添加成功"
        except Exception as e:
            return False, f"添加失败：{str(e)}"
    
    def _update_memory(self, index: int, content: str, 
                      tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """更新现有记忆"""
        try:
            memories = self._read_memories()
            
            if index >= len(memories):
                return False, "记忆索引超出范围"
            
            # 更新记忆内容
            memories[index]['content'] = content
            if tags:
                memories[index]['tags'] = tags
            memories[index]['timestamp'] = datetime.now().isoformat()
            memories[index]['confidence'] = 1.0  # 用户纠正 = 高置信度
            
            # 写回文件
            self._write_memories(memories)
            
            self._log_fix("update", content)
            return True, "记忆更新成功"
        except Exception as e:
            return False, f"更新失败：{str(e)}"
    
    def _write_memories(self, memories: List[Dict]):
        """写回记忆文件"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            f.write("# MEMORY.md\n\n")
            f.write("<!-- Core Memory - Permanent Storage -->\n\n")
            
            for memory in memories:
                tags_str = f" <!-- tags: {', '.join(memory['tags'])} -->" if memory.get('tags') else ""
                f.write(f"[{memory['timestamp']}] {memory['content']}{tags_str}\n")
    
    def _log_fix(self, action: str, content: str):
        """记录修复日志"""
        with open(self.fix_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {action.upper()}: {content}\n")
    
    # ========================================================================
    # Fix 3: 会话启动验证
    # ========================================================================
    
    def validate_session_memory(self) -> Dict:
        """
        验证会话启动时的记忆
        
        Returns:
            dict: 验证结果
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'memories_count': 0,
        }
        
        # 检查记忆文件是否存在
        if not self.memory_file.exists():
            result['warnings'].append("MEMORY.md 不存在，将创建新文件")
            return result
        
        # 读取并验证记忆
        try:
            memories = self._read_memories()
            result['memories_count'] = len(memories)
            
            if len(memories) == 0:
                result['warnings'].append("记忆文件为空")
            
            # 检查重复条目
            duplicates = self._find_duplicates(memories)
            if duplicates:
                result['errors'].append(f"发现 {len(duplicates)} 个重复条目")
                result['valid'] = False
            
            # 检查冲突条目
            conflicts = self._find_conflicts(memories)
            if conflicts:
                result['errors'].append(f"发现 {len(conflicts)} 个冲突条目")
                result['valid'] = False
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"读取记忆失败：{str(e)}")
        
        return result
    
    def _find_duplicates(self, memories: List[Dict]) -> List[Dict]:
        """查找重复条目"""
        seen = {}
        duplicates = []
        
        for memory in memories:
            key = self._extract_key_info(memory['content'])
            if key in seen:
                duplicates.append(memory)
            else:
                seen[key] = memory
        
        return duplicates
    
    def _find_conflicts(self, memories: List[Dict]) -> List[Dict]:
        """查找冲突条目（相同关键信息但内容不同）"""
        # 简化版本：检查 URL/路径是否对应多个不同值
        urls = {}
        conflicts = []
        
        for memory in memories:
            url = self._extract_key_info(memory['content'])
            if url.startswith('http'):
                if url in urls and urls[url] != memory['content']:
                    conflicts.append(memory)
                else:
                    urls[url] = memory['content']
        
        return conflicts
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def get_fix_statistics(self) -> Dict:
        """获取修复统计信息"""
        stats = {
            'workspace': str(self.workspace),
            'memory_file_exists': self.memory_file.exists(),
            'memories_count': 0,
            'fix_log_exists': self.fix_log_file.exists(),
            'fix_actions': 0,
        }
        
        if self.memory_file.exists():
            stats['memories_count'] = len(self._read_memories())
        
        if self.fix_log_file.exists():
            with open(self.fix_log_file, 'r') as f:
                stats['fix_actions'] = sum(1 for _ in f)
        
        return stats


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    workspace = "~/.openclaw/workspace"
    plugin = MemoryFixPlugin(workspace)
    
    print("测试 F000 记忆系统修复插件\n")
    
    # 测试 1：存储记忆（带去重）
    print("测试 1: 存储记忆（带去重）")
    success, msg = plugin.store_with_dedup(
        "用户偏好使用中文",
        memory_type="semantic",
        tags=["preference", "language"]
    )
    print(f"  {msg}")
    
    # 测试 2：验证会话记忆
    print("\n测试 2: 验证会话记忆")
    validation = plugin.validate_session_memory()
    print(f"  有效：{validation['valid']}")
    print(f"  记忆数：{validation['memories_count']}")
    if validation['errors']:
        print(f"  错误：{validation['errors']}")
    if validation['warnings']:
        print(f"  警告：{validation['warnings']}")
    
    # 测试 3：获取统计
    print("\n测试 3: 获取统计信息")
    stats = plugin.get_fix_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
