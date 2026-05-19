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
claw-mem decay module - Oblivion forgetting mechanism (v2.14.0)

Provides edge-level exponential decay for the MultiGraphMemory,
replacing the legacy MemoryDecay class.

Core components:
  - DecayConfig: Tunable configuration dataclass.
  - DecayController: Edge weight computation and cleanup.
  - DecayScheduler: Periodic + event-driven decay triggering.
"""

from .controller import DecayController
from .functions import (
    HALF_LIFE,
    LAMBDA,
    DecayConfig,
    calculate_weight,
    exponential_decay,
    half_life_to_days,
)
from .scheduler import DecayScheduler

__all__ = [
    "exponential_decay",
    "calculate_weight",
    "half_life_to_days",
    "DecayConfig",
    "HALF_LIFE",
    "LAMBDA",
    "DecayController",
    "DecayScheduler",
]
