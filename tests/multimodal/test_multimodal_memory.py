"""
Tests for claw-mem Multimodal Module (v2.4.0)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from datetime import datetime


class TestMemoryType:
    """Test MemoryType enum"""

    def test_type_values(self):
        from claw_mem.multimodal import MemoryType
        assert MemoryType.TEXT.value == "text"
        assert MemoryType.IMAGE.value == "image"
        assert MemoryType.FILE.value == "file"
        assert MemoryType.AUDIO.value == "audio"
        assert MemoryType.VIDEO.value == "video"


class TestImageMemory:
    """Test ImageMemory dataclass"""

    def test_creation(self):
        from claw_mem.multimodal import ImageMemory
        memory = ImageMemory(
            image_id="img-001",
            description="A sunset",
            path="/path/to/image.png"
        )
        assert memory.image_id == "img-001"
        assert memory.description == "A sunset"
        assert memory.path == "/path/to/image.png"


class TestFileMemory:
    """Test FileMemory dataclass"""

    def test_creation(self):
        from claw_mem.multimodal import FileMemory
        memory = FileMemory(
            file_id="file-001",
            filename="document.pdf",
            file_type="pdf",
            path="/path/to/file.pdf",
            size_bytes=1024
        )
        assert memory.file_id == "file-001"
        assert memory.filename == "document.pdf"
        assert memory.file_type == "pdf"
        assert memory.size_bytes == 1024


class TestMultimodalMemoryStore:
    """Test MultimodalMemoryStore"""

    @pytest.fixture
    def store(self):
        import claw_mem.multimodal as modal_module
        modal_module._multimodal_store = None
        from claw_mem.multimodal import get_multimodal_store
        return get_multimodal_store('./workspace-test/multimodal')

    def test_store_image(self, store):
        """Test storing image memory"""
        image_id = store.store_image('/path/to/image.png', 'A beautiful sunset')
        assert image_id is not None
        assert len(image_id) > 0

    def test_store_file(self, store):
        """Test storing file memory"""
        file_id = store.store_file('/path/to/file.pdf', 'pdf')
        assert file_id is not None
        assert len(file_id) > 0

    def test_get_image(self, store):
        """Test retrieving image memory"""
        image_id = store.store_image('/path/to/image.png', 'Test image')
        retrieved = store.get_image(image_id)

        assert retrieved is not None
        assert retrieved.image_id == image_id
        assert retrieved.description == 'Test image'

    def test_get_file(self, store):
        """Test retrieving file memory"""
        file_id = store.store_file('/path/to/file.pdf', 'pdf')
        retrieved = store.get_file(file_id)

        assert retrieved is not None
        assert retrieved.file_id == file_id
        assert retrieved.file_type == 'pdf'

    def test_get_stats(self, store):
        """Test getting statistics"""
        store.store_image('/path/to/image.png', 'Image 1')
        store.store_file('/path/to/file.pdf', 'pdf')

        stats = store.get_stats()
        assert 'total_images' in stats
        assert 'total_files' in stats
        assert stats['total_images'] >= 1
        assert stats['total_files'] >= 1


class TestGetMultimodalStore:
    """Test get_multimodal_store function"""

    def test_singleton(self):
        import claw_mem.multimodal as modal_module
        modal_module._multimodal_store = None

        from claw_mem.multimodal import get_multimodal_store
        store1 = get_multimodal_store('./workspace-test/multimodal')
        store2 = get_multimodal_store('./workspace-test/multimodal')

        assert store1 is store2
