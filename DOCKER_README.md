# Customer Support Application - Docker Setup

This Docker Compose setup allows you to run the entire customer support application stack with containers.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- `.env` file with your configuration (especially OpenAI API key)

## Quick Start

### Option 1: Use the startup script
```bash
./start-docker.sh
```

### Option 2: Manual Docker Compose commands
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Services

The stack includes:

1. **Database (PostgreSQL)**: `localhost:5432`
   - Database: `brs_prototype_db`
   - User: `postgres`
   - Password: `postgres` (from .env)

2. **Backend API (FastAPI)**: `localhost:8001`
   - FastAPI server with OpenAI integration
   - Auto-reloads on code changes

3. **Frontend (React + Vite)**: `localhost:5173`
   - React development server
   - Hot reloading enabled

## Environment Variables

Make sure your `.env` file contains:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/brs_prototype_db
POSTGRES_DB=brs_prototype_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# API URLs
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
docker-compose logs -f db

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend

# Rebuild and restart
docker-compose up --build

# Stop and remove everything (including volumes)
docker-compose down -v

# Access database
docker-compose exec db psql -U postgres -d brs_prototype_db

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

### Database issues
- Check if database is healthy: `docker-compose ps`
- Access database directly: `docker-compose exec db psql -U postgres`

### Port conflicts
If ports are already in use, you can modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "8002:8001"  # Maps host port 8002 to container port 8001
```
