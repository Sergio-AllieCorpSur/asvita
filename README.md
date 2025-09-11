# ACIL Storage API

REST API to manage **Datarooms**, **Folders**, and **Files**. It exposes endpoints to list/create entities, upload/download/delete files, and persists state with **SQLAlchemy** and **Alembic**.

- **Framework:** Flask + Flask-RESTX (Swagger/OpenAPI)
- **ORM:** SQLAlchemy 2.x
- **Migrations:** Alembic
- **Deploy:** Render via Docker
- **File storage:** `instance/uploads` (configurable)

> Note: Large directories like `asyncio`, `werkzeug`, etc. in your tree are **environment/dependencies**, not application source.

---

## 📁 Project Structure (relevant)

├─ app/
│ ├─ init.py # create_app(), extensions, blueprints
│ ├─ extensions.py # DB, RESTX, CORS, etc.
│ ├─ routes.py # namespace/route registration
│ ├─ database/
│ │ ├─ db.py # engine/session helpers
│ │ └─ models/ # SQLAlchemy models
│ │ ├─ dataroom.py
│ │ ├─ folder.py
│ │ ├─ file.py
│ │ ├─ user.py
│ │ └─ ...
│ └─ features/
│ └─ storage/
│ ├─ aplications/services/ # domain services
│ │ ├─ datarooms_services.py
│ │ ├─ folders_services.py
│ │ └─ storege_services.py
│ └─ interfaces/web/
│ └─ restx.py # Flask-RESTX resources/namespaces
│
├─ instance/
│ └─ uploads/ # default file storage
│
├─ migrations/ # Alembic (env.py, versions/)
│
└─ manage.py / wsgi.py # (if present) CLI/WSGI entrypoints


---

## 🔌 Environment Variables

Configure the service via env vars (use a local `.env` in dev):

| Variable             | Example / Default                           | Purpose                                  |
|----------------------|---------------------------------------------|------------------------------------------|
| `FLASK_ENV`          | `development`                               | Run mode                                  |
| `SECRET_KEY`         | `change-me`                                 | Flask secret                              |
| `DATABASE_URL`       | `postgresql+psycopg2://user:pass@host/db`   | Database URL                              |
| `UPLOAD_FOLDER`      | `instance/uploads`                          | File storage directory                    |
| `MAX_CONTENT_LENGTH` | `104857600` (100 MB)                        | Upload size limit (optional)              |
| `CORS_ORIGINS`       | `*` or `https://your-frontend.app`          | Allowed origins (CORS)                    |
| `PORT`               | `8000`                                      | Exposed port (Render injects `$PORT`)     |

**.env example**
```env
FLASK_ENV=development
SECRET_KEY=change-me
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/acil_storage
UPLOAD_FOLDER=instance/uploads
CORS_ORIGINS=*
MAX_CONTENT_LENGTH=104857600
PORT=8000

▶️ Run Locally

Requirements: Python 3.11+ (or 3.12/3.13), pip, virtualenv.

# 1) Create & activate venv
python -m venv .venv
source .venv/bin/activate                # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Apply migrations
alembic upgrade head

# 4) Run dev server
flask --app app run --port 8000          # or: python manage.py run
# If you use an app factory:
# flask --app "app:create_app()" run --port 8000

🗃️ Database Migrations (Alembic)
# create new migration from models
alembic revision --autogenerate -m "add something"

# apply latest
alembic upgrade head

# rollback one step
alembic downgrade -1

Datarooms
Ensure migrations/env.py loads your models’ target_metadata.
GET    /api/v1/storage/datarooms
POST   /api/v1/storage/datarooms
GET    /api/v1/storage/datarooms/{dataroom_id}
PUT    /api/v1/storage/datarooms/{dataroom_id}
DELETE /api/v1/storage/datarooms/{dataroom_id}

Folders
GET    /api/v1/storage/datarooms/{dataroom_id}/folders
POST   /api/v1/storage/datarooms/{dataroom_id}/folders   ; optional parent_id
PATCH  /api/v1/storage/folders/{folder_id}               ; rename
DELETE /api/v1/storage/folders/{folder_id}               ; recursive delete

Files
GET    /api/v1/storage/folders/{folder_id}/files
POST   /api/v1/storage/datarooms/{dataroom_id}/folders/{folder_id}/files
       Content-Type: multipart/form-data
       Body: file=<binary>, name=<string>, [description=<string>]

GET    /api/v1/storage/files/{file_id}                   ; stream/download
DELETE /api/v1/storage/files/{file_id}

Example response (GET /folders/{folder_id}/files)

[
  {
    "id": "cde1f8e0-5a1f-4642-8150-c50ceeb0c6ce",
    "name": "extracto_cuenta202409 (2).pdf",
    "original_filename": "extracto_cuenta202409.pdf",
    "size_bytes": 139246,
    "content_type": "application/pdf",
    "storage_path": "...",
    "version": 1
  }
]

Quick upload test (curl)
curl -X POST \
  -F "file=@/path/to/file.pdf" \
  -F "name=file.pdf" \
  http://localhost:8000/api/v1/storage/datarooms/<d>/folders/<f>/files

🐳 Docker (Production)

Multi-stage image with Gunicorn:
# --- build stage ---
FROM python:3.12-slim AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# --- runtime stage ---
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PORT=8000 \
    UPLOAD_FOLDER=/app/instance/uploads
COPY --from=build /app /app
RUN mkdir -p /app/instance/uploads
EXPOSE 8000
# If you use an app factory in app/__init__.py:
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:${PORT}", "app:create_app()"]
# If you have wsgi.py exposing 'app':
# CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:${PORT}", "wsgi:app"]

Run with Docker locally

docker build -t acil-storage-api .
docker run --env-file .env -p 8000:8000 acil-storage-api

🚀 Deploy on Render (Docker)

New → Web Service → Build from repo, pick your repo.

Runtime: Docker (Render will detect your Dockerfile).

Env vars: set DATABASE_URL, SECRET_KEY, UPLOAD_FOLDER, etc.

Port: Render injects $PORT; Gunicorn binds to it.

Deploy.

If using local disk for uploads, remember Render’s ephemeral filesystem resets on deploys. Use a persistent disk or external blob storage (e.g., S3/GCS) for production.

🔐 CORS & Security

Allow your frontend origin via CORS_ORIGINS.

Set a sensible MAX_CONTENT_LENGTH for uploads.

Keep secrets in environment (don’t commit .env).

Add authentication/authorization (JWT/Session) as needed (not included here).

🔧 Troubleshooting

Swagger not showing endpoints: ensure restx.py namespaces are registered in routes.py and loaded in create_app().

400/415 on uploads: send multipart/form-data and the file field; don’t manually set Content-Type when using FormData.

CORS blocked: configure CORS_ORIGINS (exact frontend origin recommended in production).

Upload path errors: confirm UPLOAD_FOLDER exists and is writable inside the container.

DB connection issues on Render: verify DATABASE_URL and any network/allowlist constraints.

📝 Makefile (optional)

run:
\tflask --app app run --port 8000

migrate:
\talembic revision --autogenerate -m "$(m)"

upgrade:
\talembic upgrade head

docker-build:
\tdocker build -t acil-storage-api .

docker-run:
\tdocker run --env-file .env -p 8000:8000 acil-storage-api

📄 License

This project is distributed under your organization’s chosen license (e.g., MIT). Update this section as needed.

Want me to add a **Table of Contents** and a small **Render badge** at the top too?


