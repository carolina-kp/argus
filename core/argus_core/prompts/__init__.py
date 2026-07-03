"""Versioned prompt templates. Load with `load_prompt("rag_answer_v1")`."""
from pathlib import Path

_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    return (_DIR / f"{name}.txt").read_text(encoding="utf-8")
