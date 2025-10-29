from __future__ import annotations

from typing import Any, AsyncIterator
import json

from chatkit.types import (
    Attachment,
    ClientToolCallItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    ProgressUpdateEvent,
    AssistantMessageContentPartTextDelta,
    ThreadItemAddedEvent,
    AssistantMessageItem,
)
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from openai.types.responses import ResponseInputContentParam

from .config import settings
from starlette.responses import JSONResponse
from chatkit.server import ChatKitServer, StreamingResult

from .schedule_state import SCHEDULE_MANAGER
from .postgres_store import PostgreSQLStore
from .database import SessionLocal
from .langgraph_agent import langgraph_agent
from .routers import schedule_router

DEFAULT_THREAD_ID = "demo_default_thread"


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _is_tool_completion_item(item: Any) -> bool:
    return isinstance(item, ClientToolCallItem)


class LangGraphChatKitAdapter:
    """Adapter that converts LangGraph agent responses to ChatKit streaming format."""

    @staticmethod
    async def stream_agent_response_from_langgraph(
        user_message: str,
        thread_id: str = DEFAULT_THREAD_ID,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Convert LangGraph agent streaming to ChatKit ThreadStreamEvent format."""

        # Use the streaming LangGraph agent
        messages = [{"role": "user", "content": user_message}]

        # Accumulate the full response for final message persistence
        full_response_parts = []

        async for chunk in langgraph_agent.stream_response(thread_id, messages):
            chunk_type = chunk.get("type")

            if chunk_type == "text":
                # Convert text chunks to ChatKit text deltas for real-time streaming
                content = chunk.get("content", "")
                if content:
                    # Store for final message
                    full_response_parts.append(content)
                    # Stream the delta
                    yield AssistantMessageContentPartTextDelta(content_index=0, delta=content)

            elif chunk_type == "tool_call_start":
                # Tool call starting
                tool_name = chunk.get("tool_name", "")
                yield ProgressUpdateEvent(text=f"🔧 Using tool: {tool_name}...", icon="bolt")

            elif chunk_type == "tool_result":
                # Tool execution completed
                tool_name = chunk.get("tool_name", "")
                result = chunk.get("result", {})

                # Format the result in a more meaningful way
                result_text = ""
                if isinstance(result, dict):
                    if "message" in result:
                        result_text = result["message"]
                        # Add additional context for better user experience
                        if tool_name == "show_schedule_overview":
                            teachers = result.get("teachers", {})
                            if teachers:
                                teacher_summary = []
                                for tid, data in teachers.items():
                                    teacher_summary.append(
                                        f"  • {data['name']}: {data['current_load']:.1f}h / {data['max_load']}h ({data['utilization']})"
                                    )
                                result_text += (
                                    "\n\nTeacher Workloads:\n" + "\n".join(teacher_summary) + "\n"
                                )
                        elif tool_name == "assign_section":
                            if "result" in result and result.get("success"):
                                res = result["result"]
                                result_text = f"✅ Successfully assigned {res['section_id']} to {res['teacher_name']}. New load: {res['teacher_new_load']:.1f}h"
                    elif "error" in result:
                        result_text = f"❌ Error: {result['error']}"
                    else:
                        # For other structured results, format them nicely
                        if tool_name == "show_load_distribution" and "loads" in result:
                            loads = result["loads"]
                            load_summary = "\n".join(
                                [f"  • {name}: {load:.1f}h" for name, load in loads.items()]
                            )
                            result_text = f"Teaching Load Distribution:\n{load_summary}"
                            # Don't include the image path in the response to avoid broken links
                            if "histogram_path" in result:
                                result_text += "\n(Histogram image available)"
                        else:
                            # Filter out image paths and other non-user-friendly data
                            clean_result = {
                                k: v for k, v in result.items() if k not in ["histogram_path"]
                            }
                            result_text = json.dumps(clean_result, indent=2)
                else:
                    result_text = str(result)

                # Add to full response
                full_response_parts.append(f"\n\n{result_text}")

                # Send tool result as progress update
                yield ProgressUpdateEvent(text=f"✅ {tool_name}: {result_text}", icon="sparkle")

            elif chunk_type == "error":
                # Handle errors
                error_msg = chunk.get("content", "Unknown error")
                full_response_parts.append(f"\n\n❌ Error: {error_msg}")
                yield ProgressUpdateEvent(text=f"❌ Error: {error_msg}", icon="circle-question")

        # Create a final persistent message with the complete response
        if full_response_parts:
            import uuid
            from datetime import datetime

            complete_response = "".join(full_response_parts).strip()

            # Create the assistant message item for persistence
            assistant_item = AssistantMessageItem(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                thread_id=thread_id,
                created_at=datetime.now(),
                content=[{"type": "output_text", "text": complete_response}],
            )

            # Add the complete message to the thread
            yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_item)


class LangGraphSchedulingServer(ChatKitServer[dict[str, Any]]):
    def __init__(self) -> None:
        store = PostgreSQLStore(SessionLocal)
        super().__init__(store)
        self.store = store
        self.adapter = LangGraphChatKitAdapter()

    def _resolve_thread_id(self, thread: ThreadMetadata | None) -> str:
        return thread.id if thread and thread.id else DEFAULT_THREAD_ID

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        if item is None:
            return

        if _is_tool_completion_item(item):
            return

        message_text = _user_message_text(item)
        if not message_text:
            return

        # Use the LangGraph adapter to stream responses
        thread_id = self._resolve_thread_id(thread)
        async for event in self.adapter.stream_agent_response_from_langgraph(
            message_text, thread_id
        ):
            yield event

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported in this demo.")


langgraph_scheduling_server = LangGraphSchedulingServer()

app = FastAPI(title="LangGraph Academic Scheduling API", debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Keep simple for now - settings.cors_origins would need to be added to config
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper Pydantic response models
app.include_router(schedule_router)


def get_server() -> LangGraphSchedulingServer:
    return langgraph_scheduling_server


@app.post("/schedule/chatkit")
async def chatkit_endpoint(
    request: Request, server: LangGraphSchedulingServer = Depends(get_server)
) -> Response:
    payload = await request.body()
    result = await server.process(payload, {"request": request})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)


def _thread_param(thread_id: str | None) -> str:
    return thread_id or DEFAULT_THREAD_ID


# Note: /schedule/state and /schedule/health are now served by the schedule_router
# Additional scheduling endpoints are available through the schedule_router
