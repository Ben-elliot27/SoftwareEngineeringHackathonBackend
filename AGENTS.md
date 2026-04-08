# AGENTS.md

## Project Snapshot
FastAPI async backend for a timesheet workflow: employees log hours, managers/admins approve or reject entries.

## Architecture
```
Request → FastAPI Router → Repository (SQLAlchemy async) → PostgreSQL
```
- `src/main.py` — app factory, CORS, lifespan (DB init + dev seed)
- `src/app/api/__init__.py` — version-prefixed router (`/api/v1/...`)
- `src/app/api/deps.py` — shared FastAPI `Depends`: `get_db`, `get_current_user`, `require_admin`, `require_manager_or_admin`
- `src/app/core/config.py` — Pydantic `Settings` (env / `.env` file)
- `src/app/core/security.py` — bcrypt password hashing + PyJWT token helpers

## Key Models (`src/app/db/models/`)
| Model | Table | Notes |
|-------|-------|-------|
| `User` | `users` | roles: `employee`, `manager`, `admin`; stores `hashed_password` |
| `TimeCode` | `time_codes` | short code + description; soft-disabled via `is_active` |
| `TimesheetEntry` | `timesheet_entries` | links user + time code; status: `pending/approved/rejected` |
| `UserTimeCodeAccess` | `user_time_code_access` | m2m — which users may use which time codes |

## Authentication & Authorisation
- **Login**: `POST /api/v1/auth/login` (OAuth2 Password Flow) → returns JWT Bearer token.
- All protected endpoints require `Authorization: Bearer <token>`.
- Roles enforced via `Depends(deps.require_admin)` / `Depends(deps.require_manager_or_admin)`.

| Endpoint | Who |
|----------|-----|
| `GET /users/` | admin |
| `POST /users/` | admin |
| `PATCH/DELETE /users/{id}` | admin |
| `GET /users/me` | any authenticated |
| `GET /time-codes/` | any (employees see only their allowed codes) |
| `POST /time-codes/` | admin |
| `PATCH/DELETE /time-codes/{id}` | admin |
| `GET/POST /time-codes/{id}/access/{uid}` | admin |
| `GET /timesheets/` | employees see own; managers/admins see all |
| `POST /timesheets/` | any (employees can only submit for themselves) |
| `POST /timesheets/{id}/approve` | manager / admin |
| `POST /timesheets/{id}/reject` | manager / admin |

## Time-Code Access Control
Employees must be explicitly granted access to time codes via `UserTimeCodeAccess`.
Use `POST /api/v1/time-codes/{id}/access/{user_id}` (admin token required).

## Adding Features
1. Extend Pydantic schemas (`src/app/schemas/`)
2. Add repository functions (`src/app/db/repository/`)
3. Add/update route handler (`src/app/api/routes/`)
4. Use `Depends(deps.get_current_user)` + role checks as needed

## Local Dev
```bash
docker compose up -d db
cd src && uvicorn main:app --reload
# Dev seed creates: admin@example.com, alice@example.com, bob@example.com, carol@example.com
# Default passwords: <name>password123  (e.g. adminpassword123)
```

## No Migration Scripts
Tables are created via `Base.metadata.create_all` on startup. Alembic is a dependency but has no migration tree.
