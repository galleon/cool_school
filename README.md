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
- ChatKit domain key exported as `VITE_SCHEDULE_CHATKIT_API_DOMAIN_KEY`

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
export VITE_SCHEDULE_CHATKIT_API_DOMAIN_KEY="your-domain-key"
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

## 🔬 Key Innovation: LangGraph-ChatKit Adapter

The **LangGraph-ChatKit Adapter** is the core technical achievement that enables LangGraph agents to work seamlessly with OpenAI's ChatKit interface. This adapter:

- **🔄 Protocol Translation**: Converts LangGraph streaming events to ChatKit's ThreadStreamEvent format in real-time
- **✨ Rich UI Features**: Provides progress indicators, tool execution feedback, and formatted results
- **📱 Visual Excellence**: Supports icons, markdown rendering, and real-time text streaming
- **🛡️ Error Handling**: Graceful error display with appropriate visual cues
- **🔧 Extensible Design**: Easy to add new tools and custom formatting

**📖 Deep Dive Documentation:**
- **[LangGraph-ChatKit Adapter Protocol](./CHATKIT_ADAPTER_PROTOCOL.md)** - Complete protocol specification and visual components
- **[Technical Implementation Guide](./TECHNICAL_IMPLEMENTATION.md)** - Implementation details, patterns, and extension points

##  Documentation

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

## 🎮 Try the Application

Open `http://localhost:5173` and experiment with prompts such as:

- **"Show me the current schedule overview"**
- **"Find all scheduling violations"**
- **"Rebalance the teaching workloads"**
- **"Swap CS101-A from Alice to Bob"**
- **"Show me the load distribution"**
- **"Find unassigned sections"**

The agent will execute the appropriate scheduling tools and display results with real-time progress indicators.
