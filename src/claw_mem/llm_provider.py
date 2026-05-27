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
LLM Provider (v4.7.0)

Lightweight LLM generation interface shared by SemanticMergeScheduler (F1)
and ConflictDetector (F3). Supports OpenAI API-compatible backends.
"""

import os
from typing import Optional


class LLMProvider:
    """LLM generation provider for memory merge/detect tasks.

    Supported providers:
      - "openai": Uses the openai Python package.
      - "local":  Uses an OpenAI-compatible local endpoint (e.g. Ollama, vLLM).
      - "auto":   Tries local first, falls back to openai.

    On failure returns empty string so callers can degrade gracefully.
    """

    def __init__(
        self,
        provider: str = "auto",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1")

    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        """Generate text via the configured LLM backend.

        Returns empty string on any error so callers can degrade.
        """
        if self.provider == "openai":
            return self._openai_generate(prompt, system, max_tokens)
        elif self.provider == "local":
            return self._local_generate(prompt, system, max_tokens)
        else:  # auto
            result = self._local_generate(prompt, system, max_tokens)
            if result:
                return result
            return self._openai_generate(prompt, system, max_tokens)

    def _openai_generate(self, prompt: str, system: str, max_tokens: int) -> str:
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=self.api_key)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return ""

    def _local_generate(self, prompt: str, system: str, max_tokens: int) -> str:
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(
                api_key=self.api_key or "not-needed",
                base_url=self.base_url,
            )
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return ""

    def health_check(self) -> bool:
        """Check whether the configured LLM is reachable."""
        result = self.generate("Hello", max_tokens=8)
        return bool(result)

    def __repr__(self) -> str:
        return f"LLMProvider(provider={self.provider!r}, model={self.model!r})"
