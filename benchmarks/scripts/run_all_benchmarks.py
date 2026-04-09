#!/usr/bin/env python3
"""
Run all benchmarks for claw-mem

This script runs all three benchmarks (LongMemEval, LoCoMo, ConvoMem)
and generates a comprehensive performance report.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# claw-mem imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from claw_mem import MemoryManager

# Benchmark runners
from longmemeval_runner import LongMemEvalRunner
from locomo_runner import LoCoMoRunner
from convomem_runner import ConvoMemRunner


class BenchmarkOrchestrator:
    """Orchestrates all benchmarks and generates comprehensive report."""

    def __init__(self, workspace: str = "workspace"):
        """
        Initialize benchmark orchestrator.

        Args:
            workspace: Memory manager workspace
        """
        self.workspace = workspace
        self.memory_manager = MemoryManager(workspace)
        self.results = {
            "longmemeval": None,
            "locomo": None,
            "convomem": None,
            "overall": {}
        }

    def run_all_benchmarks(self, data_dirs: Dict[str, str] = None) -> Dict:
        """
        Run all benchmarks.

        Args:
            data_dirs: Dictionary of data directories for each benchmark

        Returns:
            Complete results dictionary
        """
        if data_dirs is None:
            data_dirs = {
                "longmemeval": "data/longmemeval",
                "locomo": "data/locomo",
                "convomem": "data/convomem"
            }

        print(f"\n{'='*80}")
        print(f"claw-mem Performance Benchmarks")
        print(f"{'='*80}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        start_time = time.time()

        # Run LongMemEval
        print("\n" + "="*80)
        print("Running LongMemEval Benchmark...")
        print("="*80 + "\n")
        try:
            longmemeval_runner = LongMemEvalRunner(
                memory_manager=self.memory_manager,
                data_dir=data_dirs["longmemeval"]
            )
            self.results["longmemeval"] = longmemeval_runner.run_test()
            longmemeval_report = longmemeval_runner.generate_report()
            longmemeval_runner.save_results()
        except FileNotFoundError as e:
            print(f"⚠️  LongMemEval data not found: {e}")
            self.results["longmemeval"] = {"error": str(e)}

        # Clear memory for next benchmark
        self.memory_manager = MemoryManager(self.workspace)

        # Run LoCoMo
        print("\n" + "="*80)
        print("Running LoCoMo Benchmark...")
        print("="*80 + "\n")
        try:
            locomo_runner = LoCoMoRunner(
                memory_manager=self.memory_manager,
                data_dir=data_dirs["locomo"]
            )
            self.results["locomo"] = locomo_runner.run_evaluation()
            locomo_report = locomo_runner.generate_report()
            locomo_runner.save_results()
        except FileNotFoundError as e:
            print(f"⚠️  LoCoMo data not found: {e}")
            self.results["locomo"] = {"error": str(e)}

        # Clear memory for next benchmark
        self.memory_manager = MemoryManager(self.workspace)

        # Run ConvoMem
        print("\n" + "="*80)
        print("Running ConvoMem Benchmark...")
        print("="*80 + "\n")
        try:
            convomem_runner = ConvoMemRunner(
                memory_manager=self.memory_manager,
                data_dir=data_dirs["convomem"]
            )
            self.results["convomem"] = convomem_runner.run_evaluation()
            convomem_report = convomem_runner.generate_report()
            convomem_runner.save_results()
        except FileNotFoundError as e:
            print(f"⚠️  ConvoMem data not found: {e}")
            self.results["convomem"] = {"error": str(e)}

        # Calculate overall scores
        self.results["overall"] = self.calculate_overall_scores()

        elapsed_time = time.time() - start_time

        # Print final summary
        self.print_final_summary(elapsed_time)

        return self.results

    def calculate_overall_scores(self) -> Dict:
        """Calculate overall scores across all benchmarks."""
        scores = {
            "longmemeval_accuracy": 0.0,
            "locomo_accuracy": 0.0,
            "convomem_accuracy": 0.0,
            "overall_score": 0.0
        }

        # LongMemEval accuracy
        if self.results["longmemeval"] and "summary" in self.results["longmemeval"]:
            scores["longmemeval_accuracy"] = self.results["longmemeval"]["summary"]["accuracy"]

        # LoCoMo accuracy
        if self.results["locomo"] and "overall" in self.results["locomo"]:
            scores["locomo_accuracy"] = self.results["locomo"]["overall"]["qa_accuracy"]

        # ConvoMem accuracy
        if self.results["convomem"] and "overall" in self.results["convomem"]:
            scores["convomem_accuracy"] = self.results["convomem"]["overall"]["accuracy"]

        # Calculate overall score (weighted average)
        # Weights: LongMemEval 40%, LoCoMo 35%, ConvoMem 25%
        scores["overall_score"] = (
            scores["longmemeval_accuracy"] * 0.40 +
            scores["locomo_accuracy"] * 0.35 +
            scores["convomem_accuracy"] * 0.25
        )

        return scores

    def print_final_summary(self, elapsed_time: float):
        """Print final summary of all benchmarks."""
        print(f"\n{'='*80}")
        print(f"FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Time: {elapsed_time:.2f} seconds")
        print(f"{'='*80}\n")

        # LongMemEval summary
        if self.results["longmemeval"] and "summary" in self.results["longmemeval"]:
            print("LongMemEval:")
            print(f"  Accuracy: {self.results['longmemeval']['summary']['accuracy']:.2%}")
            print(f"  Target: {self.results['longmemeval']['summary']['target_accuracy']:.2%}")
            print(f"  Status: {'✅ PASS' if self.results['longmemeval']['summary']['target_achieved'] else '❌ FAIL'}")
        else:
            print("LongMemEval: ⚠️  SKIPPED (no data)")

        # LoCoMo summary
        if self.results["locomo"] and "overall" in self.results["locomo"]:
            print("\nLoCoMo:")
            print(f"  QA Accuracy: {self.results['locomo']['overall']['qa_accuracy']:.2%}")
            print(f"  Event Summary F1: {self.results['locomo']['overall']['event_summary_f1']:.2%}")
            print(f"  Dialog Coherence: {self.results['locomo']['overall']['dialog_coherence']:.2%}")
            print(f"  Average Score: {self.results['locomo']['overall']['average_score']:.2%}")
        else:
            print("\nLoCoMo: ⚠️  SKIPPED (no data)")

        # ConvoMem summary
        if self.results["convomem"] and "overall" in self.results["convomem"]:
            print("\nConvoMem:")
            print(f"  Accuracy: {self.results['convomem']['overall']['accuracy']:.2%}")
            print(f"  Average Recall: {self.results['convomem']['overall']['avg_recall']:.2%}")
            print(f"  Average Precision: {self.results['convomem']['overall']['avg_precision']:.2%}")
            print(f"  Average F1: {self.results['convomem']['overall']['avg_f1']:.2%}")
        else:
            print("\nConvoMem: ⚠️  SKIPPED (no data)")

        # Overall score
        print(f"\n{'='*80}")
        print(f"OVERALL SCORE: {self.results['overall']['overall_score']:.2%}")
        print(f"{'='*80}")

        # Target achievement
        target_achieved = (
            self.results['overall']['longmemeval_accuracy'] >= 0.75 and
            self.results['overall']['locomo_accuracy'] >= 0.80 and
            self.results['overall']['convomem_accuracy'] >= 0.75
        )
        print(f"\nTarget Achievement: {'✅ ALL TARGETS MET' if target_achieved else '❌ SOME TARGETS NOT MET'}")
        print(f"{'='*80}\n")

    def save_comprehensive_report(self, output_dir: str = "reports"):
        """Save comprehensive report to file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"benchmark_report_{timestamp}.json"

        report = {
            "benchmark_suite": "claw-mem Performance Benchmarks",
            "timestamp": datetime.now().isoformat(),
            "workspace": self.workspace,
            "results": self.results,
            "targets": {
                "longmemeval_accuracy": 0.75,
                "locomo_accuracy": 0.80,
                "convomem_accuracy": 0.75,
                "overall_score": 0.75
            },
            "achievement": {
                "longmemeval": self.results['overall']['longmemeval_accuracy'] >= 0.75,
                "locomo": self.results['overall']['locomo_accuracy'] >= 0.80,
                "convomem": self.results['overall']['convomem_accuracy'] >= 0.75,
                "overall": self.results['overall']['overall_score'] >= 0.75
            }
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Comprehensive report saved to: {report_file}")

        return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run all claw-mem benchmarks")
    parser.add_argument("--workspace", default="workspace", help="Memory manager workspace")
    parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    parser.add_argument("--longmemeval-data", default="data/longmemeval", help="LongMemEval data directory")
    parser.add_argument("--locomo-data", default="data/locomo", help="LoCoMo data directory")
    parser.add_argument("--convomem-data", default="data/convomem", help="ConvoMem data directory")

    args = parser.parse_args()

    # Create data directories dictionary
    data_dirs = {
        "longmemeval": args.longmemeval_data,
        "locomo": args.locomo_data,
        "convomem": args.convomem_data
    }

    # Create orchestrator
    orchestrator = BenchmarkOrchestrator(workspace=args.workspace)

    # Run all benchmarks
    results = orchestrator.run_all_benchmarks(data_dirs=data_dirs)

    # Save comprehensive report
    report = orchestrator.save_comprehensive_report(output_dir=args.output_dir)

    return report


if __name__ == "__main__":
    main()
