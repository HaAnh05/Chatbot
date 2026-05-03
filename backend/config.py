import os


LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "llm")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "0"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatbot.db")
