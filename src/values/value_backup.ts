// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Value Backup - Values local storage
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as crypto from "crypto";
import { UserValueStore, userValueToDict } from "./user_value_store";

// ── Backup metadata type ───────────────────────────────────────────────

export interface BackupMetadata {
  userId: string;
  backupId: string;
  createdAt: Date;
  filePath: string;
  fileSize: number;
  valuesCount: number;
  checksum: string;
}

export function backupMetadataToDict(m: BackupMetadata): Record<string, unknown> {
  return {
    user_id: m.userId,
    backup_id: m.backupId,
    created_at: m.createdAt.toISOString(),
    file_path: m.filePath,
    file_size: m.fileSize,
    values_count: m.valuesCount,
    checksum: m.checksum,
  };
}

export function backupMetadataFromDict(data: Record<string, unknown>): BackupMetadata {
  return {
    userId: data.user_id as string,
    backupId: data.backup_id as string,
    createdAt: new Date(data.created_at as string),
    filePath: data.file_path as string,
    fileSize: data.file_size as number,
    valuesCount: data.values_count as number,
    checksum: (data.checksum as string) || "",
  };
}

// ── Backup manager ─────────────────────────────────────────────────────

export class ValueBackup {
  private _metadataFile: string;

  constructor(
    private _valueStore: UserValueStore = new UserValueStore(),
    backupDir?: string,
  ) {
    const dir = backupDir || path.join(os.homedir(), ".claw_mem", "backups");
    fs.mkdirSync(dir, { recursive: true });
    this.backupDir = dir;
    this._metadataFile = path.join(dir, "metadata.json");
  }

  backupDir: string;

  /** Export user values to file. Returns backup metadata. */
  exportValues(userId: string, exportPath?: string): BackupMetadata {
    // Get user values
    const userValues = this._valueStore.getUserValues(userId);
    if (!userValues) {
      throw new Error(`User ${userId} not found`);
    }

    // Generate backup ID and path
    const backupId = crypto.randomUUID().slice(0, 8);

    const resolvedPath =
      exportPath ||
      path.join(
        this.backupDir,
        `${userId}_${new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19)}.json`,
      );

    // Export data

    const exportData: Record<string, unknown> = {
      user_id: userId,
      exported_at: new Date().toISOString(),
      version: "2.2.0",
      values: userValueToDict(userValues),
    };

    // Write file
    const jsonStr = JSON.stringify(exportData, null, 2);
    fs.writeFileSync(resolvedPath, jsonStr, "utf-8");

    // Calculate simple checksum
    const checksum = String(Math.abs(hashCode(jsonStr))).slice(0, 16);

    // Create metadata
    const stat = fs.statSync(resolvedPath);
    const metadata: BackupMetadata = {
      userId,
      backupId,
      createdAt: new Date(),
      filePath: resolvedPath,
      fileSize: stat.size,
      valuesCount:
        userValues.principles.length +
        Object.keys(userValues.preferences).length +
        userValues.redLines.length,
      checksum,
    };

    // Save metadata
    this._saveMetadata(metadata);

    return metadata;
  }

  /** Import user values from file. Returns true if import was successful. */
  importValues(userId: string, importPath: string, overwrite: boolean = false): boolean {
    // Read file
    if (!fs.existsSync(importPath)) {
      throw new Error(`Backup file not found: ${importPath}`);
    }

    const content = fs.readFileSync(importPath, "utf-8");
    const data = JSON.parse(content) as Record<string, unknown>;

    if (!data.values) {
      throw new Error("Invalid backup file format");
    }

    const importedValues = data.values as Record<string, unknown>;

    // Get existing values
    const existing = this._valueStore.getUserValues(userId);

    if (existing && !overwrite) {
      throw new Error(`User ${userId} already exists. Use overwrite=true to replace.`);
    }

    // Import principles
    const principles = (importedValues.principles as string[]) || [];
    for (const principle of principles) {
      this._valueStore.savePrinciple(userId, principle);
    }

    // Import preferences
    const preferences = (importedValues.preferences as Record<string, unknown>) || {};
    for (const [key, value] of Object.entries(preferences)) {
      this._valueStore.savePreference(userId, key, value);
    }

    // Import red lines
    const redLines = (importedValues.red_lines as string[]) || [];
    for (const line of redLines) {
      this._valueStore.saveRedLine(userId, line);
    }

    return true;
  }

  /** List backup files. */
  listBackups(userId?: string): BackupMetadata[] {
    const metadataList: BackupMetadata[] = [];

    let allMetadata: Record<string, Record<string, unknown>> = {};
    if (fs.existsSync(this._metadataFile)) {
      try {
        allMetadata = JSON.parse(
          fs.readFileSync(this._metadataFile, "utf-8"),
        ) as Record<string, Record<string, unknown>>;
      } catch {
        allMetadata = {};
      }
    }

    for (const [backupId, metaData] of Object.entries(allMetadata)) {
      if (userId === undefined || metaData.user_id === userId) {
        try {
          metadataList.push(backupMetadataFromDict(metaData));
        } catch {
          // skip invalid entries
        }
      }
    }

    // Sort by time descending
    metadataList.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

    return metadataList;
  }

  /** Get user backup metadata summary. */
  backupMetadata(userId: string): Record<string, unknown> {
    const backups = this.listBackups(userId);

    if (backups.length === 0) {
      return {
        user_id: userId,
        backup_count: 0,
        latest_backup: null,
        total_size: 0,
      };
    }

    return {
      user_id: userId,
      backup_count: backups.length,
      latest_backup: backupMetadataToDict(backups[0]),
      total_size: backups.reduce((sum, b) => sum + b.fileSize, 0),
    };
  }

  /** Delete backup by ID. Returns true if deletion was successful. */
  deleteBackup(backupId: string): boolean {
    let allMetadata: Record<string, Record<string, unknown>> = {};
    if (fs.existsSync(this._metadataFile)) {
      try {
        allMetadata = JSON.parse(
          fs.readFileSync(this._metadataFile, "utf-8"),
        ) as Record<string, Record<string, unknown>>;
      } catch {
        return false;
      }
    } else {
      return false;
    }

    if (!(backupId in allMetadata)) return false;

    const metaData = allMetadata[backupId];
    const filePath = metaData.file_path as string;

    // Delete file
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }

    // Delete metadata
    delete allMetadata[backupId];
    fs.writeFileSync(this._metadataFile, JSON.stringify(allMetadata, null, 2), "utf-8");

    return true;
  }

  /** Save backup metadata. */
  private _saveMetadata(metadata: BackupMetadata): void {
    let allMetadata: Record<string, Record<string, unknown>> = {};
    if (fs.existsSync(this._metadataFile)) {
      try {
        allMetadata = JSON.parse(
          fs.readFileSync(this._metadataFile, "utf-8"),
        ) as Record<string, Record<string, unknown>>;
      } catch {
        allMetadata = {};
      }
    }

    allMetadata[metadata.backupId] = backupMetadataToDict(metadata);
    fs.writeFileSync(this._metadataFile, JSON.stringify(allMetadata, null, 2), "utf-8");
  }
}

/** Simple string hash function for checksums. */
function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const chr = str.charCodeAt(i);
    hash = (hash << 5) - hash + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
}
