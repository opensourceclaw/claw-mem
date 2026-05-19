# Copyright 2026 Peter Cheng
"""Global test fixtures to prevent test isolation issues."""

import pytest


@pytest.fixture(autouse=True)
def _reset_global_singletons():
    """Reset all module-level singletons after each test to prevent cross-test
    state contamination (v3.1.0 test isolation fix)."""
    yield
    # Reset synonym expander
    try:
        from claw_mem.retrieval import synonym_expander

        synonym_expander._synonym_expander = None
    except Exception:
        pass
    # Reset compressor V2
    try:
        from claw_mem.compression.memory_compression_v2 import reset_compressor

        reset_compressor()
    except Exception:
        pass
    # Reset compressor V1
    try:
        from claw_mem.compression import reset_compressor
    except Exception:
        pass
    try:
        from claw_mem.compression.memory_compression import _compressor
        import claw_mem.compression.memory_compression as mc

        mc._compressor = None
    except Exception:
        pass
