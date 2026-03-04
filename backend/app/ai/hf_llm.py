from langchain_groq import ChatGroq
import os

chat_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.4,
    max_tokens=512,
    api_key=os.getenv("GROQ_API_KEY")
)