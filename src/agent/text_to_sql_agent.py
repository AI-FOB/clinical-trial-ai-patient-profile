"""Text-to-SQL agent for the clinical SDTM database.

Sends the DB schema + a natural-language question to the configured LLM
(NVIDIA Nemotron by default, or Groq - see `llm_config.py`), validates that the
returned SQL is a single read-only SELECT, executes it against a read-only
SQLite connection and returns the SQL + results as markdown.
"""
import os
import re
import sqlite3
from functools import lru_cache

import pandas as pd
from langchain_core.messages import HumanMessage

from src.agent.llm_config import get_llm

PROCESSED_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "processed"
)
DB_PATH = os.path.join(PROCESSED_DATA_DIR, "clinical_data.db")

_READ_ONLY_PATTERN = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)
_FORBIDDEN_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|VACUUM)\b",
    re.IGNORECASE,
)


def _connect_read_only() -> sqlite3.Connection:
    """Opens the clinical DB in read-only mode so LLM-generated SQL can never mutate data."""
    uri = f"file:{DB_PATH.replace(os.sep, '/')}?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


@lru_cache(maxsize=1)
def get_schema() -> str:
    """Returns the database schema as a string (cached; call get_schema.cache_clear() on refresh)."""
    if not os.path.exists(DB_PATH):
        return ""
    parts = []
    with _connect_read_only() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for (table_name,) in cur.fetchall():
            cur.execute(f'PRAGMA table_info("{table_name}");')
            cols = [c[1] for c in cur.fetchall()]
            parts.append(f"Table: {table_name}\nColumns: {', '.join(cols)}")
    return "\n\n".join(parts)


@lru_cache(maxsize=1)
def _cached_llm():
    """Single LLM client per process (Streamlit additionally wraps this in st.cache_resource)."""
    return get_llm()


def _clean_sql(raw: str) -> str:
    sql = raw.strip()
    sql = re.sub(r"^```(?:sql)?", "", sql, flags=re.IGNORECASE).strip()
    sql = re.sub(r"```$", "", sql).strip()
    return sql.rstrip(";").strip()


def _validate_sql(sql: str) -> None:
    if not _READ_ONLY_PATTERN.match(sql) or _FORBIDDEN_PATTERN.search(sql) or ";" in sql:
        raise ValueError("Only single read-only SELECT statements are permitted.")


def query_agent(query: str, llm=None, schema: str | None = None) -> str:
    """Translates a natural-language question to SQL, executes it read-only and returns markdown."""
    if not os.path.exists(DB_PATH):
        return f"Database not found at {DB_PATH}. Please run the data pipeline first."

    llm = llm or _cached_llm()
    schema = schema if schema is not None else get_schema()

    # We bypass Langchain's complex AgentExecutor entirely for bulletproof stability.
    prompt = f"""You are an expert clinical data analyst and SQLite specialist.
Given the following CDISC SDTM database schema, write a valid SQLite query to answer the user's question.

SCHEMA:
{schema}

USER QUESTION: {query}

CDISC SDTM DOMAIN RULES:
1. Historical trial context: this is a COMPLETED clinical trial. For "enrolled" or
   "currently enrolled" subjects, DO NOT filter by `RFENDTC IS NULL` (in a completed
   trial only Screen Failures have a null RFENDTC).
2. Treatment arms (DM.ARM / DM.ACTARM): when counting subjects by arm, include ALL arms
   (GROUP BY ARM with no completion filter). Keep 'Screen Failure' as its own group
   rather than dropping completed subjects.
3. Adverse events (AE): severity is in AESEV ('MILD', 'MODERATE', 'SEVERE');
   seriousness is in AESER ('Y' / 'N'). Compare using these exact uppercase values.

INSTRUCTIONS:
- ONLY return the raw SQL query (a single SELECT statement).
- DO NOT wrap it in markdown formatting (like ```sql).
- DO NOT explain anything or add conversational text.
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        sql_query = _clean_sql(response.content)
        _validate_sql(sql_query)

        with _connect_read_only() as conn:
            df = pd.read_sql_query(sql_query, conn)

        output = f"**Generated SQL Query:**\n```sql\n{sql_query}\n```\n\n"
        if df.empty:
            output += "**Query Result:**\nNo data returned."
        else:
            output += f"**Query Result:**\n\n{df.head(200).to_markdown(index=False)}"
        return output

    except Exception as e:
        return f"Error executing query: {str(e)}"
