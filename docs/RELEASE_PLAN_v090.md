# claw-mem v0.9.0 开发计划

**版本：** v0.8.0 → v0.9.0  
**主题：** Stability & Performance (稳定与性能)  
**周期：** 2026-03-21 → 2026-04-11 (3 周)  
**状态：** 📋 规划中  
**Created:** 2026-03-21

---

## 🎯 核心原则

> **"文本优先，稳定第一，解决遗留问题，渐进增强"**

### 优先级排序

```
1. 文本记忆性能优化 ⭐⭐⭐ (90% 使用场景)
2. 稳定性和可靠性 ⭐⭐⭐ (不能影响 OpenClaw)
3. 图片基础支持 ⭐⭐ (少量使用，不依赖 CLIP)
4. CLIP/音频等 ⭐ (可选，默认禁用)
```

---

## 📋 v0.8.0 遗留问题回顾

### 问题 1: 记忆检索准确性 (F000 已部分解决)

**当前状态：**
- ✅ 准确率从 <80% → >95%
- ⚠️ 但仍有边界情况处理不好

**遗留问题：**
- [ ] 长文本检索性能下降
- [ ] 多条目冲突时选择逻辑不够智能
- [ ] 上下文相关检索不够准确

---

### 问题 2: 索引重建性能

**当前状态：**
- ✅ 懒加载已实现
- ✅ 索引持久化已实现
- ⚠️ 但大索引 (>10MB) 加载仍慢

**遗留问题：**
- [ ] 10 万 + 记忆条目时加载 >5 秒
- [ ] 索引重建期间无法检索
- [ ] 内存占用过高 (>500MB)

---

### 问题 3: 配置管理

**当前状态：**
- ✅ 自动检测工作区
- ✅ 友好错误提示
- ⚠️ 但配置项分散，难以管理

**遗留问题：**
- [ ] 配置文件分散 (config.json, .env, 代码硬编码)
- [ ] 缺少配置验证
- [ ] 配置变更需要重启

---

### 问题 4: 数据完整性

**当前状态：**
- ✅ 备份/恢复功能
- ✅ 检查点机制
- ⚠️ 但缺少主动数据健康检查

**遗留问题：**
- [ ] 缺少定期健康检查
- [ ] 数据损坏检测被动
- [ ] 缺少数据清理机制

---

### 问题 5: 多模态支持

**当前状态：**
- ❌ 完全不支持
- ⚠️ 用户有图片存储需求

**需求：**
- [ ] 图片本地存储
- [ ] 图片 - 文本关联检索
- [ ] 不依赖 CLIP (老旧设备友好)

---

## 🎯 v0.9.0 功能规划

### P0 - 必须发布 (核心稳定性)

| ID | 功能 | 描述 | 工作量 | 优先级 |
|----|------|------|--------|--------|
| **T001** | 检索性能优化 | 长文本检索优化，缓存改进 | 3 天 | 🔴 |
| **T002** | 索引优化 | 增量索引，分块加载，内存优化 | 3 天 | 🔴 |
| **T003** | 配置统一管理 | 单一配置文件，热重载 | 2 天 | 🔴 |
| **T004** | 数据健康检查 | 定期检查，主动清理 | 2 天 | 🔴 |
| **T005** | 异常恢复增强 | 更好的错误处理和恢复 | 2 天 | 🔴 |

**小计：** 12 天

---

### P1 - 强烈推荐 (图片基础)

| ID | 功能 | 描述 | 工作量 | 优先级 |
|----|------|------|--------|--------|
| **I001** | 图片本地存储 | 保存 OpenClaw 对话中的图片 | 2 天 | 🟡 |
| **I002** | 图片元数据 | 时间、大小、格式，无 CLIP | 1 天 | 🟡 |
| **I003** | 图片 - 文本关联 | 关联对话上下文 | 2 天 | 🟡 |
| **I004** | 图片文本检索 | 通过关联文本 BM25 检索 | 2 天 | 🟡 |
| **I005** | 配置开关 | 图片存储启用/禁用 | 1 天 | 🟡 |

**小计：** 8 天

---

### P2 - 可选增强 (有硬件支持时)

| ID | 功能 | 描述 | 工作量 | 优先级 |
|----|------|------|--------|--------|
| **O001** | CLIP 支持 (可选) | 配置启用，硬件检测 | 3 天 | 🟢 |
| **O002** | 图片语义检索 | CLIP 启用后可用 | 2 天 | 🟢 |
| **O003** | 音频存储 (可选) | 本地存储，无转写 | 2 天 | 🟢 |

**小计：** 7 天

---

## 📅 时间规划

### 推荐方案：3 周迭代 (15 个工作日)

```
第 1 周 (3.24-3.28): P0 核心稳定性
├─ 周一 - 周三：T001 检索性能优化
├─ 周四 - 周五：T002 索引优化
└─ 周六：周会 + 文档

第 2 周 (3.31-4.4): P0 完成 + P1 开始
├─ 周一：T003 配置统一管理
├─ 周二 - 周三：T004 数据健康检查
├─ 周四 - 周五：T005 异常恢复增强
└─ 周六：P0 功能测试

第 3 周 (4.7-4.11): P1 图片支持 + 发布
├─ 周一 - 周三：I001-I004 图片基础功能
├─ 周四：I005 配置开关 + 集成测试
└─ 周五：文档 + 发布准备
```

**发布日期：** 2026-04-11 (周五)

---

### 备选方案：2 周精简版 (如果时间紧张)

```
第 1 周 (3.24-3.28): P0 核心 (部分)
├─ T001 检索性能优化
├─ T002 索引优化 (部分)
└─ T005 异常恢复增强

第 2 周 (3.31-4.4): P0 完成 + 发布
├─ T003 配置管理
├─ T004 数据健康检查
└─ 发布准备

P1 图片功能 → 推迟到 v0.9.1
```

**发布日期：** 2026-04-04 (周五)

---

## 🔧 技术方案详细设计

### T001: 检索性能优化

**问题分析：**
```
当前问题:
- 长文本 (>1000 字) 检索慢 (>500ms)
- 多类型检索重复计算
- 缺少查询缓存

目标:
- 长文本检索 <200ms (P95)
- 缓存命中率 >80%
- 内存占用 <100MB
```

**技术方案：**
```python
class OptimizedRetriever:
    def __init__(self):
        # L1 缓存：最近查询 (LRU, 1000 条)
        self.query_cache = LRUCache(max_size=1000)
        
        # L2 缓存：常用结果 (TTL 5 分钟)
        self.result_cache = TTLCache(max_size=5000, ttl=300)
        
        # 分块索引：长文本分块检索
        self.chunk_index = ChunkedIndex(chunk_size=500)
    
    def search(self, query: str, filters: dict) -> List[Memory]:
        # 1. 检查缓存
        cache_key = f"{query}:{filters}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        # 2. 分块检索 (长文本优化)
        if len(query) > 500:
            results = self.chunk_search(query, filters)
        else:
            results = self.bm25_search(query, filters)
        
        # 3. 缓存结果
        self.query_cache[cache_key] = results
        
        return results
```

**验收标准：**
- [ ] 短文本检索 <50ms (P95)
- [ ] 长文本检索 <200ms (P95)
- [ ] 缓存命中率 >80%
- [ ] 内存占用 <100MB

---

### T002: 索引优化

**问题分析：**
```
当前问题:
- 10 万 + 条目加载 >5 秒
- 全量加载，内存占用高
- 重建期间无法检索

目标:
- 10 万条目加载 <2 秒
- 分块加载，按需载入
- 重建期间可检索旧索引
```

**技术方案：**
```python
class OptimizedIndex:
    def __init__(self, index_dir: str):
        self.index_dir = index_dir
        self.index_meta = self._load_metadata()  # 只加载元数据
        
        # 延迟加载实际索引
        self.index_data = None
    
    def _load_metadata(self):
        """只加载元数据 (大小、版本、条目数)"""
        meta_path = os.path.join(self.index_dir, "meta.json")
        with open(meta_path, 'r') as f:
            return json.load(f)
    
    def search(self, query: str):
        """按需加载索引块"""
        if self.index_data is None:
            self._load_index_blocks()  # 分块加载
        
        return self._search_index(query)
    
    def _load_index_blocks(self):
        """分块加载索引，避免一次性加载"""
        # 实现分块加载逻辑
        pass
```

**验收标准：**
- [ ] 10 万条目加载 <2 秒
- [ ] 内存占用 <200MB
- [ ] 支持增量更新
- [ ] 重建期间可检索

---

### T003: 配置统一管理

**问题分析：**
```
当前问题:
- 配置分散 (config.json, .env, 代码)
- 配置变更需要重启
- 缺少配置验证

目标:
- 单一配置文件 (~/.claw-mem/config.yml)
- 支持热重载
- 配置验证和默认值
```

**技术方案：**
```yaml
# ~/.claw-mem/config.yml

version: "0.9.0"

# 存储配置
storage:
  workspace: "~/.openclaw/workspace"
  backup_dir: "~/.claw-mem/backups"
  max_memory_size_mb: 100
  
# 检索配置
retrieval:
  max_results: 10
  cache_size: 1000
  cache_ttl_seconds: 300
  
# 图片配置 (新增)
multimodal:
  image:
    enabled: true
    store_original: true
    enable_clip: false  # 默认禁用
    clip_model: "auto"  # auto/rn50/vit-b-32
    
# 性能配置
performance:
  enable_lazy_loading: true
  index_chunk_size: 10000
  max_memory_mb: 500
  
# 健康检查
health:
  enabled: true
  check_interval_hours: 24
  auto_cleanup: true
```

**验收标准：**
- [ ] 单一配置文件
- [ ] 支持热重载
- [ ] 配置验证
- [ ] 向后兼容

---

### T004: 数据健康检查

**问题分析：**
```
当前问题:
- 被动检测数据损坏
- 缺少定期清理
- 用户不知道数据状态

目标:
- 定期主动检查
- 自动清理过期数据
- 健康状态可视化
```

**技术方案：**
```python
class HealthChecker:
    def __init__(self, config: Config):
        self.config = config
        self.last_check = None
    
    def check_all(self) -> HealthReport:
        """全面健康检查"""
        report = HealthReport()
        
        # 1. 索引健康
        report.index_health = self._check_index()
        
        # 2. 数据完整性
        report.data_integrity = self._check_data_integrity()
        
        # 3. 磁盘空间
        report.disk_space = self._check_disk_space()
        
        # 4. 记忆过期
        report.expired_memories = self._check_expired()
        
        return report
    
    def auto_cleanup(self):
        """自动清理过期数据"""
        if not self.config.health.auto_cleanup:
            return
        
        # 清理过期记忆
        cleaned = self._cleanup_expired_memories()
        
        # 清理旧备份
        self._cleanup_old_backups()
        
        return cleaned
```

**验收标准：**
- [ ] 每 24 小时自动检查
- [ ] 发现问题自动修复
- [ ] 清理过期数据
- [ ] 健康报告可视化

---

### I001-I005: 图片基础支持

**技术方案：**
```python
class ImageStorage:
    def __init__(self, config: Config):
        self.config = config
        self.storage_dir = os.path.join(
            config.workspace, "memory", "images"
        )
    
    def store_image(self, image_data: bytes, context: dict) -> str:
        """存储图片，返回图片 ID"""
        # 1. 生成唯一 ID
        image_id = self._generate_id(image_data)
        
        # 2. 存储原图
        image_path = os.path.join(self.storage_dir, f"{image_id}.jpg")
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        # 3. 提取元数据
        metadata = {
            'id': image_id,
            'path': image_path,
            'size': len(image_data),
            'format': self._detect_format(image_data),
            'created_at': datetime.now().isoformat(),
            'context': context,  # 关联的对话文本
        }
        
        # 4. 存储元数据 (SQLite)
        self._save_metadata(metadata)
        
        # 5. 索引关联文本 (BM25)
        if context.get('text'):
            self._index_context(image_id, context['text'])
        
        return image_id
    
    def search_images(self, query: str) -> List[dict]:
        """通过文本检索图片"""
        # 1. BM25 检索关联文本
        results = self.bm25_search(query)
        
        # 2. 返回图片元数据
        return [self._get_metadata(r['image_id']) for r in results]
```

**验收标准：**
- [ ] 图片本地存储
- [ ] 关联对话文本
- [ ] 通过文本检索图片
- [ ] 配置开关控制
- [ ] 不依赖 CLIP

---

## 📊 成功标准

### 性能指标

| 指标 | v0.8.0 | v0.9.0 目标 | 改进 |
|------|--------|-------------|------|
| 短文本检索 | 100ms | <50ms | 2x |
| 长文本检索 | 500ms | <200ms | 2.5x |
| 索引加载 (10 万) | 5s | <2s | 2.5x |
| 内存占用 | 500MB | <200MB | 2.5x |
| 缓存命中率 | 0% | >80% | 新增 |

### 稳定性指标

| 指标 | v0.8.0 | v0.9.0 目标 |
|------|--------|-------------|
| 检索准确率 | >95% | >97% |
| 配置成功率 | >90% | >99% |
| 异常恢复率 | 80% | >95% |
| 数据完整性 | 被动检测 | 主动检查 |

### 功能指标

| 功能 | 状态 |
|------|------|
| 图片存储 | ✅ 支持 |
| 图片检索 | ✅ 文本检索 |
| CLIP 支持 | ⚠️ 可选 (默认禁用) |
| 音频支持 | ❌ 暂不支持 |

---

## ⚠️ 风险管理

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 索引优化复杂度高 | 中 (40%) | 高 | 分阶段实现，先解决主要问题 |
| 配置热重载不稳定 | 中 (35%) | 中 | 保留重启回退方案 |
| 图片存储性能影响 | 低 (20%) | 中 | 异步处理，不阻塞主流程 |

### 进度风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| P0 功能延期 | 中 (40%) | 高 | 优先保证 P0，P1 可推迟 |
| 测试时间不足 | 高 (60%) | 中 | 自动化测试，持续集成 |
| 文档不完善 | 中 (50%) | 低 | 代码即文档，简化文档 |

---

## 📋 验收清单

### P0 核心功能 (必须)

- [ ] T001 检索性能优化完成
- [ ] T002 索引优化完成
- [ ] T003 配置统一管理完成
- [ ] T004 数据健康检查完成
- [ ] T005 异常恢复增强完成
- [ ] 性能指标全部达标
- [ ] 稳定性指标全部达标

### P1 图片功能 (推荐)

- [ ] I001 图片本地存储完成
- [ ] I002 图片元数据完成
- [ ] I003 图片 - 文本关联完成
- [ ] I004 图片文本检索完成
- [ ] I005 配置开关完成
- [ ] 图片功能测试通过

### P2 可选功能 (有时间再做)

- [ ] O001 CLIP 支持 (可选)
- [ ] O002 图片语义检索
- [ ] O003 音频存储

### 文档和测试

- [ ] 用户文档更新
- [ ] 开发文档更新
- [ ] API 文档更新
- [ ] 单元测试 >90% 覆盖
- [ ] 集成测试通过
- [ ] 性能测试达标

---

## 🎯 与 v0.8.0 的对比

| 维度 | v0.8.0 | v0.9.0 |
|------|--------|--------|
| **主题** | 用户体验 | 稳定性能 |
| **重点** | 功能丰富 | 解决遗留问题 |
| **性能** | 基础优化 | 深度优化 |
| **稳定性** | 基础稳定 | 增强恢复 |
| **多模态** | 无 | 图片基础 (无 CLIP) |
| **配置** | 分散 | 统一 |
| **数据健康** | 被动 | 主动 |

---

*Last Updated: 2026-03-21*  
*Target Release: 2026-04-11*  
*Project Status: 📋 Planning*  
*claw-mem Project - Est. 2026*  
*"Make OpenClaw Truly Remember"*
