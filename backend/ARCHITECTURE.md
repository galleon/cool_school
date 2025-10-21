# Academic Scheduling Assistant - Architecture & Implementation

## Overview

This project supports **both OpenAI Agents and LangGraph** as the underlying agent framework. You can easily switch between implementations without changing the frontend code.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                             │
│                   (React + TS)                          │ ← ChatKit Integration
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/WebSocket
                  ▼
┌─────────────────────────────────────────────────────────┐
│                  ENTRY POINT                           │
├─────────────────────────────────────────────────────────┤
│ main.py         │ config.py                             │ ← Dynamic routing
└─────────────────┬───────────────────────────────────────┘
                  │ Environment-based routing
                  ▼
┌─────────────────────────────────────────────────────────┐
│                 SERVER IMPLEMENTATIONS                  │
├─────────────────────────────────────────────────────────┤
│ openai_server.py    │ langgraph_server.py              │ ← FastAPI apps
└─────────────────┬───────────────┬───────────────────────┘
                  │               │
                  ▼               ▼
┌─────────────────────────────────────────────────────────┐
│                   AGENT CLASSES                        │
├─────────────────────────────────────────────────────────┤
│ openai_agent.py     │ langgraph_agent.py               │ ← Agent logic
└─────────────────┬───────────────┬───────────────────────┘
                  │               │
                  ▼               ▼
┌─────────────────────────────────────────────────────────┐
│                   TOOL WRAPPERS                        │
├─────────────────────────────────────────────────────────┤
│ openai_tools.py     │ langgraph_tools.py               │ ← Framework adapters
└─────────────────┬───────────────┬───────────────────────┘
                  │               │
                  └───────┬───────┘
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC                        │
├─────────────────────────────────────────────────────────┤
│              core_tools.py                              │ ← Pure functions
└─────────────────────────────────────────────────────────┘
```

## 📁 File Structure

| File                  | Size  | Purpose                           |
| --------------------- | ----- | --------------------------------- |
| `main.py`             | 371B  | **Entry Point** - Dynamic routing |
| `openai_server.py`    | 5.7KB | **OpenAI FastAPI Server**         |
| `langgraph_server.py` | 11KB  | **LangGraph FastAPI Server**      |
| `openai_agent.py`     | 2KB   | **OpenAI Agent Factory**          |
| `langgraph_agent.py`  | 11KB  | **LangGraph Agent Class**         |
| `openai_tools.py`     | 4KB   | **OpenAI Tool Wrappers**          |
| `langgraph_tools.py`  | 2KB   | **LangGraph Tool Wrappers**       |
| `core_tools.py`       | 9KB   | **Backend-Agnostic Logic**        |

## Implementation Details

### Original Implementation (OpenAI Agents)
- **File**: `app/openai_server.py`
- **Agent**: `app/openai_agent.py`
- Uses OpenAI's `agents` framework and `openai-chatkit`
- Direct integration with ChatKit streaming protocol

### New Implementation (LangGraph)
- **File**: `app/langgraph_server.py`
- **Agent**: `app/langgraph_agent.py`
- Uses LangGraph for agent orchestration with OpenAI LLMs
- Custom adapter to convert LangGraph streaming to ChatKit format

## Key Features Ported to LangGraph

All scheduling tools have been successfully ported:
- ✅ `show_schedule_overview()` - Complete teacher/section overview
- ✅ `show_load_distribution()` - Workload analysis with charts
- ✅ `show_violations()` - Find overloaded teachers or conflicts
- ✅ `rebalance()` - OR-Tools optimization for load balancing
- ✅ `swap()` - Move section assignments between teachers
- ✅ `show_unassigned()` - Find sections needing assignment
- ✅ `assign_section()` - Assign sections to qualified teachers

## Switching Between Implementations

### Method 1: Configuration File (Recommended)

Edit `app/config.py`:

```python
# For OpenAI Agents (original)
AGENT_BACKEND = "openai"

# For LangGraph (new)
AGENT_BACKEND = "langgraph"
```

Then run with the unified entry point:
```bash
uv run uvicorn app.main:app --reload --port 8001
```

### Method 2: Direct Module Selection

**OpenAI Agents:**
```bash
uv run uvicorn app.openai_server:app --reload --port 8001
```

**LangGraph:**
```bash
uv run uvicorn app.langgraph_server:app --reload --port 8001
```

## Dependencies

The `pyproject.toml` now includes both sets of dependencies:

### Original Dependencies
- `openai>=1.40`
- `openai-chatkit>=1.0.2,<2`
- `agents` (from OpenAI)

### New LangGraph Dependencies
- `langchain>=0.1.0`
- `langchain-openai>=0.1.0`
- `langgraph>=0.1.0`

## Implementation Details

### LangGraph Agent Architecture

The LangGraph implementation uses a simplified approach that maintains ChatKit compatibility:

1. **SimpleLangGraphAgent**: Core agent class with tool registry
2. **LangGraphChatKitAdapter**: Converts LangGraph streaming to ChatKit events
3. **Tool Functions**: Direct ports of original OpenAI agent tools

### Streaming Protocol Compatibility

The adapter converts between formats:

```python
# LangGraph chunk -> ChatKit ThreadStreamEvent
{
    "type": "text",
    "content": "Hello..."
}
# becomes ->
{
    "type": "text.delta",
    "data": {"text": "Hello..."}
}
```

### Tool Calling

Both implementations support the same tool interface:
- Function calling with typed parameters
- Tool result processing and display
- Error handling and user feedback

## Testing

Test the LangGraph agent:
```bash
# Set environment variables
export OPENAI_API_KEY="your-key-here"

# Run test script
uv run python test_langgraph.py
```

## Frontend Compatibility

The frontend ChatKit component works identically with both backends:
- Same API endpoints (`/schedule/chatkit`, `/schedule/state`)
- Same streaming event format
- Same tool calling and response handling
- No frontend changes required

## Benefits of LangGraph Implementation

1. **Flexibility**: More control over agent execution flow
2. **Extensibility**: Easier to add complex multi-step workflows
3. **Debugging**: Better visibility into agent state and execution
4. **Customization**: More options for tool orchestration and memory
5. **Framework Independence**: Less dependency on OpenAI's specific agent framework

## Migration Notes

- All existing functionality is preserved
- Frontend requires no changes
- Environment variables remain the same
- Tool behaviors are identical
- Schedule state management unchanged

## Performance Considerations

- **OpenAI Agents**: Direct integration, minimal overhead
- **LangGraph**: Slight additional overhead for conversion layer
- Both use streaming for real-time response updates
- Tool execution performance is identical (same underlying functions)

## Future Enhancements

The LangGraph implementation provides foundation for:
- Multi-agent conversations
- Complex workflow orchestration
- Custom memory and state management
- Integration with other LLM providers
- Advanced planning and reasoning capabilities

Choose the implementation that best fits your needs - both provide the same user experience!
