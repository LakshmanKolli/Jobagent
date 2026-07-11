"""
Natural Language to SQL Assistant
----------------------------------
Takes a plain-English question, uses an LLM to translate it into a SQL query
against a known schema, executes it on a local SQLite database, and returns
the results in a readable format.

Usage:
    python nl_to_sql.py

Requirements:
    pip install openai --break-system-packages
    export OPENAI_API_KEY=sk-...

This is a minimal, self-contained example meant as a starting point for a
portfolio project. It uses SQLite + a small sample "sales" dataset so it
runs with zero external setup, but the same pattern works against
Postgres/SQL Server/Snowflake by swapping the DB connection.
"""

import os
import sqlite3
import json
from openai import OpenAI

DB_PATH = "sample_sales.db"

# ---------------------------------------------------------------------------
# 1. Set up a tiny sample database (idempotent - safe to re-run)
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY,
    region TEXT,
    product TEXT,
    quantity INTEGER,
    unit_price REAL,
    sale_date TEXT
);
"""

SAMPLE_ROWS = [
    (1, "West", "Widget A", 10, 25.0, "2026-01-05"),
    (2, "East", "Widget B", 5, 40.0, "2026-01-06"),
    (3, "West", "Widget A", 8, 25.0, "2026-02-02"),
    (4, "South", "Widget C", 12, 15.0, "2026-02-10"),
    (5, "East", "Widget A", 20, 25.0, "2026-03-01"),
    (6, "North", "Widget B", 7, 40.0, "2026-03-15"),
]

SCHEMA_DESCRIPTION = """
Table: sales
Columns:
  sale_id     INTEGER  -- unique id
  region      TEXT     -- one of: West, East, South, North
  product     TEXT     -- product name, e.g. Widget A
  quantity    INTEGER  -- units sold
  unit_price  REAL     -- price per unit in USD
  sale_date   TEXT     -- ISO date string YYYY-MM-DD
"""


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA_SQL)
    cur = conn.execute("SELECT COUNT(*) FROM sales")
    if cur.fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)", SAMPLE_ROWS
        )
        conn.commit()
    return conn


# ---------------------------------------------------------------------------
# 2. Ask the LLM to turn a question into SQL
# ---------------------------------------------------------------------------
def question_to_sql(client: OpenAI, question: str) -> str:
    prompt = f"""You are a SQL assistant. Given the schema below, write a single
SQLite query that answers the user's question. Return ONLY valid JSON of the
form {{"sql": "<query>"}} with no other text.

Schema:
{SCHEMA_DESCRIPTION}

Question: {question}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = response.choices[0].message.content.strip()
    content = content.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(content)
    return parsed["sql"]


def run_query(conn: sqlite3.Connection, sql: str):
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return columns, rows


def print_table(columns, rows):
    if not rows:
        print("(no results)")
        return
    widths = [max(len(str(c)), *(len(str(r[i])) for r in rows)) for i, c in enumerate(columns)]
    header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
    print(header)
    print("-" * len(header))
    for r in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(r, widths)))


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY environment variable first.")
        return

    client = OpenAI(api_key=api_key)
    conn = setup_database()

    print("NL-to-SQL Assistant (sample 'sales' table). Type 'exit' to quit.\n")
    while True:
        question = input("Ask a question about sales: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        try:
            sql = question_to_sql(client, question)
            print(f"\nGenerated SQL:\n  {sql}\n")
            columns, rows = run_query(conn, sql)
            print_table(columns, rows)
            print()
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()
