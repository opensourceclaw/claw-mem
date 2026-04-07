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
Data Portability Module

Provides export and import capabilities for claw-mem data.

This is a key differentiator from short-term context management:
users own their data and can export it in standard formats,
ensuring 100% data portability.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import zipfile
import tempfile
import shutil


@dataclass
class ExportOptions:
    """Options for data export"""
    include_memories: bool = True
    include_timeline: bool = True
    include_knowledge_graph: bool = True
    include_decisions: bool = True
    include_firsts: bool = True
    include_config: bool = False
    format: str = "json"  # json, markdown, or both
    compress: bool = True


@dataclass
class ImportOptions:
    """Options for data import"""
    merge: bool = True  # Merge with existing data or replace
    validate: bool = True  # Validate data before import
    skip_errors: bool = False  # Skip invalid entries or fail


@dataclass
class ExportResult:
    """Result of export operation"""
    success: bool
    path: Optional[str] = None
    format: str = "json"
    size_bytes: int = 0
    entries_exported: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class ImportResult:
    """Result of import operation"""
    success: bool
    entries_imported: int = 0
    entries_skipped: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DataPortability:
    """
    Data export and import for claw-mem.
    
    This ensures 100% data portability - users own their data
    and can export it in standard formats.
    
    Features:
    - Export to JSON (structured, machine-readable)
    - Export to Markdown (human-readable, portable)
    - Export to ZIP archive (complete backup)
    - Import from JSON/ZIP
    - Merge or replace on import
    - Validate data on import
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize DataPortability.
        
        Args:
            workspace: Path to claw-mem workspace
        """
        self.workspace = workspace
        self.export_dir = workspace / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_json(
        self,
        output_path: Optional[str] = None,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export all data to JSON format.
        
        Args:
            output_path: Optional output file path
            options: Export options
            
        Returns:
            ExportResult with export details
        """
        if options is None:
            options = ExportOptions()
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.export_dir / f"claw-mem-export-{timestamp}.json")
        
        try:
            data = {
                "version": "2.0.0",
                "exported_at": datetime.now().isoformat(),
                "source": "claw-mem",
                "data": {}
            }
            
            entries_count = 0
            errors = []
            
            # Export timeline
            if options.include_timeline:
                timeline_data = self._export_timeline()
                data["data"]["timeline"] = timeline_data
                entries_count += len(timeline_data.get("events", []))
            
            # Export knowledge graph
            if options.include_knowledge_graph:
                kg_data = self._export_knowledge_graph()
                data["data"]["knowledge_graph"] = kg_data
                entries_count += len(kg_data.get("entities", []))
                entries_count += len(kg_data.get("relations", []))
            
            # Export decisions
            if options.include_decisions:
                decisions_data = self._export_decisions()
                data["data"]["decisions"] = decisions_data
                entries_count += len(decisions_data)
            
            # Export firsts
            if options.include_firsts:
                firsts_data = self._export_firsts()
                data["data"]["firsts"] = firsts_data
                entries_count += len(firsts_data)
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            size_bytes = os.path.getsize(output_path)
            
            return ExportResult(
                success=True,
                path=output_path,
                format="json",
                size_bytes=size_bytes,
                entries_exported=entries_count,
                errors=errors,
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[str(e)],
            )
    
    def export_to_markdown(
        self,
        output_dir: Optional[str] = None,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export all data to Markdown format (human-readable).
        
        Args:
            output_dir: Optional output directory
            options: Export options
            
        Returns:
            ExportResult with export details
        """
        if options is None:
            options = ExportOptions()
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = str(self.export_dir / f"claw-mem-export-{timestamp}")
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            entries_count = 0
            errors = []
            
            # Export README
            readme_content = self._generate_readme()
            with open(output_path / "README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            # Export timeline
            if options.include_timeline:
                timeline_md = self._export_timeline_markdown()
                with open(output_path / "TIMELINE.md", "w", encoding="utf-8") as f:
                    f.write(timeline_md)
                entries_count += timeline_md.count("## ")
            
            # Export knowledge graph
            if options.include_knowledge_graph:
                kg_md = self._export_knowledge_graph_markdown()
                with open(output_path / "KNOWLEDGE_GRAPH.md", "w", encoding="utf-8") as f:
                    f.write(kg_md)
                entries_count += kg_md.count("- ")
            
            # Export decisions
            if options.include_decisions:
                decisions_md = self._export_decisions_markdown()
                with open(output_path / "DECISIONS.md", "w", encoding="utf-8") as f:
                    f.write(decisions_md)
                entries_count += decisions_md.count("### ")
            
            # Calculate total size
            total_size = sum(
                os.path.getsize(output_path / f)
                for f in os.listdir(output_path)
                if os.path.isfile(output_path / f)
            )
            
            return ExportResult(
                success=True,
                path=output_dir,
                format="markdown",
                size_bytes=total_size,
                entries_exported=entries_count,
                errors=errors,
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[str(e)],
            )
    
    def export_to_zip(
        self,
        output_path: Optional[str] = None,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        """
        Export all data to a ZIP archive (complete backup).
        
        Args:
            output_path: Optional output file path
            options: Export options
            
        Returns:
            ExportResult with export details
        """
        if options is None:
            options = ExportOptions()
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.export_dir / f"claw-mem-backup-{timestamp}.zip")
        
        try:
            # Create temp directory for export
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Export JSON
                json_path = temp_path / "data.json"
                json_result = self.export_to_json(str(json_path), options)
                
                if not json_result.success:
                    return json_result
                
                # Export Markdown
                md_dir = temp_path / "markdown"
                md_result = self.export_to_markdown(str(md_dir), options)
                
                # Create ZIP
                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    # Add JSON
                    zf.write(json_path, "data.json")
                    
                    # Add Markdown files
                    if md_result.success:
                        for file_path in md_dir.glob("*.md"):
                            zf.write(file_path, f"markdown/{file_path.name}")
                
                size_bytes = os.path.getsize(output_path)
                entries_count = json_result.entries_exported
                
                return ExportResult(
                    success=True,
                    path=output_path,
                    format="zip",
                    size_bytes=size_bytes,
                    entries_exported=entries_count,
                    errors=[],
                )
                
        except Exception as e:
            return ExportResult(
                success=False,
                errors=[str(e)],
            )
    
    def import_from_json(
        self,
        input_path: str,
        options: Optional[ImportOptions] = None,
    ) -> ImportResult:
        """
        Import data from JSON file.
        
        Args:
            input_path: Path to JSON file
            options: Import options
            
        Returns:
            ImportResult with import details
        """
        if options is None:
            options = ImportOptions()
        
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Validate structure
            if options.validate:
                if not self._validate_import_data(data):
                    return ImportResult(
                        success=False,
                        errors=["Invalid data structure"],
                    )
            
            entries_imported = 0
            entries_skipped = 0
            errors = []
            
            # Import timeline
            if "timeline" in data.get("data", {}):
                imported, skipped, errs = self._import_timeline(
                    data["data"]["timeline"],
                    merge=options.merge,
                )
                entries_imported += imported
                entries_skipped += skipped
                errors.extend(errs)
            
            # Import knowledge graph
            if "knowledge_graph" in data.get("data", {}):
                imported, skipped, errs = self._import_knowledge_graph(
                    data["data"]["knowledge_graph"],
                    merge=options.merge,
                )
                entries_imported += imported
                entries_skipped += skipped
                errors.extend(errs)
            
            # Import decisions
            if "decisions" in data.get("data", {}):
                imported, skipped, errs = self._import_decisions(
                    data["data"]["decisions"],
                    merge=options.merge,
                )
                entries_imported += imported
                entries_skipped += skipped
                errors.extend(errs)
            
            # Import firsts
            if "firsts" in data.get("data", {}):
                imported, skipped, errs = self._import_firsts(
                    data["data"]["firsts"],
                    merge=options.merge,
                )
                entries_imported += imported
                entries_skipped += skipped
                errors.extend(errs)
            
            return ImportResult(
                success=True,
                entries_imported=entries_imported,
                entries_skipped=entries_skipped,
                errors=errors if not options.skip_errors else [],
            )
            
        except Exception as e:
            return ImportResult(
                success=False,
                errors=[str(e)],
            )
    
    def import_from_zip(
        self,
        input_path: str,
        options: Optional[ImportOptions] = None,
    ) -> ImportResult:
        """
        Import data from ZIP archive.
        
        Args:
            input_path: Path to ZIP file
            options: Import options
            
        Returns:
            ImportResult with import details
        """
        if options is None:
            options = ImportOptions()
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract ZIP
                with zipfile.ZipFile(input_path, "r") as zf:
                    zf.extractall(temp_path)
                
                # Import from JSON
                json_path = temp_path / "data.json"
                if json_path.exists():
                    return self.import_from_json(str(json_path), options)
                else:
                    return ImportResult(
                        success=False,
                        errors=["No data.json found in archive"],
                    )
                    
        except Exception as e:
            return ImportResult(
                success=False,
                errors=[str(e)],
            )
    
    def migrate_from_openclaw_dream(
        self,
        dream_export_path: str,
        options: Optional[ImportOptions] = None,
    ) -> ImportResult:
        """
        Migrate data from OpenClaw Dream format.
        
        This allows users to migrate from OpenClaw's built-in
        memory system to claw-mem.
        
        Args:
            dream_export_path: Path to OpenClaw Dream export
            options: Import options
            
        Returns:
            ImportResult with migration details
        """
        if options is None:
            options = ImportOptions()
        
        try:
            # Try to detect format and convert
            # This is a placeholder - actual implementation would
            # need to understand OpenClaw Dream's export format
            return ImportResult(
                success=False,
                errors=["OpenClaw Dream migration not yet implemented"],
            )
            
        except Exception as e:
            return ImportResult(
                success=False,
                errors=[str(e)],
            )
    
    # Internal export methods
    
    def _export_timeline(self) -> Dict[str, Any]:
        """Export timeline data"""
        timeline_dir = self.workspace / "timeline"
        if not timeline_dir.exists():
            return {"events": []}
        
        events = []
        for year_file in timeline_dir.glob("year_*.json"):
            with open(year_file, "r", encoding="utf-8") as f:
                year_events = json.load(f)
                events.extend(year_events)
        
        return {"events": events}
    
    def _export_knowledge_graph(self) -> Dict[str, Any]:
        """Export knowledge graph data"""
        kg_dir = self.workspace / "knowledge_graph"
        if not kg_dir.exists():
            return {"entities": [], "relations": []}
        
        entities = []
        entities_file = kg_dir / "entities.json"
        if entities_file.exists():
            with open(entities_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                entities = data.get("entities", [])
        
        relations = []
        relations_file = kg_dir / "relations.json"
        if relations_file.exists():
            with open(relations_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                relations = data.get("relations", [])
        
        return {"entities": entities, "relations": relations}
    
    def _export_decisions(self) -> List[Dict[str, Any]]:
        """Export decisions data"""
        decisions_dir = self.workspace / "decisions"
        decisions_file = decisions_dir / "decisions.json"
        
        if not decisions_file.exists():
            return []
        
        with open(decisions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("decisions", [])
    
    def _export_firsts(self) -> List[Dict[str, Any]]:
        """Export first events data"""
        # First events are stored in timeline with type "first_time"
        timeline_data = self._export_timeline()
        return [
            e for e in timeline_data.get("events", [])
            if e.get("event_type") == "first_time"
        ]
    
    def _generate_readme(self) -> str:
        """Generate README for export"""
        return """# claw-mem Data Export

This export contains your digital life data from claw-mem.

## Files

- `data.json` - Complete structured data export
- `markdown/` - Human-readable Markdown export
  - `TIMELINE.md` - Your life timeline
  - `KNOWLEDGE_GRAPH.md` - People, places, and connections
  - `DECISIONS.md` - Important decisions you've made

## Data Ownership

This data belongs to you. You can:
- Import it into another claw-mem instance
- Convert it to other formats
- Store it anywhere you want
- Share it or keep it private

## Import Instructions

To import this data into claw-mem:

```python
from claw_mem import DataPortability

dp = DataPortability(workspace_path)
result = dp.import_from_zip("claw-mem-backup.zip")
print(f"Imported {result.entries_imported} entries")
```

## About claw-mem

claw-mem is your digital memory system - "Your digital life, preserved forever"

https://github.com/opensourceclaw/claw-mem
"""
    
    def _export_timeline_markdown(self) -> str:
        """Export timeline as Markdown"""
        timeline_data = self._export_timeline()
        events = timeline_data.get("events", [])
        
        if not events:
            return "# Timeline\n\nNo events recorded yet.\n"
        
        md = "# Life Timeline\n\n"
        
        # Group by year
        events_by_year = {}
        for event in events:
            year = event.get("timestamp", "")[:4]
            if year not in events_by_year:
                events_by_year[year] = []
            events_by_year[year].append(event)
        
        # Sort years descending
        for year in sorted(events_by_year.keys(), reverse=True):
            md += f"## {year}\n\n"
            
            for event in events_by_year[year]:
                title = event.get("title", "Untitled")
                event_type = event.get("event_type", "other")
                importance = event.get("importance", 0.5)
                
                # Importance indicator
                if importance >= 0.7:
                    indicator = "⭐ "
                elif importance >= 0.5:
                    indicator = "• "
                else:
                    indicator = "- "
                
                md += f"{indicator}**{title}** ({event_type})\n"
                
                if event.get("description"):
                    md += f"  {event['description']}\n"
                
                md += "\n"
        
        return md
    
    def _export_knowledge_graph_markdown(self) -> str:
        """Export knowledge graph as Markdown"""
        kg_data = self._export_knowledge_graph()
        entities = kg_data.get("entities", [])
        relations = kg_data.get("relations", [])
        
        md = "# Knowledge Graph\n\n"
        
        if not entities:
            md += "No entities recorded yet.\n"
            return md
        
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            etype = entity.get("entity_type", "other")
            if etype not in entities_by_type:
                entities_by_type[etype] = []
            entities_by_type[etype].append(entity)
        
        # Export by type
        type_names = {
            "person": "People",
            "place": "Places",
            "organization": "Organizations",
            "thing": "Things",
            "concept": "Concepts",
            "event": "Events",
            "skill": "Skills",
            "project": "Projects",
            "topic": "Topics",
            "other": "Other",
        }
        
        for etype, type_entities in entities_by_type.items():
            type_name = type_names.get(etype, etype.title())
            md += f"## {type_name}\n\n"
            
            for entity in type_entities:
                name = entity.get("name", "Unknown")
                md += f"- **{name}**"
                
                if entity.get("aliases"):
                    md += f" ({', '.join(entity['aliases'])})"
                
                if entity.get("description"):
                    md += f"\n  {entity['description']}"
                
                md += "\n"
            
            md += "\n"
        
        # Relations
        if relations:
            md += "## Relationships\n\n"
            for relation in relations:
                from_id = relation.get("from_entity_id", "")
                to_id = relation.get("to_entity_id", "")
                rel_type = relation.get("relation_type", "related_to")
                md += f"- {from_id} → {rel_type} → {to_id}\n"
        
        return md
    
    def _export_decisions_markdown(self) -> str:
        """Export decisions as Markdown"""
        decisions = self._export_decisions()
        
        md = "# Important Decisions\n\n"
        
        if not decisions:
            md += "No decisions recorded yet.\n"
            return md
        
        for decision in decisions:
            title = decision.get("title", "Untitled Decision")
            status = decision.get("status", "made")
            decision_type = decision.get("decision_type", "other")
            
            status_emoji = {
                "made": "🔄",
                "completed": "✅",
                "revised": "📝",
                "abandoned": "❌",
            }.get(status, "•")
            
            md += f"### {status_emoji} {title}\n\n"
            md += f"- **Type:** {decision_type}\n"
            md += f"- **Status:** {status}\n"
            
            if decision.get("description"):
                md += f"- **Description:** {decision['description']}\n"
            
            if decision.get("chosen_option"):
                md += f"- **Decision:** {decision['chosen_option']}\n"
            
            if decision.get("reasoning"):
                md += f"- **Reasoning:** {decision['reasoning']}\n"
            
            if decision.get("lessons_learned"):
                md += f"- **Lessons:** {', '.join(decision['lessons_learned'])}\n"
            
            md += "\n"
        
        return md
    
    # Internal import methods
    
    def _validate_import_data(self, data: Dict[str, Any]) -> bool:
        """Validate import data structure"""
        if not isinstance(data, dict):
            return False
        
        if "version" not in data:
            return False
        
        if "data" not in data:
            return False
        
        return True
    
    def _import_timeline(
        self,
        timeline_data: Dict[str, Any],
        merge: bool = True,
    ) -> tuple:
        """Import timeline data"""
        events = timeline_data.get("events", [])
        
        if not merge:
            # Clear existing timeline
            timeline_dir = self.workspace / "timeline"
            if timeline_dir.exists():
                shutil.rmtree(timeline_dir)
            timeline_dir.mkdir(parents=True, exist_ok=True)
        
        imported = 0
        skipped = 0
        errors = []
        
        timeline_dir = self.workspace / "timeline"
        timeline_dir.mkdir(parents=True, exist_ok=True)
        
        for event in events:
            try:
                year = event.get("timestamp", "")[:4]
                if not year:
                    skipped += 1
                    continue
                
                year_file = timeline_dir / f"year_{year}.json"
                
                # Load existing
                year_events = []
                if year_file.exists() and merge:
                    with open(year_file, "r", encoding="utf-8") as f:
                        year_events = json.load(f)
                
                # Check for duplicates
                event_id = event.get("event_id")
                if merge and any(e.get("event_id") == event_id for e in year_events):
                    skipped += 1
                    continue
                
                year_events.append(event)
                
                # Save
                with open(year_file, "w", encoding="utf-8") as f:
                    json.dump(year_events, f, indent=2, ensure_ascii=False)
                
                imported += 1
                
            except Exception as e:
                errors.append(f"Failed to import event: {str(e)}")
        
        return imported, skipped, errors
    
    def _import_knowledge_graph(
        self,
        kg_data: Dict[str, Any],
        merge: bool = True,
    ) -> tuple:
        """Import knowledge graph data"""
        entities = kg_data.get("entities", [])
        relations = kg_data.get("relations", [])
        
        imported = 0
        skipped = 0
        errors = []
        
        kg_dir = self.workspace / "knowledge_graph"
        kg_dir.mkdir(parents=True, exist_ok=True)
        
        # Import entities
        entities_file = kg_dir / "entities.json"
        existing_entities = []
        if entities_file.exists() and merge:
            with open(entities_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_entities = data.get("entities", [])
        
        entity_ids = {e.get("entity_id") for e in existing_entities}
        
        for entity in entities:
            entity_id = entity.get("entity_id")
            if merge and entity_id in entity_ids:
                skipped += 1
                continue
            
            existing_entities.append(entity)
            imported += 1
        
        with open(entities_file, "w", encoding="utf-8") as f:
            json.dump({"entities": existing_entities}, f, indent=2, ensure_ascii=False)
        
        # Import relations
        relations_file = kg_dir / "relations.json"
        existing_relations = []
        if relations_file.exists() and merge:
            with open(relations_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_relations = data.get("relations", [])
        
        relation_ids = {r.get("relation_id") for r in existing_relations}
        
        for relation in relations:
            relation_id = relation.get("relation_id")
            if merge and relation_id in relation_ids:
                skipped += 1
                continue
            
            existing_relations.append(relation)
            imported += 1
        
        with open(relations_file, "w", encoding="utf-8") as f:
            json.dump({"relations": existing_relations}, f, indent=2, ensure_ascii=False)
        
        return imported, skipped, errors
    
    def _import_decisions(
        self,
        decisions_data: List[Dict[str, Any]],
        merge: bool = True,
    ) -> tuple:
        """Import decisions data"""
        decisions_dir = self.workspace / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)
        
        decisions_file = decisions_dir / "decisions.json"
        existing_decisions = []
        
        if decisions_file.exists() and merge:
            with open(decisions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_decisions = data.get("decisions", [])
        
        imported = 0
        skipped = 0
        errors = []
        
        decision_ids = {d.get("decision_id") for d in existing_decisions}
        
        for decision in decisions_data:
            decision_id = decision.get("decision_id")
            if merge and decision_id in decision_ids:
                skipped += 1
                continue
            
            existing_decisions.append(decision)
            imported += 1
        
        with open(decisions_file, "w", encoding="utf-8") as f:
            json.dump({"decisions": existing_decisions}, f, indent=2, ensure_ascii=False)
        
        return imported, skipped, errors
    
    def _import_firsts(
        self,
        firsts_data: List[Dict[str, Any]],
        merge: bool = True,
    ) -> tuple:
        """Import first events (stored in timeline)"""
        # First events are stored in timeline
        # Add event_type if missing
        for event in firsts_data:
            if "event_type" not in event:
                event["event_type"] = "first_time"
        
        return self._import_timeline({"events": firsts_data}, merge)
