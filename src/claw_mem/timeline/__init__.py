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
Timeline Module

Provides life timeline navigation for claw-mem.

Key Features:
- Life events by year/month/day
- Milestone detection
- Decision tracking
- "First time" events
- Emotion-based search
- Event importance scoring
"""

from .timeline import Timeline, TimelineEvent, TimelineQuery, EventType
from .milestone import MilestoneDetector, MilestoneType
from .decision import DecisionTracker, Decision, DecisionType, DecisionStatus
from .firsts import FirstEventsDetector, FirstEvent, FirstEventType
from .event_importance import EventImportanceScorer, EventImportanceScore, ImportanceFactor

__all__ = [
    # Timeline
    "Timeline",
    "TimelineEvent",
    "TimelineQuery",
    "EventType",
    # Milestone
    "MilestoneDetector",
    "MilestoneType",
    # Decision
    "DecisionTracker",
    "Decision",
    "DecisionType",
    "DecisionStatus",
    # Firsts
    "FirstEventsDetector",
    "FirstEvent",
    "FirstEventType",
    # Event Importance
    "EventImportanceScorer",
    "EventImportanceScore",
    "ImportanceFactor",
]
