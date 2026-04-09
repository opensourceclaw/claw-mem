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
Preference Detector

Detects and extracts user preferences from memories.
Part of the preference matching enhancement for claw-mem.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Preference:
    """Represents a user preference."""
    category: str  # food, movie, music, etc.
    item: str  # pizza, star wars, etc.
    sentiment: str  # like, love, hate, etc.
    confidence: float  # 0.0 to 1.0
    original_text: str  # original memory text


class PreferenceDetector:
    """
    Preference Detector
    
    Detects and extracts user preferences from memory content.
    """
    
    def __init__(self):
        """Initialize preference detector."""
        # Preference keywords with sentiment
        self.positive_keywords = [
            'favorite', 'favourite', 'love', 'like', 'enjoy', 'prefer', 'prefer to',
            'really like', 'big fan', 'into', 'passionate about', 'crazy about'
        ]
        
        self.negative_keywords = [
            'hate', 'dislike', 'don\'t like', 'can\'t stand', 'avoid', 'not into'
        ]
        
        # Category keywords
        self.category_keywords = {
            'food': ['food', 'eat', 'meal', 'restaurant', 'cuisine', 'dish', 'pizza', 'burger', 'coffee', 'tea', 'breakfast', 'lunch', 'dinner', 'snack'],
            'movie': ['movie', 'film', 'cinema', 'watch', 'actor', 'actress', 'director', 'star wars', 'marvel', 'dc', 'netflix'],
            'music': ['music', 'song', 'listen', 'band', 'artist', 'album', 'concert', 'genre', 'rock', 'pop', 'jazz', 'classical'],
            'book': ['book', 'read', 'novel', 'author', 'story', 'literature', 'kindle', 'audiobook'],
            'hobby': ['hobby', 'play', 'game', 'sport', 'tennis', 'football', 'gaming', 'guitar', 'painting', 'hiking', 'swimming'],
            'work': ['work', 'job', 'company', 'project', 'team', 'office', 'career', 'engineer', 'developer', 'manager'],
            'location': ['city', 'country', 'place', 'live', 'live in', 'from', 'location', 'travel', 'visit'],
            'person': ['name', 'who', 'person', 'friend', 'family', 'colleague', 'partner', 'spouse'],
        }
    
    def detect_preference(self, text: str) -> Optional[Preference]:
        """
        Detect preference from text.
        
        Args:
            text: Memory content
            
        Returns:
            Preference if found, None otherwise
        """
        text_lower = text.lower()
        
        # Check for positive preference
        for keyword in self.positive_keywords:
            if keyword in text_lower:
                # Extract category and item
                category = self._detect_category(text_lower)
                item = self._extract_item(text_lower, keyword)
                
                if category and item:
                    return Preference(
                        category=category,
                        item=item,
                        sentiment='positive',
                        confidence=0.8,
                        original_text=text
                    )
        
        # Check for negative preference
        for keyword in self.negative_keywords:
            if keyword in text_lower:
                category = self._detect_category(text_lower)
                item = self._extract_item(text_lower, keyword)
                
                if category and item:
                    return Preference(
                        category=category,
                        item=item,
                        sentiment='negative',
                        confidence=0.8,
                        original_text=text
                    )
        
        return None
    
    def _detect_category(self, text: str) -> Optional[str]:
        """
        Detect preference category from text.
        
        Args:
            text: Lowercase text
            
        Returns:
            Category if found, None otherwise
        """
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return None
    
    def _extract_item(self, text: str, keyword: str) -> Optional[str]:
        """
        Extract preference item from text.
        
        Args:
            text: Lowercase text
            keyword: Preference keyword (e.g., 'favorite')
            
        Returns:
            Preference item if found, None otherwise
        """
        # Pattern: "favorite X is Y" or "like Y"
        patterns = [
            rf'{keyword}\s+(\w+)\s+is\s+(.+?)(?:\.|$)',
            rf'{keyword}\s+(.+?)(?:\.|$)',
            rf'{keyword}\s+to\s+(.+?)(?:\.|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Get the last group (the item)
                item = match.group(match.lastindex).strip()
                # Clean up
                item = re.sub(r'^(a|an|the)\s+', '', item)
                if len(item) > 2 and len(item) < 100:
                    return item
        
        return None
    
    def is_preference_query(self, query: str) -> bool:
        """
        Check if query is about preferences.
        
        Args:
            query: Search query
            
        Returns:
            True if preference query, False otherwise
        """
        query_lower = query.lower()
        
        # Check for preference keywords
        preference_keywords = [
            'favorite', 'favourite', 'prefer', 'like', 'love', 'hate',
            'what kind of', 'what type of', 'what sort of',
            'best', 'worst', 'most', 'least'
        ]
        
        return any(kw in query_lower for kw in preference_keywords)
    
    def get_preference_boost(self, query: str, memory: Dict) -> float:
        """
        Get preference boost score for a memory.
        
        Args:
            query: Search query
            memory: Memory record
            
        Returns:
            Boost score (0.0 to 1.0)
        """
        # Check if query is about preferences
        if not self.is_preference_query(query):
            return 0.0
        
        # Get memory content
        content = memory.get("content", "") if isinstance(memory, dict) else getattr(memory, "content", "")
        content_lower = content.lower()
        
        # Check if memory contains preference
        preference = self.detect_preference(content)
        if not preference:
            return 0.0
        
        # Check if category matches
        query_category = self._detect_category(query.lower())
        if query_category and preference.category == query_category:
            return 1.0
        
        # Partial match
        return 0.5
    
    def extract_all_preferences(self, memories: List[Dict]) -> List[Preference]:
        """
        Extract all preferences from memories.
        
        Args:
            memories: List of memory records
            
        Returns:
            List of preferences found
        """
        preferences = []
        
        for memory in memories:
            content = memory.get("content", "") if isinstance(memory, dict) else getattr(memory, "content", "")
            preference = self.detect_preference(content)
            if preference:
                preferences.append(preference)
        
        return preferences
