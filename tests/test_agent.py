"""Smoke test for the Text-to-SQL agent (calls the live LLM; needs a key in .env).

Run from the project root:  python tests/test_agent.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.text_to_sql_agent import query_agent  # noqa: E402

if __name__ == "__main__":
    print(query_agent("How many subjects are currently enrolled in each treatment arm (ARM) in the trial?"))
