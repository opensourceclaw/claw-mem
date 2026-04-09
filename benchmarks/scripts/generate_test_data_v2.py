#!/usr/bin/env python3
"""
Generate test data with unique IDs for precise matching

This script generates test data with unique IDs to enable precise matching
in benchmarks, validating that the memory system works correctly.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import uuid


def generate_longmemeval_data_v2(output_dir: str = "data/longmemeval", num_questions: int = 100):
    """
    Generate LongMemEval test data with unique IDs for precise matching.

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
    facts = []  # Separate facts for preloading

    for category in categories:
        for i in range(num_questions):
            test_id = f"test_{category[:3]}_{i:03d}"
            question_id = f"q_{category[:3]}_{i:03d}"

            # Generate fact and ground truth that match
            if category == "information_extraction":
                topics = [
                    ("favorite color", "Blue", "The user's favorite color is Blue"),
                    ("favorite food", "Pizza", "The user's favorite food is Pizza"),
                    ("favorite movie", "Star Wars", "The user's favorite movie is Star Wars"),
                    ("favorite book", "Dune", "The user's favorite book is Dune"),
                    ("favorite hobby", "Hiking", "The user's favorite hobby is Hiking")
                ]
                topic, answer, fact = random.choice(topics)
                question = f"What is the user's {topic}?"
                ground_truth = answer

            elif category == "cross_session_reasoning":
                topics = [
                    ("job", "engineer", "The user works as a software engineer"),
                    ("family", "dog", "The user has a dog named Max"),
                    ("hobby", "hiking", "The user enjoys hiking on weekends"),
                    ("goal", "travel", "The user wants to travel to Japan"),
                    ("plan", "learn", "The user plans to learn Python")
                ]
                topic, answer, fact = random.choice(topics)
                question = f"What did the user mention about their {topic}?"
                ground_truth = f"The user mentioned {fact.lower()}"

            elif category == "temporal_reasoning":
                days_ago = random.randint(1, 30)
                topics = [
                    ("vacation", f"The user went on vacation {days_ago} days ago"),
                    ("project", f"The user started a new project {days_ago} days ago"),
                    ("birthday", f"The user's birthday was {days_ago} days ago"),
                    ("meeting", f"The user had a meeting {days_ago} days ago"),
                    ("deadline", f"The user had a deadline {days_ago} days ago")
                ]
                topic, fact = random.choice(topics)
                question = f"When did the user last mention {topic}?"
                ground_truth = f"{days_ago} days ago"

            elif category == "knowledge_updates":
                topics = [
                    ("phone number", "555-1234", "The user's phone number is 555-1234"),
                    ("email", "user@example.com", "The user's email is user@example.com"),
                    ("address", "123 Main St", "The user's address is 123 Main St"),
                    ("job title", "Senior Engineer", "The user's job title is Senior Engineer"),
                    ("relationship", "Married", "The user's relationship status is Married")
                ]
                topic, answer, fact = random.choice(topics)
                question = f"What is the user's current {topic}?"
                ground_truth = answer

            else:  # abstention
                question = f"What is the user's {random.choice(['secret password', 'bank account', 'social security number'])}?"
                ground_truth = "CANNOT_ANSWER"
                fact = None  # No fact for abstention

            test_case = {
                "id": question_id,
                "test_id": test_id,
                "category": category,
                "question": question,
                "fact": fact,
                "ground_truth": ground_truth,
                "context": {
                    "session_id": f"session_{random.randint(1, 10)}",
                    "timestamp": datetime.now().isoformat()
                }
            }

            test_data.append(test_case)

            # Add fact to facts list (except for abstention)
            if fact:
                facts.append({
                    "test_id": test_id,
                    "content": fact,
                    "category": category,
                    "timestamp": datetime.now().isoformat()
                })

    # Save test data
    test_file = output_path / "test_data.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)

    # Save facts for preloading
    facts_file = output_path / "facts.json"
    with open(facts_file, 'w') as f:
        json.dump(facts, f, indent=2)

    print(f"Generated {len(test_data)} LongMemEval test questions")
    print(f"Generated {len(facts)} facts for preloading")
    print(f"Saved to: {test_file}")
    print(f"Facts saved to: {facts_file}")

    return test_data, facts


def generate_locomo_data_v2(output_dir: str = "data/locomo", num_conversations: int = 50):
    """
    Generate LoCoMo test data with unique IDs for precise matching.

    Args:
        output_dir: Output directory
        num_conversations: Number of conversations
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    conversations = []
    qa_pairs = []
    facts = []

    for i in range(num_conversations):
        conv_id = f"conv_{i:03d}"

        # Generate conversation turns with facts
        turns = []
        base_time = datetime.now() - timedelta(days=random.randint(1, 30))

        # Pre-defined facts for this conversation
        conv_facts = [
            ("Python is great for data science", "programming"),
            ("The user loves hiking", "hobby"),
            ("Blue is the favorite color", "preference"),
            ("Works as an engineer", "job"),
            ("Has a dog named Max", "pet")
        ]

        for j, (fact_content, fact_type) in enumerate(conv_facts):
            turn_id = f"{conv_id}_turn_{j:03d}"
            test_id = f"{conv_id}_fact_{j:03d}"

            turns.append({
                "id": turn_id,
                "test_id": test_id,
                "speaker": "user",
                "content": fact_content,
                "timestamp": (base_time + timedelta(minutes=j*2)).isoformat()
            })

            facts.append({
                "test_id": test_id,
                "content": fact_content,
                "type": fact_type,
                "conversation_id": conv_id,
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

        # Generate QA pairs with precise matching
        qa_categories = ["single_hop", "multi_hop", "temporal", "open_domain", "adversarial"]

        for j, (fact_content, fact_type) in enumerate(conv_facts):
            test_id = f"{conv_id}_fact_{j:03d}"
            category = qa_categories[j % len(qa_categories)]

            qa_pairs.append({
                "test_id": test_id,
                "conversation_id": conv_id,
                "category": category,
                "question": f"What does the user think about {fact_type}?",
                "answer": fact_content,
                "fact": fact_content
            })

    # Save conversations
    conv_file = output_path / "conversations.json"
    with open(conv_file, 'w') as f:
        json.dump(conversations, f, indent=2)

    # Save QA pairs
    qa_file = output_path / "qa_pairs.json"
    with open(qa_file, 'w') as f:
        json.dump(qa_pairs, f, indent=2)

    # Save facts for preloading
    facts_file = output_path / "facts.json"
    with open(facts_file, 'w') as f:
        json.dump(facts, f, indent=2)

    print(f"Generated {len(conversations)} LoCoMo conversations")
    print(f"Generated {len(qa_pairs)} LoCoMo QA pairs")
    print(f"Generated {len(facts)} facts for preloading")
    print(f"Saved to: {conv_file}, {qa_file}, {facts_file}")

    return conversations, qa_pairs, facts


def generate_convomem_data_v2(output_dir: str = "data/convomem", num_test_cases: int = 1000):
    """
    Generate ConvoMem test data with unique IDs for precise matching.

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
    facts = []

    for i in range(num_test_cases):
        scenario = scenarios[i % len(scenarios)]
        test_id = f"test_{scenario[:4]}_{i:04d}"

        # Generate fact and ground truth that match
        if scenario == "single_turn":
            fact = "The user loves Python programming"
            question = "What programming language does the user love?"
            ground_truth = "Python"

        elif scenario == "multi_turn":
            fact = "The user discussed their job as an engineer and their hobby of hiking"
            question = "What topics did the user discuss?"
            ground_truth = "job and hobby"

        elif scenario == "temporal":
            days_ago = random.randint(1, 30)
            fact = f"The user mentioned their vacation {days_ago} days ago"
            question = "When did the user mention their vacation?"
            ground_truth = f"{days_ago} days ago"

        elif scenario == "entity":
            entity = random.choice(["Alice", "Bob", "Charlie", "Diana", "Eve"])
            relation = random.choice(["friend", "colleague", "neighbor", "teacher", "doctor"])
            fact = f"{entity} is the user's {relation}"
            question = f"Who is mentioned in this conversation?"
            ground_truth = entity

        elif scenario == "preference":
            preference = random.choice(["coffee over tea", "cats over dogs", "movies over books", "summer over winter", "morning over night"])
            fact = f"The user prefers {preference}"
            question = f"What does the user prefer?"
            ground_truth = preference.split(" over ")[0]

        else:  # factual
            fact = "The user's birthday is on March 15th"
            question = "When is the user's birthday?"
            ground_truth = "March 15th"

        # Generate conversation
        conversation = []
        base_time = datetime.now() - timedelta(days=random.randint(1, 100))

        turn_id = f"{test_id}_turn_000"
        conversation.append({
            "id": turn_id,
            "test_id": test_id,
            "speaker": "user",
            "content": fact,
            "timestamp": base_time.isoformat()
        })

        test_data.append({
            "id": test_id,
            "test_id": test_id,
            "scenario": scenario,
            "conversation": conversation,
            "question": question,
            "fact": fact,
            "expected": ground_truth,
            "context": {}
        })

        facts.append({
            "test_id": test_id,
            "content": fact,
            "scenario": scenario,
            "timestamp": base_time.isoformat()
        })

    # Save dataset
    dataset_file = output_path / "dataset.json"
    with open(dataset_file, 'w') as f:
        json.dump(test_data, f, indent=2)

    # Save facts for preloading
    facts_file = output_path / "facts.json"
    with open(facts_file, 'w') as f:
        json.dump(facts, f, indent=2)

    print(f"Generated {len(test_data)} ConvoMem test cases")
    print(f"Generated {len(facts)} facts for preloading")
    print(f"Saved to: {dataset_file}")
    print(f"Facts saved to: {facts_file}")

    return test_data, facts


def main():
    """Generate all test data with unique IDs for precise matching."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate test data with unique IDs")
    parser.add_argument("--output-dir", default="data", help="Base output directory")

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"Generating Test Data with Unique IDs (v2)")
    print(f"{'='*80}\n")

    # Generate all test data
    longmemeval_data, longmemeval_facts = generate_longmemeval_data_v2(
        output_dir=f"{args.output_dir}/longmemeval",
        num_questions=100
    )

    locomo_data, locomo_qa, locomo_facts = generate_locomo_data_v2(
        output_dir=f"{args.output_dir}/locomo",
        num_conversations=50
    )

    convomem_data, convomem_facts = generate_convomem_data_v2(
        output_dir=f"{args.output_dir}/convomem",
        num_test_cases=1000
    )

    print(f"\n{'='*80}")
    print(f"Test Data Generation Complete (v2)")
    print(f"{'='*80}")
    print(f"LongMemEval: {len(longmemeval_data)} questions, {len(longmemeval_facts)} facts")
    print(f"LoCoMo: {len(locomo_data)} conversations, {len(locomo_qa)} QA pairs, {len(locomo_facts)} facts")
    print(f"ConvoMem: {len(convomem_data)} test cases, {len(convomem_facts)} facts")
    print(f"{'='*80}\n")

    print("✅ Test data generated with unique IDs for precise matching")
    print("✅ Each test case has a test_id that matches stored facts")
    print("✅ Use facts.json files to preload memories before testing")


if __name__ == "__main__":
    main()
