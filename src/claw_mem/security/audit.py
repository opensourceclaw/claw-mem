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
Audit Logger (MVP Version)

Records all memory operations for auditing and debugging.
"""

import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path


class AuditLogger:
    """
    Audit Logger
    
    MVP version logs to file. Log rotation and analysis will be added in future iterations.
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize Audit Logger
        
        Args:
            workspace: Workspace path
        """
        self.workspace = workspace
        self.log_file = workspace / ".audit_log.jsonl"
    
    def log(self, action: str, details: Dict) -> None:
        """
        Log audit entry
        
        Args:
            action: Action type
            details: Action details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        # Append to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def get_logs(self, action_filter: Optional[str] = None, 
                 limit: int = 100) -> list:
        """
        Get audit logs
        
        Args:
            action_filter: Action type filter
            limit: Number of results
            
        Returns:
            list: Log entries
        """
        logs = []
        
        if not self.log_file.exists():
            return logs
        
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    if action_filter is None or log_entry.get("action") == action_filter:
                        logs.append(log_entry)
                        if len(logs) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        
        return logs
    
    def clear(self) -> None:
        """
        Clear audit logs
        """
        if self.log_file.exists():
            self.log_file.unlink()
