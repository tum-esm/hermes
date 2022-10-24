import starlette.exceptions


class _CustomError(starlette.exceptions.HTTPException):
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


########################################################################################
# 400 Bad request
########################################################################################


class InvalidSyntaxError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "invalid syntax"
