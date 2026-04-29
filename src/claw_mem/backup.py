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
claw-mem Backup and Restore System

Provides one-click backup and restore functionality for memory data.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from zipfile import ZipFile, ZIP_DEFLATED


class BackupManager:
    """Backup and Recovery Manager"""
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace).expanduser()
        self.backup_dir = self.workspace / ".claw-mem" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup(self, output_path: Optional[str] = None, incremental: bool = False) -> Dict[str, Any]:
        """Create backup"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_type = "incremental" if incremental else "full"
            output_path = self.backup_dir / f"backup_{backup_type}_{timestamp}.zip"
        else:
            output_path = Path(output_path)
        
        output_path = output_path.expanduser().resolve()
        files_to_backup = self._collect_files()
        
        backup_info = {
            "version": "0.8.0",
            "timestamp": datetime.now().isoformat(),
            "type": "incremental" if incremental else "full",
            "workspace": str(self.workspace),
            "files": [str(f.relative_to(self.workspace.parent)) for f in files_to_backup if f.exists()],
        }
        
        with ZipFile(output_path, 'w', compression=ZIP_DEFLATED) as zipf:
            for file_path in files_to_backup:
                if file_path.exists():
                    arcname = file_path.relative_to(self.workspace.parent)
                    zipf.write(file_path, arcname)
            zipf.writestr("backup_info.json", json.dumps(backup_info, indent=2))
        
        return {
            "success": True,
            "path": str(output_path),
            "size": output_path.stat().st_size,
            "files_count": len(files_to_backup),
            "timestamp": backup_info["timestamp"],
        }
    
    def restore(self, backup_path: str, verify_first: bool = True) -> Dict[str, Any]:
        """Restore from backup"""
        backup_path = Path(backup_path).expanduser().resolve()
        
        if not backup_path.exists():
            return {"success": False, "error": f"Backup file does not exist:{backup_path}"}
        
        if verify_first:
            verify_result = self.verify(backup_path)
            if not verify_result["valid"]:
                return {"success": False, "error": f"Backup verification failed:{verify_result.get('error', 'Unknown')}"}
        
        restored_files = []
        with ZipFile(backup_path, 'r') as zipf:
            backup_info = json.loads(zipf.read("backup_info.json"))
            for item in zipf.namelist():
                if item == "backup_info.json":
                    continue
                zipf.extract(item, self.workspace.parent)
                restored_files.append(item)
        
        return {
            "success": True,
            "restored_files": len(restored_files),
            "backup_timestamp": backup_info.get("timestamp", "Unknown"),
            "backup_type": backup_info.get("type", "Unknown"),
        }
    
    def verify(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup file"""
        backup_path = Path(backup_path).expanduser().resolve()
        
        if not backup_path.exists():
            return {"valid": False, "error": "Backup file does not exist"}
        
        try:
            with ZipFile(backup_path, 'r') as zipf:
                if "backup_info.json" not in zipf.namelist():
                    return {"valid": False, "error": "Missing backup info"}
                backup_info = json.loads(zipf.read("backup_info.json"))
            return {"valid": True, "backup_info": backup_info}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def list_backups(self) -> list:
        """List all backups"""
        if not self.backup_dir.exists():
            return []
        
        backups = []
        for file in self.backup_dir.glob("backup_*.zip"):
            backup_info = self.verify(str(file))
            backups.append({
                "path": str(file),
                "size": file.stat().st_size,
                "timestamp": backup_info.get("backup_info", {}).get("timestamp", "Unknown"),
                "type": backup_info.get("backup_info", {}).get("type", "Unknown"),
                "valid": backup_info.get("valid", False),
            })
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    def _collect_files(self) -> list:
        """Collect files to backup"""
        files = []
        memory_files = [self.workspace / "MEMORY.md", self.workspace / "memory"]
        
        for file_path in memory_files:
            if file_path.exists():
                if file_path.is_file():
                    files.append(file_path)
                elif file_path.is_dir():
                    files.extend(file_path.glob("**/*.md"))
        return files


# CLI Commands
def backup_command(workspace: str, output: Optional[str] = None, incremental: bool = False):
    manager = BackupManager(workspace)
    result = manager.backup(output_path=output, incremental=incremental)
    if result["success"]:
        print("✅ Backup successful!")
        print(f"   Path: {result['path']}")
        print(f"   Size: {result['size'] / 1024:.1f} KB")
        print(f"   Files: {result['files_count']}")


def restore_command(workspace: str, backup_path: str):
    manager = BackupManager(workspace)
    result = manager.restore(backup_path)
    if result["success"]:
        print("✅ Restore successful!")
        print(f"   Restored files: {result['restored_files']}")
        print(f"   backup时间:{result['backup_timestamp']}")
    else:
        print(f"❌ restore失败:{result.get('error')}")


def list_command(workspace: str):
    manager = BackupManager(workspace)
    backups = manager.list_backups()
    if not backups:
        print("暂无backup")
        return
    print(f"找到 {len(backups)} 个backup:\n")
    print(f"{'时间':<25} {'类型':<12} {'大小':<10} {'状态':<8} 路径")
    print("-" * 100)
    for backup in backups[:5]:
        status = "✅ 有效" if backup["valid"] else "❌ 损坏"
        print(f"{backup['timestamp']:<25} {backup['type']:<12} {backup['size']/1024:<10.1f} KB {status:<8} {backup['path']}")


if __name__ == "__main__":
    workspace = "~/.openclaw/workspace"
    manager = BackupManager(workspace)
    
    print("创建backup...")
    result = manager.backup()
    if result["success"]:
        print(f"✅ {result['path']}")
    
    print("\n列出backup...")
    list_command(workspace)
