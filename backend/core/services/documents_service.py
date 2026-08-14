from sqlite3 import Connection
from pathlib import Path
import hashlib
import re
import secrets

from fastapi import HTTPException, UploadFile

from core.database.connection import database_file
from core.database.connection import rows_to_dicts
from core.models.document_model import (
    ALLOWED_UPLOAD_CONTENT_TYPES,
    ALLOWED_UPLOAD_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    DocumentReferenceType,
    DocumentUploadType,
)
from core.schemas import UserContext


def _safe_file_name(file_name: str | None) -> str:
    clean_name = Path(file_name or "uploaded-document").name.strip()
    clean_name = re.sub(r"[^A-Za-z0-9_. -]", "_", clean_name)
    return clean_name[:140] or "uploaded-document"


def _upload_dir() -> Path:
    upload_path = database_file().parent / "uploads"
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def document_view(conn: Connection, user: UserContext):
    where = ""
    params: list[object] = []
    if user.role == "SELLER_VIEWER":
        where = """
        WHERE EXISTS (
            SELECT 1 FROM sales_orders so
            WHERE so.id = d.reference_id AND d.reference_type = 'sales_order' AND so.seller_id = ?
        )
        OR EXISTS (
            SELECT 1 FROM shipments sh
            JOIN sales_orders so ON so.id = sh.order_id
            WHERE sh.id = d.reference_id AND d.reference_type = 'shipment' AND so.seller_id = ?
        )
        OR EXISTS (
            SELECT 1 FROM inbound_receipts ir
            WHERE ir.id = d.reference_id AND d.reference_type = 'inbound_receipt' AND ir.seller_id = ?
        )
        OR d.uploaded_by = ?
        """
        params.extend([user.seller_id, user.seller_id, user.seller_id, user.id])
    elif user.role != "ORG_ADMIN":
        placeholders = ",".join("?" for _ in user.warehouse_ids)
        where = f"""
        WHERE EXISTS (
            SELECT 1 FROM sales_orders so
            WHERE so.id = d.reference_id AND d.reference_type = 'sales_order'
              AND so.warehouse_id IN ({placeholders})
        )
        OR EXISTS (
            SELECT 1 FROM shipments sh
            JOIN sales_orders so ON so.id = sh.order_id
            WHERE sh.id = d.reference_id AND d.reference_type = 'shipment'
              AND so.warehouse_id IN ({placeholders})
        )
        OR EXISTS (
            SELECT 1 FROM inbound_receipts ir
            WHERE ir.id = d.reference_id AND d.reference_type = 'inbound_receipt'
              AND ir.warehouse_id IN ({placeholders})
        )
        OR d.uploaded_by = ?
        """
        params.extend(user.warehouse_ids)
        params.extend(user.warehouse_ids)
        params.extend(user.warehouse_ids)
        params.append(user.id)
    rows = conn.execute(
        f"""
        SELECT
            d.id,
            d.document_type,
            d.reference_type,
            d.reference_id,
            d.file_name,
            d.status,
            d.original_file_name,
            d.content_type,
            d.file_size,
            d.sha256,
            d.created_at
        FROM documents d
        {where}
        ORDER BY d.id DESC
        LIMIT 100
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)


async def upload_document(
    conn: Connection,
    user: UserContext,
    *,
    file: UploadFile,
    document_type: DocumentUploadType,
    reference_type: DocumentReferenceType,
    reference_id: int,
):
    safe_name = _safe_file_name(file.filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Unsupported file extension")
    if file.content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported file type")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum allowed size is 10 MB")

    file_hash = hashlib.sha256(content).hexdigest()
    storage_name = f"{secrets.token_hex(16)}-{safe_name}"
    storage_path = _upload_dir() / storage_name
    storage_path.write_bytes(content)

    document_id = conn.execute(
        """
        INSERT INTO documents (
            document_type,
            reference_type,
            reference_id,
            file_name,
            status,
            storage_path,
            original_file_name,
            content_type,
            file_size,
            sha256,
            uploaded_by
        )
        VALUES (?, ?, ?, ?, 'UPLOADED', ?, ?, ?, ?, ?, ?)
        """,
        (
            document_type.value,
            reference_type.value,
            reference_id,
            safe_name,
            str(storage_path.relative_to(database_file().parent)),
            safe_name,
            file.content_type,
            len(content),
            file_hash,
            user.id,
        ),
    ).lastrowid
    return {
        "id": document_id,
        "document_type": document_type.value,
        "reference_type": reference_type.value,
        "reference_id": reference_id,
        "file_name": safe_name,
        "status": "UPLOADED",
        "content_type": file.content_type,
        "file_size": len(content),
        "sha256": file_hash,
    }

