from datetime import datetime, timedelta

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from gc_registry.authentication import services
from gc_registry.authentication.models import TokenRecords
from gc_registry.authentication.schemas import (
    ApiKeyInfo,
    ApiKeyRequest,
    ApiKeyResponse,
    LoginRequest,
    Token,
)
from gc_registry.authentication.services import (
    create_api_key_for_user,
    deactivate_api_key,
    get_current_user,
    get_user_api_keys,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.settings import settings as st
from gc_registry.user.models import User

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    json_data: LoginRequest | None = None,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Login for access token.

    Accepts both OAuth2PasswordRequestForm and JSON request formats.

    OAuth2PasswordRequestForm requires the syntax "username" even though in practice
    we are using the user's email address.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): The form data from the login request.
        json_data (LoginRequest, optional): The JSON data from the login request.
        write_session (Session): The database session to write to.
        read_session (Session): The database session to read from.
        esdb_client (EventStoreDBClient): The EventStoreDB client.

    Returns:
        Token: The access token.

    Raises:
        HTTPException: If invalid credentials are provided.
    """
    # Try to get credentials from JSON first, fall back to form data
    try:
        if json_data is not None:
            username = json_data.username
            password = json_data.password
        else:
            username = form_data.username
            password = form_data.password
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Invalid request format. Provide either valid JSON or form data.",
        )

    user = services.authenticate_user(username, password, read_session)

    access_token_expires = timedelta(minutes=st.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = services.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    token_record = TokenRecords(
        email=user.email,
        token=access_token,
        expires=datetime.now() + access_token_expires,
    )
    try:
        TokenRecords.create(token_record, write_session, read_session, esdb_client)
    except Exception:
        # Skip token record creation if database fails (for local testing)
        pass

    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}


@router.post("/api-key", response_model=ApiKeyResponse)
async def create_api_key(
    api_key_request: ApiKeyRequest,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Create a new API key for the authenticated user.

    Once a user has authenticated via the login endpoint with a username and password,
    they can create an API key to use for API requests. As part of the request, the user
    can specify an expiry date for the API key. If no expiry date is requested, then a default
    expiry date is used, defined in the registry settings file.

    The user can then use the API key in the request header in place of a username and password,
    using the following format:

    Authorization: API Key <key>

    The user must also provide a descriptive name for the API key. This name is used to
    identify the API key in the API key list endpoint. The user may also request to view
    all of their active API keys through the user/api-keys endpoint. The user can also
    deactivate an API key by reference to the API key ID through the user/api-key/<api_key_id> endpoint.

    Args:
        api_key_request (ApiKeyRequest): The API key creation request.
        current_user (User): The authenticated user.
        write_session (Session): The database session to write to.
        read_session (Session): The database session to read from.
        esdb_client (EventStoreDBClient): The EventStoreDB client.

    Returns:
        ApiKeyResponse: The created API key information including the key value.

    Note:
        The API key value is only returned once during creation. Store it securely.
    """
    if current_user.id is None:
        raise HTTPException(status_code=404, detail="User not found")

    api_key, api_key_record = create_api_key_for_user(
        user_id=current_user.id,
        name=api_key_request.name,
        expires_days=api_key_request.expires_days,
        write_session=write_session,
        read_session=read_session,
        esdb_client=esdb_client,
    )

    if api_key_record is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to create API key",
        )

    return ApiKeyResponse(
        id=api_key_record.id,  # type: ignore
        name=api_key_record.name,
        key=api_key,  # This is the only time the plain key is returned
        expires=api_key_record.expires,
        created_at=api_key_record.created_at,
    )


@router.get("/api-keys", response_model=list[ApiKeyInfo])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """List all API keys for the authenticated user.

    Args:
        current_user (User): The authenticated user.
        read_session (Session): The database session to read from.

    Returns:
        list[ApiKeyInfo]: List of the user's API keys (without the key values).
    """
    if current_user.id is None:
        raise HTTPException(status_code=404, detail="User not found")

    api_keys = get_user_api_keys(current_user.id, read_session)

    return [
        ApiKeyInfo(
            id=key.id,  # type: ignore
            name=key.name,
            expires=key.expires,
            created_at=key.created_at,
            is_active=key.is_active and key.expires > datetime.now(),
        )
        for key in api_keys
    ]


@router.delete("/api-key/{api_key_id}")
async def deactivate_api_key_endpoint(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Deactivate an API key, either for the current user or for another user if called by an Admin.

    Args:
        api_key_id (int): The ID of the API key to deactivate.
        current_user (User): The authenticated user.
        write_session (Session): The database session to write to.
        read_session (Session): The database session to read from.
        esdb_client (EventStoreDBClient): The EventStoreDB client.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If the API key is not found.
    """
    if current_user.id is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = current_user.id if current_user.role != UserRoles.ADMIN else None

    updated_key = deactivate_api_key(
        api_key_id=api_key_id,
        user_id=user_id,
        write_session=write_session,
        read_session=read_session,
        esdb_client=esdb_client,
    )

    if not updated_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found, or you don't have permission to deactivate it",
        )

    return {"message": "API key deactivated successfully"}
