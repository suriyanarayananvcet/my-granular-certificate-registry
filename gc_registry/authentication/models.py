from sqlmodel import Field

from gc_registry.authentication.schemas import ApiKeyBase, TokenRecordsBase


class TokenRecords(TokenRecordsBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ApiKey(ApiKeyBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
