import os
import hashlib
import uuid
from werkzeug.utils import secure_filename
from app.extensions import db
from app.database.models.file import File
from app.database.models.folder import Folder
from app.database.models.dataroom import Dataroom
from uuid import UUID


def _is_pdf(filename: str, content_type: str | None) -> bool:
    return (filename.lower().endswith(".pdf")) or (content_type and content_type.startswith("application/pdf"))


def _unique_file_name(folder_id, desired: str) -> str:
    exists = db.session.query(File.query.filter_by(
        folder_id=folder_id, name=desired).exists()).scalar()
    if not exists:
        return desired
    base, dot, ext = desired.rpartition(".")
    base = base if dot else desired
    ext = ext if dot else ""
    n = 2
    while True:
        candidate = f"{base} ({n}).{ext}" if ext else f"{base} ({n})"
        exists = db.session.query(File.query.filter_by(
            folder_id=folder_id, name=candidate).exists()).scalar()
        if not exists:
            return candidate
        n += 1


def _compute_sha256(stream) -> str:
    sha = hashlib.sha256()
    for chunk in iter(lambda: stream.read(8192), b""):
        sha.update(chunk)
    stream.seek(0)
    return sha.hexdigest()


def upload_pdf(dataroom_id: UUID, folder_id: UUID, file_storage, upload_dir: str) -> File:
    dr = Dataroom.query.get_or_404(dataroom_id)
    folder = Folder.query.get_or_404(folder_id)
    if folder.dataroom_id != dr.id:
        raise ValueError("Folder does not belong to dataroom")

    filename = secure_filename(file_storage.filename or "")
    if not filename:
        raise ValueError("Empty filename")
    if not _is_pdf(filename, file_storage.mimetype):
        raise ValueError("Only PDF files are allowed")

    # calcula checksum para info/dedupe opcional
    checksum = _compute_sha256(file_storage.stream)

    # genera ruta en disco: uploads/<dataroom>/<folder>/<uuid>.pdf
    ext = ".pdf" if not filename.lower().endswith(".pdf") else ""
    disk_name = f"{uuid.uuid4().hex}{ext}"
    dir_path = os.path.join(upload_dir, str(dr.id), str(folder.id))
    os.makedirs(dir_path, exist_ok=True)
    disk_path = os.path.join(dir_path, disk_name)
    file_storage.save(disk_path)
    size_bytes = os.path.getsize(disk_path)

    # nombre visible único por carpeta
    visible_name = _unique_file_name(folder.id, filename)

    entity = File(
        name=visible_name,
        original_filename=filename,
        content_type="application/pdf",
        size_bytes=size_bytes,
        storage_path=disk_path,
        checksum_sha256=checksum,
        version=1,
        folder_id=folder.id,
        dataroom_id=dr.id,
    )
    db.session.add(entity)
    db.session.commit()
    return entity


def get_file_by_id(file_id: UUID) -> File:
    return File.query.get_or_404(file_id)


def get_file_disk_path(file: File) -> str:
    return file.storage_path


def rename_file(file_id: UUID, new_name: str) -> File:
    f = File.query.get_or_404(file_id)
    new_name = secure_filename(new_name).replace("_", " ").strip()
    if not new_name:
        raise ValueError("Invalid name")
    new_name = _unique_file_name(f.folder_id, new_name)
    f.name = new_name
    db.session.commit()
    return f


def delete_file(file_id: UUID) -> None:
    f = File.query.get_or_404(file_id)
    try:
        if f.storage_path and os.path.exists(f.storage_path):
            os.remove(f.storage_path)
    except Exception:
        # si falla borrar archivo físico, igual borramos metadata (decisión de negocio)
        pass
    db.session.delete(f)
    db.session.commit()
