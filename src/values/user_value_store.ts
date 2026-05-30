// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * User Value Store - User values storage
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";

// ── Data type ──────────────────────────────────────────────────────────

export interface UserValue {
  userId: string;
  principles: string[];
  preferences: Record<string, unknown>;
  redLines: string[];
  createdAt: Date;
  updatedAt: Date;
}

export function userValueToDict(v: UserValue): Record<string, unknown> {
  return {
    user_id: v.userId,
    principles: v.principles,
    preferences: v.preferences,
    red_lines: v.redLines,
    created_at: v.createdAt.toISOString(),
    updated_at: v.updatedAt.toISOString(),
  };
}

export function userValueFromDict(data: Record<string, unknown>): UserValue {
  return {
    userId: data.user_id as string,
    principles: (data.principles as string[]) || [],
    preferences: (data.preferences as Record<string, unknown>) || {},
    redLines: (data.red_lines as string[]) || [],
    createdAt: data.created_at
      ? new Date(data.created_at as string)
      : new Date(),
    updatedAt: data.updated_at
      ? new Date(data.updated_at as string)
      : new Date(),
  };
}

// ── Store ──────────────────────────────────────────────────────────────

export class UserValueStore {
  private _cache: Record<string, UserValue> = {};

  /**
   * @param storagePath - Storage path, default ~/.claw_mem/values/
   */
  constructor(public storagePath: string = path.join(os.homedir(), ".claw_mem", "values")) {
    fs.mkdirSync(this.storagePath, { recursive: true });
  }

  /** Get user data file path, sanitizing user_id for the filesystem. */
  private _getUserFile(userId: string): string {
    const safeId = userId.replace(/\//g, "_").replace(/\\/g, "_");
    return path.join(this.storagePath, `${safeId}.json`);
  }

  /** Save core principle. Returns updated user values. */
  savePrinciple(userId: string, principle: string): UserValue {
    const userValues = this._getOrCreateUser(userId);
    if (!userValues.principles.includes(principle)) {
      userValues.principles.push(principle);
      userValues.updatedAt = new Date();
      this._saveUser(userValues);
    }
    return userValues;
  }

  /** Save user preference. Returns updated user values. */
  savePreference(userId: string, key: string, value: unknown): UserValue {
    const userValues = this._getOrCreateUser(userId);
    userValues.preferences[key] = value;
    userValues.updatedAt = new Date();
    this._saveUser(userValues);
    return userValues;
  }

  /** Save red line. Returns updated user values. */
  saveRedLine(userId: string, line: string): UserValue {
    const userValues = this._getOrCreateUser(userId);
    if (!userValues.redLines.includes(line)) {
      userValues.redLines.push(line);
      userValues.updatedAt = new Date();
      this._saveUser(userValues);
    }
    return userValues;
  }

  /** Get user values, or null if not found. */
  getUserValues(userId: string): UserValue | null {
    if (userId in this._cache) return this._cache[userId];

    const userFile = this._getUserFile(userId);
    if (fs.existsSync(userFile)) {
      try {
        const raw = fs.readFileSync(userFile, "utf-8");
        const data = JSON.parse(raw) as Record<string, unknown>;
        const userValues = userValueFromDict(data);
        this._cache[userId] = userValues;
        return userValues;
      } catch {
        return null;
      }
    }

    return null;
  }

  /** Delete core principle. Returns updated user values. */
  deletePrinciple(userId: string, principle: string): UserValue | null {
    const userValues = this.getUserValues(userId);
    if (!userValues) return null;

    const idx = userValues.principles.indexOf(principle);
    if (idx !== -1) {
      userValues.principles.splice(idx, 1);
      userValues.updatedAt = new Date();
      this._saveUser(userValues);
    }
    return userValues;
  }

  /** Delete red line. Returns updated user values. */
  deleteRedLine(userId: string, line: string): UserValue | null {
    const userValues = this.getUserValues(userId);
    if (!userValues) return null;

    const idx = userValues.redLines.indexOf(line);
    if (idx !== -1) {
      userValues.redLines.splice(idx, 1);
      userValues.updatedAt = new Date();
      this._saveUser(userValues);
    }
    return userValues;
  }

  /** Delete preference. Returns updated user values. */
  deletePreference(userId: string, key: string): UserValue | null {
    const userValues = this.getUserValues(userId);
    if (!userValues) return null;

    if (key in userValues.preferences) {
      delete userValues.preferences[key];
      userValues.updatedAt = new Date();
      this._saveUser(userValues);
    }
    return userValues;
  }

  /** List all user IDs stored on disk. */
  listUsers(): string[] {
    const users: string[] = [];
    try {
      const files = fs.readdirSync(this.storagePath);
      for (const f of files) {
        if (f.endsWith(".json")) {
          const userId = path.basename(f, ".json").replace(/_/g, "/");
          users.push(userId);
        }
      }
    } catch {
      // directory does not exist or is inaccessible
    }
    return users;
  }

  /** Get or create user values. */
  private _getOrCreateUser(userId: string): UserValue {
    const existing = this.getUserValues(userId);
    if (existing) return existing;

    const newUser: UserValue = {
      userId,
      principles: [],
      preferences: {},
      redLines: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    this._cache[userId] = newUser;
    return newUser;
  }

  /** Save user values to file. */
  private _saveUser(userValues: UserValue): void {
    const userFile = this._getUserFile(userValues.userId);
    fs.writeFileSync(userFile, JSON.stringify(userValueToDict(userValues), null, 2), "utf-8");
    this._cache[userValues.userId] = userValues;
  }
}
