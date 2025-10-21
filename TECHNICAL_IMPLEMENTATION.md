# LangGraph-ChatKit Adapter: Technical Implementation Guide

## Core Adapter Class

The `LangGraphChatKitAdapter` is the central component that bridges LangGraph's streaming protocol with ChatKit's event system.

### Implementation Structure

```python
class LangGraphChatKitAdapter:
    """Adapter that converts LangGraph agent responses to ChatKit streaming format."""

    @staticmethod
    async def stream_agent_response_from_langgraph(
        user_message: str,
        thread_id: str = DEFAULT_THREAD_ID,
    ) -> AsyncIterator[ThreadStreamEvent]:
```

## Event Flow Diagram

```
User Input
    ↓
[ChatKit UI]
    ↓ (HTTP POST)
[FastAPI Endpoint]
    ↓ (user_message, thread_id)
[LangGraph Agent]
    ↓ (async stream)
┌─────────────────────────────────────┐
│         ADAPTER LAYER               │
│  ┌─────────────────────────────┐    │
│  │  Event Type Detection       │    │
│  │  ├─ text                   │    │
│  │  ├─ tool_call_start        │    │
│  │  ├─ tool_result            │    │
│  │  └─ error                  │    │
│  └─────────────────────────────┘    │
│              ↓                      │
│  ┌─────────────────────────────┐    │
│  │  ChatKit Event Generation   │    │
│  │  ├─ AssistantMessageContent..│    │
│  │  ├─ ProgressUpdateEvent     │    │
│  │  └─ ThreadItemAddedEvent    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
    ↓ (ThreadStreamEvent)
[ChatKit UI] ← Real-time updates
```

## Event Transformation Details

### 1. Text Streaming Transform

```python
if chunk_type == "text":
    content = chunk.get("content", "")
    if content:
        # Accumulate for final persistence
        full_response_parts.append(content)

        # Stream immediately to UI
        yield AssistantMessageContentPartTextDelta(
            content_index=0,
            delta=content
        )
```

**Key Points:**
- `content_index=0` - First (and only) content part
- `delta` - Incremental text chunk for streaming
- Dual purpose: immediate streaming + accumulation for persistence

### 2. Tool Execution Indicators

```python
elif chunk_type == "tool_call_start":
    tool_name = chunk.get("tool_name", "")
    yield ProgressUpdateEvent(
        text=f"🔧 Using tool: {tool_name}...",
        icon="bolt"
    )
```

**Visual Result:**
- Progress indicator appears in ChatKit UI
- Icon shows "bolt" (⚡) for active execution
- Text provides context about which tool is running

### 3. Smart Result Formatting

The adapter includes intelligent formatting logic for different tool types:

```python
elif chunk_type == "tool_result":
    tool_name = chunk.get("tool_name", "")
    result = chunk.get("result", {})

    # Base message
    result_text = result.get("message", "")

    # Tool-specific enhancement
    if tool_name == "show_schedule_overview":
        teachers = result.get("teachers", {})
        if teachers:
            teacher_summary = []
            for tid, data in teachers.items():
                teacher_summary.append(
                    f"- **{data['name']}**: {data['current_load']:.1f}h/"
                    f"{data['max_load']} ({data['utilization']})"
                )
            result_text += "\\n\\n**Teacher Workloads:**\\n" + "\\n".join(teacher_summary)

    elif tool_name == "show_load_distribution":
        loads = result.get("loads", {})
        load_summary = "\\n".join([
            f"- **{name}**: {load:.1f}h" for name, load in loads.items()
        ])
        result_text = f"**Teaching Load Distribution:**\\n{load_summary}"

        if "histogram_path" in result:
            result_text += "\\n\\n*Note: Load distribution histogram available*"

    # Add to accumulating response
    full_response_parts.append(f"\\n\\n{result_text}")

    # Show progress update
    yield ProgressUpdateEvent(
        text=f"✅ {tool_name}: {result_text}",
        icon="sparkle"
    )
```

## Message Persistence Strategy

After all streaming events, the adapter creates a final persistent message:

```python
# Create complete response
complete_response = "".join(full_response_parts).strip()

# Generate unique message ID
message_id = f"msg_{uuid.uuid4().hex[:8]}"

# Create assistant message item
assistant_item = AssistantMessageItem(
    id=message_id,
    thread_id=thread_id,
    created_at=datetime.now(),
    content=[{"type": "output_text", "text": complete_response}],
)

# Add to thread
yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_item)
```

**Benefits:**
- **Thread Continuity** - Messages persist across sessions
- **Complete Context** - Full response available for reference
- **Unique IDs** - Proper message tracking and threading

## Error Handling Patterns

### Graceful Degradation

```python
elif chunk_type == "error":
    error_msg = chunk.get("content", "Unknown error")
    full_response_parts.append(f"\\n\\n❌ Error: {error_msg}")
    yield ProgressUpdateEvent(
        text=f"❌ Error: {error_msg}",
        icon="circle-question"
    )
```

### Result Processing Safety

```python
# Safe dictionary access
if isinstance(result, dict):
    if "message" in result:
        result_text = result["message"]
    elif "error" in result:
        result_text = f"❌ Error: {result['error']}"
    else:
        # Fallback for unknown result format
        clean_result = {
            k: v for k, v in result.items()
            if k not in ["histogram_path"]  # Filter internal data
        }
        result_text = json.dumps(clean_result, indent=2)
else:
    result_text = str(result)  # Fallback to string representation
```

## Performance Considerations

### Streaming Efficiency

- **Immediate Yielding** - Events sent as soon as they're processed
- **Minimal Buffering** - Only accumulate what's needed for persistence
- **Async Iterator** - Non-blocking stream processing

### Memory Management

```python
# Efficient string accumulation
full_response_parts = []  # List for efficient concatenation
# ... during processing
full_response_parts.append(content)
# ... at the end
complete_response = "".join(full_response_parts).strip()
```

## Integration with FastAPI

### Streaming Response Handler

```python
@app.post("/schedule/chatkit")
async def chatkit_endpoint(
    request: Request, server: LangGraphSchedulingServer = Depends(get_server)
) -> Response:
    """Handle ChatKit streaming requests."""

    # Parse ChatKit request
    request_data = await request.json()

    # Extract user message and thread info
    thread = request_data.get("thread", {})
    thread_id = thread.get("id", DEFAULT_THREAD_ID)

    # Stream through adapter
    return StreamingResponse(
        server.respond(thread_metadata, user_item, {}),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

## Testing Strategy

### Unit Tests for Adapter

```python
async def test_text_streaming():
    adapter = LangGraphChatKitAdapter()

    # Mock LangGraph response
    async def mock_langgraph_stream():
        yield {"type": "text", "content": "Hello"}
        yield {"type": "text", "content": " world"}

    # Test adapter transformation
    events = []
    async for event in adapter.stream_agent_response_from_langgraph("test"):
        events.append(event)

    # Verify ChatKit events
    assert isinstance(events[0], AssistantMessageContentPartTextDelta)
    assert events[0].delta == "Hello"
    assert isinstance(events[-1], ThreadItemAddedEvent)
```

### Integration Tests

```python
async def test_end_to_end_flow():
    # Test complete user message → ChatKit UI flow
    async with AsyncClient() as client:
        response = await client.post("/schedule/chatkit", json={
            "thread": {"id": "test-thread"},
            "message": {"content": [{"text": "show schedule"}]}
        })

        # Verify streaming response
        async for line in response.aiter_lines():
            event = json.loads(line)
            # Verify ChatKit event structure
```

## Extension Points

### Adding New Event Types

```python
elif chunk_type == "custom_visualization":
    # Handle custom visualizations
    viz_data = chunk.get("data", {})
    yield ProgressUpdateEvent(
        text=f"📊 Generated visualization: {viz_data['type']}",
        icon="chart"
    )
```

### Tool-Specific Formatters

```python
def format_tool_result(tool_name: str, result: dict) -> str:
    """Tool-specific result formatting."""
    formatters = {
        "show_schedule_overview": format_schedule_overview,
        "show_load_distribution": format_load_distribution,
        "assign_section": format_assignment_result,
    }

    formatter = formatters.get(tool_name, format_generic_result)
    return formatter(result)
```

## Troubleshooting Guide

### Common Issues

1. **Missing Icons**: Verify icon names match ChatKit supported icons
2. **Formatting Issues**: Ensure markdown syntax is properly escaped
3. **Stream Interruption**: Check async iterator completion and error handling
4. **Message Persistence**: Verify ThreadItemAddedEvent is always sent last

### Debug Logging

```python
import logging

logger = logging.getLogger(__name__)

async def stream_agent_response_from_langgraph(self, ...):
    logger.info(f"Starting stream for thread: {thread_id}")

    async for chunk in langgraph_agent.stream_response(thread_id, messages):
        logger.debug(f"Processing chunk: {chunk.get('type')}")
        # ... processing logic
```

This adapter represents a sophisticated bridge between two powerful systems, enabling advanced LangGraph agent capabilities within ChatKit's polished user experience.
