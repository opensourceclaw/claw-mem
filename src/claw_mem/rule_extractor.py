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
    """Extracted rule"""

    id: str
    rule_type: str
    condition: str
    action: str
    confidence: float
    source: str
    created_at: str
    applied_count: int = 0


class RuleExtractor:
    """Automatic rule extractor"""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace).expanduser()
        self.rules_file = self.workspace / ".claw-mem" / "extracted_rules.md"
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        self.rules: List[ExtractedRule] = []
        self._load_rules()

    def extract(self, conversation: str) -> Optional[ExtractedRule]:
        """Extract rules from conversation"""
        # Simple rule matching
        if "do not" in conversation and "to" in conversation:
            # Extract path
            match = re.search(r"to\s*(~?/\S+)", conversation)
            if match:
                path = match.group(1)
                return self._create_rule(
                    rule_type="FORBIDDEN_PATH",
                    condition=f"path starts with '{path}'",
                    action="REJECT",
                    confidence=0.9,
                    source=conversation,
                )

        if "do not" in conversation and "use" in conversation:
            match = re.search(r"use\s*(\S+)", conversation)
            if match:
                tool = match.group(1)
                return self._create_rule(
                    rule_type="FORBIDDEN_TOOL",
                    condition=f"tool == '{tool}'",
                    action="FORBID",
                    confidence=0.85,
                    source=conversation,
                )

        if "prefer" in conversation:
            match = re.search(r"prefer.*?use\s*(\S+)", conversation)
            if match:
                pref = match.group(1)
                return self._create_rule(
                    rule_type="PREFERENCE",
                    condition=f"preference == '{pref}'",
                    action="APPLY",
                    confidence=0.95,
                    source=conversation,
                )

        if "must" in conversation and "first" in conversation:
            return self._create_rule(
                rule_type="REQUIRE_ORDER",
                condition="sequence_check",
                action="REQUIRE_SEQUENCE",
                confidence=0.8,
                source=conversation,
            )

        return None

    def _create_rule(
        self, rule_type: str, condition: str, action: str, confidence: float, source: str
    ) -> ExtractedRule:
        """Create rule object"""
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
        """Save rule to file"""
        self.rules.append(rule)
        with open(self.rules_file, "a", encoding="utf-8") as f:
            f.write(f"\n## {rule.id}\n")
            f.write(f"- Type: {rule.rule_type}\n")
            f.write(f"- Condition: {rule.condition}\n")
            f.write(f"- Action: {rule.action}\n")
            f.write(f"- Confidence: {rule.confidence:.2f}\n")
            f.write(f"- Source: {rule.source}\n")

    def _load_rules(self):
        """Load rules from file (simplified)"""
        if not self.rules_file.exists():
            return
        # Simplified implementation: no parsing yet

    def check_before_operation(self, operation: str, context: Dict) -> Tuple[bool, str]:
        """Check all applicable rules before operation"""
        for rule in self.rules:
            if rule.rule_type == "FORBIDDEN_PATH":
                path = context.get("path", "")
                if "starts with" in rule.condition:
                    required_path = rule.condition.split("'")[1]
                    if not path.startswith(required_path):
                        return False, f"Path must be under {required_path}"

            elif rule.rule_type == "FORBIDDEN_TOOL":
                tool = context.get("tool", "")
                if "==" in rule.condition:
                    forbidden_tool = rule.condition.split("'")[1]
                    if tool == forbidden_tool:
                        return False, f"Forbidden tool: {forbidden_tool}"

        return True, "All rules check passed"

    def get_statistics(self) -> Dict:
        """Get rule statistics"""
        stats = {
            "total_rules": len(self.rules),
            "by_type": {},
            "total_applied": sum(r.applied_count for r in self.rules),
        }
        for rule in self.rules:
            rule_type = rule.rule_type
            stats["by_type"][rule_type] = stats["by_type"].get(rule_type, 0) + 1
        return stats


if __name__ == "__main__":
    workspace = "~/.openclaw/workspace"
    extractor = RuleExtractor(workspace)

    print("Testing F101 automatic rule extraction\n")

    # Test 1
    print("Test 1: Extract forbidden path rule")
    rule = extractor.extract("don't create files to ~/.openclaw/workspace/")
    if rule:
        print(f"  ✅ Extracted: {rule.rule_type} - {rule.condition}")
    else:
        print(f"  ❌ Extraction failed")

    # Test 2
    print("\nTest 2: Extract preference rule")
    rule = extractor.extract("I prefer to use Chinese")
    if rule:
        print(f"  ✅ Extracted: {rule.rule_type} - {rule.condition}")
    else:
        print(f"  ❌ Extraction failed")

    # Test 3
    print("\nTest 3: Pre-operation rule check")
    allowed, msg = extractor.check_before_operation(
        "file_write", {"path": "/Users/liantian/workspace/test.md"}
    )
    print(f"  Allowed: {allowed}, message: {msg}")

    # Test 4
    print("\nTest 4: Rule statistics")
    stats = extractor.get_statistics()
    print(f"  Total rules: {stats['total_rules']}")
    print(f"  By type: {stats['by_type']}")
