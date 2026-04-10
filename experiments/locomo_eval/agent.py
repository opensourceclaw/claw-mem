"""
NeoClaw Agent with Claw-Mem Integration

Evaluates claw-mem's memory capabilities using LoCoMo benchmark.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

# Add claw-mem src to path
# This file is at: experiments/locomo_eval/agent.py
# Need to go up 2 levels to get to claw-mem root, then into src
CLAW_MEM_ROOT = Path(__file__).parent.parent.parent  # experiments -> claw-mem
CLAW_MEM_SRC = CLAW_MEM_ROOT / "src"
sys.path.insert(0, str(CLAW_MEM_SRC))

# Add current directory for local imports
sys.path.insert(0, str(Path(__file__).parent))

from claw_mem.memory_manager import MemoryManager


@dataclass
class AgentConfig:
    """Configuration for NeoClaw Agent"""
    # Memory settings
    memory_storage_path: str = None
    max_memories: int = 10000

    # Retrieval settings
    retrieval_limit: int = 10
    retrieval_memory_type: str = "episodic"  # or None for all

    # Context settings
    max_context_length: int = 4000

    # LLM settings (to be configured by user)
    llm_provider: str = "openai"  # openai, anthropic, local
    llm_model: str = "gpt-4"
    llm_api_key: str = None


@dataclass
class RetrievalResult:
    """Result from memory retrieval"""
    memories: List[Dict[str, Any]]
    context: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class NeoClawAgent:
    """
    NeoClaw Agent with claw-mem integration for memory evaluation.

    This agent uses claw-mem for memory storage and retrieval,
    then delegates answer generation to an LLM.
    """

    def __init__(self, config: AgentConfig = None):
        """
        Initialize NeoClaw Agent

        Args:
            config: Agent configuration
        """
        self.config = config or AgentConfig()

        # Initialize memory manager
        storage_path = self.config.memory_storage_path
        if storage_path is None:
            # Use temporary path for evaluation - use unique name to avoid conflicts
            import tempfile
            import time
            storage_path = tempfile.mkdtemp(prefix=f"locomo_eval_{int(time.time())}_")

        print(f"Initializing claw-mem at: {storage_path}")

        self.memory_manager = MemoryManager(
            workspace=storage_path,
            auto_detect=False
        )

        # DON'T call start_session - it will load old index from disk
        # Instead, manually initialize session state
        self.memory_manager.session_id = "locomo_eval"
        from datetime import datetime
        self.memory_manager.session_start = datetime.now()
        self.memory_manager.working_memory = []
        self.memory_manager.working_cache.clear()

        # Clear existing index to avoid loading from global ~/.claw-mem/index
        print("  Setting up fresh index...")
        self.memory_manager.index.built = False
        self.memory_manager.index.memory_ids = set()
        self.memory_manager.index.ngram_index = {}
        if hasattr(self.memory_manager.index, 'bm25_index'):
            self.memory_manager.index.bm25_index = None

        # LLM function (to be set)
        self.llm_generate: Optional[Callable] = None

        print(f"✅ NeoClaw Agent initialized")

    def set_llm(self, generate_fn: Callable):
        """
        Set LLM generation function

        Args:
            generate_fn: Function that takes (prompt, system_prompt) and returns response
        """
        self.llm_generate = generate_fn

    def store_conversation(self, messages: List[Dict[str, Any]], sample_id: str = None) -> int:
        """
        Store conversation messages to claw-mem

        Args:
            messages: List of message dicts with 'content', 'speaker', 'session_id', etc.
            sample_id: Sample ID for metadata

        Returns:
            Number of messages stored
        """
        stored_count = 0
        session_id = sample_id or "eval_session"

        for msg in messages:
            content = msg.get('content', '')
            if not content:
                continue

            # Build metadata
            metadata = {
                'sample_id': sample_id,
                'speaker': msg.get('speaker'),
                'session_id': msg.get('session_id'),
                'role': msg.get('role'),
            }

            # Store as episodic memory (rebuild index after all stores)
            success = self.memory_manager.store(
                content=content,
                memory_type="episodic",
                tags=[msg.get('speaker', 'unknown'), msg.get('session_id', 'unknown')],
                metadata=metadata,
                update_index=True  # Enable incremental index update
            )

            if success:
                stored_count += 1

        print(f"✅ Stored {stored_count} messages to claw-mem")

        # Force build the index with our new memories
        # This ensures the index contains our data, not old data from disk
        print("  Building search index...")
        self.memory_manager.index.build(
            self.memory_manager.working_memory,
            save_index=False  # Don't save to avoid polluting global index
        )
        print(f"  ✅ Index built with {len(self.memory_manager.working_memory)} memories")

        return stored_count

    def retrieve(self, query: str, limit: int = None) -> RetrievalResult:
        """
        Retrieve relevant memories for a query

        Args:
            query: Search query
            limit: Max number of results (default from config)

        Returns:
            RetrievalResult with memories and assembled context
        """
        if limit is None:
            limit = self.config.retrieval_limit

        print(f"  🔍 Searching with query: {query[:50]}...")
        print(f"     memory_type: {self.config.retrieval_memory_type}, limit: {limit}")

        # Search memories
        memories = self.memory_manager.search(
            query=query,
            memory_type=self.config.retrieval_memory_type,
            limit=limit
        )

        print(f"     Found {len(memories)} memories")

        # Assemble context from retrieved memories
        context = self._assemble_context(memories)

        return RetrievalResult(
            memories=memories,
            context=context,
            metadata={
                'query': query,
                'retrieved_count': len(memories)
            }
        )

    def _assemble_context(self, memories: List[Dict[str, Any]]) -> str:
        """
        Assemble retrieved memories into context string

        Args:
            memories: List of memory records

        Returns:
            Formatted context string
        """
        if not memories:
            return "No relevant memories found."

        lines = ["=== Relevant Memories ==="]
        for i, mem in enumerate(memories):
            speaker = mem.get('metadata', {}).get('speaker', 'Unknown')
            session = mem.get('metadata', {}).get('session_id', '')
            content = mem.get('content', '')

            lines.append(f"\n[Memory {i+1}] ({speaker}, {session})")
            lines.append(content)

        return '\n'.join(lines)

    def answer_question(
        self,
        question: str,
        use_memory: bool = True,
        context_override: str = None
    ) -> Dict[str, Any]:
        """
        Answer a question using memory-augmented generation

        Args:
            question: The question to answer
            use_memory: Whether to use claw-mem retrieval
            context_override: If provided, use this context instead of retrieval

        Returns:
            Dict with answer, context_used, and metadata
        """
        if self.llm_generate is None:
            raise ValueError("LLM not set. Call set_llm() first.")

        # Get context
        if context_override is not None:
            context = context_override
            retrieval_metadata = {'method': 'override'}
        elif use_memory:
            result = self.retrieve(question)
            context = result.context
            retrieval_metadata = result.metadata
        else:
            context = "No context provided."
            retrieval_metadata = {'method': 'none'}

        # Build prompt
        system_prompt = """You are a helpful AI assistant with long-term memory.
Your task is to answer questions based on the provided context (retrieved memories).
If the context doesn't contain enough information to answer the question, say so."""

        user_prompt = f"""Context (retrieved memories):
{context}

Question: {question}

Please provide a helpful answer based on the context above."""

        # Generate answer
        try:
            answer = self.llm_generate(user_prompt, system_prompt)
        except Exception as e:
            answer = f"Error generating answer: {e}"

        return {
            'question': question,
            'answer': answer,
            'context_used': context,
            'retrieval_method': retrieval_metadata.get('method', 'unknown'),
            'retrieved_count': retrieval_metadata.get('retrieved_count', 0),
            'error': None if 'Error' not in answer else answer
        }

    def clear_memory(self):
        """Clear all stored memories"""
        # Reset session without loading old index
        self.memory_manager.session_id = "locomo_eval_clear"
        from datetime import datetime
        self.memory_manager.session_start = datetime.now()
        self.memory_manager.working_memory = []
        self.memory_manager.working_cache.clear()

        # Clear the index to avoid old data
        self.memory_manager.index.built = False
        self.memory_manager.index.memory_ids = set()
        self.memory_manager.index.ngram_index = {}
        if hasattr(self.memory_manager.index, 'bm25_index'):
            self.memory_manager.index.bm25_index = None

        print("🗑️  Memory cleared (fresh index)")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            'total_memories': len(self.memory_manager.working_memory),
            'index_built': self.memory_manager.index.built,
            'session_id': self.memory_manager.session_id
        }


class ComparisonAgent:
    """
    Agent that runs comparison between different memory strategies.

    Compares:
    - Full context (oracle)
    - claw-mem retrieval
    - No memory
    - RAG with observations
    - RAG with session summaries
    """

    def __init__(self, config: AgentConfig = None):
        self.agent = NeoClawAgent(config)
        self.config = config or AgentConfig()

    def set_llm(self, generate_fn: Callable):
        self.agent.set_llm(generate_fn)

    def run_comparison(
        self,
        sample,
        data_loader,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Run comparison for a single sample

        Args:
            sample: LocomoSample
            data_loader: LocomoDataLoader instance
            verbose: Print detailed results

        Returns:
            Dict with comparison results for each strategy
        """
        results = {}

        # Store conversation once
        self.agent.store_conversation(sample.messages, sample.sample_id)

        # Get QA pairs
        qa_pairs = sample.qa_pairs

        # For each strategy, answer all QA pairs
        strategies = ['full_context', 'claw_mem', 'no_memory', 'rag_observations', 'rag_summaries']

        for strategy in strategies:
            if verbose:
                print(f"\n=== Testing strategy: {strategy} ===")

            answers = []
            for i, qa in enumerate(qa_pairs):
                question = qa['question']
                expected_answer = qa['answer']

                # Get context based on strategy
                if strategy == 'full_context':
                    context = data_loader.get_conversation_text(sample)
                    context = f"Full conversation:\n{context}"
                elif strategy == 'claw_mem':
                    # Use claw-mem retrieval
                    context = None  # Will use retrieval
                elif strategy == 'no_memory':
                    context = ""
                elif strategy == 'rag_observations':
                    context = data_loader.get_observations_text(sample)
                    context = f"Observations:\n{context}"
                elif strategy == 'rag_summaries':
                    context = data_loader.get_session_summaries_text(sample)
                    context = f"Session summaries:\n{context}"

                # Get answer
                if strategy == 'claw_mem':
                    result = self.agent.answer_question(
                        question,
                        use_memory=True,
                        context_override=None
                    )
                else:
                    result = self.agent.answer_question(
                        question,
                        use_memory=False,
                        context_override=context if context else ""
                    )

                answers.append({
                    'question': question,
                    'expected': expected_answer,
                    'generated': result['answer'],
                    'retrieved_count': result.get('retrieved_count', 0)
                })

                if verbose and (i + 1) % 10 == 0:
                    print(f"  Processed {i+1}/{len(qa_pairs)} questions")

            results[strategy] = {
                'answers': answers,
                'total_questions': len(answers)
            }

            if verbose:
                print(f"  Completed {len(answers)} questions for {strategy}")

        return results


# Example LLM providers (to be extended)
class LLMProviders:
    """Collection of LLM provider functions"""

    @staticmethod
    def openai(prompt: str, system_prompt: str = "", model: str = "gpt-4", api_key: str = None) -> str:
        """OpenAI API"""
        try:
            import openai
            if api_key:
                openai.api_key = api_key

            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def anthropic(prompt: str, system_prompt: str = "", model: str = "claude-3-opus-20240229", api_key: str = None) -> str:
        """Anthropic API"""
        try:
            import anthropic
            if api_key:
                client = anthropic.Anthropic(api_key=api_key)
            else:
                client = anthropic.Anthropic()

            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def mock(prompt: str, system_prompt: str = "") -> str:
        """Mock LLM for testing (echoes prompt)"""
        return f"[Mock Response] Question: {prompt[:100]}... (LLM not configured)"


# Example usage
if __name__ == '__main__':
    from data_loader import LocomoDataLoader

    # Load data
    loader = LocomoDataLoader()
    samples = loader.load()

    # Initialize agent
    config = AgentConfig(
        retrieval_limit=5,
        memory_storage_path="/tmp/locomo_test"
    )
    agent = NeoClawAgent(config)

    # Use mock LLM
    agent.set_llm(LLMProviders.mock)

    # Store first sample
    sample = samples[0]
    agent.store_conversation(sample.messages, sample.sample_id)

    # Get stats
    print("\nMemory stats:", agent.get_memory_stats())

    # Test retrieval
    if sample.qa_pairs:
        question = sample.qa_pairs[0]['question']
        print(f"\nQuestion: {question}")

        result = agent.answer_question(question, use_memory=True)
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Retrieved: {result['retrieved_count']} memories")
