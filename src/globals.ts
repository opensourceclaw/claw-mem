// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * Minimal test utilities for TypeScript tests.
 *
 * Provides describe/it/assert compatible with the Node.js test runner
 * or standalone assertion. Written as a thin wrapper over Node's assert
 * for test files that live under tests/.
 */

import assert from "assert";

export { assert };

type TestFn = () => void | Promise<void>;

const _suites: Array<{ label: string; tests: Array<{ label: string; fn: TestFn }> }> = [];

/**
 * Group a set of related test cases.
 */
export function describe(label: string, fn: () => void): void {
  const prev = { label: "", tests: [] as Array<{ label: string; fn: TestFn }> };
  _suites.push(prev);
  fn();
  prev.label = label;
  // Pop from builder so nested describes work
  const suite = _suites.pop()!;
  _suites.push(suite);
}

/**
 * Register an individual test case.
 */
export function it(label: string, fn: TestFn): void {
  const suite = _suites[_suites.length - 1];
  if (suite) {
    suite.tests.push({ label, fn });
  }
}
