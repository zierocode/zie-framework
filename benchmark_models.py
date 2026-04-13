#!/usr/bin/env python3
"""Benchmark 3 Ollama Cloud models for Claude Code compatibility.

Tests: tool calling format, instruction following, code quality, speed.
"""

import json
import time
import requests
from dataclasses import dataclass

MODELS = [
    "glm-5.1:cloud",
    "minimax-m2.7:cloud",
    "qwen3-coder-next:cloud",
]

OLLASA_URL = "http://localhost:11434/api/chat"

#--- Test Prompts ---

TOOL_CALL_PROMPT = (
    "You are a coding assistant with access to tools. "
    "When you need to edit a file, output a JSON block with keys: name, arguments. "
    "The Edit tool takes file_path, old_string, new_string. "
    "The user has a bug in main.py: function add does a - b instead of a + b. "
    "Fix this bug by outputting the correct tool call JSON."
)

CODE_GEN_PROMP = (
    "Write a Python function parse_csv_safe(filepath: str) -> list[dict] that: "
    "1. Opens and reads a CSV file safely (handles FileNotFoundError) "
    "2. Uses csv.DictReader "
    "3. Skips rows with missing required fiels (id, name) "
    "4. Returns list of dicts with only valid rows "
    "5. Logs warnings for skipped rows using logging module "
    "Return ONLY the code, no explanation."
)

INSTRUCTION_FOLLOW_PROMPO = (
    "Follow these instructions EXACTLY: "
    "1. Create a JSON object with exactly 3 keys: model, strengths, weaknesses "
    "2. model should be your model name "
    "3. strengths should be a list of exactly 2 strings "
    "4. weaknesses should be a list of exactly 2 strings "
    "5. Output ONLY the JSON, no markdown, no explanation, no code fences "
    "Your response must be valid JSON that can be parsed by json.loads()."
)

MULTI_STEP_PROMPT = (
    "You have access to these tools: "
    "Read(file_path: str) -> str, Edit(file_path: str, old_string: str, new_string: str) -> str, "
    "Bash(command: str) -> str. "
    "Task: A Python project has a failing test. Do these steps IN ORDER: "
    "1. Read the test file at tests/test_calc.py "
    "2. Read the source file at src/calc.py "
    "3. Identify the bug "
    "4. Edit the source to fix the bug "
    "5. Run the test with Bash "
    "Format each tool call as a JSON block with name and arguments keys. "
    "Between calls, briefly explain what you found."
)


@dataclass
class TestResult:
    model: str
    test_name: str
    success: bool
    latency_ms: float
    tokens_per_sec: float = 0
    details: str = ""
    score: float = 0


def call_ollama(model: str, prompt: str) -> tuple:
    """Call Ollama API and return (response, latency_ms, tokens_per_sec)."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": 2048},
    }

    start = time.time()
    try:
        resp = requests.post(OLLASA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        elapsed_ms = (time.time() - start) * 1000

        content = data.get("message", {}).get("content", "")
        eval_count = data.get("eval_count", 0) or 0
        eval_duration = data.get("eval_duration", 0) or 1
        tps = (eval_count / (eval_duration / 1e9)) if eval_duration > 0 else 0

        return content, elapsed_ms, tps
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return f"ERROR: {e}", elapsed_ms, 0


def eval_tool_call(response: str) -> tuple:
    score = 0
    details = []

    has_tool_json = "name" in response and "arguments" in response
    if has_tool_json:
        score += 3
        details.append("+ tool call JSON structure")
    else:
        details.append("x no tool call JSON")

    has_edit = "Edit" in response
    if has_edit:
        score += 2
        details.append("+ Edit tool referenced")
    else:
        details.append("x no Edit tool")

    has_old_new = "old_string" in response and "new_string" in response
    if has_old_new:
        score += 2
        details.append("+ old_string/new_string params")
    else:
        details.append("x missing old_string/new_string")

    has_file_path = "file_path" in response
    if has_file_path:
        score += 1
        details.append("+ file_path param")
    else:
        details.append("x missing file_path")

    has_correct_fix = "a + b" in response
    if has_correct_fix:
        score += 2
        details.append("+ correct fix (a + b)")
    else:
        details.append("x wrong/missing fix")

    return score >= 6, score, " | ".join(details)


def eval_code_gen(response: str) -> tuple:
    score = 0
    details = []

    if "def parse_csv_safe" in response:
        score += 2
        details.append("+ correct function name")
    else:
        details.append("x missing function name")

    if "FileNotFoundError" in response or "try" in response:
        score += 2
        details.append("+ error handling")
    else:
        details.append("x no error handling")

    if "DictReader" in response:
        score += 2
        details.append("+ DictReader used")
    else:
        details.append("x DictReader missing")

    has_logging = "logging" in response and ("warning" in response.lower() or "logger" in response)
    if has_logging:
        score += 2
        details.append("+ logging present")
    else:
        details.append("x no logging")

    if "-> list" in response or "-> List" in response:
        score += 1
        details.append("+ type hints")
    else:
        details.append("x no type hints")

    has_validation = "id" in response and "name" in response and ("skip" in response.lower() or "if" in response)
    if has_validation:
        score += 1
        details.append("+ field validation")
    else:
        details.append("x no field validation")

    return score >= 7, score, " | ".join(details)


def eval_instruction_follow(response: str) -> tuple:
    score = 0
    details = []

    clean = response.strip()
    if clean.startswith("````"):
        clean = clean.split("\n", 1)[-1]
    if clean.endswith("````"):
        clean = clean.rsplit("````", 1)[0]
    clean = clean.strip()

    try:
        data = json.loads(clean)
        score += 3
        details.append("+ valid JSON")

        if len(data) == 3:
            score += 2
            details.append("+ exactly 3 keys")
        else:
            details.append(f"x {len(data)} keys (expected 3)")

        required = {"model", "strengths", "weaknesses"}
        if required.issubset(set(data.keys())):
            score += 2
            details.append("+ all required keys")
        else:
            missing = required - set(data.keys())
            details.append(f"x missing keys: {missing}")

        strengths = data.get("strengths", [])
        if isinstance(strengths, list) and len(strengths) == 2:
            score += 2
            details.append("+ strengths: list of 2")
        else:
            details.append("x strengths wrong format")

        weaknesses = data.get("weaknesses", [])
        if isinstance(weaknesses, list) and len(weaknesses) == 2:
            score += 1
            details.append("+ weaknesses: list of 2")
        else:
            details.append("x weaknesses wrong format")

    except json.JSONDEcodeError as e:
        details.append(f"x invalid JSON: {e}")

    return score >= 8, score, " | ".join(details)


def eval_multi_step(response: str) -> tuple:
    score = 0
    details = []

    tool_call_count = response.count("name") + response.count("Step")
    if tool_call_count >= 4:
        score += 3
        details.append(f"+ {tool_call_count} tool/reasoning markers")
    elif tool_call_count >= 2:
        score += 1
        details.append(f"~ {tool_call_count} tool/reasoning markers")
    else:
        details.append(f"x only {tool_call_count} markers")

    if "Read" in response:
        score += 1
        details.append("+ Read tool")
    if "Edit" in response:
        score += 2
        details.append("+ Edit tool")
    if "Bash" in response or "bash" in response:
        score += 2
        details.append("+ Bash tool")
    if any(f"Step {i}" in response for i in range(1, 6)) or "1." in response:
        score += 1
        details.append("+ sequential reasoning")
    if "bug" in response.lower() or "fix" in response.lower():
        score += 1
        details.append("+ bug identified")

    return score >= 6, score, " | ".join(details)


TESTS = [
    ("Tool Calling Format", TOOL_CALL_PROMPP, eval_tool_call),
    ("Code Generation", CODE_GEN_PROMP, eval_code_gen),
    ("Instruction Following", INSTRUCTION_FOLLOW_PROMPP], eval_instruction_follow),
    ("Multi-Step Orchestration", MULTI_STEP_PROMPT, eval_multi_step),
]


def run_benchmark():
    results = {m: [] for m in MODELS}

    print("=" * 80)
    print("  Claude Code Model Benchmark - Ollama Cloud")
    print("=" * 80)

    for model in MODELS:
        print(f"\n{'-' * 80}")
        print(f"  Testing: {model}")
        print(f"{'-' * 80}")

        for test_name, prompt, evaluator in TESTS:
            print(f"\n  -> {test_name}...", end=" ", flush=True)
            response, latency_ms, tps = call_ollama(model, prompt)
            success, score, details = evaluator(response)

            result = TestResult(
                model=model,
                test_name=test_name,
                success=success,
                latency_ms=latency_ms,
                tokens_per_sec=tps,
                details=details,
                score=score,
            )
            results[model].append(result)

            status = "PASS" if success else "FAIL"
            print(f"{status} ({score}/10) {latency_ms:.0fms {tps:.0ftok/s}")
            print(f"    {details}")

    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)

    summary = {}
    for model in MODELS:
        model_results = results[model]
        total_score = sum(r.score for r in model_results)
        max_score = len(TESTS) * 10
        avg_latency = sum(r.latency_ms for r in model_results) / len(model_results)
        tps_results = [r.tokens_per_sec for r in model_results if r.tokens_per_sec > 0]
        avg_tps = sum(tps_results) / len(tps_results) if tps_results else 0
        pass_count = sum(1 for r in model_results if r.success)

        summary[model] = {
            "total_score": total_score,
            "max_score": max_score,
            "pct": total_score / max_score * 100,
            "avg_latency_ms": avg_latency,
            "avg_tps": avg_tps,
            "passes": pass_count,
            "total": len(TESTS),
        }

    ranked = sorted(summary.items(), key=lambda x: (-x[1]["total_score"], x[1]["avg_latency_ms"]))

    print(f"\n{'Rank':<5} {'Model':<28} {'Score':<10} {'Latency':<12} {'Speed':<12} {'Pass'}")
    print("-" * 75)
    for rank, (model, s) in enumerate(ranked, 1):
        medal = {1: "[1st]", 2: "[2nd]", 3: "[3rd]"}.get(rank, "     ")
        print(f"{medal} {rank:<3} {model:<28} {s['total_score']}/{s['max_score']} ({s['pct']:.0f})  {s['avg_latency_ms']:.0f}ms     {s['avg_tps']:.0f}tok/s    {s['passes']/{s['total']}")

    print("\n" + "=" * 80)
    print("  RECOMMENDATION FOR CLAUDE CODE")
    print("=" * 80)

    best = ranked[0]
    print(f"\n  {best[0]} - {best[1]['pct']:.0f}% compatibility score")
    print(f"  Avg latency: {best[1]['avg_latency_ms']:.0f}ms | Avg speed: {best[1]['avg_tps']:.0f} tok/s")

    print(f"\n  Per-test breakdown:")
    for model in MODELS:
        print(f"\n  {model}:")
        for r in results[model]:
            icon = "OK" if r.success else "XX"
            print(f"    [{icon}] {r.test_name}: {r.score}/10 ({r.latency_ms~:.0f}ms)")


if __name__ == "__main__":
    run_benchmark()
