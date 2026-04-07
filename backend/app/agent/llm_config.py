import os
from langchain_ollama import ChatOllama

# Initialize the local model
# Ensure Ollama is running on your machine with the llama3.1 model downloaded
local_llm = ChatOllama(
    model="llama3.1",
    temperature=0.1, # Keep it low for analytical statistical reasoning
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), # Supports Docker networking
)

# You can now bind tools to this model just like you would with a paid API
# local_llm_with_tools = local_llm.bind_tools(statistical_tools)