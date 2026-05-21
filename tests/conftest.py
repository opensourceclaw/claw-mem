# Copyright 2026 Peter Cheng
"""Global test fixtures to prevent test isolation issues."""

import pytest

# All known singleton reset functions with their import paths.
# Each entry: (module_path, function_name)
_SINGLETON_RESETS = [
    # Config
    ("claw_mem.config_manager", None),  # reset_config not needed, reload_config exists
    # v3.2.0: Factory
    ("claw_mem.factories", "reset_default_factory"),
    # Compression
    ("claw_mem.compression.memory_compression", "reset_compressor"),
    ("claw_mem.compression.memory_compression_v2", "reset_compressor"),
    ("claw_mem.compression.f5_v2", "reset_f5_compressor"),
    ("claw_mem.compression.f5_v2", "reset_ultra_compressor"),
    # Retrieval (v3.2.0: only 2 active singletons remain)
    ("claw_mem.retrieval.search_stats", "reset_search_stats"),
    ("claw_mem.retrieval.query_cache", "reset_query_cache"),
    # Multimodal
    ("claw_mem.multimodal.multimodal_memory", "reset_multimodal_store"),
]


def _do_reset(module_path: str, func_name: str) -> None:
    """Import a reset function and call it, swallowing any errors."""
    try:
        mod = __import__(module_path, fromlist=[func_name])
        reset_fn = getattr(mod, func_name)
        reset_fn()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _reset_global_singletons():
    """Reset all module-level singletons before and after each test to prevent
    cross-test state contamination (v3.1.0 test isolation fix)."""
    # Reset before test (clean start)
    for module_path, func_name in _SINGLETON_RESETS:
        if func_name:
            _do_reset(module_path, func_name)

    yield

    # Reset after test (leave clean state)
    for module_path, func_name in _SINGLETON_RESETS:
        if func_name:
            _do_reset(module_path, func_name)
