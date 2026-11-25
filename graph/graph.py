from langgraph.graph import END, StateGraph

from graph.nodes.booking_node import booking_node
from graph.nodes.sale_node import sale_node
from graph.nodes.direct_node import direct_node
from graph.nodes.intent_node import intent_node
from graph.nodes.maintenance_node import maintenance_node

from graph.state import AgentState
from schemas.intent import IntentType

import utils.trace_logger as trace_logger


__agent_graph = None


def route_intent(state: AgentState) -> str:
    """Return the current intent used for graph routing."""

    intent = state.get("intent")
    intent_value = str(getattr(intent, "value", intent) or "").strip().lower()
    try:
        intent_str = IntentType(intent_value).value
    except ValueError:
        intent_str = IntentType.DIRECT.value

    trace_logger.step(
        "ROUTING",
        f"GRAPH CONDITIONAL ROUTING -> {intent_str.upper()}",
        input_data={"intent": intent_str},
        output_data={"target_branch": intent_str},
    )

    return intent_str


def build_graph():
    graph = StateGraph(AgentState)

    # Register Nodes
    graph.add_node("intent", intent_node)
    graph.add_node("booking", booking_node)
    graph.add_node("sales", sale_node)
    graph.add_node("direct", direct_node)
    graph.add_node("maintenance", maintenance_node)

    # Entry Point
    graph.set_entry_point("intent")

    # Intent -> Workflow
    graph.add_conditional_edges(
        "intent",
        route_intent,
        {intent.value: intent.value for intent in IntentType},
    )

    # Workflows -> END
    graph.add_edge("booking", END)
    graph.add_edge("sales", END)
    graph.add_edge("direct", END)
    graph.add_edge("maintenance", END)

    return graph.compile()


def get_agent_graph():
    global __agent_graph

    if __agent_graph is None:
        __agent_graph = build_graph()

    return __agent_graph
