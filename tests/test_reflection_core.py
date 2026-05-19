# Copyright 2026 Peter Cheng
"""Tests for reflection module."""

import pytest


class TestReflectionImports:
    def test_import_orchestrator(self):
        from claw_mem.reflection import ReflectionOrchestrator

        assert ReflectionOrchestrator is not None

    def test_import_synthesizer(self):
        from claw_mem.reflection.synthesizer import BeliefSynthesizer

        assert BeliefSynthesizer is not None

    def test_import_reflection_result(self):
        from claw_mem.reflection import ReflectionResult

        assert ReflectionResult is not None
