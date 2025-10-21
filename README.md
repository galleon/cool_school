# Academic Scheduling Assistant

An intelligent ChatKit-powered scheduling system for academic course timetabling and teacher assignment. This project demonstrates a **dual-backend architecture** supporting both OpenAI Agents and LangGraph frameworks with perfect symmetry.

## 🎯 What's Inside
- **🚀 LangGraph-ChatKit Adapter**: Revolutionary bridge enabling LangGraph agents to work seamlessly with ChatKit UI
- **Dual Backend**: FastAPI servers with OpenAI Agents OR LangGraph implementation
- **ChatKit Integration**: React UI with real-time streaming, progress indicators, and rich formatting
- **Smart Scheduling**: OR-Tools optimization for workload balancing
- **Teacher Management**: Assign courses, resolve conflicts, optimize loads
- **Clean Architecture**: Framework-agnostic business logic with symmetric implementations

## 📋 Architecture

> 📋 **For detailed architecture diagrams and technical details, see [backend/ARCHITECTURE.md](./backend/ARCHITECTURE.md)**

The system uses a layered architecture with perfect framework symmetry:

```
Frontend (React) → Entry Point (main.py) → Backend Selection (config.py)
    ↓
{OpenAI Server | LangGraph Server} → {OpenAI Agent | LangGraph Agent}
    ↓
{OpenAI Tools | LangGraph Tools} → Core Business Logic → Data Layer
```

## 🚀 Prerequisites
- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or `pip`
- OpenAI API key exported as `OPENAI_API_KEY`
- ChatKit domain key exported as `VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY`

## ⚡ Quick Start

### 1. Start the Backend

The backend automatically selects between OpenAI and LangGraph based on configuration:
### 1. Start the Backend

The backend automatically selects between OpenAI and LangGraph based on configuration:

```bash
cd backend
uv sync
export OPENAI_API_KEY="sk-proj-..."

# Option 1: Use environment variable to select backend
export AGENT_BACKEND=langgraph  # or "openai"
uv run uvicorn app.main:app --reload --port 8001

# Option 2: Start specific backend directly
uv run uvicorn app.langgraph_server:app --reload --port 8001
# OR
uv run uvicorn app.openai_server:app --reload --port 8001
```

### 2. Start the Frontend

```bash
cd frontend
npm install
export VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY="your-domain-key"
npm run dev
```

### 3. Start with Docker

```bash
# Use LangGraph backend (default)
docker-compose up -d

# Use OpenAI backend
AGENT_BACKEND=openai docker-compose up -d
```

## 🛠️ Available Tools

The scheduling assistant provides these capabilities:

- **📊 Schedule Overview** - Complete view of teachers, sections, and assignments
- **📈 Load Distribution** - Workload analysis with visualizations
- **⚠️ Violation Detection** - Find overloaded teachers or scheduling conflicts
- **🔄 Smart Rebalancing** - OR-Tools optimization for balanced workloads
- **↔️ Section Swapping** - Reassign sections between qualified teachers
- **📋 Unassigned Tracking** - Find sections needing teacher assignment
- **✅ Section Assignment** - Assign sections to qualified teachers

## 🔧 Framework Switching

Switch between agent frameworks without code changes:

```bash
# Use LangGraph (default)
export AGENT_BACKEND=langgraph

# Use OpenAI Agents
export AGENT_BACKEND=openai
```

Both implementations provide identical functionality and responses.

## � Key Innovation: LangGraph-ChatKit Adapter

The **LangGraph-ChatKit Adapter** is the core technical achievement that enables LangGraph agents to work seamlessly with OpenAI's ChatKit interface. This adapter:

- **🔄 Protocol Translation**: Converts LangGraph streaming events to ChatKit's ThreadStreamEvent format in real-time
- **✨ Rich UI Features**: Provides progress indicators, tool execution feedback, and formatted results
- **📱 Visual Excellence**: Supports icons, markdown rendering, and real-time text streaming
- **🛡️ Error Handling**: Graceful error display with appropriate visual cues
- **🔧 Extensible Design**: Easy to add new tools and custom formatting

**📖 Deep Dive Documentation:**
- **[LangGraph-ChatKit Adapter Protocol](./CHATKIT_ADAPTER_PROTOCOL.md)** - Complete protocol specification and visual components
- **[Technical Implementation Guide](./TECHNICAL_IMPLEMENTATION.md)** - Implementation details, patterns, and extension points

## �📚 Documentation

- **[Architecture & Implementation Guide](./backend/ARCHITECTURE.md)** - Complete system design, framework comparison, and technical details
- **[Docker Setup](./DOCKER_README.md)** - Container deployment guide

## 🧪 Testing

```bash
cd backend

# Run LangGraph tests
export OPENAI_API_KEY="sk-test-key"
uv run python tests/test_langgraph.py

# Run integration tests
uv run python tests/test_integration.py

# Compare agent implementations
uv run python tests/test_agent_comparison.py
```

## 🎯 Key Features

- **🔄 Dual Backend Support**: Switch between OpenAI Agents and LangGraph seamlessly
- **🎨 Clean Architecture**: Perfect framework symmetry with shared business logic
- **⚡ Real-time Streaming**: Live responses through ChatKit integration
- **🧠 Smart Optimization**: OR-Tools integration for optimal scheduling
- **🔧 Easy Configuration**: Environment-based backend selection
- **🐳 Docker Ready**: Complete containerized deployment
- **🧪 Well Tested**: Comprehensive test coverage for both backends

## 🚀 Production Deployment

The system is production-ready with:
- Framework-agnostic design for vendor flexibility
- Clean separation of concerns for maintainability
- Comprehensive testing for reliability
- Container-based deployment for scalability
uv run uvicorn app.main:app --reload --port 8001
```

The API exposes ChatKit at `http://127.0.0.1:8001/support/chatkit` and helper endpoints under `/support/*`.

### 2. Run the React frontend

```bash
cd examples/customer-support/frontend
npm install
npm run dev
```

The dev server runs at `http://127.0.0.1:5171` and proxies `/support` calls back to the API, which covers local iteration.

From the `examples/customer-support` directory you can also run `npm start` to launch the backend (`uv sync` + Uvicorn) and frontend together. Ensure `uv` is installed and required environment variables (for example `OPENAI_API_KEY` and `VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY`) are exported before using this shortcut.

Regarding the domain public key, you can use any string during local development. However, for production deployments:

1. Host the frontend on infrastructure you control behind a managed domain.
2. Register that domain on the [domain allowlist page](https://platform.openai.com/settings/organization/security/domain-allowlist) and mirror it in `examples/customer-support/frontend/vite.config.ts` under `server.allowedHosts`.
3. Set `VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY` to the key returned by the allowlist page and verify it surfaces in `examples/customer-support/frontend/src/lib/config.ts`.

When you need to test remote-access scenarios ahead of launch, temporarily expose the app with a tunnel—e.g. `ngrok http 5171` or `cloudflared tunnel --url http://localhost:5171`—and allowlist that hostname first.

### 3. Try the workflow

Open the printed URL and experiment with prompts such as:

- `Can you move me to seat 14C on flight OA476?`
- `I need to cancel my trip and request a refund.`
- `Add one more checked bag to my reservation.`

The agent invokes the appropriate tools and the timeline updates automatically in the side panel.
