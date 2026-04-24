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
Feedback Handler - 反馈处理机制
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from claw_mem.values import UserValueStore


class FeedbackStatus(Enum):
    """反馈状态"""
    PENDING = "pending"       # 待确认
    ACCEPTED = "accepted"     # 已接受
    REJECTED = "rejected"     # 已拒绝
    EXPIRED = "expired"       # 已过期


@dataclass
class ValueSuggestion:
    """价值观建议"""
    id: str
    user_id: str
    suggestion_type: str  # "principle", "preference", "red_line"
    content: str
    evidence: List[str] = field(default_factory=list)
    status: FeedbackStatus = FeedbackStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "suggestion_type": self.suggestion_type,
            "content": self.content,
            "evidence": self.evidence,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
        }


class FeedbackHandler:
    """反馈处理器 - 管理用户对价值观的确认"""

    def __init__(self, value_store: Optional[UserValueStore] = None):
        """初始化反馈处理器

        Args:
            value_store: 用户价值观存储
        """
        self.value_store = value_store or UserValueStore()

        # 待确认的建议
        self._pending_suggestions: Dict[str, List[ValueSuggestion]] = {}

        # 历史建议
        self._suggestion_history: List[ValueSuggestion] = []

    def request_confirmation(self, user_id: str, value_type: str, content: str, evidence: List[str] = None) -> ValueSuggestion:
        """请求用户确认价值观

        Args:
            user_id: 用户 ID
            value_type: 价值观类型 ("principle", "preference", "red_line")
            content: 价值观内容
            evidence: 证据列表

        Returns:
            ValueSuggestion: 创建的建议
        """
        import uuid

        suggestion = ValueSuggestion(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            suggestion_type=value_type,
            content=content,
            evidence=evidence or []
        )

        # 添加到待确认列表
        if user_id not in self._pending_suggestions:
            self._pending_suggestions[user_id] = []

        self._pending_suggestions[user_id].append(suggestion)
        self._suggestion_history.append(suggestion)

        return suggestion

    def process_feedback(self, suggestion_id: str, accepted: bool) -> bool:
        """处理用户反馈

        Args:
            suggestion_id: 建议 ID
            accepted: 是否接受

        Returns:
            bool: 是否成功处理
        """
        # 查找建议
        suggestion = None
        for s in self._suggestion_history:
            if s.id == suggestion_id:
                suggestion = s
                break

        if not suggestion:
            return False

        # 更新状态
        suggestion.status = FeedbackStatus.ACCEPTED if accepted else FeedbackStatus.REJECTED
        suggestion.responded_at = datetime.now(timezone.utc)

        # 如果接受，更新到价值观存储
        if accepted:
            user_id = suggestion.user_id

            if suggestion.suggestion_type == "principle":
                self.value_store.save_principle(user_id, suggestion.content)

            elif suggestion.suggestion_type == "preference":
                # 偏好需要解析 key-value
                # 简化：假设 content 格式为 "key:value"
                if ":" in suggestion.content:
                    key, value = suggestion.content.split(":", 1)
                    self.value_store.save_preference(user_id, key.strip(), value.strip())

            elif suggestion.suggestion_type == "red_line":
                self.value_store.save_red_line(user_id, suggestion.content)

        # 从待确认列表中移除
        user_id = suggestion.user_id
        if user_id in self._pending_suggestions:
            self._pending_suggestions[user_id] = [
                s for s in self._pending_suggestions[user_id]
                if s.id != suggestion_id
            ]

        return True

    def suggest_update(self, suggestion: Dict[str, Any]) -> ValueSuggestion:
        """建议更新价值观

        Args:
            suggestion: 建议数据

        Returns:
            ValueSuggestion: 创建的建议
        """
        return self.request_confirmation(
            user_id=suggestion["user_id"],
            value_type=suggestion.get("type", "principle"),
            content=suggestion["content"],
            evidence=suggestion.get("evidence", [])
        )

    def get_pending_suggestions(self, user_id: str) -> List[ValueSuggestion]:
        """获取待确认的建议

        Args:
            user_id: 用户 ID

        Returns:
            List[ValueSuggestion]: 待确认的建议列表
        """
        return self._pending_suggestions.get(user_id, [])

    def get_accepted_suggestions(self, user_id: str) -> List[ValueSuggestion]:
        """获取已接受的建议

        Args:
            user_id: 用户 ID

        Returns:
            List[ValueSuggestion]: 已接受的建议列表
        """
        return [
            s for s in self._suggestion_history
            if s.user_id == user_id and s.status == FeedbackStatus.ACCEPTED
        ]

    def get_rejected_suggestions(self, user_id: str) -> List[ValueSuggestion]:
        """获取已拒绝的建议

        Args:
            user_id: 用户 ID

        Returns:
            List[ValueSuggestion]: 已拒绝的建议列表
        """
        return [
            s for s in self._suggestion_history
            if s.user_id == user_id and s.status == FeedbackStatus.REJECTED
        ]

    def clear_expired(self, max_age_hours: int = 24) -> int:
        """清除过期的建议

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            int: 清除的数量
        """
        now = datetime.now(timezone.utc)
        expired = []

        for suggestion in self._suggestion_history:
            if suggestion.status == FeedbackStatus.PENDING:
                age = (now - suggestion.created_at).total_seconds() / 3600
                if age > max_age_hours:
                    suggestion.status = FeedbackStatus.EXPIRED
                    suggestion.responded_at = now
                    expired.append(suggestion)

        return len(expired)


__all__ = [
    "FeedbackStatus",
    "ValueSuggestion",
    "FeedbackHandler",
]
