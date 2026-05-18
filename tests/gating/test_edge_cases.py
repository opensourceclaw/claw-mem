"""
Edge case tests - WriteTimeGating
"""

import pytest
import threading
from claw_mem.gating import WriteTimeGating, SalienceScorer


class TestWriteTimeGatingEdgeCases:
    """WriteTimeGating edge case tests"""

    def test_empty_item(self):
        """Test empty input"""
        gating = WriteTimeGating()
        result = gating.write({})
        # Should handle empty input without crash
        assert result.stored is True

    def test_none_content(self):
        """Test None content"""
        gating = WriteTimeGating()
        result = gating.write({"content": None})
        assert result.stored is True

    def test_very_long_content(self):
        """Test very long content"""
        gating = WriteTimeGating()
        long_content = "test" * 10000  # ~20,000 characters
        result = gating.write({"content": long_content})
        assert result.stored is True

    def test_special_characters(self):
        """Test special characters"""
        gating = WriteTimeGating()
        special = "\n\t\r\0\x00\\\"'"
        result = gating.write({"content": special})
        assert result.stored is True

    def test_unicode_content(self):
        """Test Unicode content"""
        gating = WriteTimeGating()
        unicode_content = "中文🎉🚀💎\u0000\uffff"
        result = gating.write({"content": unicode_content})
        assert result.stored is True

    def test_extreme_salience_scores(self):
        """Test extreme salience scores"""
        gating = WriteTimeGating(threshold=0.5)

        # Very high salience
        high_item = {
            "content": "critical information",
            "source": "user",
            "verified": True,
            "context": {"key": "value"},
        }
        result = gating.write(high_item)
        assert result.tier == "active"

        # Very low salience
        low_item = {"content": "ordinary info", "source": "external", "verified": False}
        result = gating.write(low_item)
        assert result.stored is True

    def test_threshold_boundary(self):
        """Test threshold boundary"""
        gating = WriteTimeGating(threshold=0.6)

        boundary_item = {"content": "boundary test", "source": "agent"}
        result = gating.write(boundary_item)
        assert result.stored is True

    def test_concurrent_writes(self):
        """Test concurrent writes"""
        gating = WriteTimeGating()
        results = []

        def write_item(i):
            result = gating.write({"content": f"item_{i}", "source": "user"})
            results.append(result)

        threads = [threading.Thread(target=write_item, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r.stored for r in results)

    def test_all_source_types(self):
        """Test all source types"""
        gating = WriteTimeGating()
        sources = ["user", "agent", "system", "external"]

        for source in sources:
            result = gating.write({"content": "test", "source": source})
            assert result.stored is True
            assert result.tier in ["active", "cold"]


class TestSalienceScorerEdgeCases:
    """SalienceScorer edge case tests"""

    def test_empty_content(self):
        """Test empty content"""
        scorer = SalienceScorer()
        score = scorer.compute({"content": "", "source": "user"})
        assert 0.0 <= score <= 1.0

    def test_unknown_source(self):
        """Test unknown source"""
        scorer = SalienceScorer()
        score = scorer.compute({"content": "test", "source": "unknown"})
        assert 0.0 <= score <= 1.0

    def test_missing_fields(self):
        """Test missing fields"""
        scorer = SalienceScorer()
        score = scorer.compute({})
        assert 0.0 <= score <= 1.0

    def test_repeated_content(self):
        """Test repeated content"""
        scorer = SalienceScorer()

        score1 = scorer.compute({"content": "repeated content", "source": "user"})
        score2 = scorer.compute({"content": "repeated content", "source": "user"})

        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0

    def test_very_long_content(self):
        """Test very long content"""
        scorer = SalienceScorer()
        long_content = "test" * 10000
        score = scorer.compute({"content": long_content, "source": "user"})
        assert 0.0 <= score <= 1.0

    def test_all_source_types(self):
        """Test all source types"""
        scorer = SalienceScorer()
        sources = ["user", "agent", "system", "external", "unknown"]

        for source in sources:
            score = scorer.compute({"content": "test", "source": source})
            assert 0.0 <= score <= 1.0, f"Source {source} failed"


class TestErrorHandling:
    """Error handling tests"""

    def test_custom_weights(self):
        """Test custom weights"""
        weights = {"source_reputation": 0.5, "novelty": 0.3, "reliability": 0.2}
        scorer = SalienceScorer(weights=weights)
        assert scorer.weights == weights

    def test_zero_threshold(self):
        """Test zero threshold"""
        gating = WriteTimeGating(threshold=0.0)
        result = gating.write({"content": "test", "source": "external"})
        assert result.stored is True

    def test_full_threshold(self):
        """Test max threshold"""
        gating = WriteTimeGating(threshold=1.0)
        result = gating.write({"content": "test", "source": "user"})
        assert result.stored is True


class TestPerformance:
    """Performance tests"""

    def test_write_latency(self):
        """Test write latency < 10ms"""
        import time

        gating = WriteTimeGating()

        start = time.time()
        for i in range(100):
            gating.write({"content": f"test_{i}", "source": "user"})
        elapsed = time.time() - start

        avg_latency = elapsed / 100 * 1000
        print(f"\nAverage write latency: {avg_latency:.2f}ms")
        assert avg_latency < 10

    def test_scoring_latency(self):
        """Test scoring latency < 5ms"""
        import time

        scorer = SalienceScorer()

        start = time.time()
        for i in range(100):
            scorer.compute({"content": f"test_{i}", "source": "user"})
        elapsed = time.time() - start

        avg_latency = elapsed / 100 * 1000
        print(f"\nAverage scoring latency: {avg_latency:.2f}ms")
        assert avg_latency < 5

    def test_memory_usage(self):
        """Test memory usage < 10MB"""
        import tracemalloc
        import sys

        tracemalloc.start()

        gating = WriteTimeGating()
        for i in range(1000):
            gating.write({"content": f"test_{i}", "source": "user"})

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        print(f"\nPeak memory: {peak_mb:.2f}MB")
        assert peak_mb < 10

    def test_high_volume_writes(self):
        """Test high volume writes"""
        import time

        gating = WriteTimeGating()

        start = time.time()
        for i in range(1000):
            gating.write({"content": f"test_{i}", "source": "user"})
        elapsed = time.time() - start

        print(f"\n1000 writes: {elapsed*1000:.2f}ms")
        assert elapsed < 1.0  # 1000 writes should complete within 1 second
