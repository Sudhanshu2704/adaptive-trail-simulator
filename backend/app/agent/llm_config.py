import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

if LLM_PROVIDER == "groq":
    from langchain_groq import ChatGroq

    local_llm = ChatGroq(
        model="llama3-8b-8192",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    print("[LLM] Using Groq API (llama3-8b-8192)")

else:
    from langchain_ollama import ChatOllama

    local_llm = ChatOllama(
        model="llama3.1",
        temperature=0.1,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    print("[LLM] Using local Ollama (llama3.1)")