// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Multimodal Memory Module for claw-mem
 *
 * Supports multimodal memory storage for images, files, etc.
 */

import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";

export enum MemoryType {
  TEXT = "text",
  IMAGE = "image",
  FILE = "file",
  AUDIO = "audio",
  VIDEO = "video",
}

export interface ImageMemoryData {
  image_id: string;
  description: string;
  path: string;
  thumbnail_path: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export class ImageMemory {
  imageId: string;
  description: string;
  path: string;
  thumbnailPath: string | null;
  metadata: Record<string, unknown>;
  createdAt: Date;

  constructor(
    imageId: string,
    description: string,
    path: string,
    thumbnailPath?: string | null,
    metadata?: Record<string, unknown>,
    createdAt?: Date,
  ) {
    this.imageId = imageId;
    this.description = description;
    this.path = path;
    this.thumbnailPath = thumbnailPath ?? null;
    this.metadata = metadata ?? {};
    this.createdAt = createdAt ?? new Date();
  }

  toDict(): ImageMemoryData {
    return {
      image_id: this.imageId,
      description: this.description,
      path: this.path,
      thumbnail_path: this.thumbnailPath,
      metadata: { ...this.metadata },
      created_at: this.createdAt.toISOString(),
    };
  }
}

export interface FileMemoryData {
  file_id: string;
  filename: string;
  file_type: string;
  path: string;
  size_bytes: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

export class FileMemory {
  fileId: string;
  filename: string;
  fileType: string;
  path: string;
  sizeBytes: number;
  metadata: Record<string, unknown>;
  createdAt: Date;

  constructor(
    fileId: string,
    filename: string,
    fileType: string,
    path: string,
    sizeBytes: number = 0,
    metadata?: Record<string, unknown>,
    createdAt?: Date,
  ) {
    this.fileId = fileId;
    this.filename = filename;
    this.fileType = fileType;
    this.path = path;
    this.sizeBytes = sizeBytes;
    this.metadata = metadata ?? {};
    this.createdAt = createdAt ?? new Date();
  }

  toDict(): FileMemoryData {
    return {
      file_id: this.fileId,
      filename: this.filename,
      file_type: this.fileType,
      path: this.path,
      size_bytes: this.sizeBytes,
      metadata: { ...this.metadata },
      created_at: this.createdAt.toISOString(),
    };
  }
}

export interface MultimodalStats {
  total_images: number;
  total_files: number;
  total_size_bytes: number;
  image_descriptions: string[];
}

/**
 * Multimodal memory storage.
 *
 * Supports memory storage for non-text content such as images and files.
 */
export class MultimodalMemoryStore {
  basePath: string;

  private _imageMemories: Map<string, ImageMemory>;
  private _fileMemories: Map<string, FileMemory>;

  /**
   * @param basePath - Base directory for multimodal storage (default "./workspace/multimodal")
   */
  constructor(basePath: string = "./workspace/multimodal") {
    this.basePath = basePath;
    this._imageMemories = new Map();
    this._fileMemories = new Map();

    fs.mkdirSync(this.basePath, { recursive: true });
  }

  /**
   * Store an image memory.
   *
   * @param imagePath   - Image file path
   * @param description - Image description
   * @param metadata    - Additional metadata
   * @returns Image memory ID
   */
  storeImage(
    imagePath: string,
    description: string,
    metadata?: Record<string, unknown>,
  ): string {
    const imageId = this._generateId(imagePath);

    const storageDir = path.join(this.basePath, "images");
    const storagePath = path.join(storageDir, path.basename(imagePath));
    fs.mkdirSync(storageDir, { recursive: true });

    // Note: In real implementation, would copy file here.
    // For now, just store reference.

    const memory = new ImageMemory(imageId, description, storagePath, null, metadata ?? {});

    this._imageMemories.set(imageId, memory);
    return imageId;
  }

  /**
   * Store a file memory.
   *
   * @param filePath  - File path
   * @param fileType  - File type (inferred from extension if not provided)
   * @param metadata  - Additional metadata
   * @returns File memory ID
   */
  storeFile(
    filePath: string,
    fileType?: string,
    metadata?: Record<string, unknown>,
  ): string {
    const filePathObj = path.parse(filePath);
    const fileId = this._generateId(filePath);

    // Determine file type
    const resolvedFileType = fileType ?? filePathObj.ext.slice(1);

    // Get file size
    let sizeBytes = 0;
    try {
      const stat = fs.statSync(filePath);
      sizeBytes = stat.size;
    } catch {
      // file may not exist yet
    }

    // Copy to storage
    const storageDir = path.join(this.basePath, "files");
    const storagePath = path.join(storageDir, filePathObj.base);
    fs.mkdirSync(storageDir, { recursive: true });

    const memory = new FileMemory(
      fileId,
      filePathObj.base,
      resolvedFileType,
      storagePath,
      sizeBytes,
      metadata ?? {},
    );

    this._fileMemories.set(fileId, memory);
    return fileId;
  }

  /**
   * Get an image memory by ID.
   *
   * @param imageId - Image memory ID
   * @returns ImageMemory or undefined
   */
  getImage(imageId: string): ImageMemory | undefined {
    return this._imageMemories.get(imageId);
  }

  /**
   * Get a file memory by ID.
   *
   * @param fileId - File memory ID
   * @returns FileMemory or undefined
   */
  getFile(fileId: string): FileMemory | undefined {
    return this._fileMemories.get(fileId);
  }

  /**
   * Search images by description text.
   *
   * @param query - Search query
   * @param limit - Maximum results (default 10)
   * @returns Matching ImageMemory instances
   */
  searchByDescription(query: string, limit: number = 10): ImageMemory[] {
    const lower = query.toLowerCase();
    const results: ImageMemory[] = [];

    for (const memory of this._imageMemories.values()) {
      if (memory.description.toLowerCase().includes(lower)) {
        results.push(memory);
      }
    }

    return results.slice(0, limit);
  }

  /**
   * Get storage statistics.
   *
   * @returns Stats object
   */
  getStats(): MultimodalStats {
    let totalSize = 0;
    for (const f of this._fileMemories.values()) {
      totalSize += f.sizeBytes;
    }

    return {
      total_images: this._imageMemories.size,
      total_files: this._fileMemories.size,
      total_size_bytes: totalSize,
      image_descriptions: [...this._imageMemories.values()].map((m) => m.description),
    };
  }

  /**
   * Generate a unique ID from content using SHA-256.
   */
  private _generateId(content: string): string {
    return crypto.createHash("sha256").update(content, "utf-8").digest("hex").slice(0, 16);
  }
}

// Global singleton instance
let _multimodalStore: MultimodalMemoryStore | null = null;

/**
 * Get the global multimodal storage instance.
 *
 * @param basePath - Base path for storage
 * @returns MultimodalMemoryStore instance
 */
export function getMultimodalStore(basePath: string = "./workspace/multimodal"): MultimodalMemoryStore {
  if (_multimodalStore === null) {
    _multimodalStore = new MultimodalMemoryStore(basePath);
  }
  return _multimodalStore;
}

/**
 * Reset the global multimodal store instance (for testing).
 */
export function resetMultimodalStore(): void {
  _multimodalStore = null;
}
