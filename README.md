# Natural Language to SQL Assistant

A small GenAI tool that lets a business user ask a plain-English question
("what were total sales by region in Q1?") and get back a SQL query plus the
result set — no SQL knowledge required.

## How it works
1. A fixed schema description is sent to an LLM (OpenAI `gpt-4o-mini`) along
   with the user's natural-language question.
2. The LLM returns a SQL query as structured JSON.
3. The query runs against a local SQLite sample `sales` table.
4. Results print as a formatted table.

## Why this project
This mirrors a common enterprise pattern: pairing an LLM with a data
warehouse schema to give non-technical stakeholders self-service access to
data, without them needing to write SQL. It directly touches skills relevant
to both Data Engineering (schema design, query execution) and Data/Business
Analysis (translating business questions into data answers).

## Run it
```bash
pip install openai --break-system-packages
export OPENAI_API_KEY=sk-...
python nl_to_sql.py
```

Example questions to try:
- "What is total revenue by region?"
- "Which product sold the most units in Q1 2026?"
- "Show me all sales in the West region over $200"

## Extending it
- Swap SQLite for Postgres/SQL Server/Snowflake by changing the connection
  in `setup_database()` and updating `SCHEMA_DESCRIPTION`.
- Add guardrails: validate generated SQL is read-only (`SELECT` only) before
  execution to prevent destructive queries.
- Add a simple Streamlit front end for a demo-able UI.
