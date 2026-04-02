"""
Configurable Rule Engine v1.0.4

Allows users to define custom validation rules via YAML/JSON configuration.
Supports hot-reload of configuration.

License: Apache-2.0
Documentation Standard: 100% English (Apache International Open Source Standard)
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Rule:
    """Represents a validation rule"""
    name: str
    rule_type: str
    patterns: List[str]
    message: str
    severity: str


class RuleEngine:
    """Configurable rule engine for validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize rule engine with default config path"""
        self.rules: List[Rule] = []
        
        # Default config path (deployed location)
        if config_path is None:
            config_path = str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'config' / 'rules.json')
        
        # Create directory if not exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.config_path = config_path
        self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load rules from configuration file"""
        path = Path(config_path)
        
        if not path.exists():
            self._create_default_config(path)
            return
        
        with open(path, 'r') as f:
            config = json.load(f)
        
        self.rules = []
        for rule_config in config.get('rules', []):
            rule = Rule(
                name=rule_config['name'],
                rule_type=rule_config['type'],
                patterns=rule_config.get('patterns', []),
                message=rule_config.get('message', 'Rule violation detected'),
                severity=rule_config.get('severity', 'error')
            )
            self.rules.append(rule)
    
    def _create_default_config(self, path: Path):
        """Create default configuration file"""
        default_config = {
            'rules': [
                {
                    'name': 'package_name_validation',
                    'type': 'forbidden_words',
                    'patterns': ['neorl', 'neomind', 'neo-rl', 'neo_rl'],
                    'message': 'Invalid package name detected',
                    'severity': 'error'
                },
                {
                    'name': 'documentation_language',
                    'type': 'forbidden_words',
                    'patterns': ['中文', '汉语', 'chinese'],
                    'message': 'Documentation must be 100% English',
                    'severity': 'critical'
                },
                {
                    'name': 'release_title_format',
                    'type': 'regex',
                    'patterns': ['^[a-z][a-z0-9_-]*\\s+v\\d+\\.\\d+\\.\\d+$'],
                    'message': 'Release title must be: {project} v{version}',
                    'severity': 'error'
                }
            ]
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        self.load_config(str(path))
    
    def validate(self, text: str) -> List[Dict[str, Any]]:
        """Validate text against all rules"""
        violations = []
        
        for rule in self.rules:
            if rule.rule_type == 'forbidden_words':
                for pattern in rule.patterns:
                    if pattern.lower() in text.lower():
                        violations.append({
                            'rule': rule.name,
                            'type': rule.rule_type,
                            'pattern': pattern,
                            'message': rule.message,
                            'severity': rule.severity
                        })
            
            elif rule.rule_type == 'regex':
                for pattern in rule.patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        violations.append({
                            'rule': rule.name,
                            'type': rule.rule_type,
                            'pattern': pattern,
                            'message': rule.message,
                            'severity': rule.severity
                        })
        
        return violations
    
    def reload_config(self):
        """Reload configuration (hot-reload)"""
        if self.config_path:
            self.load_config(self.config_path)
