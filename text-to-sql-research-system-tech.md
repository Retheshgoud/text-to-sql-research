# AI Text-to-SQL System — Technical Documentation

## 📦 Repository Name

`ai-text-to-sql-system`

---

# 🧠 Overview

This project implements a system that converts natural language queries into SQL, executes them on a database, and returns results. It includes a baseline implementation and an improved system using schema-aware prompting and validation.

---

# 🧰 PHASE 1: Environment Setup

## 1. Prerequisites

* Python 3.10+
* pip

## 2. Project Setup

```bash
mkdir ai-text-to-sql-system
cd ai-text-to-sql-system
```

## 3. Virtual Environment

```bash
python -m venv venv
```

### Activate

**Windows:**

```bash
venv\Scripts\activate
```

**Mac/Linux:**

```bash
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install openai langchain pandas sqlalchemy psycopg2-binary python-dotenv matplotlib
```

## 5. Environment Variables

Create `.env` file:

```env
OPENAI_API_KEY=your_api_key
```

---

# 📂 PHASE 2: Database & Dataset Setup

## 1. Database

* Use SQLite (recommended)
* Load Chinook sample database

## 2. Database Connection

```python
from sqlalchemy import create_engine
engine = create_engine("sqlite:///chinook.db")
```

## 3. Query Dataset

Create `data/queries.csv`

| question | ground_truth_sql |
| -------- | ---------------- |

* Add 50–100 queries

---

# ⚙️ PHASE 3: Baseline Implementation

## 1. SQL Generation

```python
from openai import OpenAI
client = OpenAI()

def generate_sql(question):
    prompt = f"Convert to SQL: {question}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

## 2. SQL Execution

```python
import pandas as pd

def execute_sql(sql):
    try:
        return pd.read_sql(sql, engine)
    except Exception as e:
        return str(e)
```

---

# 📊 PHASE 4: Logging System

## Output File

Create `results/results.csv`

## Schema

| question | generated_sql | success | error | latency |

## Logging Example

```python
import time

start = time.time()
sql = generate_sql(q)
result = execute_sql(sql)
end = time.time()

log = {
    "question": q,
    "generated_sql": sql,
    "success": isinstance(result, pd.DataFrame),
    "error": None if isinstance(result, pd.DataFrame) else result,
    "latency": end - start
}
```

---

# 🧠 PHASE 5: Improved System

## 1. Schema-Aware Prompting

```text
Database schema:
Tables: ...

Question: ...
Generate SQL:
```

## 2. Validation Layer

* Catch SQL errors
* Validate table/column usage

## 3. Retry Mechanism

* On failure, re-prompt model with error context

---

# 📊 PHASE 6: Experiment Execution

## Run Systems

* Baseline
* Improved

## Comparison

```python
df.groupby("method")["success"].mean()
```

---

# 📈 PHASE 7: Visualization

```python
import matplotlib.pyplot as plt

df.groupby("method")["success"].mean().plot(kind="bar")
plt.show()
```

---

# 📁 Suggested Project Structure

```
ai-text-to-sql-system/
│
├── data/
│   └── queries.csv
│
├── results/
│   └── results.csv
│
├── src/
│   ├── baseline.py
│   ├── improved.py
│   ├── db.py
│   └── utils.py
│
├── .env
├── requirements.txt
└── README.md
```

---

# ⚙️ Technical Environment Summary

* Language: Python 3.10+
* LLM: OpenAI API
* Database: SQLite / PostgreSQL
* ORM/Connector: SQLAlchemy
* Data Processing: pandas
* Visualization: matplotlib
* Environment: python-dotenv

---

# ✅ Status

System supports:

* Natural language → SQL generation
* Query execution
* Logging and evaluation
* Performance comparison between baseline and improved approaches
