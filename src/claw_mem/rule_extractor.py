#!/usr/bin/env python3
"""
claw-mem Auto Rule Extraction (Simplified)

Automatically extracts Pre-flight Check rules from user corrections.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExtractedRule:
    """提取的规则"""
    id: str
    rule_type: str
    condition: str
    action: str
    confidence: float
    source: str
    created_at: str
    applied_count: int = 0


class RuleExtractor:
    """自动规则提取器"""
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace).expanduser()
        self.rules_file = self.workspace / ".claw-mem" / "extracted_rules.md"
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        self.rules: List[ExtractedRule] = []
        self._load_rules()
    
    def extract(self, conversation: str) -> Optional[ExtractedRule]:
        """从对话中提取规则"""
        # 简单规则匹配
        if "不要" in conversation and "到" in conversation:
            # 提取路径
            match = re.search(r'到\s*(~?/\S+)', conversation)
            if match:
                path = match.group(1)
                return self._create_rule(
                    rule_type="FORBIDDEN_PATH",
                    condition=f"path starts with '{path}'",
                    action="REJECT",
                    confidence=0.9,
                    source=conversation
                )
        
        if "不要" in conversation and "使用" in conversation:
            match = re.search(r'使用\s*(\S+)', conversation)
            if match:
                tool = match.group(1)
                return self._create_rule(
                    rule_type="FORBIDDEN_TOOL",
                    condition=f"tool == '{tool}'",
                    action="FORBID",
                    confidence=0.85,
                    source=conversation
                )
        
        if "偏好" in conversation:
            match = re.search(r'偏好.*?使用\s*(\S+)', conversation)
            if match:
                pref = match.group(1)
                return self._create_rule(
                    rule_type="PREFERENCE",
                    condition=f"preference == '{pref}'",
                    action="APPLY",
                    confidence=0.95,
                    source=conversation
                )
        
        if "必须" in conversation and "先" in conversation:
            return self._create_rule(
                rule_type="REQUIRE_ORDER",
                condition="sequence_check",
                action="REQUIRE_SEQUENCE",
                confidence=0.8,
                source=conversation
            )
        
        return None
    
    def _create_rule(self, rule_type: str, condition: str, action: str, 
                    confidence: float, source: str) -> ExtractedRule:
        """创建规则对象"""
        rule_id = f"rule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        rule = ExtractedRule(
            id=rule_id,
            rule_type=rule_type,
            condition=condition,
            action=action,
            confidence=confidence,
            source=source[:100],
            created_at=datetime.now().isoformat(),
        )
        self._save_rule(rule)
        return rule
    
    def _save_rule(self, rule: ExtractedRule):
        """保存规则到文件"""
        self.rules.append(rule)
        with open(self.rules_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {rule.id}\n")
            f.write(f"- 类型：{rule.rule_type}\n")
            f.write(f"- 条件：{rule.condition}\n")
            f.write(f"- 动作：{rule.action}\n")
            f.write(f"- 置信度：{rule.confidence:.2f}\n")
            f.write(f"- 来源：{rule.source}\n")
    
    def _load_rules(self):
        """从文件加载规则（简化版）"""
        if not self.rules_file.exists():
            return
        # 简化实现：暂不解析
    
    def check_before_operation(self, operation: str, context: Dict) -> Tuple[bool, str]:
        """操作前检查所有适用规则"""
        for rule in self.rules:
            if rule.rule_type == "FORBIDDEN_PATH":
                path = context.get('path', '')
                if 'starts with' in rule.condition:
                    required_path = rule.condition.split("'")[1]
                    if not path.startswith(required_path):
                        return False, f"路径必须在 {required_path}"
            
            elif rule.rule_type == "FORBIDDEN_TOOL":
                tool = context.get('tool', '')
                if '==' in rule.condition:
                    forbidden_tool = rule.condition.split("'")[1]
                    if tool == forbidden_tool:
                        return False, f"禁止使用工具：{forbidden_tool}"
        
        return True, "所有规则检查通过"
    
    def get_statistics(self) -> Dict:
        """获取规则统计"""
        stats = {
            'total_rules': len(self.rules),
            'by_type': {},
            'total_applied': sum(r.applied_count for r in self.rules),
        }
        for rule in self.rules:
            rule_type = rule.rule_type
            stats['by_type'][rule_type] = stats['by_type'].get(rule_type, 0) + 1
        return stats


if __name__ == "__main__":
    workspace = "~/.openclaw/workspace"
    extractor = RuleExtractor(workspace)
    
    print("测试 F101 自动规则提取\n")
    
    # 测试 1
    print("测试 1: 提取禁止路径规则")
    rule = extractor.extract("不要创建文件到 ~/.openclaw/workspace/")
    if rule:
        print(f"  ✅ 提取成功：{rule.rule_type} - {rule.condition}")
    else:
        print(f"  ❌ 提取失败")
    
    # 测试 2
    print("\n测试 2: 提取偏好规则")
    rule = extractor.extract("我偏好使用中文")
    if rule:
        print(f"  ✅ 提取成功：{rule.rule_type} - {rule.condition}")
    else:
        print(f"  ❌ 提取失败")
    
    # 测试 3
    print("\n测试 3: 操作前规则检查")
    allowed, msg = extractor.check_before_operation(
        "file_write",
        {'path': '/Users/liantian/workspace/test.md'}
    )
    print(f"  允许：{allowed}, 消息：{msg}")
    
    # 测试 4
    print("\n测试 4: 规则统计")
    stats = extractor.get_statistics()
    print(f"  总规则数：{stats['total_rules']}")
    print(f"  按类型：{stats['by_type']}")
