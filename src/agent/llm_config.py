"""LLM provider configuration for the Medical Reviewer AI Agent.

Default provider is NVIDIA AI Endpoints (Nemotron-3 Super 120B); Groq is the
recommended alternative. Ollama (local) and OpenAI are also supported.

All settings are read from environment variables, loaded from a git-ignored
`.env` file at the project root (see `.env.example`):
    LLM_PROVIDER      nvidia | groq | ollama | openai   (default: nvidia)
    NVIDIA_API_KEY    required when LLM_PROVIDER=nvidia
    GROQ_API_KEY      required when LLM_PROVIDER=groq
"""
import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Load secrets from a local, git-ignored .env file (see .env.example)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

# Select provider: "ollama", "openai", "groq", or "nvidia"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "nvidia")

# NVIDIA settings (get a key at build.nvidia.com; set NVIDIA_API_KEY in .env)
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen-2.5-32b") 

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

def get_llm():
    """Returns the configured LLM instance based on environment variables."""
    if LLM_PROVIDER == "nvidia":
        print(f"Initializing NVIDIA LLM: {NVIDIA_MODEL}")
        return ChatNVIDIA(
            api_key=NVIDIA_API_KEY,
            model=NVIDIA_MODEL,
            temperature=0,
            timeout=120
        )
    elif LLM_PROVIDER == "groq":
        print(f"Initializing Groq LLM: {GROQ_MODEL}")
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0
        )
    elif LLM_PROVIDER == "ollama":
        print(f"Initializing Ollama LLM: {OLLAMA_MODEL}")
        return ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=0
        )
    elif LLM_PROVIDER == "openai":
        print(f"Initializing OpenAI LLM: {OPENAI_MODEL}")
        return ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            temperature=0
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
