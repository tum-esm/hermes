import hashlib
import secrets

import passlib.context

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
# Access Token Flow
########################################################################################


async def authenticate(request, database_client):
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
        query, arguments = database.build(
            template="read-permissions.sql",
            template_arguments={},
            query_arguments={"access_token_hash": hash_token(access_token)},
        )
        result = await database_client.fetch(query, *arguments)
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    result = database.dictify(result)
    # If the result is empty the access token is invalid
    if len(result) == 0:
        logger.warning(f"{request.method} {request.url.path} -- Invalid access token")
        raise errors.UnauthorizedError()
    user_identifier = result[0]["user_identifier"]
    # A user can have multiple permissions, the query's LEFT JOIN can produce None
    permissions = [
        entry["network_identifier"]
        for entry in result
        if entry["network_identifier"] is not None
    ]
    return user_identifier, permissions
