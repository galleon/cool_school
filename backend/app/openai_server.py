from __future__ import annotations

from typing import Any, AsyncIterator

from agents import RunConfig, Runner
from agents.model_settings import ModelSettings
from chatkit.agents import AgentContext, stream_agent_response
from chatkit.server import ChatKitServer, StreamingResult
from chatkit.types import (
    Attachment,
    ClientToolCallItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from openai.types.responses import ResponseInputContentParam
from starlette.responses import JSONResponse

from .agent_utils import format_schedule_context
from .config import settings
from .database import SessionLocal
from .openai_agent import scheduling_agent
from .postgres_store import PostgreSQLStore
from .routers import schedule_router

DEFAULT_THREAD_ID = "demo_default_thread"

DEFAULT_THREAD_ID = "demo_default_thread"


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _format_schedule_context() -> str:
    """Format the current schedule state as context for the agent."""
    return format_schedule_context()


def _is_tool_completion_item(item: Any) -> bool:
    return isinstance(item, ClientToolCallItem)


class SchedulingServer(ChatKitServer[dict[str, Any]]):
    def __init__(self) -> None:
        db_session = SessionLocal()
        store = PostgreSQLStore(db_session)
        super().__init__(store)
        self.store = store
        self.db_session = db_session
        self.agent = scheduling_agent

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

        context_prompt = _format_schedule_context()
        combined_prompt = (
            f"{context_prompt}\n\nUser request: {message_text}\n"
            "Respond as the academic scheduling assistant."
        )

        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )
        result = Runner.run_streamed(
            self.agent,
            combined_prompt,
            context=agent_context,
            run_config=RunConfig(model_settings=ModelSettings(temperature=0.4)),
        )

        async for event in stream_agent_response(agent_context, result):
            yield event

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported in this demo.")


scheduling_server = SchedulingServer()

app = FastAPI(title="ChatKit Academic Scheduling API", debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Keep simple for now - could use settings.cors_origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper Pydantic response models
app.include_router(schedule_router)


def get_server() -> SchedulingServer:
    return scheduling_server


@app.post("/schedule/chatkit")
async def chatkit_endpoint(
    request: Request, server: SchedulingServer = Depends(get_server)
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
