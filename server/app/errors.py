import starlette.exceptions


class _CustomError(starlette.exceptions.HTTPException):
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class InvalidSyntaxError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "Invalid Syntax"


class ResourceExistsError(_CustomError):
    STATUS_CODE = 409
    DETAIL = "Resource Exists"


class InternalServerError(_CustomError):
    STATUS_CODE = 500
    DETAIL = "Internal Server Error"
