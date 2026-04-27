# Vector DB Migration Guide

## 快速开始

```python
from claw_mem.vector_db import VectorDBFactory, VectorDBType

# 1. 选择数据库类型 (当前MVP用ChromaDB)
db_type = VectorDBType.CHROMADB

# 2. 配置 (各数据库不同)
config = {
    # ChromaDB 配置
    "path": "./vector_store",      # 本地存储路径
    "collection_name": "memories",
    "embedding_model": "all-MiniLM-L6-v2"
}

# 3. 创建插件
plugin = VectorDBFactory.create(db_type, config)

# 4. 使用
plugin.connect()
plugin.add(
    documents=["用户的喜好是 Pizza"],
    ids=["memory_001"],
    metadata=[{"type": "preference", "category": "food"}]
)

results = plugin.search("用户喜欢什么?", top_k=5)
for r in results:
    print(f"{r.content} (score: {r.score:.2f})")
```

---

## 在不同环境切换

### 开发/测试环境 (本地优先)
```python
config = {
    "type": VectorDBType.CHROMADB,
    "path": "./dev_vector_store"
}
```

### 生产环境 (云端)
```python
# Qdrant
config = {
    "type": VectorDBType.QDRANT,
    "host": "localhost",
    "port": 6333
}

# 或 Pinecone
config = {
    "type": VectorDBType.PINECONE,
    "api_key": "your-api-key",
    "environment": "us-west1"
}
```

---

## 新增插件模板

```python
from claw_mem.vector_db import VectorDBPlugin, VectorDBType, VectorDBFactory

class MyCustomPlugin(VectorDBPlugin):
    """自定义向量数据库插件"""

    def __init__(self, config):
        super().__init__(config)
        # 初始化逻辑

    def connect(self) -> bool:
        # 实现连接
        pass

    # ... 实现其他抽象方法

# 注册插件
VectorDBFactory.register(VectorDBType.MYCUSTOM, MyCustomPlugin)
```
