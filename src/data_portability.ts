// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Data Portability (Import/Export | TS)
 *
 * Exports and imports memory data for backup and migration.
 */

import * as fs from "fs";
import * as path from "path";
import { EpisodicStorage } from "./storage/episodic";
import { SemanticStorage } from "./storage/semantic";
import { ProceduralStorage } from "./storage/procedural";

export interface ExportOptions {
  format?: "json" | "markdown";
  includeEpisodic?: boolean;
  includeSemantic?: boolean;
  includeProcedural?: boolean;
}

export interface ExportResult {
  files: string[];
  recordCount: number;
  format: string;
  outputDir: string;
}

export interface ImportResult {
  importedCount: number;
  errors: string[];
}

export class DataPortability {
  private workspace: string;

  constructor(workspace: string) {
    this.workspace = workspace;
  }

  exportData(outputDir: string, options: ExportOptions = {}): ExportResult {
    const format = options.format ?? "json";
    const files: string[] = [];
    let recordCount = 0;
    fs.mkdirSync(outputDir, { recursive: true });

    if (options.includeEpisodic !== false) {
      const ep = new EpisodicStorage(this.workspace);
      const records = ep.getAll();
      recordCount += records.length;
      const outPath = path.join(outputDir, "episodic_export.json");
      fs.writeFileSync(outPath, JSON.stringify(records, null, 2), "utf-8");
      files.push(outPath);
    }

    if (options.includeSemantic !== false) {
      const sem = new SemanticStorage(this.workspace);
      const records = sem.getAll();
      recordCount += records.length;
      const outPath = path.join(outputDir, "semantic_export.json");
      fs.writeFileSync(outPath, JSON.stringify(records, null, 2), "utf-8");
      files.push(outPath);
    }

    if (options.includeProcedural !== false) {
      const proc = new ProceduralStorage(this.workspace);
      const records = proc.getAll();
      recordCount += records.length;
      const outPath = path.join(outputDir, "procedural_export.json");
      fs.writeFileSync(outPath, JSON.stringify(records, null, 2), "utf-8");
      files.push(outPath);
    }

    return { files, recordCount, format, outputDir };
  }

  importData(inputDir: string): ImportResult {
    const imported: number[] = [];
    const errors: string[] = [];

    const importFile = (file: string, storage: { store(r: Record<string, unknown>): void }): void => {
      try {
        const data = JSON.parse(fs.readFileSync(file, "utf-8")) as Array<Record<string, unknown>>;
        for (const r of data) {
          try { storage.store(r); imported.push(1); }
          catch (e) { errors.push(`Error importing record: ${e}`); }
        }
      } catch (e) { errors.push(`Error reading ${file}: ${e}`); }
    };

    const epFile = path.join(inputDir, "episodic_export.json");
    if (fs.existsSync(epFile)) importFile(epFile, new EpisodicStorage(this.workspace));

    const semFile = path.join(inputDir, "semantic_export.json");
    if (fs.existsSync(semFile)) importFile(semFile, new SemanticStorage(this.workspace));

    const procFile = path.join(inputDir, "procedural_export.json");
    if (fs.existsSync(procFile)) importFile(procFile, new ProceduralStorage(this.workspace));

    return { importedCount: imported.length, errors };
  }
}
