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
Tests for Data Portability Module
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import json
import zipfile

from claw_mem.data_portability import (
    DataPortability,
    ExportOptions,
    ImportOptions,
    ExportResult,
    ImportResult,
)


class TestExportOptions:
    """Tests for ExportOptions"""
    
    def test_default_options(self):
        """Test default export options"""
        options = ExportOptions()
        
        assert options.include_memories is True
        assert options.include_timeline is True
        assert options.include_knowledge_graph is True
        assert options.format == "json"
        assert options.compress is True
    
    def test_custom_options(self):
        """Test custom export options"""
        options = ExportOptions(
            include_memories=False,
            include_timeline=True,
            format="markdown",
        )
        
        assert options.include_memories is False
        assert options.include_timeline is True
        assert options.format == "markdown"


class TestImportOptions:
    """Tests for ImportOptions"""
    
    def test_default_options(self):
        """Test default import options"""
        options = ImportOptions()
        
        assert options.merge is True
        assert options.validate is True
        assert options.skip_errors is False


class TestDataPortability:
    """Tests for DataPortability"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def dp(self, temp_workspace):
        """Create DataPortability instance"""
        return DataPortability(temp_workspace)
    
    def test_export_to_json_empty(self, dp):
        """Test exporting empty data to JSON"""
        result = dp.export_to_json()
        
        assert result.success is True
        assert result.format == "json"
        assert result.entries_exported == 0
    
    def test_export_to_json_with_timeline(self, dp, temp_workspace):
        """Test exporting with timeline data"""
        # Create some timeline data
        timeline_dir = temp_workspace / "timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        events = [
            {
                "event_id": "evt_001",
                "title": "Test Event",
                "event_type": "milestone",
                "timestamp": "2026-04-07T10:00:00",
            }
        ]
        
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events, f)
        
        result = dp.export_to_json()
        
        assert result.success is True
        assert result.entries_exported == 1
        assert result.size_bytes > 0
    
    def test_export_to_markdown_empty(self, dp):
        """Test exporting empty data to Markdown"""
        result = dp.export_to_markdown()
        
        assert result.success is True
        assert result.format == "markdown"
    
    def test_export_to_markdown_with_data(self, dp, temp_workspace):
        """Test exporting with data to Markdown"""
        # Create timeline data
        timeline_dir = temp_workspace / "timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        events = [
            {
                "event_id": "evt_001",
                "title": "Test Event",
                "description": "A test event",
                "event_type": "milestone",
                "timestamp": "2026-04-07T10:00:00",
                "importance": 0.8,
            }
        ]
        
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events, f)
        
        result = dp.export_to_markdown()
        
        assert result.success is True
        assert result.path is not None
    
    def test_export_to_zip(self, dp):
        """Test exporting to ZIP archive"""
        result = dp.export_to_zip()
        
        assert result.success is True
        assert result.format == "zip"
        assert result.path is not None
        assert result.path.endswith(".zip")
    
    def test_export_to_zip_creates_valid_archive(self, dp):
        """Test that ZIP archive is valid"""
        result = dp.export_to_zip()
        
        assert result.success is True
        
        # Verify ZIP is valid
        with zipfile.ZipFile(result.path, "r") as zf:
            files = zf.namelist()
            assert "data.json" in files
    
    def test_import_from_json_empty(self, dp):
        """Test importing empty JSON"""
        # Create empty export
        export_result = dp.export_to_json()
        
        # Import it
        import_result = dp.import_from_json(export_result.path)
        
        assert import_result.success is True
        assert import_result.entries_imported == 0
    
    def test_import_from_json_with_data(self, dp, temp_workspace):
        """Test importing JSON with data"""
        # Create export with data
        timeline_dir = temp_workspace / "timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        events = [
            {
                "event_id": "evt_001",
                "title": "Test Event",
                "event_type": "milestone",
                "timestamp": "2026-04-07T10:00:00",
            }
        ]
        
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events, f)
        
        # Export
        export_result = dp.export_to_json()
        
        # Clear timeline
        shutil.rmtree(timeline_dir)
        
        # Import
        import_result = dp.import_from_json(export_result.path)
        
        assert import_result.success is True
        assert import_result.entries_imported >= 1
    
    def test_import_from_zip(self, dp):
        """Test importing from ZIP archive"""
        # Create export
        export_result = dp.export_to_zip()
        
        # Import
        import_result = dp.import_from_zip(export_result.path)
        
        assert import_result.success is True
    
    def test_import_validates_structure(self, dp, temp_workspace):
        """Test that import validates data structure"""
        # Create invalid JSON
        invalid_path = temp_workspace / "invalid.json"
        with open(invalid_path, "w") as f:
            json.dump({"invalid": "data"}, f)
        
        # Import with validation
        import_result = dp.import_from_json(str(invalid_path))
        
        assert import_result.success is False
        assert len(import_result.errors) > 0
    
    def test_import_merge_mode(self, dp, temp_workspace):
        """Test import merge mode"""
        # Create initial data
        timeline_dir = temp_workspace / "timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        events1 = [{"event_id": "evt_001", "title": "Event 1", "timestamp": "2026-04-07"}]
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events1, f)
        
        # Export
        export_result = dp.export_to_json()
        
        # Add more data
        events2 = [{"event_id": "evt_002", "title": "Event 2", "timestamp": "2026-04-08"}]
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events1 + events2, f)
        
        # Import with merge (should keep existing data)
        import_result = dp.import_from_json(export_result.path, ImportOptions(merge=True))
        
        assert import_result.success is True
    
    def test_import_replace_mode(self, dp, temp_workspace):
        """Test import replace mode"""
        # Create initial data
        timeline_dir = temp_workspace / "timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        events1 = [{"event_id": "evt_001", "title": "Event 1", "timestamp": "2026-04-07"}]
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events1, f)
        
        # Export
        export_result = dp.export_to_json()
        
        # Add more data
        events2 = [{"event_id": "evt_002", "title": "Event 2", "timestamp": "2026-04-08"}]
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events1 + events2, f)
        
        # Import without merge (should replace existing data)
        import_result = dp.import_from_json(export_result.path, ImportOptions(merge=False))
        
        assert import_result.success is True
    
    def test_roundtrip(self, dp, temp_workspace):
        """Test export and import roundtrip"""
        # Create data
        timeline_dir = temp_workspace / "timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        events = [
            {
                "event_id": "evt_001",
                "title": "Original Event",
                "event_type": "milestone",
                "timestamp": "2026-04-07T10:00:00",
                "importance": 0.8,
            }
        ]
        
        with open(timeline_dir / "year_2026.json", "w") as f:
            json.dump(events, f)
        
        # Export
        export_result = dp.export_to_json()
        assert export_result.success is True
        
        # Clear
        shutil.rmtree(timeline_dir)
        
        # Import
        import_result = dp.import_from_json(export_result.path)
        assert import_result.success is True
        
        # Verify data
        timeline_dir.mkdir(parents=True, exist_ok=True)
        with open(timeline_dir / "year_2026.json") as f:
            imported_events = json.load(f)
        
        assert len(imported_events) == 1
        assert imported_events[0]["title"] == "Original Event"


class TestExportResult:
    """Tests for ExportResult"""
    
    def test_success_result(self):
        """Test successful export result"""
        result = ExportResult(
            success=True,
            path="/path/to/export.json",
            format="json",
            size_bytes=1024,
            entries_exported=10,
        )
        
        assert result.success is True
        assert result.path == "/path/to/export.json"
        assert result.entries_exported == 10
    
    def test_failure_result(self):
        """Test failed export result"""
        result = ExportResult(
            success=False,
            errors=["Error message"],
        )
        
        assert result.success is False
        assert len(result.errors) == 1


class TestImportResult:
    """Tests for ImportResult"""
    
    def test_success_result(self):
        """Test successful import result"""
        result = ImportResult(
            success=True,
            entries_imported=10,
            entries_skipped=2,
        )
        
        assert result.success is True
        assert result.entries_imported == 10
        assert result.entries_skipped == 2
    
    def test_failure_result(self):
        """Test failed import result"""
        result = ImportResult(
            success=False,
            errors=["Import failed"],
        )
        
        assert result.success is False
        assert len(result.errors) == 1
