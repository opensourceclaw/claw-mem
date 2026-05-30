// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

import { MultimodalMemoryStore, resetMultimodalStore, MemoryType } from "../../src/multimodal/multimodal_memory";

// ── Multimodal Memory Tests ────────────────────────────────────────

function testStoreAndRetrieve(): boolean {
  const store = new MultimodalMemoryStore("/tmp/test-multimodal-store");

  // Store an image
  const imageId = store.storeImage("/tmp/test-photo.png", "A test photo", {
    resolution: "1920x1080",
  });
  if (!imageId || imageId.length !== 16) {
    console.error(`FAIL: Expected 16-char image ID, got "${imageId}" (len ${imageId.length})`);
    return false;
  }

  // Retrieve image
  const image = store.getImage(imageId);
  if (!image) {
    console.error("FAIL: Should retrieve stored image");
    return false;
  }
  if (image.description !== "A test photo") {
    console.error(`FAIL: Expected description "A test photo", got "${image.description}"`);
    return false;
  }
  if (image.metadata.resolution !== "1920x1080") {
    console.error(`FAIL: Expected metadata.resolution "1920x1080", got "${image.metadata.resolution}"`);
    return false;
  }

  // Store a file
  const fileId = store.storeFile("/tmp/test-doc.pdf", "application/pdf", {
    author: "Peter",
  });
  if (!fileId || fileId.length !== 16) {
    console.error(`FAIL: Expected 16-char file ID, got "${fileId}"`);
    return false;
  }

  // Retrieve file
  const file = store.getFile(fileId);
  if (!file) {
    console.error("FAIL: Should retrieve stored file");
    return false;
  }
  if (file.filename !== "test-doc.pdf") {
    console.error(`FAIL: Expected filename "test-doc.pdf", got "${file.filename}"`);
    return false;
  }
  if (file.fileType !== "application/pdf") {
    console.error(`FAIL: Expected fileType "application/pdf", got "${file.fileType}"`);
    return false;
  }

  console.log("  PASS: Store and retrieve multimodal memories");
  return true;
}

function testSearchByDescription(): boolean {
  const store = new MultimodalMemoryStore("/tmp/test-multimodal-search");

  store.storeImage("/tmp/photo1.png", "Sunset over the mountains");
  store.storeImage("/tmp/photo2.png", "Mountain lake reflection");
  store.storeImage("/tmp/photo3.png", "City skyline at night");

  const results = store.searchByDescription("mountain");
  if (results.length !== 2) {
    console.error(`FAIL: Expected 2 results for "mountain", got ${results.length}`);
    return false;
  }

  const noResults = store.searchByDescription("ocean");
  if (noResults.length !== 0) {
    console.error(`FAIL: Expected 0 results for "ocean", got ${noResults.length}`);
    return false;
  }

  const stats = store.getStats();
  if (stats.total_images !== 3) {
    console.error(`FAIL: Expected 3 total images, got ${stats.total_images}`);
    return false;
  }
  if (stats.image_descriptions.length !== 3) {
    console.error(`FAIL: Expected 3 image descriptions, got ${stats.image_descriptions.length}`);
    return false;
  }

  console.log("  PASS: Search by description and stats");
  return true;
}

// ── Run ────────────────────────────────────────────────────────────

function run(): void {
  console.log("\nMultimodal Module Tests\n");

  let passed = 0;
  let failed = 0;

  const tests: [string, () => boolean][] = [
    ["Store and retrieve multimodal memories", testStoreAndRetrieve],
    ["Search by description and stats", testSearchByDescription],
  ];

  for (const [name, fn] of tests) {
    try {
      if (fn()) {
        passed++;
      } else {
        console.error(`  FAIL: ${name}`);
        failed++;
      }
    } catch (err) {
      console.error(`  ERROR: ${name} — ${err}`);
      failed++;
    }
  }

  // Cleanup
  resetMultimodalStore();

  console.log(`\nResults: ${passed} passed, ${failed} failed\n`);
  if (failed > 0) process.exit(1);
}

run();
