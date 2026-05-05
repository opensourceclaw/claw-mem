#!/usr/bin/env node

/**
 * claw-mem Post-Install Script
 *
 * Automatically merges claw-mem plugin configuration into
 * the user's OpenClaw config (~/.openclaw/openclaw.json).
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OPENCLAW_CONFIG = resolve(process.env.HOME || '~', '.openclaw', 'openclaw.json');
const AUTO_CONFIG_FILE = resolve(__dirname, '..', 'auto-config.json');

function loadJson(filepath) {
  try {
    if (!existsSync(filepath)) {
      return null;
    }
    return JSON.parse(readFileSync(filepath, 'utf-8'));
  } catch (err) {
    console.error(`[claw-mem post-install] Failed to read ${filepath}: ${err.message}`);
    return null;
  }
}

function saveJson(filepath, data) {
  try {
    writeFileSync(filepath, JSON.stringify(data, null, 2) + '\n', 'utf-8');
    console.log(`[claw-mem post-install] Config saved to ${filepath}`);
    return true;
  } catch (err) {
    console.error(`[claw-mem post-install] Failed to write ${filepath}: ${err.message}`);
    return false;
  }
}

function mergeConfig(existing, auto) {
  const merged = { ...existing };

  if (!merged.plugins) {
    merged.plugins = {};
  }

  // Merge plugins.allow
  if (auto.plugins?.allow) {
    const existingAllow = merged.plugins.allow || [];
    merged.plugins.allow = [...new Set([...existingAllow, ...auto.plugins.allow])];
  }

  // Merge plugins.slots
  if (auto.plugins?.slots) {
    if (!merged.plugins.slots) {
      merged.plugins.slots = {};
    }
    for (const [key, value] of Object.entries(auto.plugins.slots)) {
      if (!merged.plugins.slots[key]) {
        merged.plugins.slots[key] = value;
        console.log(`[claw-mem post-install] Added slot: ${key} = ${value}`);
      }
    }
  }

  // Merge plugins.entries
  if (auto.plugins?.entries) {
    if (!merged.plugins.entries) {
      merged.plugins.entries = {};
    }
    for (const [key, entry] of Object.entries(auto.plugins.entries)) {
      if (!merged.plugins.entries[key]) {
        merged.plugins.entries[key] = entry;
        console.log(`[claw-mem post-install] Added new plugin entry: ${key}`);
      } else {
        if (entry.config) {
          if (!merged.plugins.entries[key].config) {
            merged.plugins.entries[key].config = {};
          }
          for (const [configKey, configValue] of Object.entries(entry.config)) {
            if (!(configKey in merged.plugins.entries[key].config)) {
              merged.plugins.entries[key].config[configKey] = configValue;
              console.log(`[claw-mem post-install] Added default config: ${key}.${configKey}`);
            }
          }
        }
      }
    }
  }

  return merged;
}

function main() {
  console.log('[claw-mem post-install] Starting auto-configuration...');

  const existingConfig = loadJson(OPENCLAW_CONFIG);
  if (!existingConfig) {
    console.error('[claw-mem post-install] OpenClaw config not found, skipping auto-config.');
    return 1;
  }

  const autoConfig = loadJson(AUTO_CONFIG_FILE);
  if (!autoConfig) {
    console.error('[claw-mem post-install] Auto-config file not found, skipping.');
    return 1;
  }

  const mergedConfig = mergeConfig(existingConfig, autoConfig);
  if (saveJson(OPENCLAW_CONFIG, mergedConfig)) {
    console.log('[claw-mem post-install] Auto-configuration complete.');
    return 0;
  }

  return 1;
}

process.exit(main());
