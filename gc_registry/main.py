import os
import datetime
import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Callable

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.templating import Jinja2Templates
from markdown import markdown
from pyinstrument import Profiler
from pyinstrument.renderers.html import HTMLRenderer
from pyinstrument.renderers.speedscope import SpeedscopeRenderer
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from .account.routes import router as account_router
from .authentication.routes import router as auth_router
from .certificate.routes import router as certificate_router
from .core.database.db import get_db_name_to_client
from .core.error_handling import (
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from .core.models.base import LoggingLevelRequest
from .device.routes import router as device_router
from .logging_config import logger, set_logger_and_children_level
from .measurement.routes import router as measurements_router
from .settings import settings
from .storage.routes import router as storage_router
from .user.routes import router as user_router

STATIC_DIR_FP = Path(__file__).parent / "static"

csrf_bearer = HTTPBearer()

descriptions = {}
for desc in ["api", "certificate", "storage"]:
    static_dir = STATIC_DIR_FP / "descriptions" / f"{desc}.md"
    with open(static_dir, "r") as file:
        descriptions[desc] = markdown(file.read())

tags_metadata = [
    {
        "name": "Certificates",
        "description": descriptions["certificate"],
    },
    {
        "name": "Storage",
        "description": descriptions["storage"],
    },
    {
        "name": "Users",
        "description": "Individuals affiliated with an Organisation that can manage zero or more Accounts.",
    },
    {
        "name": "Accounts",
        "description": """Accounts receive GC Bundles issued from zero or more Devices, and can transfer them to other Accounts.
                        Can be managed by one or more Users with sufficient access privileges.""",
    },
    {
        "name": "Devices",
        "description": "Production or consumption units against which GC Bundles can be either issued or cancelled.",
    },
]


# --- Middleware and CORS Setup ---

# Default local origins
origins = [
    "http://localhost:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://localhost:3000",
]

# Add production origins from settings
origins.extend(settings.cors_origins)

# Absolute fallback for this specific Vercel deployment to stop CORS errors
vercel_origin = "https://my-granular-certificate-registry-n6t50x4mi.vercel.app"
if vercel_origin not in origins:
    origins.append(vercel_origin)

logger.info(f"Initialized CORS origins: {origins}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    logger.info("Starting up application...")

    try:
        # Consolidate Seeding & Verification into Lifespan
        try:
            from sqlmodel import select
            from gc_registry.user.models import User
            from gc_registry.core.database.db import get_read_session, get_write_session
            from gc_registry.authentication.services import get_password_hash
            from gc_registry.core.database import events
            from gc_registry.core.models.base import UserRoles
            
            admin_email = "admin@registry.com"
            logger.info(f"🔍 Checking for admin user: {admin_email}")
            
            with get_read_session() as read_session:
                admin = read_session.exec(select(User).where(User.email == admin_email)).first()
            
            if admin:
                logger.info(f"✅ Verified: {admin_email} exists in database.")
            else:
                logger.info(f"🌱 Seeding missing admin user: {admin_email}")
                
                # Handle optional ESDB with a strict timeout/safety
                esdb_client = None
                try:
                    logger.info("Connecting to EventStoreDB (optional)...")
                    esdb_client = events.get_esdb_client()
                    logger.info("Connected to EventStoreDB.")
                except Exception as e:
                    logger.warning(f"⚠️ EventStoreDB not available ({str(e)}), skipping event logging for seeding.")
                    esdb_client = None
                    
                logger.info("Generating password hash...")
                hashed_pw = get_password_hash("admin123")
                logger.info("Password hash generated.")
                
                admin_user_dict = {
                    "email": admin_email,
                    "name": "Production Admin",
                    "hashed_password": hashed_pw,
                    "role": UserRoles.ADMIN,
                }
                
                logger.info("Writing admin user to database...")
                with get_write_session() as write_session:
                    with get_read_session() as read_session:
                        User.create(admin_user_dict, write_session, read_session, esdb_client)
                logger.info(f"✅ Created: {admin_email} successfully.")
                
        except Exception as seed_err:
            logger.error(f"❌ Critical error during startup seeding: {str(seed_err)}")
            import traceback
            logger.error(traceback.format_exc())

        logger.info("Application startup complete")
        yield

    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        raise

    finally:
        logger.info("Shutting down application...")
        try:
            # TODO: Close database connections
            logger.info("Application shutdown complete")
        except Exception as e:
            logger.error(f"Error during application shutdown: {str(e)}")
            raise


app = FastAPI(
    openapi_tags=tags_metadata,
    title="Energy Tag API Specification",
    description=descriptions["api"],
    version="2.0",
    contact={
        "name": "Please direct feedback to",
        "email": "connor@futureenergy.associates",
    },
    docs_url="/docs",
    dependencies=[Depends(get_db_name_to_client)],
    lifespan=lifespan,
)

# 1. ProxyHeadersMiddleware (Outermost - handles SSL termination/Original IP)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 2. SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.MIDDLEWARE_SECRET_KEY)

# 3. CORSMiddleware (Handles preflights and domain white-listing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "Accept", "Origin"],
    expose_headers=["*"],
)


# --- Error Handling & Logging ---

@app.exception_handler(Exception)
async def production_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure CORS headers are ALWAYS present."""
    logger.exception(f"Unhandled error for {request.method} {request.url.path}")
    
    # Extract origin for the error response CORS header
    origin = request.headers.get("origin")
    # Set allowed origin explicitly or fallback
    allowed_origin = origin if origin in origins else (origins[0] if origins else "*")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc) if settings.ENVIRONMENT != "PROD" else "An unexpected error occurred."
        },
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# Register specific handlers
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: HTTPException):
    logger.warning(f"404 Not Found: {request.method} {request.url.path}")
    return await http_exception_handler(request, exc)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# --- Router Inclusions ---

app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/user")
app.include_router(account_router, prefix="/account")
app.include_router(device_router, prefix="/device")
app.include_router(certificate_router, prefix="/certificate")
app.include_router(storage_router, prefix="/storage")
app.include_router(measurements_router, prefix="/measurement")

# Admin/Seed router
from .seed_endpoint import router as seed_router
app.include_router(seed_router, prefix="/admin")

# Demo/Emergency router
from .emergency_user import router as emergency_router
app.include_router(emergency_router, prefix="/demo")

# Main Demo Page
from .demo_page import router as demo_page_router
app.include_router(demo_page_router, prefix="")

openapi_data = app.openapi()

templates = Jinja2Templates(directory=STATIC_DIR_FP / "templates")


@app.get("/debug/env", tags=["Core"])
async def debug_env():
    """Diagnostic endpoint to see what variables are reaching the container."""
    # Only allow in non-PROD or with a specific flag if possible
    # For now, we need this to see why Railway is failing
    env_data = {}
    for k, v in os.environ.items():
        if any(secret in k.upper() for secret in ["KEY", "PASS", "SECRET", "URL", "TOKEN"]):
            # Mask sensitive values
            if v:
                env_data[k] = f"len:{len(v)} | {v[:4]}...{v[-4:]}" if len(v) > 8 else f"len:{len(v)} | ****"
            else:
                env_data[k] = "EMPTY"
        else:
            env_data[k] = v
    
    return {
        "environment_vars": env_data,
        "settings_db_url_is_none": settings.DATABASE_URL is None,
        "settings_db_url_len": len(settings.DATABASE_URL) if settings.DATABASE_URL else 0,
        "settings_env": settings.ENVIRONMENT,
        "settings_pg_host": settings.POSTGRES_HOST,
        "settings_pg_port": settings.POSTGRES_PORT,
        "settings_pg_db": settings.POSTGRES_DB
    }


@app.get("/", response_class=HTMLResponse, tags=["Core"])
async def read_root(request: Request):
    params = {
        "request": request,
        "head": {"title": "EnergyTag API Specification"},
        "body": [
            {"tag": "h1", "value": "EnergyTag API Specification"},
            {
                "tag": "p",
                "value": """This documentation outlines the first iteration of the EnergyTag
                            Granular Certificiate API Specification. Please direct all comments
                            to connor@futureenergy.associates""",
            },
            {
                "tag": "a",
                "tag_kwargs": {"href": f"{request.url._url}redoc"},
                "value": "/redoc",
            },
        ],
    }

    return templates.TemplateResponse("index.jinja", params)


@app.post("/change_log_level", tags=["Core"])
async def change_log_level_endpoint(request: LoggingLevelRequest):
    """Change the logging level at runtime for all relevant loggers."""
    global logger, uvicorn_logger, uvicorn_access_logger, fastapi_logger

    numeric_level = getattr(logging, request.level)

    # List of all loggers to modify
    loggers_to_update = [
        logger,  # Application logger
        uvicorn_logger,  # Main Uvicorn logger
        uvicorn_access_logger,  # Uvicorn access log
        fastapi_logger,  # FastAPI logger
    ]

    for logger_instance in loggers_to_update:
        set_logger_and_children_level(logger_instance, numeric_level)

    # Debug information to verify changes
    debug_info = {}
    for logger_instance in loggers_to_update:
        # Handle root logger specially
        current_name = logger_instance.name if logger_instance.name else "root"

        debug_info[current_name] = {
            "effective_level": logging.getLevelName(
                logger_instance.getEffectiveLevel()
            ),
            "handlers": [
                {"handler": str(handler), "level": logging.getLevelName(handler.level)}
                for handler in logger_instance.handlers
            ],
        }

        # Add information about child loggers
        if logger_instance.name:  # Skip for root logger
            children = [
                name
                for name in logging.root.manager.loggerDict
                if name.startswith(logger_instance.name + ".")
            ]
            for child_name in children:
                child_logger = logging.getLogger(child_name)
                debug_info[child_name] = {
                    "effective_level": logging.getLevelName(
                        child_logger.getEffectiveLevel()
                    ),
                    "handlers": [
                        {
                            "handler": str(handler),
                            "level": logging.getLevelName(handler.level),
                        }
                        for handler in child_logger.handlers
                    ],
                }

    return {
        "message": f"Log level changed to {request.level}",
        "logger_status": debug_info,
    }


if settings.PROFILING_ENABLED:
    profile_type: str = "html"

    @app.middleware("http")
    async def profile_request(request: Request, call_next: Callable):
        """Profile the current request

        Taken from https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
        with small improvements.

        """
        # we map a profile type to a file extension, as well as a pyinstrument profile renderer
        profile_type_to_ext = {"html": "html", "speedscope": "speedscope.json"}
        profile_type_to_renderer = {
            "html": HTMLRenderer,
            "speedscope": SpeedscopeRenderer,
        }

        # we profile the request along with all additional middlewares, by interrupting
        # the program every 1ms1 and records the entire stack at that point
        with Profiler(interval=0.001, async_mode="enabled") as profiler:
            response = await call_next(request)

        # we dump the profiling into a file
        extension = profile_type_to_ext[profile_type]
        renderer = profile_type_to_renderer[profile_type]()

        # create a new dated folder in core/profiling with todays date
        todays_date = datetime.datetime.now().strftime("%Y-%m-%d")
        profiling_dir = Path(__file__).parent / "core" / "profiling" / todays_date
        profiling_dir.mkdir(exist_ok=True)

        with open(Path(profiling_dir, f"profile.{extension}"), "w") as out:
            out.write(profiler.output(renderer=renderer))
        return response
