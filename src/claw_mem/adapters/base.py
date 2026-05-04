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
Base Adapter abstract class for OpenClaw version-specific strategies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class AdapterError(Exception):
    """Adapter-level error for version detection or strategy failures."""
    pass


class BaseAdapter(ABC):
    """
    Abstract base for version-specific adapter strategies.

    Each strategy encapsulates version-differentiated behaviors:
    - build_context: How memory context is assembled for prompt injection
    - resolve_flush_plan: How compaction thresholds are calculated
    - format_search_result: How individual search hits are formatted
    - get_initialize_response: What the bridge sends on startup
    """

    @abstractmethod
    def get_version(self) -> str:
        """Return the OpenClaw version this strategy targets (e.g. '2.8.0')."""
        ...

    @abstractmethod
    def build_context(self, memory_manager: Any, params: Dict) -> Dict:
        """
        Build layered/tiered memory context for prompt injection.

        Args:
            memory_manager: The MemoryManager instance for memory access.
            params: Request parameters including topK and query.

        Returns:
            Dict with 'context', 'count', and optional 'token_info'.
        """
        ...

    @abstractmethod
    def resolve_flush_plan(self, memory_manager: Any, params: Dict) -> Dict:
        """
        Compute a dynamic compaction (flush) plan based on memory state.

        Args:
            memory_manager: The MemoryManager instance for memory stats.
            params: Request parameters.

        Returns:
            Dict with threshold values, prompt strings, and compaction path.
        """
        ...

    @abstractmethod
    def format_search_result(self, result: Dict) -> Dict:
        """
        Format a single raw search result into a normalized dict.

        Args:
            result: Raw memory dict from MemoryManager.search().

        Returns:
            Normalized dict with version-appropriate field names.
        """
        ...

    @abstractmethod
    def get_initialize_response(self) -> Dict:
        """
        Return the startup response sent by the bridge after initialization.

        Returns:
            Dict with version-specific status info.
        """
        ...
