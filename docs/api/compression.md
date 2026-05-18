# Compression API

## CompressionSpectrum (v2.18.0+)

Four-tier compression: Episodes → Skills → Rules → Principles.
Default enabled since v2.18.0.

```python
cs = CompressionSpectrum(
    memory_manager=mm,
    access_threshold=5,   # Episodes accessed N times → Skill
    apply_threshold=3,    # Skill applied N times → Rule
    verify_threshold=2,   # Rule verified N times → Principle
)

# Trigger-based compression
result = cs.record_access("memory_id")  # May trigger Skill
result = cs.record_apply("skill_id")    # May trigger Rule
result = cs.record_verify("rule_id")    # May trigger Principle

# Runtime config
cs.configure_thresholds(access=3, apply=2)

# Query compressed memories
compressed = cs.get_compressed(memory_id="mem_123")
stats = cs.get_stats()
```

## MemoryCompressorV2

Sawtooth-pattern memory compression with deduplication.

```python
compressor = MemoryCompressorV2(memory_manager)
result = compressor.compress()  # Triggered by thresholds
```
