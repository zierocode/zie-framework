# Pattern Extraction Algorithm

**Purpose:** Document the algorithm for extracting patterns from session transcripts.

## Overview

Pattern extraction runs in two phases:
1. **Heuristic analysis** — frequency-based, rule-driven
2. **LLM-based analysis** — optional, gated by config

## Phase 1: Heuristic Analysis

### Tool Sequence Detection

```python
# Detect repeated tool call sequences
sequences = extract_tool_sequences(transcript)
# Example: [Write, Bash(test), Bash(commit)] × 5 times

for seq, count in sequences.items():
    if count >= 3:  # Minimum frequency threshold
        patterns.append({
            "category": "workflow",
            "description": f"Repeated sequence: {seq}",
            "frequency": count,
        })
```

### Keyword Frequency Analysis

```python
# Extract top keywords from session
keywords = extract_keywords(transcript, top_n=5)
# TF-IDF style scoring, filter stop words
```

### Code Pattern Detection

```python
# Detect repeated code structures
for file in modified_files:
    patterns.extend(detect_code_patterns(file))
    # Naming conventions
    # Function lengths
    # Class structures
```

## Phase 2: LLM-Based Analysis (Optional)

**Gated by:** `zie_memory_enabled=true` AND `auto_learn_llm_enabled=true`

**Prompt:**
```
Analyze this session transcript and extract:
1. Key decisions made
2. Recurring patterns or workflows
3. Learnings or insights
4. Anti-patterns to avoid

Return as JSON: {decisions: [], patterns: [], learnings: []}
```

**Token budget:** ~2000 input, ~500 output

## Confidence Scoring

```python
def score_confidence(pattern, session_history):
    """Calculate confidence score 0.0-1.0"""
    
    # Frequency component (40%)
    freq_score = min(1.0, pattern.frequency / 10)
    
    # Consistency component (30%)
    consistency = calculate_consistency(pattern, session_history)
    
    # Recency component (30%)
    days_old = (now - pattern.first_seen).days
    recency_score = math.exp(-days_old / 30)
    
    return (0.4 * freq_score + 
            0.3 * consistency + 
            0.3 * recency_score)
```

## Auto-Apply Threshold

Patterns with `confidence >= 0.95` are marked `auto_apply: true`.

These patterns are candidates for `auto-improve` to automatically apply.

## Output Format

Patterns are written to session memory JSON:

```json
{
  "patterns": [
    {
      "id": "workflow-20260414-001",
      "category": "workflow",
      "description": "TDD loop: test → implement → refactor",
      "confidence": 0.97,
      "evidence": ["test-unit before Write", "refactor after green"],
      "frequency": 5,
      "auto_apply": true
    }
  ]
}
```

## Performance Requirements

- **Overhead:** <1s per session end
- **Async execution:** Run in background, don't block session end
- **Memory:** <10MB peak during extraction
