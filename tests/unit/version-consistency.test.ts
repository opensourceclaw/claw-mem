// 版本位一致性断言:VERSION(src/version.ts) === package.json === openclaw.plugin.json

import { describe, it, expect } from "vitest";
import * as fs from "fs";
import { VERSION } from "../../src/version";

describe("version consistency", () => {
  it("VERSION 与 package.json / openclaw.plugin.json 一致", () => {
    const pkg = JSON.parse(fs.readFileSync("package.json", "utf-8"));
    const plugin = JSON.parse(fs.readFileSync("openclaw.plugin.json", "utf-8"));

    expect(pkg.version).toBe(VERSION);
    expect(plugin.version).toBe(VERSION);
  });
});
