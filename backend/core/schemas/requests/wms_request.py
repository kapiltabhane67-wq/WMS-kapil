from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


Role = Literal["ORG_ADMIN", "WAREHOUSE_MANAGER", "RECEIVER", "PICKER_PACKER", "SELLER_VIEWER"]
Code24 = Annotated[str, Field(min_length=2, max_length=24, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
Code40 = Annotated[str, Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
SkuCode = Annotated[str, Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
Barcode = Annotated[str, Field(min_length=4, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
ReferenceCode = Annotated[str, Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/#-]*$")]
Name120 = Annotated[str, Field(min_length=2, max_length=120)]
Password = Annotated[str, Field(min_length=8, max_length=120)]


class StrictRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


def validate_password_strength(value: str) -> str:
    if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
        raise ValueError("Password must contain at least one letter and one number")
    return value


def normalize_legacy_email(value):
    if not isinstance(value, str):
        return value
    clean_value = value.strip().lower()
    if clean_value.endswith("@whitfield.local"):
        return clean_value.replace("@whitfield.local", "@whitfieldwms.com")
    if clean_value.endswith("@client.local"):
        return clean_value.replace("@client.local", "@client.example.com")
    return clean_value


class LoginIn(StrictRequest):
    email: EmailStr
    password: str = Field(min_length=1, max_length=120)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_old_demo_email(cls, value):
        return normalize_legacy_email(value)


class ReceiptItemIn(StrictRequest):
    sku: SkuCode
    bin_code: Code40
    good_qty: int = Field(default=0, ge=0, le=100000)
    damaged_qty: int = Field(default=0, ge=0, le=100000)


class ReceiptCompleteIn(StrictRequest):
    seller_code: Code24
    warehouse_code: Code24
    receipt_ref: ReferenceCode
    items: list[ReceiptItemIn] = Field(min_length=1, max_length=200)


class OrderItemIn(StrictRequest):
    sku: SkuCode
    quantity: int = Field(gt=0, le=100000)


class OrderImportIn(StrictRequest):
    seller_code: Code24
    marketplace: Code40
    external_order_id: ReferenceCode
    preferred_warehouse_code: Code24 | None = None
    ship_to_name: Name120
    ship_to_city: Annotated[str, Field(min_length=2, max_length=80)]
    items: list[OrderItemIn] = Field(min_length=1, max_length=200)

    @field_validator("preferred_warehouse_code", mode="before")
    @classmethod
    def empty_preferred_warehouse_to_none(cls, value):
        return None if value == "" else value


class PickScanIn(StrictRequest):
    sku: SkuCode
    bin_code: Code40
    quantity: int = Field(gt=0, le=100000)


class PackIn(StrictRequest):
    carrier: Code40 = "UPS"
    weight_oz: float = Field(gt=0, le=10000)
    length_in: float = Field(gt=0, le=200)
    width_in: float = Field(gt=0, le=200)
    height_in: float = Field(gt=0, le=200)


class InventoryAdjustmentIn(StrictRequest):
    seller_code: Code24
    warehouse_code: Code24
    sku: SkuCode
    bin_code: Code40
    quantity_delta: int
    reason: Annotated[str, Field(min_length=5, max_length=240)]


class SellerCreateIn(StrictRequest):
    code: Code24
    name: Name120


class WarehouseCreateIn(StrictRequest):
    code: Code24
    name: Name120
    city: Annotated[str, Field(min_length=2, max_length=80)]
    state: Annotated[str, Field(min_length=2, max_length=40)]


class BinCreateIn(StrictRequest):
    warehouse_code: Code24
    code: Code40
    zone: str = Field(min_length=1, max_length=40)
    rack: str = Field(min_length=1, max_length=40)
    shelf: str = Field(min_length=1, max_length=40)


class ProductCreateIn(StrictRequest):
    seller_code: Code24
    sku: SkuCode
    upc: Barcode
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)


class UserCreateIn(StrictRequest):
    email: EmailStr
    full_name: Name120
    role: Role
    password: Password
    seller_code: Code24 | None = None
    warehouse_codes: list[Code24] = Field(default_factory=list, max_length=20)

    @field_validator("seller_code", mode="before")
    @classmethod
    def empty_seller_to_none(cls, value):
        return None if value == "" else value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_old_demo_email(cls, value):
        return normalize_legacy_email(value)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return validate_password_strength(value)


class SellerUpdateIn(StrictRequest):
    name: Name120


class WarehouseUpdateIn(StrictRequest):
    name: Name120
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=40)


class BinUpdateIn(StrictRequest):
    zone: str = Field(min_length=1, max_length=40)
    rack: str = Field(min_length=1, max_length=40)
    shelf: str = Field(min_length=1, max_length=40)


class ProductUpdateIn(StrictRequest):
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    upc: Barcode


class UserUpdateIn(StrictRequest):
    full_name: Name120
    role: Role
    seller_code: Code24 | None = None
    warehouse_codes: list[Code24] = Field(default_factory=list, max_length=20)

    @field_validator("seller_code", mode="before")
    @classmethod
    def empty_seller_to_none(cls, value):
        return None if value == "" else value


class UserPasswordResetIn(StrictRequest):
    password: Password

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        return validate_password_strength(value)


class UserActiveIn(StrictRequest):
    active: bool


class SettingsUpdateIn(StrictRequest):
    organization_name: str = Field(default="", max_length=160)
    default_carrier: str = Field(default="", max_length=80)
    low_stock_threshold: int = Field(default=5, ge=0)
    marketplace_provider: str = Field(default="", max_length=80)
    marketplace_status: str = Field(default="NOT_CONFIGURED", max_length=80)
    carrier_provider: str = Field(default="", max_length=80)
    carrier_status: str = Field(default="NOT_CONFIGURED", max_length=80)
    ai_document_extraction: bool = False
    ai_voice_commands: bool = False
    ai_rag_assistant: bool = False
    policy_require_receipt_reference: bool = True
    policy_require_pick_scan: bool = True
