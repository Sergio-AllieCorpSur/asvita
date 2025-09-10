# app/features/storage/interfaces/web/restx.py
from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, current_app, send_file
from werkzeug.datastructures import FileStorage
from uuid import UUID

# services existentes
from app.features.storage.aplications.services.datarooms_services import (
    create_dataroom, list_datarooms, get_dataroom
)
from app.features.storage.aplications.services.folders_services import (
    create_folder, list_folder_contents, rename_folder, delete_folder_recursive,
)
from app.features.storage.aplications.services.storege_services import (
    upload_pdf, rename_file, delete_file, get_file_by_id, get_file_disk_path,
)

ns = Namespace(
    "storage",
    description="Datarooms, carpetas y archivos",
    path="/api/v1/storage",    # prefijo de todas las rutas de este namespace
)

# --- Modelos para Swagger (response/request) ---
dataroom_model = ns.model("Dataroom", {
    "id": fields.String,
    "name": fields.String,
    "description": fields.String,
})

create_dataroom_model = ns.model("CreateDataroom", {
    "name": fields.String(required=True),
    "description": fields.String,
})

folder_model = ns.model("Folder", {
    "id": fields.String,
    "name": fields.String,
    "path": fields.String,
    "parent_id": fields.String,
})

folder_contents_model = ns.model("FolderContents", {
    "folders": fields.List(fields.Nested(folder_model)),
    "files": fields.List(fields.Raw),   # simplificado
})

file_model = ns.model("File", {
    "id": fields.String,
    "name": fields.String,
    "original_filename": fields.String,
    "size_bytes": fields.Integer,
    "content_type": fields.String,
    "storage_path": fields.String,
    "version": fields.Integer,
})

upload_parser = ns.parser()
upload_parser.add_argument("file", type=FileStorage,
                           location="files", required=True, help="PDF a subir")

rename_parser = ns.model("Rename", {
    "name": fields.String(required=True),
})

# ---------- Health ----------


@ns.route("/ping")
class Ping(Resource):
    def get(self):
        """Healthcheck."""
        return {"status": "ok"}

# ---------- Datarooms ----------


@ns.route("/datarooms")
class DataroomList(Resource):
    @ns.marshal_list_with(dataroom_model)
    def get(self):
        """Lista datarooms."""
        return list_datarooms()

    @ns.expect(create_dataroom_model, validate=True)
    @ns.marshal_with(dataroom_model, code=201)
    def post(self):
        """Crea un dataroom."""
        data = request.get_json()
        dr = create_dataroom(
            name=data["name"], description=data.get("description"))
        return dr, 201


@ns.route("/datarooms/<uuid:dataroom_id>")
class DataroomDetail(Resource):
    @ns.marshal_with(dataroom_model)
    def get(self, dataroom_id: UUID):
        """Obtiene un dataroom por ID."""
        dr = get_dataroom(dataroom_id)
        if not dr:
            ns.abort(404, "Dataroom no encontrado")
        return dr

# ---------- Folders ----------


@ns.route("/datarooms/<uuid:dataroom_id>/folders")
class FolderCreate(Resource):
    @ns.expect(ns.model("CreateFolder", {
        "name": fields.String(required=True),
        "parent_id": fields.String,
    }), validate=True)
    @ns.marshal_with(folder_model, code=201)
    def post(self, dataroom_id: UUID):
        """Crea una carpeta (opcionalmente dentro de parent_id)."""
        data = request.get_json()
        f = create_folder(dataroom_id=dataroom_id, parent_id=data.get(
            "parent_id"), name=data["name"])
        return {"id": str(f.id), "name": f.name, "path": f.path, "parent_id": str(f.parent_id) if f.parent_id else None}, 201


@ns.route("/datarooms/<uuid:dataroom_id>/folders/<uuid:folder_id>/contents")
class FolderContents(Resource):
    @ns.marshal_with(folder_contents_model)
    def get(self, dataroom_id: UUID, folder_id: UUID):
        """Lista subcarpetas y archivos de una carpeta."""
        return list_folder_contents(dataroom_id=dataroom_id, folder_id=folder_id)


@ns.route("/folders/<uuid:folder_id>")
class FolderDetail(Resource):
    @ns.expect(rename_parser, validate=True)
    def patch(self, folder_id: UUID):
        """Renombra una carpeta."""
        data = request.get_json()
        f = rename_folder(folder_id=folder_id, new_name=data["name"])
        return {"id": str(f.id), "name": f.name, "path": f.path}

    def delete(self, folder_id: UUID):
        """Borra una carpeta (recursivo)."""
        delete_folder_recursive(folder_id=folder_id)
        return "", 204

# ---------- Files ----------
# define upload endpoint


upload_parser = ns.parser()
upload_parser.add_argument(
    "file",
    type=FileStorage,
    location="files",     # <-- importante
    required=True,
    help="PDF a subir",
)
# si quieres pasar nombre/desc opcionales en el mismo form:
upload_parser.add_argument("name", type=str, location="form")
upload_parser.add_argument("description", type=str, location="form")


@ns.route("/datarooms/<uuid:dataroom_id>/folders/<uuid:folder_id>/files")
class FileUpload(Resource):
    @ns.expect(upload_parser)
    # <-- esto hace que Swagger muestre el selector de archivos
    @ns.doc(consumes=["multipart/form-data"])
    @ns.marshal_with(file_model, code=201)
    def post(self, dataroom_id: UUID, folder_id: UUID):
        """Sube un PDF."""
        args = upload_parser.parse_args()
        saved = upload_pdf(
            dataroom_id=dataroom_id,
            folder_id=folder_id,
            file_storage=args["file"],  # nombre del campo: "file"
            upload_dir=current_app.config["UPLOAD_FOLDER"],
        )
        return saved, 201


@ns.route("/files/<uuid:file_id>")
class FileDetail(Resource):
    def get(self, file_id: UUID):
        """Devuelve el PDF (stream)."""
        f = get_file_by_id(file_id)
        path = get_file_disk_path(f)
        return send_file(path, mimetype=f.content_type, as_attachment=False, download_name=f.name)

    @ns.expect(rename_parser, validate=True)
    def patch(self, file_id: UUID):
        """Renombra un archivo."""
        data = request.get_json()
        f = rename_file(file_id=file_id, new_name=data["name"])
        return {"id": str(f.id), "name": f.name}

    def delete(self, file_id: UUID):
        """Borra un archivo."""
        delete_file(file_id)
        return "", 204
