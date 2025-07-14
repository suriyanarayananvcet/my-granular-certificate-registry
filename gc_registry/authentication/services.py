import datetime
import secrets
from datetime import timedelta
from typing import cast

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, and_, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.authentication.models import ApiKey
from gc_registry.authentication.schemas import APIKeyUpdate
from gc_registry.core.database import db
from gc_registry.core.models.base import UserRoles
from gc_registry.settings import settings as st
from gc_registry.user.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


JWT_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired JWT access-token",
    headers={"WWW-Authenticate": "Bearer"},
)


API_KEY_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired API key",
    headers={"WWW-Authenticate": "API Key"},
)


MISSING_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify that the provided password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash the provided password."""
    return pwd_context.hash(password)


def get_user(email: str, read_session: Session) -> User | None:
    """Retrieve a User from the database matching the provided name.

    Args:
        email (str): The email address of the User to retrieve.
        read_session (Session): The database session to read from.

    Returns:
        user: The User object matching the provided name.

    Raises:
        HTTPException: If the user does not exist, return a 404.

    """
    user = read_session.exec(select(User).where(User.email == email)).first()

    return user


def authenticate_user(email: str, password: str, read_session: Session) -> User:
    """Authenticate a user by verifying their password.

    Args:
        email (str): The email address of the User to authenticate.
        password (str): The password to verify.
        read_session (Session): The database session to read from.

    Returns:
        user: The User object matching the provided name.

    Raises:
        HTTPException: If the user's password is incorrect, return a 401.

    """
    user = get_user(email, read_session)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{email}' not found.",
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Password for '{email}' is incorrect.",
        )
    return user


def create_access_token(
    data: dict, expires_delta: datetime.timedelta | None = None
) -> str:
    """Create an access token with the provided data and expiration.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (datetime.timedelta): The time delta in seconds until the token expires.

    Returns:
        encoded_jwt: The encoded JWT token.

    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now() + expires_delta
    else:
        expire = datetime.datetime.now() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, st.JWT_SECRET_KEY, algorithm=st.JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    jwt_token: str | None = Depends(oauth2_scheme),
    api_key_credentials: HTTPAuthorizationCredentials | None = Depends(api_key_header),
    read_session: Session = Depends(db.get_read_session),
) -> User:
    """Return the currently authenticated user.

    Priority order:
    1. JWT access token  (`Authorization: Bearer <token>`)
    2. API key           (`Authorization: API Key <key>`)

    Returns:
        The authenticated ``User`` instance.

    Raises:
        HTTPException: With a contextual message that specifies which type of
        credentials failed or if no credentials were supplied.
    """
    # JWT path
    if jwt_token:
        try:
            payload = jwt.decode(
                jwt_token,
                st.JWT_SECRET_KEY,
                algorithms=[st.JWT_ALGORITHM],
            )
            email: str | None = payload.get("sub")
            if email and (user := get_user(email, read_session)):
                return user
        except JWTError:
            # A JWT was supplied but is invalid → raise immediately.
            raise JWT_CREDENTIALS_EXCEPTION
        # If we reach here a JWT **was** supplied but the user wasn’t found.
        raise JWT_CREDENTIALS_EXCEPTION

    # API-key path
    if api_key_credentials:
        api_key = str(api_key_credentials).split("API Key ")[1]
        if user := get_user_by_api_key(api_key, read_session):
            return user
        raise API_KEY_CREDENTIALS_EXCEPTION

    # No credentials supplied
    raise MISSING_CREDENTIALS_EXCEPTION


async def get_current_active_admin(
    current_user: User = Depends(get_current_user),
):
    """Ensure that the current user is an Admin.

    Args:
        current_user (User): The current user to validate.

    Returns:
        current_user: The validated User object.

    Raises:
        HTTPException: If the user is not an Admin, return a 401.

    """
    if current_user.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User must be an Admin to perform this action.",
        )
    return current_user


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def get_api_key_hash(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify that the provided API key matches the hashed key."""
    return pwd_context.verify(plain_key, hashed_key)


def get_user_by_api_key(api_key: str, read_session: Session) -> User | None:
    """Retrieve a User from the database using an API key.

    Args:
        api_key (str): The API key to validate.
        read_session (Session): The database session to read from.

    Returns:
        User | None: The User object if the API key is valid and active, None otherwise.
    """

    utc_now = datetime.datetime.now(datetime.timezone.utc)

    # Query for active API keys that haven't expired
    key_records = read_session.exec(
        select(ApiKey).where(
            and_(
                ApiKey.is_active == True,  # noqa: E712
                ApiKey.expires > utc_now,
            )
        )
    ).all()

    for key_record in key_records:
        if verify_api_key(api_key, key_record.key_hash):
            # Get the user associated with this API key
            user = read_session.exec(
                select(User).where(User.id == key_record.user_id)
            ).first()
            return user

    return None


def create_api_key_for_user(
    user_id: int,
    name: str,
    expires_days: int | None,
    write_session: Session,
    read_session: Session,
    esdb_client,
) -> tuple[str, ApiKey]:
    """Create a new API key for a user.

    Args:
        user_id (int): The ID of the user to create the API key for.
        name (str): A descriptive name for the API key.
        expires_days (int | None): Number of days until expiry, or None for default.
        write_session (Session): The database session to write to.
        read_session (Session): The database session to read from.
        esdb_client: The EventStoreDB client.

    Returns:
        tuple[str, ApiKey]: The plain API key and the created ApiKey record.
    """

    # Generate the API key
    api_key = generate_api_key()
    key_hash = get_api_key_hash(api_key)

    # Set expiration
    if expires_days is None:
        expires_days = st.API_KEY_EXPIRE_DAYS
    elif expires_days > st.API_KEY_MAX_EXPIRE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"API key expiry cannot exceed {st.API_KEY_MAX_EXPIRE_DAYS} days",
        )

    expires = (datetime.datetime.now() + timedelta(days=expires_days)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    # Create the API key record
    api_key_data = {
        "user_id": user_id,
        "name": name,
        "key_hash": key_hash,
        "expires": expires,
        "is_active": True,
    }

    api_key_record = ApiKey.create(
        api_key_data, write_session, read_session, esdb_client
    )

    return api_key, cast(ApiKey, api_key_record[0])


def get_user_api_keys(user_id: int, read_session: Session) -> list[ApiKey]:
    """Get all API keys for a user.

    Args:
        user_id (int): The ID of the user.
        read_session (Session): The database session to read from.

    Returns:
        list[ApiKey]: List of the user's API keys.
    """
    return read_session.exec(select(ApiKey).where(ApiKey.user_id == user_id)).all()


def deactivate_api_key(
    api_key_id: int,
    write_session: Session,
    read_session: Session,
    esdb_client,
    user_id: int | None = None,
) -> ApiKey | None:
    """Deactivate an API key for a user.

    Args:
        api_key_id (int): The ID of the API key to deactivate.
        user_id (int): The ID of the user (for authorization).
        write_session (Session): The database session to write to.
        read_session (Session): The database session to read from.
        esdb_client: The EventStoreDB client.

    Returns:
        ApiKey | None: The updated API key record, or None if not found/authorized.
    """
    query: SelectOfScalar = select(ApiKey).where(ApiKey.id == api_key_id)
    if user_id:
        query = query.where(ApiKey.user_id == user_id)

    # Get the API key and verify ownership
    api_key = read_session.exec(query).first()

    if not api_key:
        return None

    # Update the API key to inactive
    api_key = write_session.merge(api_key)
    update_data = APIKeyUpdate(is_active=False)
    updated_key = api_key.update(update_data, write_session, read_session, esdb_client)

    return updated_key
