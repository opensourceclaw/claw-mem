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
Tests for Knowledge Graph Module
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from claw_mem.knowledge_graph import (
    KnowledgeGraph,
    Entity,
    EntityType,
    Relation,
    RelationType,
)


class TestEntity:
    """Tests for Entity"""
    
    def test_create_entity(self):
        """Test creating an entity"""
        entity = Entity(
            entity_id="ent_001",
            name="John Doe",
            entity_type=EntityType.PERSON,
            description="A software engineer",
        )
        
        assert entity.entity_id == "ent_001"
        assert entity.name == "John Doe"
        assert entity.entity_type == EntityType.PERSON
    
    def test_entity_to_dict(self):
        """Test entity serialization"""
        entity = Entity(
            entity_id="ent_002",
            name="Google",
            entity_type=EntityType.ORGANIZATION,
            aliases=["Alphabet"],
        )
        
        data = entity.to_dict()
        assert data["entity_id"] == "ent_002"
        assert data["name"] == "Google"
        assert "Alphabet" in data["aliases"]
    
    def test_entity_from_dict(self):
        """Test entity deserialization"""
        data = {
            "entity_id": "ent_003",
            "name": "Paris",
            "entity_type": "place",
            "aliases": ["City of Light"],
            "description": "Capital of France",
            "properties": {"country": "France"},
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
            "source_memory_ids": [],
            "confidence": 0.9,
        }
        
        entity = Entity.from_dict(data)
        assert entity.name == "Paris"
        assert entity.entity_type == EntityType.PLACE
        assert "City of Light" in entity.aliases
    
    def test_add_alias(self):
        """Test adding alias"""
        entity = Entity(
            entity_id="ent_004",
            name="Machine Learning",
            entity_type=EntityType.CONCEPT,
        )
        
        entity.add_alias("ML")
        assert "ML" in entity.aliases
        assert len(entity.aliases) == 1
        
        # Adding same alias again should not duplicate
        entity.add_alias("ML")
        assert len(entity.aliases) == 1


class TestRelation:
    """Tests for Relation"""
    
    def test_create_relation(self):
        """Test creating a relation"""
        relation = Relation(
            relation_id="rel_001",
            from_entity_id="ent_001",
            to_entity_id="ent_002",
            relation_type=RelationType.KNOWS,
        )
        
        assert relation.relation_id == "rel_001"
        assert relation.from_entity_id == "ent_001"
        assert relation.to_entity_id == "ent_002"
        assert relation.relation_type == RelationType.KNOWS
    
    def test_relation_to_dict(self):
        """Test relation serialization"""
        relation = Relation(
            relation_id="rel_002",
            from_entity_id="ent_001",
            to_entity_id="ent_003",
            relation_type=RelationType.WORKS_AT,
            properties={"role": "Engineer"},
        )
        
        data = relation.to_dict()
        assert data["relation_id"] == "rel_002"
        assert data["relation_type"] == "works_at"
        assert data["properties"]["role"] == "Engineer"
    
    def test_relation_from_dict(self):
        """Test relation deserialization"""
        data = {
            "relation_id": "rel_003",
            "from_entity_id": "ent_001",
            "to_entity_id": "ent_004",
            "relation_type": "interested_in",
            "properties": {},
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
            "source_memory_ids": [],
            "confidence": 1.0,
        }
        
        relation = Relation.from_dict(data)
        assert relation.from_entity_id == "ent_001"
        assert relation.relation_type == RelationType.INTERESTED_IN


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def graph(self, temp_workspace):
        """Create KnowledgeGraph instance"""
        return KnowledgeGraph(temp_workspace)
    
    def test_add_entity(self, graph):
        """Test adding an entity"""
        entity = graph.add_entity(
            name="Alice",
            entity_type=EntityType.PERSON,
            description="A friend",
        )
        
        assert entity.entity_id.startswith("ent_")
        assert entity.name == "Alice"
        assert len(graph.entities) == 1
    
    def test_add_entity_with_alias(self, graph):
        """Test adding entity with alias"""
        entity = graph.add_entity(
            name="Bob",
            entity_type=EntityType.PERSON,
            aliases=["Robert", "Bobby"],
        )
        
        assert len(entity.aliases) == 2
        assert graph.find_entity("Robert") == entity
        assert graph.find_entity("Bobby") == entity
    
    def test_find_entity(self, graph):
        """Test finding entity"""
        entity = graph.add_entity(
            name="Charlie",
            entity_type=EntityType.PERSON,
        )
        
        found = graph.find_entity("Charlie")
        assert found == entity
        
        # Case insensitive
        found = graph.find_entity("charlie")
        assert found == entity
    
    def test_add_relation(self, graph):
        """Test adding a relation"""
        alice = graph.add_entity("Alice", EntityType.PERSON)
        bob = graph.add_entity("Bob", EntityType.PERSON)
        
        relation = graph.add_relation(
            from_entity_id=alice.entity_id,
            to_entity_id=bob.entity_id,
            relation_type=RelationType.KNOWS,
        )
        
        assert relation is not None
        assert relation.relation_type == RelationType.KNOWS
        assert len(graph.relations) == 1
    
    def test_get_neighbors(self, graph):
        """Test getting neighbors"""
        alice = graph.add_entity("Alice", EntityType.PERSON)
        bob = graph.add_entity("Bob", EntityType.PERSON)
        charlie = graph.add_entity("Charlie", EntityType.PERSON)
        
        graph.add_relation(alice.entity_id, bob.entity_id, RelationType.KNOWS)
        graph.add_relation(alice.entity_id, charlie.entity_id, RelationType.KNOWS)
        
        neighbors = graph.get_neighbors(alice.entity_id)
        assert len(neighbors) == 2
    
    def test_find_path(self, graph):
        """Test finding paths"""
        alice = graph.add_entity("Alice", EntityType.PERSON)
        bob = graph.add_entity("Bob", EntityType.PERSON)
        charlie = graph.add_entity("Charlie", EntityType.PERSON)
        
        graph.add_relation(alice.entity_id, bob.entity_id, RelationType.KNOWS)
        graph.add_relation(bob.entity_id, charlie.entity_id, RelationType.KNOWS)
        
        paths = graph.find_path(alice.entity_id, charlie.entity_id)
        assert len(paths) >= 1
        assert alice.entity_id in paths[0]
        assert charlie.entity_id in paths[0]
    
    def test_search_entities(self, graph):
        """Test searching entities"""
        graph.add_entity("Alice Smith", EntityType.PERSON)
        graph.add_entity("Bob Johnson", EntityType.PERSON)
        graph.add_entity("Alice Corp", EntityType.ORGANIZATION)
        
        results = graph.search_entities("Alice")
        assert len(results) == 2
        
        results = graph.search_entities("Alice", entity_type=EntityType.PERSON)
        assert len(results) == 1
    
    def test_entity_timeline(self, graph):
        """Test entity timeline"""
        alice = graph.add_entity("Alice", EntityType.PERSON)
        google = graph.add_entity("Google", EntityType.ORGANIZATION)
        python = graph.add_entity("Python", EntityType.SKILL)
        
        graph.add_relation(alice.entity_id, google.entity_id, RelationType.WORKS_AT)
        graph.add_relation(alice.entity_id, python.entity_id, RelationType.HAS_SKILL)
        
        timeline = graph.get_entity_timeline(alice.entity_id)
        assert len(timeline) == 2
    
    def test_get_stats(self, graph):
        """Test getting statistics"""
        graph.add_entity("Alice", EntityType.PERSON)
        graph.add_entity("Google", EntityType.ORGANIZATION)
        graph.add_entity("Python", EntityType.SKILL)
        
        alice = graph.find_entity("Alice")
        google = graph.find_entity("Google")
        graph.add_relation(alice.entity_id, google.entity_id, RelationType.WORKS_AT)
        
        stats = graph.get_stats()
        assert stats["total_entities"] == 3
        assert stats["total_relations"] == 1
        assert "person" in stats["entity_types"]
        assert "organization" in stats["entity_types"]
    
    def test_persistence(self, temp_workspace):
        """Test graph persistence"""
        # Create and populate graph
        graph1 = KnowledgeGraph(temp_workspace)
        alice = graph1.add_entity("Alice", EntityType.PERSON)
        bob = graph1.add_entity("Bob", EntityType.PERSON)
        graph1.add_relation(alice.entity_id, bob.entity_id, RelationType.KNOWS)
        
        # Create new graph instance (should load from disk)
        graph2 = KnowledgeGraph(temp_workspace)
        
        assert len(graph2.entities) == 2
        assert len(graph2.relations) == 1
        assert graph2.find_entity("Alice") is not None
    
    def test_clear(self, graph):
        """Test clearing graph"""
        graph.add_entity("Alice", EntityType.PERSON)
        graph.add_entity("Bob", EntityType.PERSON)
        
        graph.clear()
        
        assert len(graph.entities) == 0
        assert len(graph.relations) == 0
    
    def test_duplicate_entity(self, graph):
        """Test adding duplicate entity"""
        entity1 = graph.add_entity("Alice", EntityType.PERSON)
        entity2 = graph.add_entity("Alice", EntityType.PERSON)
        
        # Should return same entity
        assert entity1.entity_id == entity2.entity_id
        assert len(graph.entities) == 1


class TestKnowledgeGraphIntegration:
    """Integration tests for Knowledge Graph"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_complex_graph(self, temp_workspace):
        """Test building a complex graph"""
        graph = KnowledgeGraph(temp_workspace)
        
        # Add people
        alice = graph.add_entity("Alice", EntityType.PERSON, description="Software Engineer")
        bob = graph.add_entity("Bob", EntityType.PERSON, description="Product Manager")
        charlie = graph.add_entity("Charlie", EntityType.PERSON, description="Designer")
        
        # Add organizations
        google = graph.add_entity("Google", EntityType.ORGANIZATION)
        startup = graph.add_entity("Startup Inc", EntityType.ORGANIZATION)
        
        # Add skills
        python = graph.add_entity("Python", EntityType.SKILL)
        design = graph.add_entity("UI Design", EntityType.SKILL)
        
        # Add relations
        graph.add_relation(alice.entity_id, google.entity_id, RelationType.WORKS_FOR)
        graph.add_relation(alice.entity_id, python.entity_id, RelationType.HAS_SKILL)
        graph.add_relation(bob.entity_id, google.entity_id, RelationType.WORKS_FOR)
        graph.add_relation(bob.entity_id, startup.entity_id, RelationType.INTERESTED_IN)
        graph.add_relation(charlie.entity_id, startup.entity_id, RelationType.WORKS_AT)
        graph.add_relation(charlie.entity_id, design.entity_id, RelationType.HAS_SKILL)
        graph.add_relation(alice.entity_id, bob.entity_id, RelationType.KNOWS)
        graph.add_relation(bob.entity_id, charlie.entity_id, RelationType.KNOWS)
        
        # Verify structure
        stats = graph.get_stats()
        assert stats["total_entities"] == 7
        assert stats["total_relations"] == 8
        
        # Find path from Alice to Charlie
        paths = graph.find_path(alice.entity_id, charlie.entity_id)
        assert len(paths) >= 1
        
        # Get Alice's neighbors
        neighbors = graph.get_neighbors(alice.entity_id)
        assert len(neighbors) == 3  # Google, Python, Bob
