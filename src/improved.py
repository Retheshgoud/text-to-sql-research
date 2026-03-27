"""
Improved Text-to-SQL system.
Injects real database schema into the prompt so the model
knows exact table and column names.
Logs results to results/results_improved.csv
"""
import os
import time
import re
import pandas as pd
import ollama
from dotenv import load_dotenv
from db import execute_sql, get_schema

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
QUERIES_PATH = "data/queries.json"
RESULTS_PATH = "results/results_improved.csv"

SCHEMA = get_schema()


def build_prompt(question):
    return (
        "You are a SQL expert. Use the following SQLite database schema to answer the question.\n\n"
        f"Schema:\n{SCHEMA}\n\n"
        "Rules:\n"
        "- Use only table and column names from the schema above.\n"
        "- Return ONLY the SQL query, no explanations, no markdown, no code blocks.\n"
        "- Do not add a semicolon at the end.\n"
        "- Use AVG() not average(), use standard SQLite functions only.\n\n"
        f"Question: {question}\n\n"
        "SQL:"
    )


def extract_sql(text):
    text = text.strip()
    # Strip markdown code blocks
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(";")
    # If no code block, take everything up to the first blank line after SQL starts
    # to drop any trailing explanation the model may add
    sql_started = False
    collected = []
    for line in text.splitlines():
        stripped = line.strip()
        if not sql_started:
            if re.match(r"(SELECT|WITH|INSERT|UPDATE|DELETE)", stripped, re.IGNORECASE):
                sql_started = True
                collected.append(stripped)
        else:
            if stripped == "" and collected:
                break
            collected.append(stripped)
    result = " ".join(collected).rstrip(";") if collected else text.rstrip(";")
    return result


def generate_sql(question):
    prompt = build_prompt(question)
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response["message"]["content"]
    return extract_sql(raw)


def run_improved():
    os.makedirs("results", exist_ok=True)
    queries = pd.read_json(QUERIES_PATH)
    logs = []

    print(f"Running improved on {len(queries)} queries using model: {MODEL}")
    print(f"Schema injected ({len(SCHEMA.splitlines())} tables)\n")

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
            "method": "improved"
        })

        status = "OK  " if success else "FAIL"
        print(f"[{i+1:02d}/{len(queries)}] {status} ({latency}s) — {question[:60]}")

    df = pd.DataFrame(logs)
    df.to_csv(RESULTS_PATH, index=False)

    print(f"\nResults saved to {RESULTS_PATH}")
    print(f"Success rate: {df['success'].mean():.1%}")
    print(f"Avg latency:  {df['latency'].mean():.2f}s")


if __name__ == "__main__":
    run_improved()
