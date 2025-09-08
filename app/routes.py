# app/routes.py
from flask_restx import Api

api = Api(
    title="Asvita Dataroom API",
    version="1.0.0",
    doc="/api/docs",            # Swagger UI
    prefix="",                  # dejamos paths completos en cada namespace
)


def register_routes(app):
    api.init_app(app)

    # Importa y registra namespaces por feature (como routers en FastAPI)
    from app.features.storage.interfaces.web.restx import ns as storage_ns
    api.add_namespace(storage_ns)    # path lo define el namespace
