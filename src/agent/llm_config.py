"""NVIDIA NIM LLM client for the Medical Reviewer AI Agent.

This project uses NVIDIA AI Endpoints exclusively (Nemotron-3 Super 120B).
Settings are read from environment variables, loaded from a git-ignored
`.env` file at the project root (see `.env.example`):
    NVIDIA_API_KEY    required - get one at https://build.nvidia.com
    NVIDIA_MODEL      optional (default: nvidia/nemotron-3-super-120b-a12b)
"""
import os

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")


def get_llm() -> ChatNVIDIA:
    """Returns the NVIDIA NIM chat model. Raises if NVIDIA_API_KEY is not set."""
    if not NVIDIA_API_KEY:
        raise EnvironmentError(
            "NVIDIA_API_KEY is not set. Copy .env.example to .env and add your key "
            "from https://build.nvidia.com."
        )
    print(f"Initializing NVIDIA LLM: {NVIDIA_MODEL}")
    return ChatNVIDIA(api_key=NVIDIA_API_KEY, model=NVIDIA_MODEL, temperature=0, timeout=120)
