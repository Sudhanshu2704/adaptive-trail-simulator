import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

if LLM_PROVIDER == "nvidia":
    from langchain_openai import ChatOpenAI

    local_llm = ChatOpenAI(
        model="google/gemma-4-31b-it",
        temperature=1.00,
        top_p=0.95,
        max_tokens=16384,
        api_key=os.getenv("NVIDIA_API_KEY", "placeholder"),
        base_url="https://integrate.api.nvidia.com/v1",
        model_kwargs={"extra_body": {"chat_template_kwargs": {"enable_thinking": True}}},
    )
    print("[LLM] Using NVIDIA API (google/gemma-4-31b-it)")

else:
    from langchain_ollama import ChatOllama

    local_llm = ChatOllama(
        model="llama3.1",
        temperature=0.1,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    print("[LLM] Using local Ollama (llama3.1)")