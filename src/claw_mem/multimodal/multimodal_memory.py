"""
Multimodal Memory Module for claw-mem v2.4.0

Supports multimodal memory storage for images, files, etc.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryType(Enum):
    """Memory type"""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class ImageMemory:
    """Image memory"""

    image_id: str
    description: str
    path: str
    thumbnail_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FileMemory:
    """File memory"""

    file_id: str
    filename: str
    file_type: str
    path: str
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class MultimodalMemoryStore:
    """
    Multimodal memory storage

    Supports memory storage for non-text content such as images and files.
    """

    def __init__(self, base_path: str = "./workspace/multimodal"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Storage for different types
        self._image_memories: Dict[str, ImageMemory] = {}
        self._file_memories: Dict[str, FileMemory] = {}

    def store_image(
        self, image_path: str, description: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store image memory

        Args:
            image_path: Image file path
            description: Image description
            metadata: Additional metadata

        Returns:
            Image memory ID
        """
        # Generate ID from content hash
        image_id = self._generate_id(image_path)

        # Copy image to storage
        storage_path = self.base_path / "images" / Path(image_path).name
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Note: In real implementation, would copy file here
        # For now, just store reference

        memory = ImageMemory(
            image_id=image_id,
            description=description,
            path=str(storage_path),
            metadata=metadata or {},
        )

        self._image_memories[image_id] = memory
        return image_id

    def store_file(
        self,
        file_path: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store file memory

        Args:
            file_path: File path
            file_type: File type
            metadata: Additional metadata

        Returns:
            File memory ID
        """
        file_path_obj = Path(file_path)
        file_id = self._generate_id(file_path)

        # Determine file type
        if file_type is None:
            file_type = file_path_obj.suffix.lstrip(".")

        # Get file size
        size_bytes = 0
        if file_path_obj.exists():
            size_bytes = file_path_obj.stat().st_size

        # Copy to storage
        storage_path = self.base_path / "files" / file_path_obj.name
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        memory = FileMemory(
            file_id=file_id,
            filename=file_path_obj.name,
            file_type=file_type,
            path=str(storage_path),
            size_bytes=size_bytes,
            metadata=metadata or {},
        )

        self._file_memories[file_id] = memory
        return file_id

    def get_image(self, image_id: str) -> Optional[ImageMemory]:
        """Get image memory"""
        return self._image_memories.get(image_id)

    def get_file(self, file_id: str) -> Optional[FileMemory]:
        """Get file memory"""
        return self._file_memories.get(file_id)

    def search_by_description(self, query: str, limit: int = 10) -> List[ImageMemory]:
        """Search images by description"""
        query_lower = query.lower()
        results = []

        for memory in self._image_memories.values():
            if query_lower in memory.description.lower():
                results.append(memory)

        return results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        total_size = sum(f.size_bytes for f in self._file_memories.values())

        return {
            "total_images": len(self._image_memories),
            "total_files": len(self._file_memories),
            "total_size_bytes": total_size,
            "image_descriptions": [m.description for m in self._image_memories.values()],
        }

    def _generate_id(self, content: str) -> str:
        """Generate unique ID"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# Global instance
_multimodal_store: Optional[MultimodalMemoryStore] = None


def get_multimodal_store(base_path: str = "./workspace/multimodal") -> MultimodalMemoryStore:
    """Get multimodal storage instance"""
    global _multimodal_store
    if _multimodal_store is None:
        _multimodal_store = MultimodalMemoryStore(base_path)
    return _multimodal_store


def reset_multimodal_store() -> None:
    """Reset global multimodal store instance (for testing)."""
    global _multimodal_store
    _multimodal_store = None
