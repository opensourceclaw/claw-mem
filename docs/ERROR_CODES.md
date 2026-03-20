# claw-mem Error Codes

**Version**: 0.8.0  
**Language**: Chinese (中文)  
**Last Updated**: 2026-03-20

---

## 📖 错误码列表

### INDEX_NOT_FOUND

**说明**: 记忆索引文件未找到

**原因**:
- 首次启动，索引尚未构建
- 索引文件被意外删除
- 索引路径配置错误

**解决方案**:
```
系统会自动重建索引，等待即可完成（约 1 秒）
```

**示例输出**:
```
[错误] 记忆索引未找到，正在重建...
[建议] 首次启动需要重建索引，请稍候（约 1 秒）
[错误码] INDEX_NOT_FOUND
[详情] 索引路径：~/.claw-mem/index/index_v0.8.0.pkl.gz
```

---

### WORKSPACE_NOT_FOUND

**说明**: 未找到 OpenClaw 工作区

**原因**:
- OpenClaw 未安装
- 工作区路径配置错误
- 使用了非标准工作区路径

**解决方案**:
```
1. 确认已正确安装 OpenClaw
2. 检查默认路径：~/.openclaw/workspace
3. 或手动指定工作区路径：memory = MemoryManager(workspace="/your/path")
```

**示例输出**:
```
[错误] 未找到 OpenClaw 工作区
[建议] 请确认已正确安装 OpenClaw，或手动指定工作区路径
[错误码] WORKSPACE_NOT_FOUND
[详情] 已搜索以下路径:
  - ~/.openclaw/workspace
  - ~/.config/openclaw/workspace
  - /current/dir
```

---

### MEMORY_CORRUPTED

**说明**: 记忆文件损坏

**原因**:
- 磁盘错误
- 意外断电
- 文件被意外修改

**解决方案**:
```
系统会自动从最近的备份恢复
如反复出现此问题，请检查磁盘健康状态
```

**示例输出**:
```
[错误] 记忆文件已损坏，尝试从备份恢复...
[建议] 系统会自动从最近的备份恢复，如反复出现此问题请检查磁盘
[错误码] MEMORY_CORRUPTED
[详情] 损坏文件：~/.openclaw/workspace/memory/2026-03-20.md
```

---

### PERMISSION_DENIED

**说明**: 权限不足，无法访问文件

**原因**:
- 文件权限设置阻止访问
- 使用了错误的用户运行

**解决方案**:
```
1. 检查文件权限：ls -l <file>
2. 修改权限：chmod 644 <file>
3. 或以正确用户身份运行
```

**示例输出**:
```
[错误] 权限不足，无法访问文件
[建议] 请检查文件权限或使用 chmod 命令修改权限
[错误码] PERMISSION_DENIED
[详情] 无法访问：~/.openclaw/workspace/MEMORY.md
```

---

### CONFIGURATION_ERROR

**说明**: 配置项设置错误

**原因**:
- 配置文件格式错误
- 配置值不合法
- 缺少必需的配置项

**解决方案**:
```
1. 检查配置文件格式
2. 参考文档确认配置值范围
3. 或运行 claw-mem --help 查看可用选项
```

**示例输出**:
```
[错误] 配置项 'workspace' 设置错误
[建议] 请检查配置文件或运行 claw-mem --help 查看可用选项
[错误码] CONFIGURATION_ERROR
[详情] 当前值：/invalid/path
```

---

### MEMORY_RETRIEVAL_ERROR

**说明**: 记忆检索失败

**原因**:
- 搜索词过于复杂
- 记忆文件不存在
- 索引损坏

**解决方案**:
```
1. 简化搜索关键词
2. 检查记忆文件是否存在
3. 重建索引：删除 ~/.claw-mem/index/ 后重启
```

**示例输出**:
```
[错误] 记忆检索失败
[建议] 请尝试简化搜索关键词或检查记忆文件是否存在
[错误码] MEMORY_RETRIEVAL_ERROR
[详情] 搜索词：复杂的搜索查询语句
```

---

### VALIDATION_ERROR

**说明**: 数据验证失败

**原因**:
- 输入数据格式不正确
- 数据类型不匹配
- 值超出允许范围

**解决方案**:
```
检查输入格式并修正
参考文档确认正确的数据格式
```

**示例输出**:
```
[错误] 验证失败：memory_type
[建议] 请检查输入格式是否正确
[错误码] VALIDATION_ERROR
[详情] 值：invalid_type
原因：必须是 'episodic', 'semantic', 或 'procedural'
```

---

### NETWORK_ERROR

**说明**: 网络连接失败

**原因**:
- 网络不可用
- 目标服务器不可达
- 防火墙阻止

**解决方案**:
```
1. 检查网络连接
2. 确认目标服务可用
3. 检查防火墙设置
4. 稍后重试
```

**示例输出**:
```
[错误] 网络连接失败
[建议] 请检查网络连接或稍后重试
[错误码] NETWORK_ERROR
[详情] 目标 URL: https://example.com/api
```

---

### DEPENDENCY_ERROR

**说明**: 缺少 Python 依赖包

**原因**:
- 依赖包未安装
- 版本不兼容
- 安装失败

**解决方案**:
```
1. 运行 pip install <dependency>
2. 检查 requirements.txt
3. 使用 pip install -e . 重新安装
```

**示例输出**:
```
[错误] 缺少依赖：rank-bm25
[建议] 请运行 'pip install rank-bm25' 安装
[错误码] DEPENDENCY_ERROR
[详情] 缺失的依赖：rank-bm25
```

---

## 🛠️ 使用友好错误系统

### 在代码中抛出错误

```python
from claw_mem import IndexNotFoundError, WorkspaceNotFoundError

# 索引未找到
raise IndexNotFoundError("~/.claw-mem/index/index.pkl")

# 工作区未找到
raise WorkspaceNotFoundError([
    "~/.openclaw/workspace",
    "~/.config/openclaw/workspace"
])
```

### 捕获并显示错误

```python
from claw_mem import FriendlyError

try:
    # 可能出错的操作
    memory = MemoryManager()
except FriendlyError as e:
    # 自动显示友好的中文错误信息
    print(e)
```

### 查询错误码文档

```python
from claw_mem import get_error_documentation

# 获取错误码详细说明
print(get_error_documentation("INDEX_NOT_FOUND"))
```

---

## 📊 错误统计

| 错误码 | 出现频率 | 严重程度 |
|--------|---------|---------|
| INDEX_NOT_FOUND | 高（首次启动） | 低（自动恢复） |
| WORKSPACE_NOT_FOUND | 中 | 中 |
| MEMORY_CORRUPTED | 低 | 中（自动恢复） |
| PERMISSION_DENIED | 低 | 中 |
| CONFIGURATION_ERROR | 中 | 低 |
| MEMORY_RETRIEVAL_ERROR | 中 | 低 |
| VALIDATION_ERROR | 低 | 低 |
| NETWORK_ERROR | 低 | 中 |
| DEPENDENCY_ERROR | 低（首次安装） | 低 |

---

## 🎯 最佳实践

### 1. 使用预定义错误类型

```python
# ✅ 好的做法：使用预定义错误
raise IndexNotFoundError(path)

# ❌ 不好的做法：使用通用异常
raise Exception("Index not found")
```

### 2. 提供有用的建议

```python
# ✅ 好的做法：提供具体建议
raise WorkspaceNotFoundError(
    searched_paths,
    suggestion="请确认已正确安装 OpenClaw"
)

# ❌ 不好的做法：没有建议
raise WorkspaceNotFoundError(searched_paths)
```

### 3. 包含详细信息

```python
# ✅ 好的做法：包含详细信息
raise PermissionDeniedError(
    path,
    details=f"文件所有者：{owner}, 权限：{perms}"
)

# ❌ 不好的做法：信息不足
raise PermissionDeniedError(path)
```

---

**文档版本**: 0.8.0  
**最后更新**: 2026-03-20  
**维护者**: Peter Cheng
