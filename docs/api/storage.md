# Storage API

## EpisodicStorage
Stores conversation episodes. 30-day TTL.
```python
storage = EpisodicStorage(workspace="/path")
storage.store(memory_record)          # Store episode
records = storage.get_all()           # All records
recent = storage.get_recent(limit=20) # Recent records
storage.cleanup_expired()             # Remove expired
```

## SemanticStorage
Stores extracted facts/concepts. Permanent.
```python
storage = SemanticStorage(workspace="/path")
storage.store(memory_record)
results = storage.search_by_tag("python")
storage.update(memory_id, new_content)
```

## ProceduralStorage
Stores skills/workflows. File-based.
```python
storage = ProceduralStorage(workspace="/path")
storage.store(memory_record)
skills = storage.get_skill("redis_setup")
results = storage.search_by_keyword("redis")
```

## GroundTruthStore (v2.14.0+)
Preserves raw conversation transcripts per session.
```python
gt = GroundTruthStore(workspace="/path")
gt.store_turn(session_id, messages)
records = gt.get_session(session_id)
results = gt.search(keyword="error")
sessions = gt.list_sessions()
```
