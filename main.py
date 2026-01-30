from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from langgraph.graph import MessagesState, START, StateGraph

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

model = init_chat_model(
    "gpt-4.1",
    temperature=0
)

weather_agent = create_agent(model, tools=[get_weather], name="weather_expert")
general_agent = create_agent(model, tools=[], name="general_assistant")

def router(state: MessagesState):
    last_message = state["messages"][-1].content.lower()
    if "weather" in last_message:
        return "weather_expert"
    return "general_assistant"

builder = StateGraph(MessagesState)
builder.add_node("weather_expert", weather_agent)
builder.add_node("general_assistant", general_agent)

builder.add_conditional_edges(START, router)

graph = builder.compile()

response = graph.invoke({"messages": [{"role": "user", "content": "what is the weather in sf"}]})


print(response["messages"][-1].content)