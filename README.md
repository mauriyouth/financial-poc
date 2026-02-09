# Financial POC - Development Guide

Quick reference for running and testing the application.

## Quick Start

```bash
# Start everything
make local-stack   # Start infrastructure (DB, Redis, MinIO, etc.)
make api          # Run backend (terminal 1)
make worker       # Run parser worker (terminal 2)
make front        # Run frontend (terminal 3)
```

## Available Commands

### Services
- `make api` - Run backend API server (port 8000)
- `make worker` - Run document parsing worker  
- `make front` - Run frontend dev server (port 3000)
- `make local-stack` - Start all infrastructure
- `make stack-down` - Stop infrastructure
- `make stack-clean` - Stop and remove volumes

### Testing
- `make test` - Run all tests (backend + frontend)
- `make test-back` - Run backend tests only
- `make test-front` - Run frontend tests only

### Linting
- `make lint` - Lint all code
- `make lint-back` - Lint backend only
- `make lint-front` - Lint frontend only
- `make fix` - Auto-fix backend linting issues
- `make format` - Format backend code

### Help
- `make help` - Show all available commands

## Project Structure

```
financial-poc/
├── backend/          # Python FastAPI backend
├── frontend/         # Next.js frontend
├── infra/
│   └── local-stack/  # Docker infrastructure
└── Makefile         # Unified commands
```

## Development Workflow

1. **Start infrastructure**: `make local-stack`
2. **Run services**: Open 3 terminals and run `make api`, `make worker`, `make front`
3. **Access apps**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
4. **Before commit**: `make lint` and `make test`
