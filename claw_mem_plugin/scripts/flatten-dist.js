#!/usr/bin/env node
// claw-mem plugin dist flattener
// tsc with rootDir ".." produces nested dist/src/ and dist/claw_mem_plugin/
// This script flattens everything into dist/ with correct require() paths.

const fs = require("fs");
const path = require("path");

const DIST = path.join(__dirname, "..", "dist");

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) { walk(full, files); }
    else { files.push(full); }
  }
  return files;
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

// ── Step 1: move all files from dist/src/ to dist/ ──
const srcDir = path.join(DIST, "src");
if (fs.existsSync(srcDir)) {
  const files = walk(srcDir);
  for (const file of files) {
    const rel = path.relative(srcDir, file);
    const dest = path.join(DIST, rel);
    ensureDir(path.dirname(dest));
    fs.renameSync(file, dest);
  }
  // Remove empty dirs under dist/src/
  fs.rmSync(srcDir, { recursive: true, force: true });
}

// ── Step 2: move index.js from dist/claw_mem_plugin/ to dist/ ──
const pluginDir = path.join(DIST, "claw_mem_plugin");
if (fs.existsSync(pluginDir)) {
  const idx = path.join(pluginDir, "index.js");
  if (fs.existsSync(idx)) {
    fs.copyFileSync(idx, path.join(DIST, "index.js"));
  }
  const dts = path.join(pluginDir, "index.d.ts");
  if (fs.existsSync(dts)) {
    fs.copyFileSync(dts, path.join(DIST, "index.d.ts"));
  }
  fs.rmSync(pluginDir, { recursive: true, force: true });
}

// ── Step 3: copy openclaw.plugin.json to dist/ ──
const pluginJson = path.join(__dirname, "..", "openclaw.plugin.json");
if (fs.existsSync(pluginJson)) {
  fs.copyFileSync(pluginJson, path.join(DIST, "openclaw.plugin.json"));
}

// ── Step 4: fix require() paths ──
// In dist/index.js: "./src/bridge" → "./bridge", "./src/memory_manager" → "./memory_manager"
const indexJs = path.join(DIST, "index.js");
if (fs.existsSync(indexJs)) {
  let content = fs.readFileSync(indexJs, "utf-8");
  content = content.replace(/require\("\.\.\/src\/([^"]+)"\)/g, 'require("./$1")');
  fs.writeFileSync(indexJs, content);
}

// ── Step 5: verify ──
const finalFiles = walk(DIST).map(f => path.relative(DIST, f)).sort();
console.log("[flatten-dist] dist/ files:", finalFiles.filter(f => f.endsWith(".js")).length, "JS files");
console.log("[flatten-dist] index.js:", fs.existsSync(path.join(DIST, "index.js")));
console.log("[flatten-dist] openclaw.plugin.json:", fs.existsSync(path.join(DIST, "openclaw.plugin.json")));
