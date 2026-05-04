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
AdapterRegistry: Version detection and strategy/adapter factory.

Detection priority:
1. OPENCLAW_VERSION environment variable
2. Configuration file (~/.openclaw/openclaw.json)
3. Default: v2 (current)
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from .base import BaseAdapter, AdapterError
from .v1 import V1Strategy
from .v2 import V2Strategy
from .openclaw_adapter import OpenClawAdapter


class AdapterRegistry:
    """Factory for creating version-appropriate adapter strategies."""

    # Map version major numbers to strategy classes
    _strategies = {
        "v1": V1Strategy,
        "1": V1Strategy,
        "v2": V2Strategy,
        "2": V2Strategy,
    }

    @classmethod
    def detect_version_key(cls) -> str:
        """
        Detect the OpenClaw version to use.

        Priority:
        1. OPENCLAW_VERSION env var
        2. ~/.openclaw/openclaw.json config
        3. Default: 'v2'
        """
        # 1. Environment variable
        env_version = os.environ.get("OPENCLAW_VERSION")
        if env_version:
            env_version = env_version.strip()
            env_major = env_version.split(".")[0]
            if env_major in cls._strategies:
                return f"v{env_major}"
            return f"v{env_major}"

        # 2. Config file
        config_path = Path.home() / ".openclaw" / "openclaw.json"
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    version = config.get("version", "2")
                    version = str(version).strip()
                    version_major = version.split(".")[0]
                    if version_major in cls._strategies:
                        return f"v{version_major}"
                    return f"v{version_major}"
        except (json.JSONDecodeError, IOError, OSError):
            pass

        # 3. Default
        return "v2"

    @classmethod
    def create_strategy(cls, version_key: Optional[str] = None) -> BaseAdapter:
        """
        Create a version-specific strategy instance.

        Args:
            version_key: Version key (e.g. 'v1', 'v2'). Auto-detected if None.

        Returns:
            BaseAdapter strategy instance.

        Raises:
            AdapterError: If version_key is unrecognized.
        """
        if version_key is None:
            version_key = cls.detect_version_key()

        strategy_cls = cls._strategies.get(version_key)
        if strategy_cls is None:
            raise AdapterError(
                f"Unknown adapter version: '{version_key}'. "
                f"Supported: {list(cls._strategies.keys())}"
            )

        return strategy_cls()

    @classmethod
    def create_adapter(
        cls,
        memory_manager: Any,
        version_key: Optional[str] = None,
    ) -> OpenClawAdapter:
        """
        Create a full OpenClawAdapter with detected strategy.

        Args:
            memory_manager: The MemoryManager instance to wrap.
            version_key: Version key override. Auto-detected if None.

        Returns:
            Configured OpenClawAdapter instance.
        """
        strategy = cls.create_strategy(version_key)
        return OpenClawAdapter(memory_manager, strategy)
