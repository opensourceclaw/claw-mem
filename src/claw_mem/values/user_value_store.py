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
User Value Store - uservaluesstorage
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
from pathlib import Path


@dataclass
class UserValue:
    """uservalues数据结构"""
    user_id: str
    principles: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    red_lines: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """convert为字典"""
        return {
            "user_id": self.user_id,
            "principles": self.principles,
            "preferences": self.preferences,
            "red_lines": self.red_lines,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserValue":
        """从字典创建"""
        return cls(
            user_id=data["user_id"],
            principles=data.get("principles", []),
            preferences=data.get("preferences", {}),
            red_lines=data.get("red_lines", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(timezone.utc),
        )


class UserValueStore:
    """uservaluesstorage"""

    def __init__(self, storage_path: Optional[Path] = None):
        """initializestorage

        Args:
            storage_path: storage路径，默认 ~/.claw_mem/values/
        """
        if storage_path is None:
            storage_path = Path.home() / ".claw_mem" / "values"

        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._cache: Dict[str, UserValue] = {}

    def _get_user_file(self, user_id: str) -> Path:
        """getuser数据文件路径"""
        # Sanitize user_id for filesystem
        safe_id = user_id.replace("/", "_").replace("\\", "_")
        return self.storage_path / f"{safe_id}.json"

    def save_principle(self, user_id: str, principle: str) -> UserValue:
        """save核心原则

        Args:
            user_id: user ID
            principle: 原则内容

        Returns:
            UserValue: update后的uservalues
        """
        user_values = self._get_or_create_user(user_id)

        if principle not in user_values.principles:
            user_values.principles.append(principle)
            user_values.updated_at = datetime.now(timezone.utc)
            self._save_user(user_values)

        return user_values

    def save_preference(self, user_id: str, key: str, value: Any) -> UserValue:
        """saveuserpreference

        Args:
            user_id: user ID
            key: preference键
            value: preference值

        Returns:
            UserValue: update后的uservalues
        """
        user_values = self._get_or_create_user(user_id)

        user_values.preferences[key] = value
        user_values.updated_at = datetime.now(timezone.utc)
        self._save_user(user_values)

        return user_values

    def save_red_line(self, user_id: str, line: str) -> UserValue:
        """save红线

        Args:
            user_id: user ID
            line: 红线内容

        Returns:
            UserValue: update后的uservalues
        """
        user_values = self._get_or_create_user(user_id)

        if line not in user_values.red_lines:
            user_values.red_lines.append(line)
            user_values.updated_at = datetime.now(timezone.utc)
            self._save_user(user_values)

        return user_values

    def get_user_values(self, user_id: str) -> Optional[UserValue]:
        """getuservalues

        Args:
            user_id: user ID

        Returns:
            Optional[UserValue]: uservalues，if不存在返回 None
        """
        if user_id in self._cache:
            return self._cache[user_id]

        user_file = self._get_user_file(user_id)
        if user_file.exists():
            try:
                data = json.loads(user_file.read_text(encoding="utf-8"))
                user_values = UserValue.from_dict(data)
                self._cache[user_id] = user_values
                return user_values
            except (json.JSONDecodeError, KeyError):
                return None

        return None

    def delete_principle(self, user_id: str, principle: str) -> Optional[UserValue]:
        """delete核心原则

        Args:
            user_id: user ID
            principle: 原则内容

        Returns:
            Optional[UserValue]: update后的uservalues
        """
        user_values = self.get_user_values(user_id)
        if not user_values:
            return None

        if principle in user_values.principles:
            user_values.principles.remove(principle)
            user_values.updated_at = datetime.now(timezone.utc)
            self._save_user(user_values)

        return user_values

    def delete_red_line(self, user_id: str, line: str) -> Optional[UserValue]:
        """delete红线

        Args:
            user_id: user ID
            line: 红线内容

        Returns:
            Optional[UserValue]: update后的uservalues
        """
        user_values = self.get_user_values(user_id)
        if not user_values:
            return None

        if line in user_values.red_lines:
            user_values.red_lines.remove(line)
            user_values.updated_at = datetime.now(timezone.utc)
            self._save_user(user_values)

        return user_values

    def delete_preference(self, user_id: str, key: str) -> Optional[UserValue]:
        """deletepreference

        Args:
            user_id: user ID
            key: preference键

        Returns:
            Optional[UserValue]: update后的uservalues
        """
        user_values = self.get_user_values(user_id)
        if not user_values:
            return None

        if key in user_values.preferences:
            del user_values.preferences[key]
            user_values.updated_at = datetime.now(timezone.utc)
            self._save_user(user_values)

        return user_values

    def list_users(self) -> List[str]:
        """列出所有user ID

        Returns:
            List[str]: user ID 列表
        """
        users = []
        for f in self.storage_path.glob("*.json"):
            user_id = f.stem.replace("_", "/")
            users.append(user_id)
        return users

    def _get_or_create_user(self, user_id: str) -> UserValue:
        """get或创建uservalues"""
        user_values = self.get_user_values(user_id)
        if user_values is None:
            user_values = UserValue(user_id=user_id)
            self._cache[user_id] = user_values
        return user_values

    def _save_user(self, user_values: UserValue) -> None:
        """saveuservalues到文件"""
        user_file = self._get_user_file(user_values.user_id)
        user_file.write_text(
            json.dumps(user_values.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        self._cache[user_values.user_id] = user_values


__all__ = ["UserValue", "UserValueStore"]
