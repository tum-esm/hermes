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
    """Authenticate a user based on the authorization header."""
    # Check for authorization header
    access_token = request.headers.get("authorization")
    if not access_token or not access_token.startswith("Bearer "):
        logger.warning(
            f"{request.method} {request.url.path} -- Missing or invalid authorization"
            " header"
        )
        raise errors.UnauthorizedError()
    access_token = access_token[7:]
    # Check if access token is valid
    try:
        query, arguments = database.build(
            template="read-session.sql",
            template_arguments={},
            query_arguments={"access_token_hash": hash_token(access_token)},
        )
        result = await database_client.fetch(query, *arguments)
        user_identifier = database.dictify(result)[0]["user_identifier"]
    except IndexError:
        logger.warning(f"{request.method} {request.url.path} -- Invalid access token")
        raise errors.UnauthorizedError()
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -- Unknown error: {repr(e)}")
        raise errors.InternalServerError()
    # Return user identifier on successful authentication
    return user_identifier
