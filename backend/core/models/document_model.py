from enum import StrEnum


class DocumentUploadType(StrEnum):
    RECEIPT = "RECEIPT"
    INVOICE = "INVOICE"
    SHIPPING_LABEL = "SHIPPING_LABEL"
    PACKING_SLIP = "PACKING_SLIP"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    RETURN_DOCUMENT = "RETURN_DOCUMENT"
    OTHER = "OTHER"


class DocumentReferenceType(StrEnum):
    MANUAL_UPLOAD = "manual_upload"
    INBOUND_RECEIPT = "inbound_receipt"
    SALES_ORDER = "sales_order"
    SHIPMENT = "shipment"


ALLOWED_UPLOAD_CONTENT_TYPES = {
    "application/pdf",
    "text/csv",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
}

ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".csv",
    ".txt",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
