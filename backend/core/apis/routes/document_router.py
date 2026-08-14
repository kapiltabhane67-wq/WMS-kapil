from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from core.apis.dependencies import current_user
from core.database.connection import db_connection
from core.models.document_model import DocumentReferenceType, DocumentUploadType
from core.schemas import UserContext
from core.services.wms_service import document_view, upload_document


router = APIRouter()


@router.get("/v1/documents")
def documents(user: UserContext = Depends(current_user)):
    with db_connection() as conn:
        return document_view(conn, user)


@router.post("/v1/documents/upload")
async def upload(
    document_type: Annotated[DocumentUploadType, Form()],
    reference_type: Annotated[DocumentReferenceType, Form()] = DocumentReferenceType.MANUAL_UPLOAD,
    reference_id: Annotated[int, Form(ge=0)] = 0,
    file: UploadFile = File(...),
    user: UserContext = Depends(current_user),
):
    with db_connection() as conn:
        effective_reference_id = reference_id if reference_id > 0 else user.id
        return await upload_document(
            conn,
            user,
            file=file,
            document_type=document_type,
            reference_type=reference_type,
            reference_id=effective_reference_id,
        )
