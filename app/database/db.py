import os
from urllib.parse import urlparse, quote_plus

# Carga .env en local (no sobrescribe vars ya presentes en el entorno)
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass


def _normalize_url(url: str) -> str:
    """
    Normaliza a formato válido para SQLAlchemy/psycopg2:
    - quita 'jdbc:' si viene de DBeaver,
    - 'postgres://' -> 'postgresql+psycopg2://',
    - añade driver psycopg2 si falta.
    """
    if not url:
        return url
    if url.startswith("jdbc:"):
        url = url.replace("jdbc:", "", 1)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _compose_from_parts() -> str | None:
    """
    Construye la URL a partir de piezas del .env:
    - DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT
    - Si no hay DB_HOST, intenta parsear DB_CONNECTION_NAME (jdbc:postgresql://host:port/)
    - Añade ?sslmode= si existe DB_SSLMODE
    """
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "")
    name = os.getenv("DB_NAME")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT") or "5432"
    sslmode = os.getenv("DB_SSLMODE")

    if not host:
        conn = os.getenv("DB_CONNECTION_NAME", "")
        if conn:
            conn = conn.replace("jdbc:", "", 1)
            parsed = urlparse(conn)
            host = parsed.hostname
            port = str(parsed.port or port)

    if not (user and name and host):
        return None

    user_enc = quote_plus(user)
    # si password está vacío, construimos sin ':'
    auth = f"{user_enc}:{quote_plus(password)}@" if password != "" else f"{user_enc}@"

    url = f"postgresql+psycopg2://{auth}{host}:{port}/{name}"
    if sslmode:
        sep = "?" if "?" not in url else "&"
        url = f"{url}{sep}sslmode={sslmode}"
    return url


def get_database_url() -> str:
    """
    Prioridad:
    1) DATABASE_INTERNAL_URL (Render - interno)
    2) DATABASE_URL (Render - externo o interno)
    3) Partes del .env (DB_*) o DB_CONNECTION_NAME
    4) Fallback local
    """
    url = os.getenv("DATABASE_INTERNAL_URL") or os.getenv("DATABASE_URL")
    if url:
        return _normalize_url(url)

    url = _compose_from_parts()
    if url:
        return _normalize_url(url)

    return "postgresql+psycopg2://app:app@localhost:5432/dataroom"
