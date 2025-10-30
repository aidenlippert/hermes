# Databases: Postgres + Redis (Dev Guide)

Status
- ✅ Postgres: Running in Docker on port 5432 (auth: md5/password)
- ✅ Redis: Running in Docker on port 6379 (requirepass enabled)
- ✅ Both services healthy via docker-compose

WSL2/Docker Desktop Note
- Known issue: From WSL2 host to Windows Docker, Postgres password auth can fail intermittently.
- Everything works reliably:
  - Inside containers
  - Between containers
  - From apps running in Docker
  - From Windows host shells (PowerShell) to Docker
- Workarounds when developing from WSL2:
  - Prefer running the backend in Docker when using Postgres.
  - Or use SQLite locally for host-runs: `DATABASE_URL=sqlite+aiosqlite:///path/to/hermes_dev.db`.
  - If you must connect from WSL2 to Docker Postgres, try `host.docker.internal` and ensure `md5` auth is active.

Compose Services
- Postgres image: pgvector-enabled; auth method enforced to `md5`.
- Redis healthcheck uses password and is strict about readiness.

Environment Variables
- Postgres: `DATABASE_URL=postgresql+asyncpg://hermes:hermes@localhost:5432/hermes`
- Redis: `REDIS_URL=redis://:hermes_dev_password@localhost:6379/0`

Quick Tests
- Postgres (inside container):
  ```bash
  docker exec -it hermes_postgres psql -U hermes -d hermes -c "SELECT 'IT WORKS!' AS status;"
  ```
- Redis (from host):
  ```bash
  redis-cli -a hermes_dev_password ping
  ```

Recreate Volumes (destructive)
- Use if auth settings changed or data is corrupted:
  ```bash
  docker compose down -v
  docker compose up -d
  ```

Local Dev Modes
- Docker DBs + Host Backend (Windows PowerShell):
  ```powershell
  $env:DATABASE_URL = 'postgresql+asyncpg://hermes:hermes@localhost:5432/hermes'
  $env:REDIS_URL = 'redis://:hermes_dev_password@localhost:6379/0'
  python -m uvicorn backend.main_v2:app --host 127.0.0.1 --port 8000 --log-level info
  ```
- Pure Host (SQLite) for maximum portability:
  ```powershell
  $env:DATABASE_URL = 'sqlite+aiosqlite:///c:/Users/aiden/hermes/hermes_dev.db'
  python -m uvicorn backend.main_v2:app --host 127.0.0.1 --port 8000 --log-level info
  ```

Troubleshooting
- Password auth failures from WSL2:
  - Verify Postgres is using `md5` (compose sets it); if migrating from old volumes, recreate with `down -v`.
  - Try connecting from Windows PowerShell instead of WSL2.
  - Use `host.docker.internal` instead of `localhost` from WSL2.
- Redis AUTH errors:
  - Ensure `REDIS_URL` includes `:password@` and DB index `/0`.
- Missing tables:
  - Run migrations: `alembic upgrade head`, or start the app which initializes schema in dev.

Backups (dev)
- Dump:
  ```bash
  docker exec hermes_postgres pg_dump -U hermes -d hermes > backup.sql
  ```
- Restore:
  ```bash
  docker exec -i hermes_postgres psql -U hermes -d hermes < backup.sql
  ```

Notes
- For production, use managed Postgres/Redis with automated backups and monitoring.
- Keep `DATABASE_URL`/`REDIS_URL` in env files or secret managers; never commit secrets.
