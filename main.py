from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from langgraph.graph import MessagesState, START, END, StateGraph
from langchain.tools import tool

model = init_chat_model(
    "gpt-4.1",
    temperature=0
)

@tool
def get_flight_status(flight_number: str) -> str:
    """Retrieves the current status and timing for a specific flight number."""
    return f"Flight {flight_number} is on time!"

@tool
def check_hotel_availability(location: str) -> str:
    """Checks for available hotels in a specific city or area."""
    return f"Hotels in {location} are available!"

@tool
def get_itinerary_details(itinerary_id: str) -> str:
    """Fetches detailed scheduling information for a saved itinerary."""
    return f"Itinerary {itinerary_id} is ready for viewing."

flight_worker = create_agent(model, tools=[get_flight_status], name="flight_expert")
hotel_worker = create_agent(model, tools=[check_hotel_availability], name="hotel_expert")
itinerary_worker = create_agent(model, tools=[get_itinerary_details], name="itinerary_expert")

@tool
def flight_subtask(request: str) -> str:
    """Delegate flight-related questions (status, booking, delays) to the flight expert."""
    result = flight_worker.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def hotel_subtask(request: str) -> str:
    """Delegate lodging and accommodation inquiries to the hotel expert."""
    result = hotel_worker.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def itinerary_subtask(request: str) -> str:
    """Delegate complex scheduling and trip planning tasks to the itinerary expert."""
    result = itinerary_worker.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

SUPERVISOR_PROMPT = (
    "You are a helpful supervisor. "
    "You are responsible for routing the user request to the appropriate agent. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

supervisor_agent = create_agent(
    model,
    tools=[flight_subtask, hotel_subtask, itinerary_subtask ],
    system_prompt=SUPERVISOR_PROMPT,
)

builder = StateGraph(MessagesState)
builder.add_node("supervisor", supervisor_agent)
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", END)

graph = builder.compile()

flight_prompt = "what is the flight number for the flight from cmb to sf this weekend",
hotel_prompt = "what is the hotel name for the budget hotel in sf",
itinerary_prompt = "what is the itinerary for the trip to sf",
general_prompt = "what is the latest iPhone version",

response = graph.invoke({"messages": [
    {"role": "user", "content": "what is the flight number for the flight from cmb to sf this weekend"},
    {"role": "system", "content": "your an helpful assistant, but you dont ask for preferences and try to come up with the most convinent option to fill the gaps"}
    ]})
print(response["messages"][-1].content)