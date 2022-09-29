import starlette.applications
import starlette.routing
import starlette.responses

import app.settings as settings


async def get_status(request):
    """Return some status information about the server."""
    return starlette.responses.JSONResponse(
        {
            "commit_sha": settings.COMMIT_SHA,
            "branch_name": settings.BRANCH_NAME,
        }
    )


app = starlette.applications.Starlette(
    routes=[
        starlette.routing.Route(
            path="/status",
            endpoint=get_status,
            methods=["GET"],
        ),
    ]
)
