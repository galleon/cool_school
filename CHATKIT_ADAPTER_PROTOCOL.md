# LangGraph-ChatKit Adapter Protocol Documentation

## Overview

This document describes the **LangGraph-ChatKit Adapter**, a critical bridge that enables LangGraph agents to seamlessly integrate with OpenAI's ChatKit UI framework. This adapter is the core few lines of code that allows us to use LangGraph's advanced graph-based agent architecture while maintaining full compatibility with ChatKit's rich streaming interface.

## Architecture

The adapter follows a **streaming event transformation pattern** that converts LangGraph's internal streaming format into ChatKit's ThreadStreamEvent protocol in real-time.

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│  LangGraph  │───▶│  Adapter Layer   │───▶│   ChatKit   │
│   Agent     │    │ (Event Transform)│    │     UI      │
└─────────────┘    └──────────────────┘    └─────────────┘
```

## ChatKit Protocol Components

### Core Event Types

ChatKit expects these specific event types for real-time streaming:

1. **`AssistantMessageContentPartTextDelta`** - Streaming text content
2. **`ProgressUpdateEvent`** - Tool execution progress with icons
3. **`ThreadItemAddedEvent`** - Final message persistence
4. **`AssistantMessageItem`** - Complete message objects

### Visual Components Available

ChatKit supports rich visual elements through the ProgressUpdateEvent system:

#### Icons Available
- `"bolt"` - Tool execution indicator (🔧)
- `"sparkle"` - Success/completion (✅)
- `"circle-question"` - Error/warning (❌)
- Custom emojis and text indicators

#### UI Features
- **Real-time text streaming** - Character-by-character display
- **Progress indicators** - Tool execution feedback
- **Message persistence** - Final threaded conversation
- **Markdown rendering** - Rich formatting support
- **Theme adaptation** - Dark/light mode support
- **Custom styling** - Configurable colors, radius, grayscale

## Protocol Mapping

### 1. Text Streaming (`text` → `AssistantMessageContentPartTextDelta`)

**LangGraph Output:**
```python
{
    "type": "text",
    "content": "Here is the current schedule..."
}
```

**ChatKit Transformation:**
```python
yield AssistantMessageContentPartTextDelta(
    content_index=0,
    delta=content
)
```

**Result:** Real-time character-by-character text streaming in the chat interface.

### 2. Tool Execution Start (`tool_call_start` → `ProgressUpdateEvent`)

**LangGraph Output:**
```python
{
    "type": "tool_call_start",
    "tool_name": "show_schedule_overview"
}
```

**ChatKit Transformation:**
```python
yield ProgressUpdateEvent(
    text=f"🔧 Using tool: {tool_name}...",
    icon="bolt"
)
```

**Result:** Progress indicator appears showing tool execution with spinning/loading visual.

### 3. Tool Results (`tool_result` → `ProgressUpdateEvent` + formatting)

**LangGraph Output:**
```python
{
    "type": "tool_result",
    "tool_name": "show_schedule_overview",
    "result": {
        "message": "Schedule overview retrieved",
        "teachers": {"t_alice": {...}, "t_bob": {...}}
    }
}
```

**ChatKit Transformation:**
```python
# Format result with markdown for rich display
result_text = result["message"]
if tool_name == "show_schedule_overview":
    teacher_summary = []
    for tid, data in teachers.items():
        teacher_summary.append(
            f"- **{data['name']}**: {data['current_load']:.1f}h/{data['max_load']} ({data['utilization']})"
        )
    result_text += "\\n\\n**Teacher Workloads:**\\n" + "\\n".join(teacher_summary)

yield ProgressUpdateEvent(
    text=f"✅ {tool_name}: {result_text}",
    icon="sparkle"
)
```

**Result:** Formatted tool results with markdown rendering and success indicator.

### 4. Error Handling (`error` → `ProgressUpdateEvent`)

**LangGraph Output:**
```python
{
    "type": "error",
    "content": "Tool execution failed"
}
```

**ChatKit Transformation:**
```python
yield ProgressUpdateEvent(
    text=f"❌ Error: {error_msg}",
    icon="circle-question"
)
```

**Result:** Error message with warning icon and red styling.

### 5. Message Persistence (`complete` → `ThreadItemAddedEvent`)

**Final Step:**
```python
complete_response = "".join(full_response_parts).strip()

assistant_item = AssistantMessageItem(
    id=f"msg_{uuid.uuid4().hex[:8]}",
    thread_id=thread_id,
    created_at=datetime.now(),
    content=[{"type": "output_text", "text": complete_response}],
)

yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_item)
```

**Result:** Complete message added to conversation history for persistence.

## Advanced Features

### Markdown Formatting

The adapter enhances tool results with markdown formatting:

```python
# Before (plain text)
"Alice: 8.0h/12.0 (66.7%)"

# After (markdown)
"- **Alice**: 8.0h/12.0 (66.7%)"
```

This enables:
- **Bold teacher names**
- **Bullet points** for lists
- **Structured formatting** for complex data
- **Rich text rendering** in ChatKit

### Tool-Specific Formatting

Different tools get custom formatting:

```python
if tool_name == "show_schedule_overview":
    # Enhanced teacher workload display
elif tool_name == "show_load_distribution":
    # Formatted load summaries with note about histograms
elif tool_name == "assign_section":
    # Success confirmation with new load info
```

### State Management

The adapter maintains:
- **Thread continuity** across multiple interactions
- **Response accumulation** for final message persistence
- **Error state handling** with graceful fallbacks
- **Tool execution context** for enhanced formatting

## Integration Points

### Backend Integration

```python
class LangGraphSchedulingServer(ChatKitServer[dict[str, Any]]):
    async def respond(self, thread: ThreadMetadata, item: UserMessageItem, context):
        # Convert ChatKit request to LangGraph format
        user_message = item.content[0]["text"]

        # Stream through adapter
        async for event in self.adapter.stream_agent_response_from_langgraph(
            user_message, thread.id
        ):
            yield event
```

### Frontend Integration

```tsx
<ChatKit
    control={chatkit.control}
    startScreen={{
        greeting: "Welcome to Academic Scheduling Assistant",
        prompts: ["Show schedule overview", "Find conflicts"]
    }}
    theme={{
        colorScheme: "dark",
        radius: "round"
    }}
/>
```

## Key Benefits

1. **Seamless Integration** - LangGraph agents work natively with ChatKit UI
2. **Rich Visual Feedback** - Progress indicators, icons, and formatted results
3. **Real-time Streaming** - Character-level text streaming for responsive UX
4. **Error Handling** - Graceful error display with appropriate visual cues
5. **Extensible Design** - Easy to add new tools and formatting rules
6. **Framework Agnostic** - Adapter pattern allows swapping underlying agent frameworks

## Comparison with OpenAI Native

| Feature            | OpenAI Native              | LangGraph + Adapter                |
| ------------------ | -------------------------- | ---------------------------------- |
| **Streaming**      | Built-in ThreadStreamEvent | ✅ Full compatibility via adapter   |
| **Tool Calls**     | Native ChatKit tools       | ✅ Custom tool integration          |
| **Progress UI**    | Automatic                  | ✅ Custom progress indicators       |
| **Error Handling** | Built-in                   | ✅ Custom error formatting          |
| **Flexibility**    | Limited to OpenAI          | ✅ Any LangGraph agent architecture |
| **Customization**  | ChatKit constraints        | ✅ Full control over formatting     |

## Future Enhancements

Potential adapter improvements:
- **Rich Cards** - Structured data display cards
- **Interactive Elements** - Buttons, forms, and action triggers
- **File Attachments** - Document and image support
- **Custom Icons** - Tool-specific visual indicators
- **Animation Support** - Smooth transitions and loading states
- **Batch Updates** - Efficient bulk progress updates
