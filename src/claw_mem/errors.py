#!/usr/bin/env python3
"""
claw-mem Friendly Error System

All errors are in Chinese with fix suggestions.
"""

from typing import Optional


class FriendlyError(Exception):
    """Friendly error message base class"""
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[str] = None
    ):
        self.message = message
        self.suggestion = suggestion
        self.error_code = error_code
        self.details = details
        super().__init__(self.format())
    
    def format(self) -> str:
        """Format error message"""
        output = f"[错误] {self.message}\n"
        
        if self.suggestion:
            output += f"[建议] {self.suggestion}\n"
        
        if self.error_code:
            output += f"[错误码] {self.error_code}\n"
        
        if self.details:
            output += f"[详情] {self.details}\n"
        
        return output
    
    def __str__(self) -> str:
        return self.format()


# ============================================================================
# Pre-defined error types
# ============================================================================

class IndexNotFoundError(FriendlyError):
    """Index not found error"""
    
    def __init__(self, index_path: str, suggestion: Optional[str] = None):
        super().__init__(
            message="记忆索引未找到，正在重建...",
            suggestion=suggestion or "首次启动需要重建索引，请稍候（约 1 秒）",
            error_code="INDEX_NOT_FOUND",
            details=f"索引路径：{index_path}"
        )


class WorkspaceNotFoundError(FriendlyError):
    """Workspace not found error"""
    
    def __init__(self, searched_paths: list, suggestion: Optional[str] = None):
        paths_str = "\n  - ".join(searched_paths)
        super().__init__(
            message="未找到 OpenClaw 工作区",
            suggestion=suggestion or "请确认已正确安装 OpenClaw，或手动指定工作区路径",
            error_code="WORKSPACE_NOT_FOUND",
            details=f"已搜索以下路径:\n  - {paths_str}"
        )


class MemoryCorruptedError(FriendlyError):
    """Memory file corrupted error"""
    
    def __init__(self, file_path: str, suggestion: Optional[str] = None):
        super().__init__(
            message="记忆文件已损坏，尝试从备份恢复...",
            suggestion=suggestion or "系统会自动从最近的备份恢复，如反复出现此问题请检查磁盘",
            error_code="MEMORY_CORRUPTED",
            details=f"损坏文件：{file_path}"
        )


class PermissionDeniedError(FriendlyError):
    """Permission denied error"""
    
    def __init__(self, path: str, suggestion: Optional[str] = None):
        super().__init__(
            message="权限不足，无法访问文件",
            suggestion=suggestion or "请检查文件权限或使用 chmod 命令修改权限",
            error_code="PERMISSION_DENIED",
            details=f"无法访问：{path}"
        )


class ConfigurationError(FriendlyError):
    """Configuration error"""
    
    def __init__(self, config_key: str, current_value: str, suggestion: Optional[str] = None):
        super().__init__(
            message=f"配置项 '{config_key}' 设置错误",
            suggestion=suggestion or "请检查配置文件或运行 claw-mem --help 查看可用选项",
            error_code="CONFIGURATION_ERROR",
            details=f"当前值：{current_value}"
        )


class MemoryRetrievalError(FriendlyError):
    """记忆检索错误"""
    
    def __init__(self, query: str, suggestion: Optional[str] = None):
        super().__init__(
            message="记忆检索失败",
            suggestion=suggestion or "请尝试简化搜索关键词或检查记忆文件是否存在",
            error_code="MEMORY_RETRIEVAL_ERROR",
            details=f"搜索词：{query}"
        )


class ValidationError(FriendlyError):
    """验证错误"""
    
    def __init__(self, field: str, value: str, reason: str, suggestion: Optional[str] = None):
        super().__init__(
            message=f"验证失败：{field}",
            suggestion=suggestion or "请检查输入格式是否正确",
            error_code="VALIDATION_ERROR",
            details=f"值：{value}\n原因：{reason}"
        )


class NetworkError(FriendlyError):
    """网络错误"""
    
    def __init__(self, url: str, suggestion: Optional[str] = None):
        super().__init__(
            message="网络连接失败",
            suggestion=suggestion or "请检查网络连接或稍后重试",
            error_code="NETWORK_ERROR",
            details=f"目标 URL: {url}"
        )


class DependencyError(FriendlyError):
    """依赖缺失错误"""
    
    def __init__(self, dependency: str, suggestion: Optional[str] = None):
        super().__init__(
            message=f"缺少依赖：{dependency}",
            suggestion=suggestion or f"请运行 'pip install {dependency}' 安装",
            error_code="DEPENDENCY_ERROR",
            details=f"缺失的依赖：{dependency}"
        )


# ============================================================================
# 错误码文档
# ============================================================================

ERROR_CODE_DOCUMENTATION = {
    "INDEX_NOT_FOUND": {
        "description": "记忆索引文件未找到",
        "cause": "首次启动或索引文件被删除",
        "solution": "系统会自动重建索引，等待即可完成"
    },
    "WORKSPACE_NOT_FOUND": {
        "description": "未找到 OpenClaw 工作区",
        "cause": "OpenClaw 未安装或工作区路径Configuration error",
        "solution": "安装 OpenClaw 或手动指定工作区路径"
    },
    "MEMORY_CORRUPTED": {
        "description": "记忆文件损坏",
        "cause": "磁盘错误、意外断电或文件被意外修改",
        "solution": "系统会自动从备份恢复，如反复出现请检查磁盘"
    },
    "PERMISSION_DENIED": {
        "description": "权限不足",
        "cause": "文件权限设置阻止访问",
        "solution": "使用 chmod 修改文件权限或以正确用户身份运行"
    },
    "CONFIGURATION_ERROR": {
        "description": "配置项错误",
        "cause": "配置文件格式错误或值不合法",
        "solution": "检查配置文件或参考文档修正配置"
    },
    "MEMORY_RETRIEVAL_ERROR": {
        "description": "记忆检索失败",
        "cause": "搜索词过于复杂或记忆文件不存在",
        "solution": "简化搜索词或检查记忆文件"
    },
    "VALIDATION_ERROR": {
        "description": "数据验证失败",
        "cause": "输入数据格式不正确",
        "solution": "检查输入格式并修正"
    },
    "NETWORK_ERROR": {
        "description": "网络连接失败",
        "cause": "网络不可用或目标服务器不可达",
        "solution": "检查网络连接或稍后重试"
    },
    "DEPENDENCY_ERROR": {
        "description": "缺少 Python 依赖",
        "cause": "依赖包未安装或版本不兼容",
        "solution": "使用 pip 安装缺失的依赖"
    }
}


def get_error_documentation(error_code: str) -> str:
    """获取错误码的详细文档"""
    if error_code not in ERROR_CODE_DOCUMENTATION:
        return f"错误码 '{error_code}' 暂无文档"
    
    doc = ERROR_CODE_DOCUMENTATION[error_code]
    output = f"错误码：{error_code}\n"
    output += f"说明：{doc['description']}\n"
    output += f"原因：{doc['cause']}\n"
    output += f"解决方案：{doc['solution']}\n"
    
    return output


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 示例 1：索引未找到
    try:
        raise IndexNotFoundError("~/.claw-mem/index/index_v0.8.0.pkl.gz")
    except FriendlyError as e:
        print(e)
        print()
    
    # 示例 2：工作区未找到
    try:
        raise WorkspaceNotFoundError([
            "~/.openclaw/workspace",
            "~/.config/openclaw/workspace",
            "/current/dir"
        ])
    except FriendlyError as e:
        print(e)
        print()
    
    # 示例 3：获取错误文档
    print(get_error_documentation("INDEX_NOT_FOUND"))
