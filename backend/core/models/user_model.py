from dataclasses import dataclass
from enum import StrEnum


class UserRole(StrEnum):
    ORG_ADMIN = "ORG_ADMIN"
    WAREHOUSE_MANAGER = "WAREHOUSE_MANAGER"
    RECEIVER = "RECEIVER"
    PICKER_PACKER = "PICKER_PACKER"
    SELLER_VIEWER = "SELLER_VIEWER"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


WAREHOUSE_ROLES = {
    UserRole.WAREHOUSE_MANAGER.value,
    UserRole.RECEIVER.value,
    UserRole.PICKER_PACKER.value,
}


@dataclass(frozen=True)
class UserRecord:
    id: int
    email: str
    full_name: str
    role: str
    seller_id: int | None
    active: int
