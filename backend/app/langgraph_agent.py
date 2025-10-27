"""Streaming LangGraph-based university schedule management agent."""

from __future__ import annotations

import json
import logging
from typing import TypedDict, Annotated, AsyncIterator

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
    from langgraph.graph import StateGraph
    from langgraph.prebuilt import ToolNode
    from langgraph.graph.message import add_messages

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from .langgraph_tools import UNIVERSITY_TOOLS
from .config import settings, get_llm_config
from .agent_utils import format_schedule_context

# Setup logging for this module
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the university schedule management agent graph."""

    messages: Annotated[list, add_messages]
    thread_id: str


class StreamingLangGraphUniversityAgent:
    """Streaming LangGraph-based university schedule management agent."""

    def __init__(self):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph dependencies not available")

        self.tools = UNIVERSITY_TOOLS
        self.tool_node = ToolNode(self.tools)

        # Initialize LLM with config from environment
        llm_config = get_llm_config()
        base_llm = ChatOpenAI(
            model=llm_config["model"],
            openai_api_key=llm_config["openai_api_key"],
            openai_api_base=llm_config["openai_api_base"],
            temperature=0.1,
            streaming=True,
        )

        # Bind tools to the LLM
        self.llm = base_llm.bind_tools(self.tools, tool_choice="auto")

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""

        def should_continue(state: AgentState) -> str:
            """Decide whether to continue or end the conversation."""
            last_message = state["messages"][-1]
            # Check for tool calls more robustly
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "end"

        def call_model(state: AgentState):
            """Call the LLM with the current state."""
            # Add system message with instructions
            system_message = SystemMessage(content=self._get_system_instructions())
            messages = [system_message] + state["messages"]

            # Invoke the LLM
            response = self.llm.invoke(messages)

            return {"messages": [response]}

        def call_tools(state: AgentState):
            """Execute tool calls."""
            last_message = state["messages"][-1]
            tool_responses = []
            thread_id = state["thread_id"]

            for tool_call in last_message.tool_calls:
                # Always set the correct thread_id (override any existing one)
                if "args" not in tool_call:
                    tool_call["args"] = {}
                tool_call["args"]["thread_id"] = thread_id

                # Find and execute the tool
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Log tool call
                logger.info(
                    f"Tool call [thread_id: {thread_id}]: {tool_name} with args: {tool_args}"
                )

                for tool_func in self.tools:
                    if tool_func.name == tool_name:
                        try:
                            result = tool_func.invoke(tool_args)
                            # Log tool result
                            logger.info(
                                f"Tool result [thread_id: {thread_id}]: {tool_name} returned: {result}"
                            )
                            tool_responses.append(
                                ToolMessage(
                                    content=json.dumps(result), tool_call_id=tool_call["id"]
                                )
                            )
                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            logger.error(
                                f"Tool error [thread_id: {thread_id}]: {tool_name} failed: {error_msg}"
                            )
                            tool_responses.append(
                                ToolMessage(content=error_msg, tool_call_id=tool_call["id"])
                            )
                        break

            return {"messages": tool_responses}

        # Build the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", call_tools)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent", should_continue, {"tools": "tools", "end": "__end__"}
        )

        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def _get_system_instructions(self) -> str:
        """Get system instructions for the agent."""
        # Get current schedule context
        schedule_context = format_schedule_context()
        
        return f"""You are a scheduling assistant for teacher-course assignment and timetabling.

{schedule_context}

Use the provided tools to answer questions about the university schedule. Choose the most appropriate tool for each request to avoid redundancy.

Available tools:
- show_schedule_overview: Get a complete overview including teachers, workloads, sections, and assignments
- show_load_distribution: Get a histogram and raw teacher load numbers
- show_violations: Check for overload or conflict violations
- rebalance: Perform automatic rebalancing of teaching assignments
- swap: Swap a section assignment between teachers
- show_unassigned: Find unassigned sections
- assign_section: Assign a section to a teacher

Guidelines:
- For "schedule overview" or "teacher workloads", use show_schedule_overview
- For "load distribution" or "histogram", use show_load_distribution
- Don't call multiple tools for the same information
- Keep responses concise and well-formatted

Always be helpful and provide clear explanations of any scheduling operations performed."""

    async def stream_response(self, thread_id: str, messages: list[dict]) -> AsyncIterator[dict]:
        """Generate a streaming response using the LangGraph agent."""
        try:
            # Log incoming user request
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            if user_messages:
                latest_user_message = user_messages[-1]["content"]
                logger.info(f"User request [thread_id: {thread_id}]: {latest_user_message}")

            # Convert message dicts to LangChain message objects
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))

            # Create initial state
            state = AgentState(messages=langchain_messages, thread_id=thread_id)

            # Track tool calls to correlate with results
            tool_call_map = {}

            # Stream through the graph execution
            async for step in self.graph.astream(state):
                step_name = list(step.keys())[0]
                step_data = step[step_name]

                if step_name == "agent":
                    # LLM is thinking/responding
                    messages = step_data.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            # Tool calls are about to be made
                            for tool_call in last_message.tool_calls:
                                tool_call_id = tool_call.get("id")
                                tool_name = tool_call["name"]
                                # Store the mapping for later correlation
                                if tool_call_id:
                                    tool_call_map[tool_call_id] = tool_name
                                yield {
                                    "type": "tool_call_start",
                                    "tool_name": tool_name,
                                    "tool_args": tool_call.get("args", {}),
                                }
                        elif hasattr(last_message, "content") and last_message.content:
                            # Regular text response - send as single chunk to avoid text replacement issues
                            content = last_message.content
                            yield {"type": "text", "content": content}

                elif step_name == "tools":
                    # Tools are being executed
                    messages = step_data.get("messages", [])
                    for message in messages:
                        if hasattr(message, "content") and hasattr(message, "tool_call_id"):
                            # Get the tool name from our mapping
                            tool_call_id = message.tool_call_id
                            tool_name = tool_call_map.get(tool_call_id, "unknown")

                            try:
                                # Try to parse tool result as JSON
                                result = json.loads(message.content)
                                yield {
                                    "type": "tool_result",
                                    "tool_name": tool_name,
                                    "result": result,
                                }
                            except json.JSONDecodeError:
                                # Plain text tool result
                                yield {
                                    "type": "tool_result",
                                    "tool_name": tool_name,
                                    "result": {"message": message.content},
                                }

        except Exception as e:
            logger.error(f"Streaming error [thread_id: {thread_id}]: {str(e)}")
            yield {
                "type": "error",
                "content": f"I encountered an error: {str(e)}. Please try rephrasing your request.",
            }

    async def respond(self, thread_id: str, messages: list[dict]) -> str:
        """Generate a non-streaming response (for backward compatibility)."""
        chunks = []
        async for chunk in self.stream_response(thread_id, messages):
            if chunk.get("type") == "text":
                chunks.append(chunk.get("content", ""))

        return (
            "".join(chunks)
            if chunks
            else "I'm having trouble processing your request. Please try again."
        )


# Factory function for backwards compatibility
def create_langgraph_agent():
    """Create a LangGraph agent instance."""
    return StreamingLangGraphUniversityAgent()


# Export the agent instance
langgraph_agent = StreamingLangGraphUniversityAgent()
