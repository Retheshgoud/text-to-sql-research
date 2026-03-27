"""
Improved Text-to-SQL system with retry mechanism.
On failure, feeds the SQL error back to the model so it can self-correct.
Logs results to results/results_retry.csv
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
RESULTS_PATH = "results/results_retry.csv"
MAX_RETRIES = 2

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


def build_retry_prompt(question, failed_sql, error):
    # Strip verbose SQLAlchemy boilerplate from error
    short_error = str(error).split("\n")[0].replace("Execution failed on sql", "").strip()
    return (
        "You are a SQL expert. The following SQL query failed. Fix it.\n\n"
        f"Schema:\n{SCHEMA}\n\n"
        f"Question: {question}\n\n"
        f"Failed SQL: {failed_sql}\n"
        f"Error: {short_error}\n\n"
        "Rules:\n"
        "- Use only table and column names from the schema above.\n"
        "- Return ONLY the corrected SQL query, no explanations, no markdown.\n"
        "- Do not add a semicolon at the end.\n\n"
        "Corrected SQL:"
    )


def extract_sql(text):
    text = text.strip()
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(";")
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
    return " ".join(collected).rstrip(";") if collected else text.rstrip(";")


def call_model(prompt):
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return extract_sql(response["message"]["content"])


def generate_with_retry(question):
    sql = call_model(build_prompt(question))
    result = execute_sql(sql)
    attempts = 1

    while not isinstance(result, pd.DataFrame) and attempts <= MAX_RETRIES:
        sql = call_model(build_retry_prompt(question, sql, result))
        result = execute_sql(sql)
        attempts += 1

    return sql, result, attempts


def run_retry():
    os.makedirs("results", exist_ok=True)
    queries = pd.read_json(QUERIES_PATH)
    logs = []

    print(f"Running improved+retry on {len(queries)} queries using model: {MODEL}")
    print(f"Schema injected ({len(SCHEMA.splitlines())} tables) | Max retries: {MAX_RETRIES}\n")

    for i, row in queries.iterrows():
        question = row["question"]
        ground_truth = row["ground_truth_sql"]

        start = time.time()
        generated_sql, result, attempts = generate_with_retry(question)
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
            "attempts": attempts,
            "method": "improved+retry"
        })

        status = "OK  " if success else "FAIL"
        retry_note = f" (retried {attempts-1}x)" if attempts > 1 else ""
        print(f"[{i+1:02d}/{len(queries)}] {status} ({latency}s){retry_note} — {question[:55]}")

    df = pd.DataFrame(logs)
    df.to_csv(RESULTS_PATH, index=False)

    print(f"\nResults saved to {RESULTS_PATH}")
    print(f"Success rate: {df['success'].mean():.1%}")
    print(f"Avg latency:  {df['latency'].mean():.2f}s")
    print(f"Queries needing retry: {(df['attempts'] > 1).sum()}")


if __name__ == "__main__":
    run_retry()
