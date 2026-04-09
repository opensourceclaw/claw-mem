#!/usr/bin/env python3
"""
Generate sample test data for benchmarks

This script generates sample test data for all three benchmarks.
For actual benchmarking, you should use the official datasets.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


def generate_longmemeval_data(output_dir: str = "data/longmemeval", num_questions: int = 100):
    """
    Generate sample LongMemEval test data.

    Args:
        output_dir: Output directory
        num_questions: Number of questions per category
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    categories = [
        "information_extraction",
        "cross_session_reasoning",
        "temporal_reasoning",
        "knowledge_updates",
        "abstention"
    ]

    test_data = []

    for category in categories:
        for i in range(num_questions):
            question_id = f"{category[:3]}_{i:03d}"

            if category == "information_extraction":
                item = random.choice(['color', 'food', 'movie', 'book', 'hobby'])
                question = f"What is the user's favorite {item}?"
                fact = f"The user's favorite {item} is {random.choice(['Python', 'Blue', 'Pizza', 'Star Wars', 'Reading'])}"
                ground_truth = fact.split(" is ")[-1]

            elif category == "cross_session_reasoning":
                topic = random.choice(['their job', 'their family', 'their hobbies', 'their goals', 'their plans'])
                answer = random.choice(['working as an engineer', 'having a dog', 'liking hiking', 'wanting to travel', 'planning to learn'])
                question = f"What did the user mention about {topic} in the previous sessions?"
                fact = f"User mentioned {answer} in a previous session"
                ground_truth = answer

            elif category == "temporal_reasoning":
                topic = random.choice(['vacation', 'project', 'birthday', 'meeting', 'deadline'])
                days = random.randint(1, 30)
                question = f"When did the user last talk about {topic}?"
                fact = f"User talked about {topic} {days} days ago"
                ground_truth = f"Last mentioned {days} days ago"

            elif category == "knowledge_updates":
                item = random.choice(['phone number', 'email', 'address', 'job title', 'relationship status'])
                answer = random.choice(["value A", "value B", "value C"])
                question = f"What is the user's current {item}?"
                fact = f"The user's current {item} is {answer}"
                ground_truth = answer

            else:  # abstention
                item = random.choice(['secret password', 'bank account', 'social security number', 'private key', 'confidential information'])
                question = f"What is the user's {item}?"
                fact = ""  # No fact should be stored for sensitive info
                ground_truth = "CANNOT_ANSWER"

            test_data.append({
                "id": question_id,
                "category": category,
                "question": question,
                "fact": fact,  # Add fact for pre-loading
                "ground_truth": ground_truth,
                "context": {
                    "session_id": f"session_{random.randint(1, 10)}",
                    "timestamp": datetime.now().isoformat()
                }
            })

    # Save test data
    test_file = output_path / "test_data.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)

    print(f"Generated {len(test_data)} LongMemEval test questions")
    print(f"Saved to: {test_file}")

    return test_data


def generate_locomo_data(output_dir: str = "data/locomo", num_conversations: int = 50):
    """
    Generate sample LoCoMo test data.

    Args:
        output_dir: Output directory
        num_conversations: Number of conversations
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    conversations = []
    qa_pairs = []

    for i in range(num_conversations):
        conv_id = f"conv_{i:03d}"

        # Generate conversation turns
        turns = []
        base_time = datetime.now() - timedelta(days=random.randint(1, 30))

        for j in range(random.randint(5, 20)):
            turn_id = f"{conv_id}_turn_{j:03d}"
            speaker = "user" if j % 2 == 0 else "assistant"

            if speaker == "user":
                content = f"I think {random.choice(['Python is great', 'I love hiking', 'My favorite color is blue', 'I work as an engineer', 'I have a dog named Max'])}"
            else:
                content = f"That's interesting! Tell me more about {random.choice(['Python', 'hiking', 'colors', 'engineering', 'pets'])}"

            turns.append({
                "id": turn_id,
                "speaker": speaker,
                "content": content,
                "timestamp": (base_time + timedelta(minutes=j*2)).isoformat()
            })

        conversations.append({
            "id": conv_id,
            "turns": turns,
            "metadata": {
                "user_id": f"user_{random.randint(1, 100)}",
                "session_count": random.randint(1, 10)
            }
        })

        # Generate QA pairs for this conversation
        qa_categories = ["single_hop", "multi_hop", "temporal_reasoning", "open_domain", "adversarial"]

        for category in qa_categories:
            qa_pairs.append({
                "conversation_id": conv_id,
                "category": category,
                "question": f"What did the user say about {random.choice(['Python', 'hiking', 'colors', 'engineering', 'pets'])}?",
                "answer": random.choice(["Python is great", "I love hiking", "My favorite color is blue", "I work as an engineer", "I have a dog named Max"])
            })

    # Save conversations
    conv_file = output_path / "conversations.json"
    with open(conv_file, 'w') as f:
        json.dump(conversations, f, indent=2)

    # Save QA pairs
    qa_file = output_path / "qa_pairs.json"
    with open(qa_file, 'w') as f:
        json.dump(qa_pairs, f, indent=2)

    print(f"Generated {len(conversations)} LoCoMo conversations")
    print(f"Generated {len(qa_pairs)} LoCoMo QA pairs")
    print(f"Saved to: {conv_file} and {qa_file}")

    return conversations, qa_pairs


def generate_convomem_data(output_dir: str = "data/convomem", num_test_cases: int = 1000):
    """
    Generate sample ConvoMem test data.

    Args:
        output_dir: Output directory
        num_test_cases: Number of test cases
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    scenarios = [
        "single_turn",
        "multi_turn",
        "temporal",
        "entity",
        "preference",
        "factual"
    ]

    test_data = []

    for i in range(num_test_cases):
        scenario = scenarios[i % len(scenarios)]
        test_id = f"{scenario[:4]}_{i:04d}"

        # Generate conversation
        conversation = []
        base_time = datetime.now() - timedelta(days=random.randint(1, 100))

        num_turns = random.randint(1, 10) if scenario in ["single_turn", "temporal", "factual"] else random.randint(5, 20)

        for j in range(num_turns):
            speaker = "user" if j % 2 == 0 else "assistant"

            if scenario == "entity":
                content = f"{random.choice(['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'])} is my {random.choice(['friend', 'colleague', 'neighbor', 'teacher', 'doctor'])}"
            elif scenario == "preference":
                content = f"I prefer {random.choice(['coffee over tea', 'cats over dogs', 'movies over books', 'summer over winter', 'morning over night'])}"
            else:
                content = f"This is turn {j} of conversation {i}"

            conversation.append({
                "id": f"{test_id}_turn_{j:03d}",
                "speaker": speaker,
                "content": content,
                "timestamp": (base_time + timedelta(minutes=j)).isoformat()
            })

        # Generate question and expected answer
        if scenario == "single_turn":
            question = "What did the user say in the first turn?"
            expected = conversation[0]["content"] if conversation else ""
        elif scenario == "multi_turn":
            question = "What topics did the user discuss?"
            expected = "Multiple topics discussed"
        elif scenario == "temporal":
            question = "When did this conversation happen?"
            expected = base_time.strftime("%Y-%m-%d")
        elif scenario == "entity":
            question = "Who is mentioned in this conversation?"
            expected = random.choice(["Alice", "Bob", "Charlie", "Diana", "Eve"])
        elif scenario == "preference":
            question = "What does the user prefer?"
            expected = random.choice(["coffee", "cats", "movies", "summer", "morning"])
        else:  # factual
            question = "What is a fact from this conversation?"
            expected = "Fact from conversation"

        test_data.append({
            "id": test_id,
            "scenario": scenario,
            "conversation": conversation,
            "question": question,
            "expected": expected,
            "context": {
                "entity": expected if scenario == "entity" else None
            }
        })

    # Save dataset
    dataset_file = output_path / "dataset.json"
    with open(dataset_file, 'w') as f:
        json.dump(test_data, f, indent=2)

    print(f"Generated {len(test_data)} ConvoMem test cases")
    print(f"Saved to: {dataset_file}")

    return test_data


def main():
    """Generate all sample test data."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate sample benchmark test data")
    parser.add_argument("--output-dir", default="data", help="Base output directory")
    parser.add_argument("--longmemeval-questions", type=int, default=100, help="Number of LongMemEval questions per category")
    parser.add_argument("--locomo-conversations", type=int, default=50, help="Number of LoCoMo conversations")
    parser.add_argument("--convomem-testcases", type=int, default=1000, help="Number of ConvoMem test cases")

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"Generating Sample Test Data")
    print(f"{'='*80}\n")

    # Generate LongMemEval data
    print("Generating LongMemEval test data...")
    longmemeval_data = generate_longmemeval_data(
        output_dir=f"{args.output_dir}/longmemeval",
        num_questions=args.longmemeval_questions
    )

    # Generate LoCoMo data
    print("\nGenerating LoCoMo test data...")
    locomo_data = generate_locomo_data(
        output_dir=f"{args.output_dir}/locomo",
        num_conversations=args.locomo_conversations
    )

    # Generate ConvoMem data
    print("\nGenerating ConvoMem test data...")
    convomem_data = generate_convomem_data(
        output_dir=f"{args.output_dir}/convomem",
        num_test_cases=args.convomem_testcases
    )

    print(f"\n{'='*80}")
    print(f"Test Data Generation Complete")
    print(f"{'='*80}")
    print(f"LongMemEval: {len(longmemeval_data)} questions")
    print(f"LoCoMo: {len(locomo_data[0])} conversations, {len(locomo_data[1])} QA pairs")
    print(f"ConvoMem: {len(convomem_data)} test cases")
    print(f"{'='*80}\n")

    print("⚠️  NOTE: This is sample data for testing purposes.")
    print("For actual benchmarking, use official datasets from:")
    print("  - LongMemEval: https://arxiv.org/abs/2410.10813")
    print("  - LoCoMo: https://github.com/snap-research/locomo")
    print("  - ConvoMem: https://github.com/SalesforceAIResearch/ConvoMem")


if __name__ == "__main__":
    main()
