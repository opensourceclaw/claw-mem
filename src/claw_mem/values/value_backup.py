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
Value Backup - values本地storage
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from claw_mem.values import UserValueStore, UserValue


@dataclass
class BackupMetadata:
    """backup元数据"""
    user_id: str
    backup_id: str
    created_at: datetime
    file_path: str
    file_size: int
    values_count: int
    checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "backup_id": self.backup_id,
            "created_at": self.created_at.isoformat(),
            "file_path": self.file_path,
            "file_size": self.file_size,
            "values_count": self.values_count,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupMetadata":
        return cls(
            user_id=data["user_id"],
            backup_id=data["backup_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            file_path=data["file_path"],
            file_size=data["file_size"],
            values_count=data["values_count"],
            checksum=data.get("checksum", ""),
        )


class ValueBackup:
    """valuesbackup管理器"""

    def __init__(self, value_store: Optional[UserValueStore] = None, backup_dir: Optional[Path] = None):
        """initializebackup管理器

        Args:
            value_store: uservaluesstorage
            backup_dir: backup目录，默认 ~/.claw_mem/backups/
        """
        self.value_store = value_store or UserValueStore()

        if backup_dir is None:
            backup_dir = Path.home() / ".claw_mem" / "backups"

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 元数据文件
        self.metadata_file = self.backup_dir / "metadata.json"

    def export_values(self, user_id: str, path: Optional[Path] = None) -> BackupMetadata:
        """exportuservalues到文件

        Args:
            user_id: user ID
            path: export路径，if为 None 则自动生成

        Returns:
            BackupMetadata: backup元数据
        """
        # getuservalues
        user_values = self.value_store.get_user_values(user_id)
        if not user_values:
            raise ValueError(f"User {user_id} not found")

        # 生成backup ID 和路径
        import uuid
        backup_id = str(uuid.uuid4())[:8]

        if path is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            path = self.backup_dir / f"{user_id}_{timestamp}.json"

        # export数据
        export_data = {
            "user_id": user_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "version": "2.2.0",
            "values": user_values.to_dict()
        }

        # 写入文件
        path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 计算简单 checksum
        checksum = str(abs(hash(str(export_data))))[:16]

        # 创建元数据
        metadata = BackupMetadata(
            user_id=user_id,
            backup_id=backup_id,
            created_at=datetime.now(timezone.utc),
            file_path=str(path),
            file_size=path.stat().st_size,
            values_count=len(user_values.principles) + len(user_values.preferences) + len(user_values.red_lines),
            checksum=checksum
        )

        # save元数据
        self._save_metadata(metadata)

        return metadata

    def import_values(self, user_id: str, path: Path, overwrite: bool = False) -> bool:
        """从文件importuservalues

        Args:
            user_id: user ID
            path: import文件路径
            overwrite: 是否覆盖现有数据

        Returns:
            bool: 是否成功import
        """
        # 读取文件
        if not path.exists():
            raise FileNotFoundError(f"Backup file not found: {path}")

        content = path.read_text(encoding="utf-8")
        data = json.loads(content)

        if "values" not in data:
            raise ValueError("Invalid backup file format")

        imported_values = data["values"]

        # checkuserID匹配
        if imported_values.get("user_id") != user_id:
            # 允许import不同user的values（创建新user）
            pass

        # get现有values
        existing = self.value_store.get_user_values(user_id)

        if existing and not overwrite:
            raise ValueError(f"User {user_id} already exists. Use overwrite=True to replace.")

        # import原则
        for principle in imported_values.get("principles", []):
            self.value_store.save_principle(user_id, principle)

        # importpreference
        for key, value in imported_values.get("preferences", {}).items():
            self.value_store.save_preference(user_id, key, value)

        # import红线
        for line in imported_values.get("red_lines", []):
            self.value_store.save_red_line(user_id, line)

        return True

    def list_backups(self, user_id: Optional[str] = None) -> List[BackupMetadata]:
        """列出backup文件

        Args:
            user_id: user ID，if为 None 则列出所有user的backup

        Returns:
            List[BackupMetadata]: backup元数据列表
        """
        metadata_list = []

        if self.metadata_file.exists():
            try:
                all_metadata = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                all_metadata = {}
        else:
            all_metadata = {}

        for backup_id, meta_data in all_metadata.items():
            if user_id is None or meta_data.get("user_id") == user_id:
                try:
                    metadata_list.append(BackupMetadata.from_dict(meta_data))
                except (KeyError, ValueError):
                    continue

        # 按时间排序
        metadata_list.sort(key=lambda m: m.created_at, reverse=True)

        return metadata_list

    def backup_metadata(self, user_id: str) -> Dict[str, Any]:
        """getuserbackup元数据

        Args:
            user_id: user ID

        Returns:
            Dict: 元数据汇总
        """
        backups = self.list_backups(user_id)

        if not backups:
            return {
                "user_id": user_id,
                "backup_count": 0,
                "latest_backup": None,
                "total_size": 0
            }

        return {
            "user_id": user_id,
            "backup_count": len(backups),
            "latest_backup": backups[0].to_dict() if backups else None,
            "total_size": sum(b.file_size for b in backups)
        }

    def delete_backup(self, backup_id: str) -> bool:
        """deletebackup

        Args:
            backup_id: backup ID

        Returns:
            bool: 是否成功delete
        """
        if self.metadata_file.exists():
            try:
                all_metadata = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return False
        else:
            return False

        if backup_id not in all_metadata:
            return False

        meta_data = all_metadata[backup_id]
        file_path = Path(meta_data["file_path"])

        # delete文件
        if file_path.exists():
            file_path.unlink()

        # delete元数据
        del all_metadata[backup_id]
        self.metadata_file.write_text(json.dumps(all_metadata, indent=2), encoding="utf-8")

        return True

    def _save_metadata(self, metadata: BackupMetadata) -> None:
        """savebackup元数据"""
        all_metadata = {}

        if self.metadata_file.exists():
            try:
                all_metadata = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        all_metadata[metadata.backup_id] = metadata.to_dict()

        self.metadata_file.write_text(json.dumps(all_metadata, indent=2), encoding="utf-8")


__all__ = [
    "BackupMetadata",
    "ValueBackup",
]
