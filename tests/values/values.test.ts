import * as path from "path";
import * as os from "os";
import * as fs from "fs";
import {
  UserValueStore,
  userValueToDict,
  userValueFromDict,
} from "../../src/values/user_value_store";
import {
  FeedbackHandler,
  FeedbackStatus,
  valueSuggestionToDict,
} from "../../src/values/feedback_handler";
import { ValueBackup, backupMetadataToDict } from "../../src/values/value_backup";

// ── Test helpers ───────────────────────────────────────────────────────

const TMP_DIR = path.join(os.tmpdir(), "claw-mem-test-values-" + Date.now());

function setup(): void {
  fs.mkdirSync(TMP_DIR, { recursive: true });
}

function teardown(): void {
  try {
    fs.rmSync(TMP_DIR, { recursive: true, force: true });
  } catch {
    // ignore
  }
}

// ── Test 1: UserValue save and retrieve principles ─────────────────────

function testSaveAndRetrievePrinciples(): void {
  setup();
  const store = new UserValueStore(path.join(TMP_DIR, "values1"));

  // Save a principle
  const result = store.savePrinciple("user1", "Always be kind");
  console.assert(result.principles.includes("Always be kind"), "Principle should be saved");

  // Duplicate save should be idempotent
  store.savePrinciple("user1", "Always be kind");
  const userValues = store.getUserValues("user1")!;
  console.assert(
    userValues.principles.length === 1,
    "Duplicate principles should not be added",
  );

  // Retrieve from a new store instance (disk-based)
  const store2 = new UserValueStore(path.join(TMP_DIR, "values1"));
  const retrieved = store2.getUserValues("user1")!;
  console.assert(retrieved !== null, "Should retrieve user values from disk");
  console.assert(
    retrieved.principles.includes("Always be kind"),
    "Should have saved principle on disk",
  );

  teardown();
  console.log("PASS: testSaveAndRetrievePrinciples");
}

// ── Test 2: UserValue CRUD operations ──────────────────────────────────

function testUserValueCRUD(): void {
  setup();
  const store = new UserValueStore(path.join(TMP_DIR, "values2"));

  // Save all three types
  store.savePrinciple("user2", "Honesty");
  store.savePreference("user2", "language", "Chinese");
  store.saveRedLine("user2", "Never share secrets");

  const values = store.getUserValues("user2")!;
  console.assert(values.principles.length === 1, "Should have 1 principle");
  console.assert(values.preferences.language === "Chinese", "Should have preference");
  console.assert(values.redLines.length === 1, "Should have 1 red line");

  // Delete principle
  store.deletePrinciple("user2", "Honesty");
  const afterDelete = store.getUserValues("user2")!;
  console.assert(afterDelete.principles.length === 0, "Principle should be deleted");

  // Delete red line
  store.deleteRedLine("user2", "Never share secrets");
  const afterRedDelete = store.getUserValues("user2")!;
  console.assert(afterRedDelete.redLines.length === 0, "Red line should be deleted");

  // Delete preference
  store.deletePreference("user2", "language");
  const afterPrefDelete = store.getUserValues("user2")!;
  console.assert(
    Object.keys(afterPrefDelete.preferences).length === 0,
    "Preference should be deleted",
  );

  teardown();
  console.log("PASS: testUserValueCRUD");
}

// ── Test 3: FeedbackHandler workflow ───────────────────────────────────

function testFeedbackHandler(): void {
  setup();
  const store = new UserValueStore(path.join(TMP_DIR, "values3"));
  const handler = new FeedbackHandler(store);

  // Request confirmation
  const suggestion = handler.requestConfirmation(
    "user3",
    "principle",
    "Be respectful",
    ["user said it in conversation"],
  );
  console.assert(suggestion.id.length > 0, "Should have an ID");
  console.assert(suggestion.status === FeedbackStatus.PENDING, "Should be PENDING");

  // Check pending
  const pending = handler.getPendingSuggestions("user3");
  console.assert(pending.length === 1, "Should have 1 pending");

  // Process feedback (accept)
  const result = handler.processFeedback(suggestion.id, true);
  console.assert(result === true, "processFeedback should return true");

  // Check it was saved to store
  const values = store.getUserValues("user3")!;
  console.assert(values.principles.includes("Be respectful"), "Principle should be saved");

  // Check accepted list
  const accepted = handler.getAcceptedSuggestions("user3");
  console.assert(accepted.length === 1, "Should have 1 accepted");

  teardown();
  console.log("PASS: testFeedbackHandler");
}

// ── Test 4: ValueBackup export and import ──────────────────────────────

function testValueBackup(): void {
  setup();
  const store = new UserValueStore(path.join(TMP_DIR, "values4"));
  const backup = new ValueBackup(store, path.join(TMP_DIR, "backups4"));

  // Setup some values
  store.savePrinciple("user4", "Principle A");
  store.savePreference("user4", "key1", "value1");
  store.saveRedLine("user4", "Red line A");

  // Export
  const meta = backup.exportValues("user4");
  console.assert(meta.userId === "user4", "Metadata should have user4");
  console.assert(meta.backupId.length > 0, "Should have backup ID");
  console.assert(meta.fileSize > 0, "File should have content");

  // List backups
  const backups = backup.listBackups("user4");
  console.assert(backups.length >= 1, "Should have at least 1 backup");

  // Import to a new user
  const store2 = new UserValueStore(path.join(TMP_DIR, "values_imported"));
  const backup2 = new ValueBackup(store2, path.join(TMP_DIR, "backups_imported"));

  // First export, then import
  const exportPath = meta.filePath;
  backup2.importValues("user5", exportPath, true);

  const imported = store2.getUserValues("user5")!;
  console.assert(imported.principles.includes("Principle A"), "Should import principles");
  console.assert(imported.redLines.includes("Red line A"), "Should import red lines");
  console.assert(imported.preferences.key1 === "value1", "Should import preferences");

  // Backup metadata
  const meta2 = backup2.backupMetadata("user5");
  console.assert((meta2.backup_count as number) >= 0, "Should have backup metadata");

  teardown();
  console.log("PASS: testValueBackup");
}

// ── Test 5: toDict / fromDict serialization ────────────────────────────

function testSerialization(): void {
  const value = {
    userId: "test_user",
    principles: ["A", "B"],
    preferences: { lang: "en" },
    redLines: ["X"],
    createdAt: new Date("2026-01-01"),
    updatedAt: new Date("2026-01-02"),
  };

  const d = userValueToDict(value);
  console.assert(d.user_id === "test_user", "toDict: user_id mismatch");
  console.assert(
    (d.principles as string[]).length === 2,
    "toDict: principles length",
  );

  const restored = userValueFromDict(d);
  console.assert(restored.userId === "test_user", "fromDict: userId mismatch");
  console.assert(restored.principles.length === 2, "fromDict: principles length");
  console.assert(restored.createdAt instanceof Date, "fromDict: createdAt is Date");

  console.log("PASS: testSerialization");
}

// ── Run all ────────────────────────────────────────────────────────────

function main(): void {
  testSaveAndRetrievePrinciples();
  testUserValueCRUD();
  testFeedbackHandler();
  testValueBackup();
  testSerialization();
  console.log("\nAll values tests passed!");
}

main();
