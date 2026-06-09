// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Feedback Handler - Feedback processing mechanism
 */

import * as crypto from "crypto";
import { UserValueStore } from "./user_value_store.js";

// ── Enums & types ──────────────────────────────────────────────────────

export enum FeedbackStatus {
  PENDING = "pending",
  ACCEPTED = "accepted",
  REJECTED = "rejected",
  EXPIRED = "expired",
}

export interface ValueSuggestion {
  id: string;
  userId: string;
  suggestionType: string; // "principle" | "preference" | "red_line"
  content: string;
  evidence: string[];
  status: FeedbackStatus;
  createdAt: Date;
  respondedAt: Date | null;
}

export function valueSuggestionToDict(s: ValueSuggestion): Record<string, unknown> {
  return {
    id: s.id,
    user_id: s.userId,
    suggestion_type: s.suggestionType,
    content: s.content,
    evidence: s.evidence,
    status: s.status,
    created_at: s.createdAt.toISOString(),
    responded_at: s.respondedAt ? s.respondedAt.toISOString() : null,
  };
}

// ── Handler ────────────────────────────────────────────────────────────

export class FeedbackHandler {
  private _pendingSuggestions: Record<string, ValueSuggestion[]> = {};
  private _suggestionHistory: ValueSuggestion[] = [];

  constructor(private _valueStore: UserValueStore = new UserValueStore()) {}

  /** Request user confirmation of values. */
  requestConfirmation(
    userId: string,
    valueType: string,
    content: string,
    evidence: string[] = [],
  ): ValueSuggestion {
    const suggestion: ValueSuggestion = {
      id: crypto.randomUUID().slice(0, 8),
      userId,
      suggestionType: valueType,
      content,
      evidence,
      status: FeedbackStatus.PENDING,
      createdAt: new Date(),
      respondedAt: null,
    };

    // Add to pending list
    if (!this._pendingSuggestions[userId]) {
      this._pendingSuggestions[userId] = [];
    }
    this._pendingSuggestions[userId].push(suggestion);
    this._suggestionHistory.push(suggestion);

    return suggestion;
  }

  /** Process user feedback. Returns true if successfully processed. */
  processFeedback(suggestionId: string, accepted: boolean): boolean {
    // Find suggestion
    const suggestion = this._suggestionHistory.find((s) => s.id === suggestionId);
    if (!suggestion) return false;

    // Update status
    suggestion.status = accepted ? FeedbackStatus.ACCEPTED : FeedbackStatus.REJECTED;
    suggestion.respondedAt = new Date();

    // If accepted, update to value store
    if (accepted) {
      const userId = suggestion.userId;

      if (suggestion.suggestionType === "principle") {
        this._valueStore.savePrinciple(userId, suggestion.content);
      } else if (suggestion.suggestionType === "preference") {
        // Preference needs key-value parsing
        // Simplified: assume content format is "key:value"
        const colonIdx = suggestion.content.indexOf(":");
        if (colonIdx !== -1) {
          const key = suggestion.content.slice(0, colonIdx).trim();
          const value = suggestion.content.slice(colonIdx + 1).trim();
          this._valueStore.savePreference(userId, key, value);
        }
      } else if (suggestion.suggestionType === "red_line") {
        this._valueStore.saveRedLine(userId, suggestion.content);
      }
    }

    // Remove from pending list
    const userId = suggestion.userId;
    if (this._pendingSuggestions[userId]) {
      this._pendingSuggestions[userId] = this._pendingSuggestions[userId].filter(
        (s) => s.id !== suggestionId,
      );
    }

    return true;
  }

  /** Suggest updating values. */
  suggestUpdate(suggestion: Record<string, unknown>): ValueSuggestion {
    return this.requestConfirmation(
      suggestion.user_id as string,
      (suggestion.type as string) || "principle",
      suggestion.content as string,
      (suggestion.evidence as string[]) || [],
    );
  }

  /** Get pending suggestions for a user. */
  getPendingSuggestions(userId: string): ValueSuggestion[] {
    return this._pendingSuggestions[userId] || [];
  }

  /** Get accepted suggestions for a user. */
  getAcceptedSuggestions(userId: string): ValueSuggestion[] {
    return this._suggestionHistory.filter(
      (s) => s.userId === userId && s.status === FeedbackStatus.ACCEPTED,
    );
  }

  /** Get rejected suggestions for a user. */
  getRejectedSuggestions(userId: string): ValueSuggestion[] {
    return this._suggestionHistory.filter(
      (s) => s.userId === userId && s.status === FeedbackStatus.REJECTED,
    );
  }

  /** Clear expired suggestions. Returns count of cleared entries. */
  clearExpired(maxAgeHours: number = 24): number {
    const now = new Date();
    let expired = 0;

    for (const suggestion of this._suggestionHistory) {
      if (suggestion.status === FeedbackStatus.PENDING) {
        const ageMs = now.getTime() - suggestion.createdAt.getTime();
        const ageHours = ageMs / (1000 * 60 * 60);
        if (ageHours > maxAgeHours) {
          suggestion.status = FeedbackStatus.EXPIRED;
          suggestion.respondedAt = now;
          expired++;
        }
      }
    }

    return expired;
  }
}
