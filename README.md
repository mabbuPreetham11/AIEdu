# IIIT Dharwad AI LMS

Full-stack AI-powered Learning Management System for IIIT Dharwad built with FastAPI, PostgreSQL, Redis/Celery, React, TypeScript, Tailwind CSS, and Docker.

## Monorepo Structure

- `backend/` FastAPI backend, SQLAlchemy models, Celery tasks, AI and third-party integration adapters
- `frontend/` React 18 + TypeScript + Vite frontend
- `infra/nginx/` reverse proxy configuration
- `.github/workflows/` CI pipeline

## Core Capabilities

- IIIT Dharwad email-only authentication with JWT access and refresh tokens
- Role-based access for admin, teacher, and student users
- Course creation, enrollment by class code, archival, syllabus extraction hooks
- AI-generated session notes with per-student editable copies
- AI-assisted assignment generation, grading, plagiarism integration scaffolding
- Teacher gradebook, student grades/rank view, analytics-ready admin panel
- Local-first development with SQLite and filesystem uploads, plus Docker infrastructure for later deployment

## Quick Start Without Docker

1. Copy environment templates:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   Copy-Item frontend\.env.example frontend\.env
   ```

2. Start the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Start the frontend in a new terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

4. Open:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/v1`
- API Docs: `http://localhost:8000/docs`

## Docker Option

If you install Docker later, you can still use:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Backend Notes

- FastAPI with async SQLAlchemy 2.0 patterns
- JWT auth with refresh tokens in HTTP-only cookies
- Redis-backed Celery worker for notifications and AI/plagiarism jobs
- Local disk storage for development, with MinIO/S3 abstraction for deployment
- Modular routers under `api/v1`

## Frontend Notes

- React 18 + TypeScript + Vite
- Redux Toolkit for auth/UI state and Zustand for lightweight feature stores
- Tailwind CSS responsive UI with reusable feature modules
- React Router protected route layout

## Important Assumptions

- Local development now defaults to SQLite and filesystem uploads so the app can run without Docker.
- AI extraction, note generation, assignment generation, grading, and chat currently use a provider abstraction with OpenAI-compatible defaults and can be extended for Anthropic or local models.
- Plagiarism and virus scanning are integrated through service interfaces and background tasks; provider-specific credentials are configured through environment variables.
- This scaffold includes representative domain flows and production-ready structure, but you should still complete provider credentials, prompt calibration, and institution-specific policy tuning before deployment.
