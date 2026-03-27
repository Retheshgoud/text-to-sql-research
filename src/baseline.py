"""
Baseline Text-to-SQL system.
Uses direct LLM prompting with no schema context.
Logs results to results/results_baseline.csv
"""
import os
import time
import re
import pandas as pd
import ollama
from dotenv import load_dotenv
from db import execute_sql

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
QUERIES_PATH = "data/queries.json"
RESULTS_PATH = "results/results_baseline.csv"


def build_prompt(question):
    return (
        "You are a SQL expert. Convert the following natural language question into a valid SQLite SQL query.\n"
        "Return ONLY the SQL query, no explanations, no markdown, no code blocks.\n\n"
        f"Question: {question}\n\n"
        "SQL:"
    )


def extract_sql(text):
    """Strip markdown code blocks if model wraps output in them."""
    text = text.strip()
    # Remove ```sql ... ``` or ``` ... ```
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def generate_sql(question):
    prompt = build_prompt(question)
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response["message"]["content"]
    return extract_sql(raw)


def run_baseline():
    os.makedirs("results", exist_ok=True)
    queries = pd.read_json(QUERIES_PATH)
    logs = []

    print(f"Running baseline on {len(queries)} queries using model: {MODEL}\n")

    for i, row in queries.iterrows():
        question = row["question"]
        ground_truth = row["ground_truth_sql"]

        start = time.time()
        generated_sql = generate_sql(question)
        result = execute_sql(generated_sql)
        latency = round(time.time() - start, 3)

        success = isinstance(result, pd.DataFrame)
        error = None if success else result

        logs.append({
            "question": question,
            "ground_truth_sql": ground_truth,
            "generated_sql": generated_sql,
            "success": success,
            "error": error,
            "latency": latency,
            "method": "baseline"
        })

        status = "OK" if success else "FAIL"
        print(f"[{i+1:02d}/{len(queries)}] {status} ({latency}s) — {question[:60]}")

    df = pd.DataFrame(logs)
    df.to_csv(RESULTS_PATH, index=False)

    print(f"\nResults saved to {RESULTS_PATH}")
    print(f"Success rate: {df['success'].mean():.1%}")
    print(f"Avg latency:  {df['latency'].mean():.2f}s")


if __name__ == "__main__":
    run_baseline()
