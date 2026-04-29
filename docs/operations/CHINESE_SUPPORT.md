# Chinese Language Support

**Version**: 0.6.0+  
**Feature**: Hybrid Chinese/English Tokenization

---

## Overview

claw-mem v0.6.0+ supports hybrid Chinese/English tokenization for optimal search performance in both languages.

---

## Tokenization Strategy

### English Text
- Word-based tokenization
- Stopword removal (the, a, an, is, are, etc.)
- Lowercase normalization

### Chinese Text
- **With Jieba**: Word-based tokenization (recommended)
- **Without Jieba**: Character-level tokenization (fallback)
- Stopword removal (的,了,是,在,etc.)

---

## Installation

### Basic Installation (English only)
```bash
pip install claw-mem
```

### With Chinese Support (Recommended)
```bash
pip install claw-mem[chinese]
# or
pip install claw-mem jieba
```

---

## Usage

### Automatic Language Detection

claw-mem automatically detects the language and applies the appropriate tokenization:

```python
from claw_mem import MemoryManager

mm = MemoryManager(workspace="~/.openclaw/workspace")
mm.start_session("session_001")

# Store Chinese memory
mm.store("用户偏好使用中文交流", memory_type="semantic", tags=["preference"])

# Store English memory
mm.store("User prefers DD/MM/YYYY date format", memory_type="semantic")

# Search works in both languages
results_cn = mm.search("中文")      # ✅ Finds Chinese memories
results_en = mm.search("date")      # ✅ Finds English memories
results_mix = mm.search("OpenClaw 助理")  # ✅ Finds mixed content
```

---

## Performance Comparison

### With Jieba (Recommended)

| Query | Results | Latency |
|-------|---------|---------|
| "中文" | ✅ Accurate | <1ms |
| "用户偏好" | ✅ Accurate | <1ms |
| "OpenClaw" | ✅ Accurate | <1ms |

### Without Jieba (Fallback)

| Query | Results | Latency |
|-------|---------|---------|
| "中文" | ✅ Good (character-level) | <1ms |
| "用户" | ✅ Good (character-level) | <1ms |
| "OpenClaw" | ✅ Accurate | <1ms |

---

## How It Works

### Tokenization Examples

**English**:
```
Input:  "User prefers DD/MM/YYYY date format"
Tokens: ["user", "prefers", "dd", "mm", "yyyy", "date", "format"]
```

**Chinese (with Jieba)**:
```
Input:  "用户偏好使用中文交流"
Tokens: ["用户", "偏好", "使用", "中文", "交流"]
```

**Chinese (without Jieba)**:
```
Input:  "用户偏好使用中文交流"
Tokens: ["用", "户", "偏", "好", "使", "用", "中", "文", "交", "流"]
```

### N-gram Index

For both languages, 3-grams are built:

**English**:
```
"user prefers dd" → [memory_id]
"prefers dd mm" → [memory_id]
"dd mm yyyy" → [memory_id]
```

**Chinese (with Jieba)**:
```
"用户 偏好 使用" → [memory_id]
"偏好 使用 中文" → [memory_id]
"使用 中文 交流" → [memory_id]
```

**Chinese (without Jieba)**:
```
"用 户 偏" → [memory_id]
"户 偏 好" → [memory_id]
"偏 好 使" → [memory_id]
```

---

## Stopwords

### English Stopwords
```
the, a, an, is, are, was, were, be, been, being,
have, has, had, do, does, did, will, would, could,
should, may, might, must, shall, can, need, dare,
ought, used, to, of, in, for, on, with, at, by,
from, as, into, through, during, before, after,
above, below
```

### Chinese Stopwords
```
的,了,是,在,和,就,都,而,及,与,着,
也,还,个,这,那,他,她,它,我,你,们,
此,其,或,等,能够,可以
```

---

## Troubleshooting

### Issue: Chinese search returns no results

**Solution 1**: Install Jieba for better tokenization
```bash
pip install jieba
```

**Solution 2**: Check if memory contains the search term
```python
# List all memories
for memory in mm.working_memory:
    print(memory['content'])
```

### Issue: Jieba loading is slow

**Expected**: First load takes ~1-2 seconds (building dictionary)

**Solution**: Jieba caches the dictionary, subsequent loads are fast

---

## API Reference

### InMemoryIndex

```python
from claw_mem.storage.index import InMemoryIndex

index = InMemoryIndex(ngram_size=3)

# Automatic language detection
index._tokenize("English text")      # Word-based
index._tokenize("中文文本")           # Jieba or character-based
index._contains_chinese("Hello")     # False
index._contains_chinese("你好")      # True
```

### MemoryManager

```python
from claw_mem import MemoryManager

mm = MemoryManager(workspace="~/.openclaw/workspace")

# Search works in both languages
results = mm.search("query", limit=10)  # Auto-detects language
```

---

## Future Improvements

- [ ] Custom user dictionary for Jieba
- [ ] Support for other CJK languages (Japanese, Korean)
- [ ] Better handling of mixed Chinese-English queries
- [ ] Stemming/lemmatization for English

---

**Last Updated**: 2026-03-18  
**Version**: 0.6.0
