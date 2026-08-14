from pydantic import BaseModel, Field

from core.schemas.requests.wms_request import Role


class UserContext(BaseModel):
    id: int
    email: str
    full_name: str
    role: Role
    seller_id: int | None = None
    warehouse_ids: list[int] = Field(default_factory=list)


class LoginOut(BaseModel):
    access_token: str
    token_type: str
    user: UserContext
