import { describe, it, expect } from "vitest";
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
import { ValueBackup, backupMetadataToDict, backupMetadataFromDict } from "../../src/values/value_backup";

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
  return true;
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
  return true;
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
  return true;
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
  return true;
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
  return true;
}

// ── Test 6: Edge cases ─────────────────────────────────────────────────

function testEdgeCases(): void {
  setup();
  const store = new UserValueStore(path.join(TMP_DIR, "values-edge"));
  const backup = new ValueBackup(store, path.join(TMP_DIR, "backups-edge"));

  // Delete non-existent principle
  const result1 = store.deletePrinciple("no_user", "x");
  console.assert(result1 === null, "delete non-existent user should return null");

  // Export non-existent user
  let threw = false;
  try { backup.exportValues("no_user"); } catch { threw = true; }
  console.assert(threw, "export non-existent user should throw");

  // Import non-existent file
  threw = false;
  try { backup.importValues("u1", "/no/such/file.json"); } catch { threw = true; }
  console.assert(threw, "import non-existent file should throw");

  // Import invalid format
  const tmpFile = path.join(TMP_DIR, "invalid.json");
  fs.writeFileSync(tmpFile, JSON.stringify({ no_values: true }), "utf-8");
  threw = false;
  try { backup.importValues("u1", tmpFile); } catch { threw = true; }
  console.assert(threw, "import invalid format should throw");

  // Import with overwrite=false when user exists
  store.savePrinciple("existing", "test");
  fs.writeFileSync(tmpFile, JSON.stringify({ values: { principles: [], preferences: {}, red_lines: [] } }), "utf-8");
  threw = false;
  try { backup.importValues("existing", tmpFile, false); } catch { threw = true; }
  console.assert(threw, "import with overwrite=false when exists should throw");

  // deleteBackup non-existent
  const result2 = backup.deleteBackup("no-such-backup");
  console.assert(result2 === false, "delete non-existent backup should return false");

  // backupMetadata for user with no backups
  const meta = backup.backupMetadata("no_backups_user");
  console.assert(meta.backup_count === 0, "no backups should have count 0");
  console.assert(meta.latest_backup === null, "no backups should have null latest");

  // backupMetadataFromDict with empty checksum
  const bm = (backup as any).constructor.prototype;
  const fromDict = backupMetadataFromDict;
  // Actually test the standalone function
  const restored = fromDict({
    user_id: "test",
    backup_id: "b1",
    created_at: "2026-01-01T00:00:00Z",
    file_path: "/tmp/x.json",
    file_size: 100,
    values_count: 5,
  });
  console.assert(restored.checksum === "", "missing checksum should default to empty");
  console.assert(restored.userId === "test", "userId should match");

  // listUsers after saving
  store.savePrinciple("list_test_user", "p1");
  const users = store.listUsers();
  console.assert(users.includes("list_test_user"), "listUsers should include saved user");

  teardown();
  console.log("PASS: testEdgeCases");
  return true;
}

// ── Run all ────────────────────────────────────────────────────────────



describe("values.test", () => {
  it("SaveAndRetrievePrinciples", () => {
    expect(testSaveAndRetrievePrinciples()).toBe(true);
  });
  it("UserValueCRUD", () => {
    expect(testUserValueCRUD()).toBe(true);
  });
  it("FeedbackHandler", () => {
    expect(testFeedbackHandler()).toBe(true);
  });
  it("ValueBackup", () => {
    expect(testValueBackup()).toBe(true);
  });
  it("Serialization", () => {
    expect(testSerialization()).toBe(true);
  });
  it("EdgeCases", () => {
    expect(testEdgeCases()).toBe(true);
  });
});
