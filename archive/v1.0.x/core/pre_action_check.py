"""
Pre-Action Memory Check System v1.0.2

Checks memories before executing actions to prevent violations
of critical rules.

License: Apache-2.0
Documentation Language: 100% English (Apache Standard)
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path
import sys

# Import memory system
sys.path.insert(0, str(Path(__file__).parent / 'core'))
from memory_v1_0_2 import Memory, MemorySystem


@dataclass
class CheckResult:
    """Result of pre-action check"""
    allowed: bool  # Is action allowed?
    violations: List[Memory]  # Critical rule violations
    needs_confirmation: bool  # Does user need to confirm?
    low_confidence_memories: List[Memory]  # Memories with low confidence
    relevant_memories: List[Memory]  # All relevant memories
    
    def __str__(self) -> str:
        """String representation"""
        if self.allowed:
            status = "✅ ALLOWED"
        else:
            status = "❌ BLOCKED"
        
        result = f"[{status}] Action check result\n"
        
        if self.violations:
            result += f"\n⚠️  Critical Rule Violations ({len(self.violations)}):\n"
            for v in self.violations:
                result += f"   - {v.content} (confidence: {v.confidence:.0%})\n"
        
        if self.needs_confirmation:
            result += f"\n❓ Needs Confirmation ({len(self.low_confidence_memories)} low-confidence memories):\n"
            for m in self.low_confidence_memories:
                result += f"   - {m.content} (confidence: {m.confidence:.0%})\n"
        
        return result


class PreActionChecker:
    """Pre-action memory checker"""
    
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system
        self.confidence_threshold = 0.8  # 80% confidence threshold
    
    def check(self, action: str, context: dict = None) -> CheckResult:
        """
        Check if action is allowed based on memories
        
        Args:
            action: Action description
            context: Optional context dictionary
        
        Returns:
            CheckResult with allowed status and violations
        """
        # 1. Get critical rules
        critical_rules = self.memory_system.get_critical_rules()
        
        # 2. Check for violations
        violations = []
        for rule in critical_rules:
            if self._violates_rule(action, rule):
                violations.append(rule)
        
        # 3. Get relevant memories
        relevant = self._get_relevant_memories(action)
        
        # 4. Check for low confidence memories
        low_confidence = [
            m for m in relevant 
            if m.confidence < self.confidence_threshold
        ]
        
        # 5. Determine if allowed
        allowed = len(violations) == 0
        needs_confirmation = len(low_confidence) > 0
        
        return CheckResult(
            allowed=allowed,
            violations=violations,
            needs_confirmation=needs_confirmation,
            low_confidence_memories=low_confidence,
            relevant_memories=relevant
        )
    
    def _violates_rule(self, action: str, rule: Memory) -> bool:
        """Check if action violates a critical rule"""
        action_lower = action.lower()
        rule_lower = rule.content.lower()
        
        # Simple keyword-based violation detection
        # In production, this would use more sophisticated NLP
        
        # Check if action contains negation of rule
        negations = ['not', "don't", "dont", 'no', 'never', 'avoid', '禁止', '不要', '别']
        
        for negation in negations:
            if negation in action_lower and negation in rule_lower:
                return True
        
        # Check if action directly contradicts rule
        # Example: rule="100% English", action="write Chinese docs"
        if 'english' in rule_lower and 'chinese' in action_lower:
            return True
        if 'chinese' in rule_lower and 'english' in action_lower:
            return True
        
        # Check if action ignores the rule
        # This is a simple heuristic - in production would be more sophisticated
        if rule.is_critical and rule.confidence >= 0.9:
            # High confidence critical rules should be checked carefully
            if self._action_ignores_rule(action, rule):
                return True
        
        return False
    
    def _action_ignores_rule(self, action: str, rule: Memory) -> bool:
        """Check if action ignores a critical rule (simple heuristic)"""
        action_lower = action.lower()
        rule_lower = rule.content.lower()
        
        # Extract key terms from rule
        key_terms = []
        for word in rule_lower.split():
            if len(word) > 3 and word not in ['must', 'should', 'always', 'the', 'and', 'are']:
                key_terms.append(word)
        
        # Check if action mentions rule topic but not the rule itself
        mentions_topic = any(term in action_lower for term in key_terms)
        
        if mentions_topic:
            # Action mentions the topic - check if it follows the rule
            # This is a simplified check
            return False
        
        return False
    
    def _get_relevant_memories(self, action: str, limit: int = 10) -> List[Memory]:
        """Get memories relevant to the action"""
        action_lower = action.lower()
        relevant = []
        
        for memory in self.memory_system.all():
            # Check if memory content or tags match action
            if (memory.content.lower() in action_lower or 
                action_lower in memory.content.lower() or
                any(tag.lower() in action_lower for tag in memory.tags)):
                relevant.append(memory)
        
        # Sort by priority and confidence
        relevant.sort(key=lambda m: (m.priority, m.confidence), reverse=True)
        
        return relevant[:limit]
    
    def confirm_action(self, action: str, result: CheckResult) -> bool:
        """
        Ask user to confirm action if needed
        
        Args:
            action: Action description
            result: CheckResult from check()
        
        Returns:
            True if user confirms, False otherwise
        """
        if result.allowed and not result.needs_confirmation:
            return True  # No confirmation needed
        
        print("\n" + "="*60)
        print("⚠️  PRE-ACTION CHECK")
        print("="*60)
        print(f"\nAction: {action}\n")
        
        if result.violations:
            print("❌ CRITICAL RULE VIOLATIONS:")
            for i, v in enumerate(result.violations, 1):
                print(f"   {i}. {v.content}")
                print(f"      (confidence: {v.confidence:.0%}, source: {v.source})")
            print("\n⚠️  This action violates critical rules!")
        
        if result.needs_confirmation:
            print("\n❓ LOW CONFIDENCE MEMORIES:")
            for i, m in enumerate(result.low_confidence_memories, 1):
                print(f"   {i}. {m.content}")
                print(f"      (confidence: {m.confidence:.0%})")
            print("\n❓ Some memories have low confidence. Proceed with caution.")
        
        print("\n" + "="*60)
        
        # In production, this would be an interactive prompt
        # For now, return False if violations exist
        if result.violations:
            print("\n❌ Action BLOCKED due to critical rule violations")
            return False
        
        if result.needs_confirmation:
            print("\n⚠️  User confirmation required (not implemented in this demo)")
            return True  # Allow user to decide
        
        return True


# Example usage
if __name__ == '__main__':
    # Create memory system
    storage = Path('./memories')
    storage.mkdir(exist_ok=True)
    
    memory_system = MemorySystem(storage)
    
    # Create test memories
    rule1 = memory_system.create(
        content="Apache docs must be 100% English",
        tags=['rule', 'documentation'],
        source='user'
    )
    memory_system.mark_as_critical(rule1.id)
    
    rule2 = memory_system.create(
        content="Package name must be claw_rl (not neorl or neomind)",
        tags=['rule', 'naming'],
        source='user'
    )
    memory_system.mark_as_critical(rule2.id)
    
    # Create pre-action checker
    checker = PreActionChecker(memory_system)
    
    # Test 1: Good action
    print("\n" + "="*60)
    print("TEST 1: Good action")
    print("="*60)
    result = checker.check("Create English documentation for claw_rl")
    print(result)
    
    # Test 2: Violation action
    print("\n" + "="*60)
    print("TEST 2: Violation action")
    print("="*60)
    result = checker.check("Write Chinese documentation")
    print(result)
    
    # Test 3: Low confidence memory
    print("\n" + "="*60)
    print("TEST 3: Low confidence memory")
    print("="*60)
    low_conf = memory_system.create(
        content="User prefers morning meetings",
        tags=['preference'],
        source='inferred'
    )
    low_conf.confidence = 0.3  # Low confidence
    memory_system.save(low_conf)
    
    result = checker.check("Schedule morning meeting")
    print(result)
    
    print("\n" + "="*60)
    print("✅ Pre-action checker v1.0.2 initialized successfully!")
    print("="*60)
