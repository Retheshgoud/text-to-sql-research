import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "sqlite:///data/chinook.db")
engine = create_engine(DB_PATH)


def get_engine():
    return engine


def execute_sql(sql):
    try:
        import pandas as pd
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        return str(e)


def get_schema():
    """Returns a string description of all tables and columns."""
    schema_lines = []
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        for (table_name,) in tables:
            cols = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            col_names = [col[1] for col in cols]
            schema_lines.append(f"{table_name}({', '.join(col_names)})")
    return "\n".join(schema_lines)


if __name__ == "__main__":
    print(get_schema())
