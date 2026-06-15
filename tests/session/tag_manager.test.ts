import { describe, it, expect } from "vitest";
import { TagManager } from "../../src/session/tag_manager.js";

describe("TagManager", () => {
  describe("generate", () => {
    it("should generate tag with correct format", () => {
      const tm = new TagManager("claw");
      const tag = tm.generate("SUMMARY", "sess_abc123");

      expect(tag).toBe("claw:session_summary:sess_abc123");
    });

    it("should throw on empty sessionId", () => {
      const tm = new TagManager();
      expect(() => tm.generate("SUMMARY", "")).toThrow(TypeError);
    });

    it("should use default prefix when none provided", () => {
      const tm = new TagManager();
      const tag = tm.generate("CONTINUITY", "sess_001");
      expect(tag).toContain("claw:");
    });

    it("should generate all tag types", () => {
      const tm = new TagManager("app");
      expect(tm.generate("SUMMARY", "s1")).toBe("app:session_summary:s1");
      expect(tm.generate("CONTINUITY", "s1")).toBe("app:session_continuity:s1");
      expect(tm.generate("PENDING", "s1")).toBe("app:session_pending:s1");
      expect(tm.generate("CONTEXT", "s1")).toBe("app:session_context:s1");
    });
  });

  describe("validate", () => {
    it("should validate a correctly formatted tag", () => {
      const tm = new TagManager("claw");
      const tag = tm.generate("SUMMARY", "sess_001");
      expect(tm.validate(tag)).toBe(true);
    });

    it("should reject tag with wrong prefix", () => {
      const tm = new TagManager("claw");
      expect(tm.validate("other:session_summary:sess_001")).toBe(false);
    });

    it("should reject tag with invalid type", () => {
      const tm = new TagManager("claw");
      expect(tm.validate("claw:invalid_type:sess_001")).toBe(false);
    });

    it("should reject empty tag", () => {
      const tm = new TagManager();
      expect(tm.validate("")).toBe(false);
    });

    it("should reject tag with empty sessionId", () => {
      const tm = new TagManager("claw");
      expect(tm.validate("claw:session_summary:")).toBe(false);
    });
  });

  describe("validateAll", () => {
    it("should separate valid and invalid tags", () => {
      const tm = new TagManager("claw");
      tm.generate("SUMMARY", "sess_001");

      const result = tm.validateAll([
        "claw:session_summary:sess_001",
        "bad:tag",
        "claw:session_continuity:sess_002",
      ]);

      expect(result.valid).toHaveLength(2);
      expect(result.invalid).toHaveLength(1);
    });
  });

  describe("getHistory", () => {
    it("should record tag generation history", () => {
      const tm = new TagManager("claw");
      tm.generate("SUMMARY", "sess_001");
      tm.generate("CONTINUITY", "sess_001");

      const history = tm.getHistory();
      expect(history).toHaveLength(2);
      expect(history[0].action).toBe("add");
      expect(history[0].tag).toBe("claw:session_summary:sess_001");
    });
  });
});
