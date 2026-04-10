"""
Locomo Data Loader

Loads and transforms LoCoMo dataset for claw-mem evaluation.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class LocomoSample:
    """Single LoCoMo sample transformed for claw-mem"""
    sample_id: str
    # Flattened conversations
    messages: List[Dict[str, Any]]  # List of {role, content, session_id, speaker}
    # QA pairs
    qa_pairs: List[Dict[str, Any]]  # List of {question, answer, evidence, category}
    # Metadata
    event_summary: Dict[str, Any]
    observations: Dict[str, Any]  # session_id -> observation
    session_summaries: Dict[str, str]  # session_id -> summary


@dataclass
class MemoryItem:
    """Claw-mem compatible memory item"""
    content: str
    memory_type: str  # "episodic", "semantic", "procedural"
    session_id: Optional[str] = None
    speaker: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LocomoDataLoader:
    """Load and transform LoCoMo dataset"""

    def __init__(self, data_path: str = None):
        """
        Initialize data loader

        Args:
            data_path: Path to locomo10.json. If None, uses default path.
        """
        if data_path is None:
            # Default path relative to this file
            base_dir = Path(__file__).parent
            data_path = base_dir / "locomo10.json"

        self.data_path = Path(data_path)
        self.samples: List[LocomoSample] = []

    def load(self) -> List[LocomoSample]:
        """Load and parse LoCoMo dataset"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.data_path}")

        with open(self.data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        self.samples = [self._transform_sample(item) for item in raw_data]
        return self.samples

    def _transform_sample(self, raw: Dict[str, Any]) -> LocomoSample:
        """Transform raw sample to LocomoSample"""
        sample_id = raw.get('sample_id', '')

        # Extract conversations as flat message list
        messages = self._extract_messages(raw.get('conversation', {}))

        # QA pairs
        qa_pairs = raw.get('qa', [])

        # Event summary
        event_summary = raw.get('event_summary', {})

        # Observations (for RAG baseline)
        observations = raw.get('observation', {})

        # Session summaries (for RAG baseline)
        session_summaries = raw.get('session_summary', {})

        return LocomoSample(
            sample_id=sample_id,
            messages=messages,
            qa_pairs=qa_pairs,
            event_summary=event_summary,
            observations=observations,
            session_summaries=session_summaries
        )

    def _extract_messages(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract messages from conversation dict, flattening sessions"""
        messages = []
        speaker_a = conversation.get('speaker_a', 'Speaker A')
        speaker_b = conversation.get('speaker_b', 'Speaker B')

        # Find all session keys (session_1, session_2, etc.)
        session_keys = sorted(
            [k for k in conversation.keys() if k.startswith('session_') and not k.endswith('_date_time')],
            key=lambda x: int(x.split('_')[1])
        )

        for session_key in session_keys:
            session_data = conversation.get(session_key, [])
            session_date = conversation.get(f'{session_key}_date_time', '')

            # Each session is a list of messages
            for msg in session_data:
                role = msg.get('speaker', 'unknown')
                content = msg.get('text', '')

                # Determine speaker name
                if role == 'A':
                    speaker = speaker_a
                elif role == 'B':
                    speaker = speaker_b
                else:
                    speaker = role

                messages.append({
                    'role': 'user' if role == 'A' else 'assistant',
                    'content': content,
                    'session_id': session_key,
                    'speaker': speaker,
                    'timestamp': session_date,
                    'speaker_role': role
                })

        return messages

    def to_memory_items(self, sample: LocomoSample) -> List[MemoryItem]:
        """
        Convert sample to claw-mem compatible memory items

        Args:
            sample: LocomoSample to convert

        Returns:
            List of MemoryItem objects
        """
        memories = []

        # Convert each message to episodic memory
        for msg in sample.messages:
            memory = MemoryItem(
                content=msg['content'],
                memory_type='episodic',
                session_id=msg.get('session_id'),
                speaker=msg.get('speaker'),
                timestamp=msg.get('timestamp'),
                metadata={
                    'sample_id': sample.sample_id,
                    'role': msg.get('role'),
                    'speaker_role': msg.get('speaker_role')
                }
            )
            memories.append(memory)

        return memories

    def get_qa_pairs(self, sample: LocomoSample) -> List[Dict[str, Any]]:
        """Get QA pairs for evaluation"""
        return sample.qa_pairs

    def get_conversation_text(self, sample: LocomoSample, max_sessions: int = None) -> str:
        """
        Get full conversation as text (for baseline comparison)

        Args:
            sample: LocomoSample
            max_sessions: If set, only include first N sessions

        Returns:
            Formatted conversation string
        """
        messages = sample.messages
        if max_sessions:
            session_ids = set()
            included = []
            for msg in messages:
                if msg.get('session_id') not in session_ids and len(session_ids) < max_sessions:
                    session_ids.add(msg.get('session_id'))
                    included.append(msg)
            messages = included

        lines = []
        for msg in messages:
            speaker = msg.get('speaker', 'Speaker')
            lines.append(f"{speaker}: {msg['content']}")

        return '\n'.join(lines)

    def get_observations_text(self, sample: LocomoSample) -> str:
        """Get all observations as text (for RAG baseline)"""
        parts = []
        for key, value in sorted(sample.observations.items()):
            if isinstance(value, dict):
                for speaker, observations in value.items():
                    if isinstance(observations, list):
                        for obs in observations:
                            if isinstance(obs, list) and len(obs) > 0:
                                parts.append(obs[0])
            elif isinstance(value, str):
                parts.append(value)
        return '\n'.join(parts)

    def get_session_summaries_text(self, sample: LocomoSample) -> str:
        """Get all session summaries as text (for RAG baseline)"""
        parts = []
        for key, value in sorted(sample.session_summaries.items()):
            if isinstance(value, str):
                parts.append(value)
        return '\n'.join(parts)


# Example usage
if __name__ == '__main__':
    loader = LocomoDataLoader()
    samples = loader.load()

    print(f"Loaded {len(samples)} samples")
    print()

    sample = samples[0]
    print(f"Sample ID: {sample.sample_id}")
    print(f"Messages: {len(sample.messages)}")
    print(f"QA pairs: {len(sample.qa_pairs)}")
    print()

    # Show first message
    if sample.messages:
        print("First message:")
        msg = sample.messages[0]
        print(f"  Speaker: {msg['speaker']}")
        print(f"  Session: {msg.get('session_id')}")
        print(f"  Content: {msg['content'][:100]}...")

    print()

    # Show first QA
    if sample.qa_pairs:
        print("First QA:")
        qa = sample.qa_pairs[0]
        print(f"  Question: {qa['question']}")
        print(f"  Answer: {qa['answer']}")
