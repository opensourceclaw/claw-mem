// claw-mem v5.0.0 — Error Classes (TypeScript)

export class ClawMemError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ClawMemError";
  }
}

export class FriendlyError extends ClawMemError {
  constructor(
    message: string,
    public suggestion?: string,
    public errorCode?: string,
    public details?: string,
  ) {
    super(message);
    this.name = "FriendlyError";
  }

  format(): string {
    let out = `[Error] ${this.message}\n`;
    if (this.suggestion) out += `[Suggestion] ${this.suggestion}\n`;
    if (this.errorCode) out += `[Error Code] ${this.errorCode}\n`;
    if (this.details) out += `[Details] ${this.details}\n`;
    return out;
  }
}

// Storage errors (v2.20.0 hierarchy)
export class StorageError extends ClawMemError {
  constructor(message: string) {
    super(message);
    this.name = "StorageError";
  }
}
export class MemoryNotFoundError extends StorageError {
  constructor(memoryId: string) {
    super(`Memory not found: ${memoryId}`);
    this.name = "MemoryNotFoundError";
  }
}
export class StorageFullError extends StorageError {
  constructor(message: string = "Storage capacity exceeded") {
    super(message);
    this.name = "StorageFullError";
  }
}
export class StorageCorruptedError extends StorageError {
  constructor(filePath: string) {
    super(`Storage corrupted: ${filePath}`);
    this.name = "StorageCorruptedError";
  }
}

// Retrieval errors
export class RetrievalError extends ClawMemError {
  constructor(message: string) {
    super(message);
    this.name = "RetrievalError";
  }
}
export class IndexNotReadyError extends RetrievalError {
  constructor(message: string = "Index not ready") {
    super(message);
    this.name = "IndexNotReadyError";
  }
}
export class QueryTooLongError extends RetrievalError {
  constructor(message: string = "Query too long") {
    super(message);
    this.name = "QueryTooLongError";
  }
}

// Compression errors
export class CompressionError extends ClawMemError {
  constructor(message: string) {
    super(message);
    this.name = "CompressionError";
  }
}
export class CompressionDisabledError extends CompressionError {
  constructor(message: string = "Compression is disabled") {
    super(message);
    this.name = "CompressionDisabledError";
  }
}

// Configuration errors
export class InvalidThresholdError extends ClawMemError {
  constructor(message: string) {
    super(message);
    this.name = "InvalidThresholdError";
  }
}
export class ConfigurationError extends FriendlyError {
  constructor(message: string, suggestion?: string) {
    super(message, suggestion, "CONFIGURATION_ERROR");
    this.name = "ConfigurationError";
  }
}
export class WorkspaceNotFoundError extends FriendlyError {
  constructor(searchedPaths: string[]) {
    super(
      "OpenClaw workspace not found",
      "Please confirm OpenClaw is installed or specify workspace path",
      "WORKSPACE_NOT_FOUND",
      `Searched paths:\n  - ${searchedPaths.join("\n  - ")}`,
    );
    this.name = "WorkspaceNotFoundError";
  }
}
export class IndexNotFoundError extends FriendlyError {
  constructor(indexPath: string) {
    super(
      "Memory index not found, rebuilding...",
      "First startup requires index rebuild (~1 second)",
      "INDEX_NOT_FOUND",
      `Index path: ${indexPath}`,
    );
    this.name = "IndexNotFoundError";
  }
}
export class MemoryCorruptedError extends FriendlyError {
  constructor(filePath: string) {
    super(
      "Memory file corrupted",
      "System will auto-recover from backup. Check disk if persists.",
      "MEMORY_CORRUPTED",
      `Corrupted file: ${filePath}`,
    );
    this.name = "MemoryCorruptedError";
  }
}
export class ValidationError extends FriendlyError {
  constructor(message: string, suggestion?: string) {
    super(message, suggestion, "VALIDATION_ERROR");
    this.name = "ValidationError";
  }
}
export class DependencyError extends FriendlyError {
  constructor(dependency: string) {
    super(
      `Missing dependency: ${dependency}`,
      `Run installation command for ${dependency}`,
      "DEPENDENCY_ERROR",
      `Missing dependency: ${dependency}`,
    );
    this.name = "DependencyError";
  }
}
