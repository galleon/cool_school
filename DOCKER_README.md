# Academic Scheduling Assistant - Docker Setup

This Docker Compose setup allows you to run the entire academic scheduling application stack with containers, supporting both OpenAI and LangGraph backends.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- `.env` file with your configuration (especially OpenAI API key)

## Quick Start

### Start with LangGraph (default)
```bash
docker-compose up -d
```

### Start with OpenAI backend
```bash
AGENT_BACKEND=openai docker-compose up -d
```

### Using the startup script
```bash
./start-docker.sh
```

## 🚀 **Running Services:**

Once started, you can access:
- **Backend**: http://localhost:8001
- **Frontend**: http://localhost:5173
- **Health Check**: http://localhost:8001/schedule/health

## 🎯 **Test the Application:**

1. **Open the app**: http://localhost:5173
2. **Try these prompts**:
   - "Show me the current schedule overview"
   - "Swap CS101-A from Alice to Bob"
   - "Help me rebalance the teaching workload"
   - "Find all unassigned sections"

## Usage Examples

### Backend Selection
```bash
# Default (LangGraph)
docker-compose up -d

# OpenAI backend
AGENT_BACKEND=openai docker-compose up -d

# LangGraph backend (explicit)
AGENT_BACKEND=langgraph docker-compose up -d
```

### Development
```bash
# Build and start with logs
docker-compose up --build

# Restart just the backend
docker-compose restart backend

# Force recreate backend with new environment
AGENT_BACKEND=openai docker-compose up -d --force-recreate backend
```

## Services

The stack includes:

1. **Backend API (FastAPI)**: `localhost:8001`
   - FastAPI server with OpenAI/LangGraph integration
   - Auto-reloads on code changes
   - In-memory storage for demo data

2. **Frontend (React + Vite)**: `localhost:5173`
   - React development server
   - Hot reloading enabled

## Environment Variables

Make sure your `.env` file contains:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Agent Backend Selection (optional)
AGENT_BACKEND=langgraph  # or 'openai'

# API URLs (optional - defaults work for Docker setup)
API_BASE_URL=http://localhost:8001
VITE_API_BASE=http://localhost:8001

# Optional
KNOWLEDGE_VECTOR_STORE_ID=your_vector_store_id
VITE_KNOWLEDGE_CHATKIT_API_DOMAIN_KEY=domain_pk_localhost_dev
```

## Useful Commands

```bash
# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend

# Rebuild and restart
docker-compose up --build

# Stop and remove everything
docker-compose down

# Access backend container
docker-compose exec backend bash

# Access frontend container
docker-compose exec frontend sh
```

## Development

The containers are set up for development with:
- Volume mounts for live code reloading
- Development servers running in containers
- Database persistence with named volumes

## Troubleshooting

### Backend issues
- Check if `.env` file has `OPENAI_API_KEY` set
- View backend logs: `docker-compose logs -f backend`

### Frontend issues
- Check if frontend dependencies are installed
- View frontend logs: `docker-compose logs -f frontend`

### Port conflicts
If ports are already in use, you can modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "8002:8001"  # Maps host port 8002 to container port 8001
```
