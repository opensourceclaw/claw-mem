"""
Locomo Evaluation Script

Runs comprehensive evaluation of claw-mem using LoCoMo benchmark.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

# Add paths
CLAW_MEM_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(CLAW_MEM_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import LocomoDataLoader
from agent import NeoClawAgent, AgentConfig, LLMProviders, ComparisonAgent


def load_llm_provider(provider: str, model: str, api_key: str = None):
    """Load LLM provider function"""
    if provider == "openai":
        return lambda prompt, system: LLMProviders.openai(prompt, system, model, api_key)
    elif provider == "anthropic":
        return lambda prompt, system: LLMProviders.anthropic(prompt, system, model, api_key)
    elif provider == "mock":
        return LLMProviders.mock
    else:
        raise ValueError(f"Unknown provider: {provider}")


def run_evaluation(
    samples,
    data_loader,
    agent: NeoClawAgent,
    sample_indices: List[int] = None,
    max_questions: int = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run evaluation on selected samples

    Args:
        samples: List of LocomoSample
        data_loader: LocomoDataLoader
        agent: NeoClawAgent instance
        sample_indices: Which samples to evaluate (None = all)
        max_questions: Max questions per sample (None = all)
        verbose: Print detailed output

    Returns:
        Evaluation results dict
    """
    if sample_indices is None:
        sample_indices = list(range(len(samples)))

    results = {
        'timestamp': datetime.now().isoformat(),
        'total_samples': len(sample_indices),
        'max_questions_per_sample': max_questions,
        'samples': []
    }

    for idx in sample_indices:
        sample = samples[idx]
        sample_id = sample.sample_id

        print(f"\n{'='*60}")
        print(f"Evaluating sample {idx+1}/{len(sample_indices)}: {sample_id}")
        print(f"{'='*60}")

        # Clear memory for fresh start
        agent.clear_memory()

        # Store conversation
        agent.store_conversation(sample.messages, sample_id)

        # Get QA pairs
        qa_pairs = sample.qa_pairs
        if max_questions:
            qa_pairs = qa_pairs[:max_questions]

        print(f"Total QA pairs: {len(qa_pairs)}")

        # Test different strategies
        strategies = {
            'full_context': lambda q: agent.answer_question(
                q['question'], use_memory=False,
                context_override=data_loader.get_conversation_text(sample)
            ),
            'claw_mem': lambda q: agent.answer_question(
                q['question'], use_memory=True
            ),
            'no_memory': lambda q: agent.answer_question(
                q['question'], use_memory=False,
                context_override=""
            ),
            'rag_observations': lambda q: agent.answer_question(
                q['question'], use_memory=False,
                context_override=data_loader.get_observations_text(sample)
            ),
            'rag_summaries': lambda q: agent.answer_question(
                q['question'], use_memory=False,
                context_override=data_loader.get_session_summaries_text(sample)
            ),
        }

        sample_results = {
            'sample_id': sample_id,
            'total_questions': len(qa_pairs),
            'strategies': {}
        }

        for strategy_name, answer_fn in strategies.items():
            print(f"\n  Strategy: {strategy_name}")
            answers = []

            for i, qa in enumerate(qa_pairs):
                try:
                    result = answer_fn(qa)
                    answers.append({
                        'question': qa['question'],
                        'expected': str(qa['answer']),
                        'generated': result['answer'],
                        'retrieved_count': result.get('retrieved_count', 0)
                    })
                except Exception as e:
                    answers.append({
                        'question': qa['question'],
                        'expected': str(qa['answer']),
                        'generated': f"Error: {e}",
                        'retrieved_count': 0
                    })

                if verbose and (i + 1) % 20 == 0:
                    print(f"    Progress: {i+1}/{len(qa_pairs)}")

            sample_results['strategies'][strategy_name] = {
                'answers': answers,
                'count': len(answers)
            }

            print(f"    Completed {len(answers)} questions")

        results['samples'].append(sample_results)

    return results


def evaluate_with_judge(
    results: Dict[str, Any],
    judge_llm_fn: Callable,
    sample_limit: int = 10
) -> Dict[str, Any]:
    """
    Evaluate generated answers using LLM-as-judge

    Args:
        results: Results from run_evaluation
        judge_llm_fn: LLM function for judging
        sample_limit: How many questions to judge per strategy

    Returns:
        Updated results with judge scores
    """
    judge_prompt = """You are an expert evaluator. Compare the generated answer to the expected answer.
Rate the response on a scale of 0-1:
- 1.0: Perfect match or equivalent meaning
- 0.7: Partially correct, minor details off
- 0.5: Partially correct, missing key information
- 0.3: Mostly incorrect but some relevance
- 0.0: Completely incorrect or no answer

Provide your rating and a brief justification."""

    # This is a placeholder - actual judge evaluation would be implemented here
    # For now, we'll mark results as "pending_judge"
    results['judge_evaluation'] = 'pending_implementation'

    return results


def save_results(results: Dict[str, Any], output_path: str):
    """Save results to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Results saved to: {output_path}")


def print_summary(results: Dict[str, Any]):
    """Print evaluation summary"""
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)

    total_questions = 0
    for sample in results['samples']:
        for strategy, data in sample['strategies'].items():
            count = data['count']
            total_questions += count
            print(f"  {sample['sample_id']} - {strategy}: {count} questions")

    print(f"\nTotal: {total_questions} question-strategy pairs evaluated")

    # Print sample results
    print("\n--- Sample Results ---")
    for sample in results['samples'][:2]:  # First 2 samples
        print(f"\n{sample['sample_id']}:")
        for strategy, data in sample['strategies'].items():
            print(f"  {strategy}: {data['count']} answers")


def main():
    parser = argparse.ArgumentParser(description="Locomo Evaluation for Claw-Mem")

    # Data options
    parser.add_argument('--data-path', type=str, default=None,
                        help='Path to locomo10.json')
    parser.add_argument('--sample-indices', type=str, default=None,
                        help='Comma-separated sample indices (e.g., "0,1,2")')
    parser.add_argument('--max-questions', type=int, default=20,
                        help='Max questions per sample')

    # LLM options
    parser.add_argument('--llm-provider', type=str, default='mock',
                        choices=['openai', 'anthropic', 'mock'],
                        help='LLM provider')
    parser.add_argument('--llm-model', type=str, default='gpt-4',
                        help='LLM model name')
    parser.add_argument('--api-key', type=str, default=None,
                        help='API key (or set OPENAI_API_KEY / ANTHROPIC_API_KEY)')

    # Agent options
    parser.add_argument('--retrieval-limit', type=int, default=10,
                        help='Max memories to retrieve')
    parser.add_argument('--storage-path', type=str, default=None,
                        help='Memory storage path')

    # Output options
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path')
    parser.add_argument('--verbose', action='store_true',
                        help='Print detailed output')

    args = parser.parse_args()

    # Load data
    print("Loading LoCoMo dataset...")
    loader = LocomoDataLoader(args.data_path)
    samples = loader.load()
    print(f"Loaded {len(samples)} samples")

    # Select samples
    if args.sample_indices:
        sample_indices = [int(x) for x in args.sample_indices.split(',')]
    else:
        sample_indices = list(range(len(samples)))

    print(f"Evaluating samples: {sample_indices}")

    # Initialize agent
    config = AgentConfig(
        retrieval_limit=args.retrieval_limit,
        memory_storage_path=args.storage_path
    )
    agent = NeoClawAgent(config)

    # Set LLM
    llm_fn = load_llm_provider(args.llm_provider, args.llm_model, args.api_key)
    agent.set_llm(llm_fn)

    # Run evaluation
    print("\nStarting evaluation...")
    results = run_evaluation(
        samples=samples,
        data_loader=loader,
        agent=agent,
        sample_indices=sample_indices,
        max_questions=args.max_questions,
        verbose=args.verbose
    )

    # Print summary
    print_summary(results)

    # Save results
    if args.output:
        save_results(results, args.output)
    else:
        # Default output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = f"locomo_eval_results_{timestamp}.json"
        save_results(results, default_output)

    print("\n✅ Evaluation complete!")


if __name__ == '__main__':
    main()
