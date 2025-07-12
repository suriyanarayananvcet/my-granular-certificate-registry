import datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from gc_registry import utils


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(SQLModel):
    access_token: str
    token_type: str
    user_id: int


class TokenRecordsBase(utils.ActiveRecord):
    email: str = Field(nullable=False)
    token: str
    expires: datetime.datetime = Field(
        default=datetime.datetime.now(tz=datetime.timezone.utc)
        + datetime.timedelta(minutes=15),
    )


class ApiKeyRequest(BaseModel):
    name: str = Field(description="A descriptive name for the API key")
    expires_days: int | None = Field(
        default=None,
        description="Number of days until the API key expires. If not provided, uses system default.",
    )


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key: str = Field(
        description="The API key value (only returned once during creation)"
    )
    expires: datetime.datetime
    created_at: datetime.datetime


class ApiKeyInfo(BaseModel):
    id: int
    name: str
    expires: datetime.datetime
    created_at: datetime.datetime
    is_active: bool


class ApiKeyBase(utils.ActiveRecord):
    user_id: int = Field(foreign_key="registry_user.id", nullable=False)
    name: str = Field(nullable=False, description="A descriptive name for the API key")
    key_hash: str = Field(nullable=False, description="Hashed version of the API key")
    expires: datetime.datetime = Field(nullable=False)
    is_active: bool = Field(default=True)


class APIKeyUpdate(BaseModel):
    name: str | None = None
    expires: datetime.datetime | None = None
    is_active: bool | None = None
