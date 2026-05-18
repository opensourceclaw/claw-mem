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
Feedback Handler - Feedback processing mechanism
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from claw_mem.values import UserValueStore


class FeedbackStatus(Enum):
    """Feedback status"""

    PENDING = "pending"  # Pending
    ACCEPTED = "accepted"  # Accepted
    REJECTED = "rejected"  # Rejected
    EXPIRED = "expired"  # Expired


@dataclass
class ValueSuggestion:
    """Value suggestion"""

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
    """Feedback processor - Manages user confirmation of values"""

    def __init__(self, value_store: Optional[UserValueStore] = None):
        """Initialize feedback processor

        Args:
            value_store: User values storage
        """
        self.value_store = value_store or UserValueStore()

        # Pending suggestions
        self._pending_suggestions: Dict[str, List[ValueSuggestion]] = {}

        # Suggestion history
        self._suggestion_history: List[ValueSuggestion] = []

    def request_confirmation(
        self, user_id: str, value_type: str, content: str, evidence: List[str] = None
    ) -> ValueSuggestion:
        """Request user confirmation of values

        Args:
            user_id: User ID
            value_type: Value type ("principle", "preference", "red_line")
            content: Value content
            evidence: Evidence list

        Returns:
            ValueSuggestion: Created suggestion
        """
        import uuid

        suggestion = ValueSuggestion(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            suggestion_type=value_type,
            content=content,
            evidence=evidence or [],
        )

        # Add to pending list
        if user_id not in self._pending_suggestions:
            self._pending_suggestions[user_id] = []

        self._pending_suggestions[user_id].append(suggestion)
        self._suggestion_history.append(suggestion)

        return suggestion

    def process_feedback(self, suggestion_id: str, accepted: bool) -> bool:
        """Process user feedback

        Args:
            suggestion_id: Suggestion ID
            accepted: Whether accepted

        Returns:
            bool: Whether successfully processed
        """
        # Find suggestion
        suggestion = None
        for s in self._suggestion_history:
            if s.id == suggestion_id:
                suggestion = s
                break

        if not suggestion:
            return False

        # Update status
        suggestion.status = FeedbackStatus.ACCEPTED if accepted else FeedbackStatus.REJECTED
        suggestion.responded_at = datetime.now(timezone.utc)

        # If accepted, update to value store
        if accepted:
            user_id = suggestion.user_id

            if suggestion.suggestion_type == "principle":
                self.value_store.save_principle(user_id, suggestion.content)

            elif suggestion.suggestion_type == "preference":
                # Preference needs key-value parsing
                # Simplified: assume content format is "key:value"
                if ":" in suggestion.content:
                    key, value = suggestion.content.split(":", 1)
                    self.value_store.save_preference(user_id, key.strip(), value.strip())

            elif suggestion.suggestion_type == "red_line":
                self.value_store.save_red_line(user_id, suggestion.content)

        # Remove from pending list
        user_id = suggestion.user_id
        if user_id in self._pending_suggestions:
            self._pending_suggestions[user_id] = [
                s for s in self._pending_suggestions[user_id] if s.id != suggestion_id
            ]

        return True

    def suggest_update(self, suggestion: Dict[str, Any]) -> ValueSuggestion:
        """Suggest updating values

        Args:
            suggestion: Suggestion data

        Returns:
            ValueSuggestion: Created suggestion
        """
        return self.request_confirmation(
            user_id=suggestion["user_id"],
            value_type=suggestion.get("type", "principle"),
            content=suggestion["content"],
            evidence=suggestion.get("evidence", []),
        )

    def get_pending_suggestions(self, user_id: str) -> List[ValueSuggestion]:
        """Get pending suggestions

        Args:
            user_id: User ID

        Returns:
            List[ValueSuggestion]: List of pending suggestions
        """
        return self._pending_suggestions.get(user_id, [])

    def get_accepted_suggestions(self, user_id: str) -> List[ValueSuggestion]:
        """Get accepted suggestions

        Args:
            user_id: User ID

        Returns:
            List[ValueSuggestion]: List of accepted suggestions
        """
        return [
            s
            for s in self._suggestion_history
            if s.user_id == user_id and s.status == FeedbackStatus.ACCEPTED
        ]

    def get_rejected_suggestions(self, user_id: str) -> List[ValueSuggestion]:
        """Get rejected suggestions

        Args:
            user_id: User ID

        Returns:
            List[ValueSuggestion]: List of rejected suggestions
        """
        return [
            s
            for s in self._suggestion_history
            if s.user_id == user_id and s.status == FeedbackStatus.REJECTED
        ]

    def clear_expired(self, max_age_hours: int = 24) -> int:
        """Clear expired suggestions

        Args:
            max_age_hours: Max retention time (hours)

        Returns:
            int: Number of cleared entries
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
