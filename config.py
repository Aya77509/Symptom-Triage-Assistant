"""Shared config. Edit MODEL_NAME to match a model you've pulled with `ollama pull`."""

OLLAMA_HOST = "http://localhost:11434"

# Any local model works; smaller/faster models are fine for this project.
# Examples: "llama3.2", "llama3.2:1b", "mistral", "qwen2.5:7b"
MODEL_NAME = "llama3.2"
