"""
Multimodal Memory Module for claw-mem v2.4.0

支持图像、文件等多模态记忆存储。
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import hashlib
import json


class MemoryType(Enum):
    """记忆类型"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class ImageMemory:
    """图像记忆"""
    image_id: str
    description: str
    path: str
    thumbnail_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FileMemory:
    """文件记忆"""
    file_id: str
    filename: str
    file_type: str
    path: str
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class MultimodalMemoryStore:
    """
    多模态记忆存储

    支持图像、文件等非文本内容的记忆存储。
    """

    def __init__(self, base_path: str = "./workspace/multimodal"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Storage for different types
        self._image_memories: Dict[str, ImageMemory] = {}
        self._file_memories: Dict[str, FileMemory] = {}

    def store_image(
        self,
        image_path: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存储图像记忆

        Args:
            image_path: 图像文件路径
            description: 图像描述
            metadata: 额外元数据

        Returns:
            图像记忆 ID
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
            metadata=metadata or {}
        )

        self._image_memories[image_id] = memory
        return image_id

    def store_file(
        self,
        file_path: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存储文件记忆

        Args:
            file_path: 文件路径
            file_type: 文件类型
            metadata: 额外元数据

        Returns:
            文件记忆 ID
        """
        file_path_obj = Path(file_path)
        file_id = self._generate_id(file_path)

        # Determine file type
        if file_type is None:
            file_type = file_path_obj.suffix.lstrip('.')

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
            metadata=metadata or {}
        )

        self._file_memories[file_id] = memory
        return file_id

    def get_image(self, image_id: str) -> Optional[ImageMemory]:
        """获取图像记忆"""
        return self._image_memories.get(image_id)

    def get_file(self, file_id: str) -> Optional[FileMemory]:
        """获取文件记忆"""
        return self._file_memories.get(file_id)

    def search_by_description(self, query: str, limit: int = 10) -> List[ImageMemory]:
        """通过描述搜索图像"""
        query_lower = query.lower()
        results = []

        for memory in self._image_memories.values():
            if query_lower in memory.description.lower():
                results.append(memory)

        return results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_size = sum(f.size_bytes for f in self._file_memories.values())

        return {
            "total_images": len(self._image_memories),
            "total_files": len(self._file_memories),
            "total_size_bytes": total_size,
            "image_descriptions": [m.description for m in self._image_memories.values()],
        }

    def _generate_id(self, content: str) -> str:
        """生成唯一 ID"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# Global instance
_multimodal_store: Optional[MultimodalMemoryStore] = None


def get_multimodal_store(base_path: str = "./workspace/multimodal") -> MultimodalMemoryStore:
    """获取多模态存储实例"""
    global _multimodal_store
    if _multimodal_store is None:
        _multimodal_store = MultimodalMemoryStore(base_path)
    return _multimodal_store
