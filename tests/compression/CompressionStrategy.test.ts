import { describe, it, expect } from "vitest";
import { TruncateStrategy, SummarizeStrategy } from "../../src/compression/CompressionStrategy";

describe("TruncateStrategy", () => {
  const strategy = new TruncateStrategy();

  it("should compress content", async () => {
    const content = "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n";
    const result = await strategy.compress(content, 10);
    expect(result).toBeDefined();
    expect(result).toContain("... (truncated) ...");
  });

  it("should estimate result with low quality", () => {
    const est = strategy.estimateResult("test", 100);
    expect(est.quality).toBe("low");
    expect(est.estimatedTokens).toBe(100);
  });

  it("should preserve head content", async () => {
    const content = "# Header\n\n## Important\n\n**User**: test\n".repeat(20);
    const result = await strategy.compress(content, 50);
    expect(result).toContain("# Header");
  });

  it("should handle short content", async () => {
    const content = "short";
    const result = await strategy.compress(content, 100);
    expect(result).toContain("short");
  });
});

describe("SummarizeStrategy", () => {
  const strategy = new SummarizeStrategy("simple");

  it("should summarize content", async () => {
    const content = "regular line\n## Important heading\nregular\n```\ncode block\n```\n";
    const result = await strategy.compress(content, 100);
    expect(result).toBeDefined();
  });

  it("should include keywords lines", async () => {
    const content = "blah\nblah\n**critical fix**\n## Release notes\nblah\n";
    const result = await strategy.compress(content, 100);
    expect(result).toContain("critical fix");
    expect(result).toContain("Release notes");
  });

  it("should fallback to tail when no keywords", async () => {
    const content = "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\nk\nl\nm\nn\no\n";
    const result = await strategy.compress(content, 100);
    expect(result).toBeDefined();
  });

  it("should estimate result with medium quality", () => {
    const est = strategy.estimateResult("test content", 100);
    expect(est.quality).toBe("medium");
  });
});
