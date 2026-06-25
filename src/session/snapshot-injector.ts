// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

import { SessionSnapshot } from "./snapshot-types.js";

export function formatRecoveryContext(s: SessionSnapshot): string {
  const lines: string[] = ["[Session Recovery]"];
  lines.push(`**Topic**: ${truncate(s.currentTopic, 120)}`);
  if (s.activeTask) {
    lines.push(`**Active Task**: ${truncate(s.activeTask.description, 200)}`);
    lines.push(`**Progress**: ${truncate(s.activeTask.progress, 200)}`);
  }
  if (s.recentDecisions.length) {
    lines.push("**Key Decisions**:");
    s.recentDecisions.slice(0, 3).forEach((d) => lines.push(`- ${truncate(d, 160)}`));
  }
  if (s.pendingItems.length) {
    lines.push("**Pending Items**:");
    s.pendingItems.slice(0, 5).forEach((p) => lines.push(`- ${truncate(p, 160)}`));
  }
  lines.push(`**Last Active**: ${new Date(s.lastActiveAt).toISOString()}`);
  return lines.join("\n");
}

function truncate(text: string, max: number): string {
  return text.length <= max ? text : text.slice(0, max - 1) + "…";
}
