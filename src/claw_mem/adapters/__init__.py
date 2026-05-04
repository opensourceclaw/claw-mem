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
claw-mem Adapters

Strategy-based abstraction layer for OpenClaw version compatibilty.
Decouples claw-mem core from OpenClaw plugin architecture changes.
"""

from .base import BaseAdapter, AdapterError
from .v2 import V2Strategy
from .v1 import V1Strategy
from .openclaw_adapter import OpenClawAdapter, SearchCache
from .registry import AdapterRegistry

__all__ = [
    "BaseAdapter",
    "AdapterError",
    "V2Strategy",
    "V1Strategy",
    "OpenClawAdapter",
    "SearchCache",
    "AdapterRegistry",
]
