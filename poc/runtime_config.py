"""Runtime settings for new runs; frozen experiment records remain unchanged."""
import os


def search_model():
    return os.environ.get("LLM_MODEL_NAME", "gpt-6-sol").strip() or "gpt-6-sol"
