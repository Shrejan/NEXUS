import os
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq

from langchain_tavily import TavilySearch

from langgraph.prebuilt import create_react_agent


# API keys
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")


# LLM
llm = ChatGroq(
    model="llama-3.1-8b-instant",

    temperature=0
)


# Web search tool
search = TavilySearch(
    max_results=3
)


# Agent
agent = create_react_agent(
    llm,
    [search]
)


# Ask the agent
question = "what new technology can i use in my handwriten text recognition project ,better then krekkan + trocr ?"
result = agent.invoke({
    "messages": [
        ("user", question)
    ]
})


# Print final answer
print(result["messages"][-1].content)