"""Document backend flow.

Generated and uploaded documents are listed with role-based visibility.
Manual uploads are validated, stored, hashed, and recorded in the documents table.
"""

from sqlite3 import Connection

from fastapi import UploadFile

from core.models.document_model import DocumentReferenceType, DocumentUploadType
from core.schemas import UserContext
from core.services.documents_service import document_view, upload_document


def documents(conn: Connection, user: UserContext):
    return document_view(conn, user)


async def upload(
    conn: Connection,
    user: UserContext,
    *,
    file: UploadFile,
    document_type: DocumentUploadType,
    reference_type: DocumentReferenceType,
    reference_id: int,
):
    effective_reference_id = reference_id if reference_id > 0 else user.id
    return await upload_document(
        conn,
        user,
        file=file,
        document_type=document_type,
        reference_type=reference_type,
        reference_id=effective_reference_id,
    )

