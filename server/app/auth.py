import hashlib
import secrets

import passlib.context
import starlette.authentication
import starlette.middleware.authentication

import app.database as database
import app.errors as errors
from app.logs import logger


########################################################################################
# Password Utilities
########################################################################################


_CONTEXT = passlib.context.CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password):
    """Hash the given password and return the hash as string."""
    return _CONTEXT.hash(password)


def verify_password(password, password_hash):
    """Return true if the password results in the hash, else False."""
    return _CONTEXT.verify(password, password_hash)


########################################################################################
# Token Utilities
########################################################################################


def generate_token():
    """Create and return a random string useful for authentication."""
    return secrets.token_hex(32)


def hash_token(token):
    """Hash the given token and return the hash as string."""
    return hashlib.sha512(token.encode("utf-8")).hexdigest()


########################################################################################
# Authentication middleware
########################################################################################


class AuthenticationMiddleware:
    """Simple route-level RBAC middleware. Structure adapted from Starlette's own."""

    def __init__(self, app):
        self.app = app

    async def _read_role_over_user(self, request):
        raise NotImplementedError()

    async def _read_role_over_network(self, request, user_identifier):
        # TODO Extract identifier from request, maybe reuse code from starlette?
        network_identifier = "81bf7042-e20f-4a97-ac44-c15853e3618f"
        # network_identifier = request.path_params["network_identifier"]
        query, arguments = database.parametrize(
            identifier="authorize",
            arguments={
                "user_identifier": user_identifier,
                "network_identifier": network_identifier,
            },
        )
        elements = await request.state.dbpool.fetch(query, *arguments)
        elements = database.dictify(elements)
        return None if len(elements) == 0 else "default"

    async def _read_role_over_sensor(self, request):
        raise NotImplementedError

    async def _authenticate(self, request):
        # Extract the access token from the authorization header
        if "authorization" not in request.headers:
            return None
        try:
            scheme, access_token = request.headers["authorization"].split()
        except ValueError:
            logger.warning("[auth] Malformed authorization header")
            return None
        if scheme.lower() != "bearer":
            logger.warning("[auth] Malformed authorization header")
            return None
        # Check if we have the access token in the database
        query, arguments = database.parametrize(
            identifier="authenticate",
            arguments={"access_token_hash": hash_token(access_token)},
        )
        elements = await request.state.dbpool.fetch(query, *arguments)
        elements = database.dictify(elements)
        # If the result set is empty, the access token is invalid
        if len(elements) == 0:
            logger.warning("[auth] Invalid access token")
            raise None
        # Read the user's permissions TODO Think about how to structure this
        user_identifier = elements[0]["user_identifier"]
        role = await self._read_role_over_network(request, user_identifier)
        return user_identifier, role

    async def __call__(self, scope, receive, send):
        # Only process HTTP requests, not websockets
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        # Instantiate request from scope to more easily access parameters
        request = starlette.requests.Request(scope)
        # Authenticate and pass the result through to the routes
        result = await self._authenticate(request)
        if result is None:
            result = None, []
        scope["auth"] = dict(zip(["user", "role"], result))
        await self.app(scope, receive, send)


async def authenticate(request, dbpool):
    """Authenticate and read a user's permissions based on authorization header."""
    # Check for authorization header
    access_token = request.headers.get("authorization")
    if not access_token or not access_token.startswith("Bearer "):
        logger.warning(
            f"{request.method} {request.url.path} -- Missing or invalid authorization"
            " header"
        )
        raise errors.UnauthorizedError()
    access_token = access_token[7:]
    # Check if access token is valid and read permissions
    try:
        query, arguments = database.parametrize(
            identifier="read-permissions",
            arguments={"access_token_hash": hash_token(access_token)},
        )
        elements = await dbpool.fetch(query, *arguments)
    except Exception as e:  # pragma: no cover
        logger.error(e, exc_info=True)
        raise errors.InternalServerError()
    elements = database.dictify(elements)
    # If the result is empty the access token is invalid
    if len(elements) == 0:
        logger.warning(f"{request.method} {request.url.path} -- Invalid access token")
        raise errors.UnauthorizedError()
    user_identifier = elements[0]["user_identifier"]
    # A user can have multiple permissions, the query's LEFT JOIN can produce None
    permissions = [
        entry["network_identifier"]
        for entry in elements
        if entry["network_identifier"] is not None
    ]
    return user_identifier, permissions
