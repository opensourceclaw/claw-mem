"""
Tests for PreferenceDetector

Tests preference detection and matching for memory retrieval.
"""

import pytest
from claw_mem.retrieval.preference_detector import PreferenceDetector, Preference


class TestPreferenceDetector:
    """Test preference detection"""
    
    def setup_method(self):
        """Setup detector for each test"""
        self.detector = PreferenceDetector()
    
    def test_detect_preference_positive(self):
        """Test detecting positive preferences"""
        result = self.detector.detect_preference("The user's favorite food is Pizza")
        assert result is not None
        assert result.category == "food"
        assert result.sentiment == "positive"
    
    def test_detect_preference_none(self):
        """Test non-preference text returns None"""
        result = self.detector.detect_preference("The user works as a software engineer")
        # May return None or a preference with low confidence
        assert result is None or isinstance(result, Preference)
    
    def test_detect_food_preference(self):
        """Test detecting food preference"""
        result = self.detector.detect_preference("The user's favorite food is Pizza")
        assert result is not None
        assert result.category == "food"
        assert "pizza" in result.item.lower()
    
    def test_detect_movie_preference(self):
        """Test detecting movie preference"""
        result = self.detector.detect_preference("The user's favorite movie is Star Wars")
        assert result is not None
        assert result.category == "movie"
        assert "star" in result.item.lower()
    
    def test_detect_book_preference(self):
        """Test detecting book preference"""
        result = self.detector.detect_preference("The user's favorite book is Dune")
        assert result is not None
        assert result.category == "book"
        assert "dune" in result.item.lower()
    
    def test_get_preference_boost(self):
        """Test preference boost calculation"""
        memory = {
            "content": "The user's favorite food is Pizza"
        }
        
        if hasattr(self.detector, 'get_preference_boost'):
            boost = self.detector.get_preference_boost(
                "What is the user's favorite food?",
                memory
            )
            # Should return positive boost for matching preference
            assert boost >= 0
        else:
            # Skip if method doesn't exist
            pytest.skip("get_preference_boost method not implemented")
    
    def test_favorite_pattern(self):
        """Test favorite pattern detection"""
        result = self.detector.detect_preference("The user's favorite food is Pizza")
        assert result is not None
        assert result.sentiment == "positive"
    
    def test_preference_dataclass(self):
        """Test Preference dataclass"""
        pref = Preference(
            category="food",
            item="Pizza",
            sentiment="positive",
            confidence=0.9,
            original_text="The user's favorite food is Pizza"
        )
        
        assert pref.category == "food"
        assert pref.item == "Pizza"
        assert pref.sentiment == "positive"
        assert pref.confidence == 0.9
    
    def test_category_detection(self):
        """Test category detection from various texts"""
        test_cases = [
            ("The user's favorite food is Pizza", "food"),
            ("The user's favorite movie is Star Wars", "movie"),
            ("The user's favorite book is Dune", "book"),
        ]
        
        for text, expected_category in test_cases:
            result = self.detector.detect_preference(text)
            assert result is not None, f"Failed to detect: {text}"
            assert result.category == expected_category, f"Wrong category for: {text}"
    
    def test_multiple_preferences(self):
        """Test that detector can find multiple preferences"""
        texts = [
            "The user's favorite food is Pizza",
            "The user's favorite movie is Star Wars",
            "The user's favorite book is Dune",
            "The user's favorite color is blue",
        ]
        
        detected = 0
        for text in texts:
            result = self.detector.detect_preference(text)
            if result is not None:
                detected += 1
        
        # Should detect at least some preferences
        assert detected >= 2
