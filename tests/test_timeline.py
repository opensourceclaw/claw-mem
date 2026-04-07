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
Tests for Timeline Module

Tests for life timeline navigation feature.
"""

import pytest
from datetime import datetime, date, timedelta
from pathlib import Path
import tempfile
import shutil

from claw_mem.timeline import (
    Timeline,
    TimelineEvent,
    TimelineQuery,
    EventType,
    MilestoneDetector,
    MilestoneType,
    DecisionTracker,
    Decision,
    DecisionType,
    DecisionStatus,
    FirstEventsDetector,
    FirstEvent,
    FirstEventType,
)


class TestTimelineEvent:
    """Tests for TimelineEvent"""
    
    def test_create_event(self):
        """Test creating a timeline event"""
        event = TimelineEvent(
            event_id="evt_001",
            title="Started new job",
            description="Started working at TechCorp as a software engineer",
            event_type=EventType.CAREER,
            timestamp=datetime(2026, 4, 7, 9, 0),
            importance=0.8,
            tags=["career", "tech"],
        )
        
        assert event.event_id == "evt_001"
        assert event.title == "Started new job"
        assert event.year == 2026
        assert event.month == 4
        assert event.day == 7
    
    def test_event_to_dict(self):
        """Test event serialization"""
        event = TimelineEvent(
            event_id="evt_002",
            title="Graduation",
            description="Graduated with a Master's degree",
            event_type=EventType.MILESTONE,
            timestamp=datetime(2025, 6, 15, 14, 0),
            importance=0.9,
        )
        
        data = event.to_dict()
        assert data["event_id"] == "evt_002"
        assert data["event_type"] == "milestone"
    
    def test_event_from_dict(self):
        """Test event deserialization"""
        data = {
            "event_id": "evt_003",
            "title": "First trip to Japan",
            "description": "Visited Tokyo for the first time",
            "event_type": "travel",
            "timestamp": "2024-03-20T10:00:00",
            "importance": 0.7,
            "tags": ["travel", "japan"],
        }
        
        event = TimelineEvent.from_dict(data)
        assert event.event_id == "evt_003"
        assert event.year == 2024
        assert "japan" in event.tags


class TestTimeline:
    """Tests for Timeline API"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def timeline(self, temp_workspace):
        """Create Timeline instance"""
        return Timeline(temp_workspace)
    
    def test_add_event(self, timeline):
        """Test adding an event"""
        event = TimelineEvent(
            event_id="evt_001",
            title="Test Event",
            description="A test event",
            event_type=EventType.OTHER,
            timestamp=datetime.now(),
        )
        
        event_id = timeline.add_event(event)
        assert event_id == "evt_001"
    
    def test_get_event(self, timeline):
        """Test retrieving an event"""
        event = TimelineEvent(
            event_id="evt_002",
            title="Test Event 2",
            description="Another test event",
            event_type=EventType.MILESTONE,
            timestamp=datetime.now(),
            importance=0.8,
        )
        
        timeline.add_event(event)
        retrieved = timeline.get_event("evt_002")
        
        assert retrieved is not None
        assert retrieved.title == "Test Event 2"
    
    def test_get_life_events(self, timeline):
        """Test getting events by year"""
        for i in range(3):
            event = TimelineEvent(
                event_id=f"evt_{i:03d}",
                title=f"Event {i}",
                description=f"Description {i}",
                event_type=EventType.OTHER,
                timestamp=datetime(2026, 4, i + 1),
            )
            timeline.add_event(event)
        
        events = timeline.get_life_events(2026)
        assert len(events) == 3
    
    def test_get_milestones(self, timeline):
        """Test getting milestones"""
        # Add milestone
        milestone = TimelineEvent(
            event_id="milestone_001",
            title="Major Achievement",
            description="Got promoted",
            event_type=EventType.MILESTONE,
            timestamp=datetime.now(),
            importance=0.9,
        )
        timeline.add_event(milestone)
        
        # Add non-milestone
        normal = TimelineEvent(
            event_id="normal_001",
            title="Regular Day",
            description="Just a regular day",
            event_type=EventType.ROUTINE,
            timestamp=datetime.now(),
            importance=0.3,
        )
        timeline.add_event(normal)
        
        milestones = timeline.get_milestones()
        assert len(milestones) == 1
        assert milestones[0].event_id == "milestone_001"
    
    def test_search_by_emotion(self, timeline):
        """Test emotion-based search"""
        event = TimelineEvent(
            event_id="evt_emotion",
            title="Happy Day",
            description="A very happy day",
            event_type=EventType.EMOTIONAL,
            timestamp=datetime.now(),
            emotions=["happy", "joyful"],
        )
        timeline.add_event(event)
        
        results = timeline.search_by_emotion("happy")
        assert len(results) == 1
        assert "happy" in results[0].emotions
    
    def test_query_with_filters(self, timeline):
        """Test query with filters"""
        for i in range(5):
            event = TimelineEvent(
                event_id=f"evt_{i:03d}",
                title=f"Event {i}",
                description=f"Description {i}",
                event_type=EventType.MILESTONE if i < 2 else EventType.OTHER,
                timestamp=datetime(2026, 4, i + 1),
                importance=0.5 + i * 0.1,
            )
            timeline.add_event(event)
        
        query = TimelineQuery(
            event_types=[EventType.MILESTONE],
            min_importance=0.5,
            limit=10,
        )
        
        results = timeline.query(query)
        assert len(results) == 2
    
    def test_get_stats(self, timeline):
        """Test getting statistics"""
        for i in range(3):
            event = TimelineEvent(
                event_id=f"evt_{i:03d}",
                title=f"Event {i}",
                description=f"Description {i}",
                event_type=[EventType.MILESTONE, EventType.CAREER, EventType.TRAVEL][i],
                timestamp=datetime(2026, 4, i + 1),
            )
            timeline.add_event(event)
        
        stats = timeline.get_stats()
        assert stats["total_events"] == 3
        assert stats["total_years"] == 1


class TestMilestoneDetector:
    """Tests for MilestoneDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create MilestoneDetector instance"""
        return MilestoneDetector()
    
    def test_detect_birthday(self, detector):
        """Test birthday detection"""
        text = "Today is my 30th birthday party!"
        detected = detector.detect(text)
        
        assert len(detected) > 0
        assert any(t == MilestoneType.BIRTHDAY for t, _ in detected)
    
    def test_detect_wedding(self, detector):
        """Test wedding detection"""
        text = "We got married last month in a beautiful ceremony"
        detected = detector.detect(text)
        
        assert len(detected) > 0
        assert any(t == MilestoneType.WEDDING for t, _ in detected)
    
    def test_detect_graduation(self, detector):
        """Test graduation detection"""
        text = "I graduated from MIT with a computer science degree"
        detected = detector.detect(text)
        
        assert len(detected) > 0
        assert any(t in [MilestoneType.GRADUATION, MilestoneType.DEGREE] for t, _ in detected)
    
    def test_detect_new_job(self, detector):
        """Test new job detection"""
        text = "Started my new job at Google this week"
        detected = detector.detect(text)
        
        assert len(detected) > 0
        assert any(t == MilestoneType.NEW_JOB for t, _ in detected)
    
    def test_score_milestone(self, detector):
        """Test milestone scoring"""
        milestone_text = "I got married today!"
        normal_text = "I had lunch at noon"
        
        milestone_score = detector.score_milestone(milestone_text)
        normal_score = detector.score_milestone(normal_text)
        
        assert milestone_score > normal_score
        assert milestone_score > 0.5
    
    def test_is_milestone(self, detector):
        """Test milestone threshold check"""
        assert detector.is_milestone("I got promoted to senior engineer!")
        assert not detector.is_milestone("I had a sandwich for lunch")


class TestDecisionTracker:
    """Tests for DecisionTracker"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def tracker(self, temp_workspace):
        """Create DecisionTracker instance"""
        return DecisionTracker(temp_workspace)
    
    def test_add_decision(self, tracker):
        """Test adding a decision"""
        decision = tracker.add_decision(
            title="Accept job offer",
            description="Decided to accept the job offer from TechCorp",
            decision_type=DecisionType.CAREER,
            options=["Accept offer", "Decline offer", "Negotiate"],
            chosen_option="Accept offer",
            reasoning="Better compensation and growth opportunities",
            importance=0.8,
        )
        
        assert decision.decision_id.startswith("dec_")
        assert decision.status == DecisionStatus.MADE
        assert len(decision.options) == 3
    
    def test_get_decision(self, tracker):
        """Test retrieving a decision"""
        decision = tracker.add_decision(
            title="Buy a house",
            description="Decided to buy a house in the suburbs",
            decision_type=DecisionType.FINANCIAL,
            importance=0.7,
        )
        
        retrieved = tracker.get_decision(decision.decision_id)
        assert retrieved is not None
        assert retrieved.title == "Buy a house"
    
    def test_update_decision(self, tracker):
        """Test updating a decision"""
        decision = tracker.add_decision(
            title="Learn Python",
            description="Decided to learn Python programming",
            decision_type=DecisionType.EDUCATION,
            importance=0.6,
        )
        
        updated = tracker.update_decision(
            decision.decision_id,
            status=DecisionStatus.COMPLETED,
            actual_outcome="Successfully learned Python and got a job",
            lessons_learned=["Practice daily", "Build projects"],
        )
        
        assert updated.status == DecisionStatus.COMPLETED
        assert len(updated.lessons_learned) == 2
    
    def test_get_decisions_by_type(self, tracker):
        """Test filtering decisions by type"""
        tracker.add_decision("Job 1", "Desc", DecisionType.CAREER)
        tracker.add_decision("Job 2", "Desc", DecisionType.CAREER)
        tracker.add_decision("Course", "Desc", DecisionType.EDUCATION)
        
        career_decisions = tracker.get_decisions(decision_type=DecisionType.CAREER)
        assert len(career_decisions) == 2
    
    def test_detect_decision(self, tracker):
        """Test decision detection"""
        decision_text = "I decided to move to San Francisco"
        normal_text = "I went to the store"
        
        assert tracker.detect_decision(decision_text)
        assert not tracker.detect_decision(normal_text)
    
    def test_classify_decision_type(self, tracker):
        """Test decision type classification"""
        career_text = "I decided to accept the job offer"
        education_text = "I decided to enroll in university"
        
        assert tracker.classify_decision_type(career_text) == DecisionType.CAREER
        assert tracker.classify_decision_type(education_text) == DecisionType.EDUCATION


class TestFirstEventsDetector:
    """Tests for FirstEventsDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create FirstEventsDetector instance"""
        return FirstEventsDetector()
    
    def test_detect_first_job(self, detector):
        """Test first job detection"""
        text = "This is my first job at a tech company"
        detected = detector.detect(text)
        
        assert len(detected) > 0
        assert any(t == FirstEventType.FIRST_JOB for t, _, _ in detected)
    
    def test_detect_first_trip(self, detector):
        """Test first trip detection"""
        text = "This was my first time traveling to Japan"
        detected = detector.detect(text)
        
        assert len(detected) > 0
        assert any(t == FirstEventType.FIRST_TRIP for t, _, _ in detected)
    
    def test_detect_first_code(self, detector):
        """Test first code detection"""
        text = "I wrote my first program today - Hello World!"
        detected = detector.detect(text)
        
        assert len(detected) > 0
        assert any(t == FirstEventType.FIRST_CODE for t, _, _ in detected)
    
    def test_is_first_event(self, detector):
        """Test first event check"""
        first_text = "This is my first time riding a bike"
        normal_text = "I rode my bike to work today"
        
        assert detector.is_first_event(first_text)
        assert not detector.is_first_event(normal_text)
    
    def test_extract_first_event(self, detector):
        """Test extracting first event"""
        text = "I got my first car today - a Honda Civic!"
        event = detector.extract_first_event(text)
        
        assert event is not None
        assert event.event_type == FirstEventType.FIRST_CAR
        assert event.importance > 0.7
    
    def test_get_first_event_suggestions(self, detector):
        """Test getting suggestions"""
        text = "This is my first time flying on a plane"
        suggestions = detector.get_first_event_suggestions(text)
        
        assert len(suggestions) > 0
        assert any("first" in s.lower() for s in suggestions)


class TestTimelineIntegration:
    """Integration tests for Timeline module"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_full_workflow(self, temp_workspace):
        """Test full workflow"""
        timeline = Timeline(temp_workspace)
        milestone_detector = MilestoneDetector()
        decision_tracker = DecisionTracker(temp_workspace)
        first_detector = FirstEventsDetector()
        
        # Add milestone event
        wedding_text = "We got married on a beautiful beach"
        milestone_type = milestone_detector.get_milestone_type(wedding_text)
        assert milestone_type == MilestoneType.WEDDING
        
        event = TimelineEvent(
            event_id="evt_wedding",
            title="Wedding Day",
            description=wedding_text,
            event_type=EventType.MILESTONE,
            timestamp=datetime.now(),
            importance=milestone_detector.score_milestone(wedding_text),
        )
        timeline.add_event(event)
        
        # Add decision
        decision = decision_tracker.add_decision(
            title="Choose wedding venue",
            description="Decided on beach wedding",
            decision_type=DecisionType.RELATIONSHIP,
            chosen_option="Beach venue",
        )
        
        # Add first event
        first_text = "This was my first trip to Hawaii for our honeymoon"
        first_event = first_detector.extract_first_event(first_text)
        assert first_event is not None
        
        # Verify timeline
        milestones = timeline.get_milestones()
        assert len(milestones) == 1
        
        decisions = decision_tracker.get_decisions()
        assert len(decisions) == 1
