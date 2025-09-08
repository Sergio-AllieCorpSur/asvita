from sqlalchemy import and_
from app.extensions import db
from app.database.models.dataroom import Dataroom
from app.database.models.folder import Folder
from app.database.models.file import File
from uuid import UUID


def _sibling_name_exists(dataroom_id, parent_id, name) -> bool:
    q = Folder.query.filter(
        and_(Folder.dataroom_id == dataroom_id,
             Folder.parent_id == parent_id, Folder.name == name)
    )
    return db.session.query(q.exists()).scalar()


def _unique_name(dataroom_id, parent_id, desired: str) -> str:
    if not _sibling_name_exists(dataroom_id, parent_id, desired):
        return desired
    base, dot, ext = desired.partition(".")  # por si usas carpetas con puntos
    n = 2
    while True:
        candidate = f"{base} ({n}){dot}{ext}" if dot else f"{base} ({n})"
        if not _sibling_name_exists(dataroom_id, parent_id, candidate):
            return candidate
        n += 1


def create_folder(dataroom_id: UUID, parent_id: str | None, name: str) -> Folder:
    dr = Dataroom.query.get_or_404(dataroom_id)
    parent = Folder.query.get(parent_id) if parent_id else None
    if parent and parent.dataroom_id != dr.id:
        raise ValueError("Parent folder does not belong to dataroom")

    name = _unique_name(dr.id, parent.id if parent else None, name)
    path = f"{(parent.path + '/') if parent else ''}{name}"
    folder = Folder(name=name, dataroom_id=dr.id,
                    parent_id=parent.id if parent else None, path=path)
    db.session.add(folder)
    db.session.commit()
    return folder


def list_folder_contents(dataroom_id: UUID, folder_id: UUID) -> dict:
    Folder.query.filter_by(
        id=folder_id, dataroom_id=dataroom_id).first_or_404()
    subfolders = Folder.query.filter_by(
        parent_id=folder_id).order_by(Folder.name).all()
    files = File.query.filter_by(folder_id=folder_id).order_by(File.name).all()
    return {
        "folders": [{"id": str(f.id), "name": f.name, "path": f.path} for f in subfolders],
        "files": [{"id": str(x.id), "name": x.name, "size_bytes": x.size_bytes, "version": x.version} for x in files],
    }


def rename_folder(folder_id: UUID, new_name: str) -> Folder:
    f = Folder.query.get_or_404(folder_id)
    # asegura nombre único entre hermanos
    new_name = _unique_name(f.dataroom_id, f.parent_id, new_name)

    old_path = f.path
    parent_path = f.path.rsplit("/", 1)[0] if "/" in f.path else ""
    new_path = f"{parent_path + '/' if parent_path else ''}{new_name}"
    f.name = new_name
    f.path = new_path

    # actualiza paths hijos por prefijo
    prefix = old_path + "/"
    descendants = Folder.query.filter(Folder.path.startswith(prefix)).all()
    for d in descendants:
        d.path = new_path + d.path[len(old_path):]
    db.session.commit()
    return f


def delete_folder_recursive(folder_id: UUID) -> None:
    f = Folder.query.get_or_404(folder_id)
    db.session.delete(f)  # ondelete + cascade se encargan del resto
    db.session.commit()
