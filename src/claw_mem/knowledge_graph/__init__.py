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
Knowledge Graph Module

Provides knowledge graph capabilities for claw-mem.

This is what makes claw-mem different from linear memory storage:
it builds a network of connected entities (people, places, things, concepts)
that mirrors how human memory actually works.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Set, Any
from enum import Enum
from pathlib import Path
import json
import uuid


class EntityType(Enum):
    """Types of entities in the knowledge graph"""
    PERSON = "person"           # People
    PLACE = "place"             # Locations
    ORGANIZATION = "organization"  # Companies, groups
    THING = "thing"             # Objects, items
    CONCEPT = "concept"         # Ideas, topics
    EVENT = "event"             # Events
    SKILL = "skill"             # Skills, abilities
    PROJECT = "project"         # Projects, tasks
    TOPIC = "topic"             # Topics of interest
    OTHER = "other"             # Other entities


class RelationType(Enum):
    """Types of relationships between entities"""
    # Person relationships
    KNOWS = "knows"                     # Knows someone
    FRIEND_OF = "friend_of"             # Friend relationship
    FAMILY_OF = "family_of"             # Family relationship
    COLLEAGUE_OF = "colleague_of"       # Work relationship
    MET_AT = "met_at"                   # Met at a place/event
    
    # Location relationships
    LOCATED_IN = "located_in"           # Entity located in place
    LIVES_IN = "lives_in"               # Person lives in place
    WORKS_AT = "works_at"               # Person works at place/org
    VISITED = "visited"                 # Visited a place
    
    # Organization relationships
    MEMBER_OF = "member_of"             # Member of organization
    FOUNDED = "founded"                 # Founded organization
    WORKS_FOR = "works_for"             # Works for organization
    
    # Concept relationships
    RELATED_TO = "related_to"           # General relationship
    PART_OF = "part_of"                 # Part of something
    INSTANCE_OF = "instance_of"         # Instance of concept
    SUBCLASS_OF = "subclass_of"         # Subclass of concept
    
    # Event relationships
    PARTICIPATED_IN = "participated_in"  # Participated in event
    HAPPENED_AT = "happened_at"          # Event happened at place
    HAPPENED_ON = "happened_on"          # Event happened on date
    
    # Skill relationships
    HAS_SKILL = "has_skill"             # Has a skill
    LEARNED_FROM = "learned_from"       # Learned from someone/something
    
    # Project relationships
    WORKING_ON = "working_on"           # Working on project
    COMPLETED = "completed"             # Completed project
    
    # Topic relationships
    INTERESTED_IN = "interested_in"     # Interested in topic
    EXPERT_IN = "expert_in"             # Expert in topic
    
    # Other
    CUSTOM = "custom"                   # Custom relationship


@dataclass
class Entity:
    """
    An entity in the knowledge graph.
    
    Entities are the nodes in the graph - people, places, things, concepts.
    
    Attributes:
        entity_id: Unique identifier
        name: Entity name
        entity_type: Type of entity
        aliases: Alternative names
        description: Description
        properties: Additional properties
        created_at: Creation timestamp
        updated_at: Last update timestamp
        source_memory_ids: IDs of source memories
        confidence: Confidence score (0.0 - 1.0)
    """
    entity_id: str
    name: str
    entity_type: EntityType
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_memory_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "aliases": self.aliases,
            "description": self.description,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_memory_ids": self.source_memory_ids,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create from dictionary"""
        return cls(
            entity_id=data["entity_id"],
            name=data["name"],
            entity_type=EntityType(data["entity_type"]),
            aliases=data.get("aliases", []),
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            source_memory_ids=data.get("source_memory_ids", []),
            confidence=data.get("confidence", 1.0),
        )
    
    def add_alias(self, alias: str):
        """Add an alias"""
        if alias not in self.aliases:
            self.aliases.append(alias)
            self.updated_at = datetime.now()
    
    def update_property(self, key: str, value: Any):
        """Update a property"""
        self.properties[key] = value
        self.updated_at = datetime.now()


@dataclass
class Relation:
    """
    A relationship between two entities.
    
    Relations are the edges in the graph.
    
    Attributes:
        relation_id: Unique identifier
        from_entity_id: Source entity ID
        to_entity_id: Target entity ID
        relation_type: Type of relationship
        properties: Additional properties
        created_at: Creation timestamp
        updated_at: Last update timestamp
        source_memory_ids: IDs of source memories
        confidence: Confidence score (0.0 - 1.0)
    """
    relation_id: str
    from_entity_id: str
    to_entity_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source_memory_ids: List[str] = field(default_factory=list)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "relation_id": self.relation_id,
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "relation_type": self.relation_type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source_memory_ids": self.source_memory_ids,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relation":
        """Create from dictionary"""
        return cls(
            relation_id=data["relation_id"],
            from_entity_id=data["from_entity_id"],
            to_entity_id=data["to_entity_id"],
            relation_type=RelationType(data["relation_type"]),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            source_memory_ids=data.get("source_memory_ids", []),
            confidence=data.get("confidence", 1.0),
        )


class KnowledgeGraph:
    """
    Knowledge Graph for claw-mem.
    
    This is the core component that makes claw-mem different from
    linear context management - it builds a network of connected
    entities that mirrors how human memory works.
    
    Features:
    - Entity management (people, places, things, concepts)
    - Relationship management (knows, works_at, interested_in, etc.)
    - Graph queries (neighbors, paths, subgraphs)
    - Entity resolution (merge duplicates)
    - Memory linking (link entities to source memories)
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize KnowledgeGraph.
        
        Args:
            workspace: Path to claw-mem workspace
        """
        self.workspace = workspace
        self.graph_dir = workspace / "knowledge_graph"
        self.graph_dir.mkdir(parents=True, exist_ok=True)
        
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.entity_index: Dict[str, str] = {}  # name -> entity_id
        self.relation_index: Dict[str, List[str]] = {}  # entity_id -> [relation_ids]
        
        self._load()
    
    def _load(self):
        """Load graph from disk"""
        entities_file = self.graph_dir / "entities.json"
        relations_file = self.graph_dir / "relations.json"
        
        if entities_file.exists():
            with open(entities_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for entity_data in data.get("entities", []):
                    entity = Entity.from_dict(entity_data)
                    self.entities[entity.entity_id] = entity
                    self.entity_index[entity.name.lower()] = entity.entity_id
                    for alias in entity.aliases:
                        self.entity_index[alias.lower()] = entity.entity_id
        
        if relations_file.exists():
            with open(relations_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for relation_data in data.get("relations", []):
                    relation = Relation.from_dict(relation_data)
                    self.relations[relation.relation_id] = relation
                    
                    # Update relation index
                    if relation.from_entity_id not in self.relation_index:
                        self.relation_index[relation.from_entity_id] = []
                    self.relation_index[relation.from_entity_id].append(relation.relation_id)
                    
                    if relation.to_entity_id not in self.relation_index:
                        self.relation_index[relation.to_entity_id] = []
                    self.relation_index[relation.to_entity_id].append(relation.relation_id)
    
    def _save(self):
        """Save graph to disk"""
        entities_file = self.graph_dir / "entities.json"
        relations_file = self.graph_dir / "relations.json"
        
        with open(entities_file, "w", encoding="utf-8") as f:
            json.dump({
                "entities": [e.to_dict() for e in self.entities.values()],
                "updated_at": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)
        
        with open(relations_file, "w", encoding="utf-8") as f:
            json.dump({
                "relations": [r.to_dict() for r in self.relations.values()],
                "updated_at": datetime.now().isoformat(),
            }, f, indent=2, ensure_ascii=False)
    
    def add_entity(
        self,
        name: str,
        entity_type: EntityType,
        description: str = "",
        aliases: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        source_memory_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Entity:
        """
        Add an entity to the graph.
        
        Args:
            name: Entity name
            entity_type: Type of entity
            description: Entity description
            aliases: Alternative names
            properties: Additional properties
            source_memory_id: ID of source memory
            confidence: Confidence score
            
        Returns:
            The created Entity
        """
        # Check if entity already exists
        existing_id = self.entity_index.get(name.lower())
        if existing_id:
            entity = self.entities[existing_id]
            entity.updated_at = datetime.now()
            if source_memory_id and source_memory_id not in entity.source_memory_ids:
                entity.source_memory_ids.append(source_memory_id)
            self._save()
            return entity
        
        entity = Entity(
            entity_id=f"ent_{uuid.uuid4().hex[:8]}",
            name=name,
            entity_type=entity_type,
            description=description,
            aliases=aliases or [],
            properties=properties or {},
            source_memory_ids=[source_memory_id] if source_memory_id else [],
            confidence=confidence,
        )
        
        self.entities[entity.entity_id] = entity
        self.entity_index[name.lower()] = entity.entity_id
        for alias in (aliases or []):
            self.entity_index[alias.lower()] = entity.entity_id
        
        self._save()
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def find_entity(self, name: str) -> Optional[Entity]:
        """Find entity by name or alias"""
        entity_id = self.entity_index.get(name.lower())
        if entity_id:
            return self.entities.get(entity_id)
        return None
    
    def add_relation(
        self,
        from_entity_id: str,
        to_entity_id: str,
        relation_type: RelationType,
        properties: Optional[Dict[str, Any]] = None,
        source_memory_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> Optional[Relation]:
        """
        Add a relation between entities.
        
        Args:
            from_entity_id: Source entity ID
            to_entity_id: Target entity ID
            relation_type: Type of relationship
            properties: Additional properties
            source_memory_id: ID of source memory
            confidence: Confidence score
            
        Returns:
            The created Relation, or None if entities don't exist
        """
        if from_entity_id not in self.entities or to_entity_id not in self.entities:
            return None
        
        relation = Relation(
            relation_id=f"rel_{uuid.uuid4().hex[:8]}",
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            relation_type=relation_type,
            properties=properties or {},
            source_memory_ids=[source_memory_id] if source_memory_id else [],
            confidence=confidence,
        )
        
        self.relations[relation.relation_id] = relation
        
        # Update indexes
        for entity_id in [from_entity_id, to_entity_id]:
            if entity_id not in self.relation_index:
                self.relation_index[entity_id] = []
            self.relation_index[entity_id].append(relation.relation_id)
        
        self._save()
        return relation
    
    def get_neighbors(self, entity_id: str) -> List[Entity]:
        """
        Get neighboring entities.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            List of neighboring entities
        """
        neighbors = []
        relation_ids = self.relation_index.get(entity_id, [])
        
        for relation_id in relation_ids:
            relation = self.relations.get(relation_id)
            if relation:
                neighbor_id = (
                    relation.to_entity_id
                    if relation.from_entity_id == entity_id
                    else relation.from_entity_id
                )
                neighbor = self.entities.get(neighbor_id)
                if neighbor and neighbor not in neighbors:
                    neighbors.append(neighbor)
        
        return neighbors
    
    def get_relations(self, entity_id: str) -> List[Relation]:
        """
        Get all relations for an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            List of relations
        """
        relation_ids = self.relation_index.get(entity_id, [])
        return [self.relations[rid] for rid in relation_ids if rid in self.relations]
    
    def find_path(self, from_entity_id: str, to_entity_id: str, max_depth: int = 3) -> List[List[str]]:
        """
        Find paths between two entities.
        
        Args:
            from_entity_id: Starting entity ID
            to_entity_id: Target entity ID
            max_depth: Maximum search depth
            
        Returns:
            List of paths (each path is a list of entity IDs)
        """
        if from_entity_id == to_entity_id:
            return [[from_entity_id]]
        
        paths = []
        visited = set()
        queue = [(from_entity_id, [from_entity_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            neighbors = self.get_neighbors(current_id)
            for neighbor in neighbors:
                if neighbor.entity_id == to_entity_id:
                    paths.append(path + [neighbor.entity_id])
                elif neighbor.entity_id not in visited:
                    queue.append((neighbor.entity_id, path + [neighbor.entity_id]))
        
        return paths
    
    def get_entity_timeline(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Get timeline of events involving an entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            List of timeline events
        """
        relations = self.get_relations(entity_id)
        timeline = []
        
        for relation in relations:
            timeline.append({
                "relation_id": relation.relation_id,
                "relation_type": relation.relation_type.value,
                "created_at": relation.created_at.isoformat(),
                "confidence": relation.confidence,
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        return timeline
    
    def search_entities(self, query: str, entity_type: Optional[EntityType] = None) -> List[Entity]:
        """
        Search entities by name or alias.
        
        Args:
            query: Search query
            entity_type: Optional entity type filter
            
        Returns:
            List of matching entities
        """
        query_lower = query.lower()
        results = []
        
        for entity in self.entities.values():
            # Type filter
            if entity_type and entity.entity_type != entity_type:
                continue
            
            # Name match
            if query_lower in entity.name.lower():
                results.append(entity)
                continue
            
            # Alias match
            if any(query_lower in alias.lower() for alias in entity.aliases):
                results.append(entity)
                continue
            
            # Description match
            if query_lower in entity.description.lower():
                results.append(entity)
                continue
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        entity_types = {}
        for entity in self.entities.values():
            type_name = entity.entity_type.value
            entity_types[type_name] = entity_types.get(type_name, 0) + 1
        
        relation_types = {}
        for relation in self.relations.values():
            type_name = relation.relation_type.value
            relation_types[type_name] = relation_types.get(type_name, 0) + 1
        
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": entity_types,
            "relation_types": relation_types,
        }
    
    def clear(self):
        """Clear the graph"""
        self.entities.clear()
        self.relations.clear()
        self.entity_index.clear()
        self.relation_index.clear()
        self._save()
