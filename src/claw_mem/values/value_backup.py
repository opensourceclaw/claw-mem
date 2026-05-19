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
Value Backup - Values local storage
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from claw_mem.values import UserValueStore


@dataclass
class BackupMetadata:
    """Backup metadata"""

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
    """Values backup manager"""

    def __init__(
        self, value_store: Optional[UserValueStore] = None, backup_dir: Optional[Path] = None
    ):
        """Initialize backup manager

        Args:
            value_store: User values storage
            backup_dir: Backup directory, default ~/.claw_mem/backups/
        """
        self.value_store = value_store or UserValueStore()

        if backup_dir is None:
            backup_dir = Path.home() / ".claw_mem" / "backups"

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file
        self.metadata_file = self.backup_dir / "metadata.json"

    def export_values(self, user_id: str, path: Optional[Path] = None) -> BackupMetadata:
        """Export user values to file

        Args:
            user_id: User ID
            path: Export path, auto-generated if None

        Returns:
            BackupMetadata: Backup metadata
        """
        # Get user values
        user_values = self.value_store.get_user_values(user_id)
        if not user_values:
            raise ValueError(f"User {user_id} not found")

        # Generate backup ID and path
        import uuid

        backup_id = str(uuid.uuid4())[:8]

        if path is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            path = self.backup_dir / f"{user_id}_{timestamp}.json"

        # Export data
        export_data = {
            "user_id": user_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "version": "2.2.0",
            "values": user_values.to_dict(),
        }

        # Write file
        path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Calculate simple checksum
        checksum = str(abs(hash(str(export_data))))[:16]

        # Create metadata
        metadata = BackupMetadata(
            user_id=user_id,
            backup_id=backup_id,
            created_at=datetime.now(timezone.utc),
            file_path=str(path),
            file_size=path.stat().st_size,
            values_count=len(user_values.principles)
            + len(user_values.preferences)
            + len(user_values.red_lines),
            checksum=checksum,
        )

        # Save metadata
        self._save_metadata(metadata)

        return metadata

    def import_values(self, user_id: str, path: Path, overwrite: bool = False) -> bool:
        """Import user values from file

        Args:
            user_id: User ID
            path: Import file path
            overwrite: Whether to overwrite existing data

        Returns:
            bool: Whether import was successful
        """
        # Read file
        if not path.exists():
            raise FileNotFoundError(f"Backup file not found: {path}")

        content = path.read_text(encoding="utf-8")
        data = json.loads(content)

        if "values" not in data:
            raise ValueError("Invalid backup file format")

        imported_values = data["values"]

        # Check user ID match
        if imported_values.get("user_id") != user_id:
            # Allow importing values from different user (creates new user)
            pass

        # Get existing values
        existing = self.value_store.get_user_values(user_id)

        if existing and not overwrite:
            raise ValueError(f"User {user_id} already exists. Use overwrite=True to replace.")

        # Import principles
        for principle in imported_values.get("principles", []):
            self.value_store.save_principle(user_id, principle)

        # Import preferences
        for key, value in imported_values.get("preferences", {}).items():
            self.value_store.save_preference(user_id, key, value)

        # Import red lines
        for line in imported_values.get("red_lines", []):
            self.value_store.save_red_line(user_id, line)

        return True

    def list_backups(self, user_id: Optional[str] = None) -> List[BackupMetadata]:
        """List backup files

        Args:
            user_id: User ID, or None to list all users' backups

        Returns:
            List[BackupMetadata]: List of backup metadata
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

        # Sort by time
        metadata_list.sort(key=lambda m: m.created_at, reverse=True)

        return metadata_list

    def backup_metadata(self, user_id: str) -> Dict[str, Any]:
        """Get user backup metadata

        Args:
            user_id: User ID

        Returns:
            Dict: Metadata summary
        """
        backups = self.list_backups(user_id)

        if not backups:
            return {"user_id": user_id, "backup_count": 0, "latest_backup": None, "total_size": 0}

        return {
            "user_id": user_id,
            "backup_count": len(backups),
            "latest_backup": backups[0].to_dict() if backups else None,
            "total_size": sum(b.file_size for b in backups),
        }

    def delete_backup(self, backup_id: str) -> bool:
        """Delete backup

        Args:
            backup_id: Backup ID

        Returns:
            bool: Whether deletion was successful
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

        # Delete file
        if file_path.exists():
            file_path.unlink()

        # Delete metadata
        del all_metadata[backup_id]
        self.metadata_file.write_text(json.dumps(all_metadata, indent=2), encoding="utf-8")

        return True

    def _save_metadata(self, metadata: BackupMetadata) -> None:
        """Save backup metadata"""
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
