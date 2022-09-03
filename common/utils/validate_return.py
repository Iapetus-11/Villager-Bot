import inspect
from functools import wraps
from typing import TYPE_CHECKING, Any

from pydantic import create_model


def validate_return(function):
    if TYPE_CHECKING:
        return function

    if "return" not in function.__annotations__:
        return function

    return_anno = function.__annotations__["return"]
    if return_anno is None:
        return_anno = type(None)

    model = create_model("ReturnValueModel", return_value=(return_anno, ...))

    def _validate_type(return_value: Any):
        model(return_value=return_value)
        return return_value

    if inspect.iscoroutinefunction(function):

        @wraps(function)
        async def _validate_return(*args, **kwargs):
            return _validate_type(await function(*args, **kwargs))

    else:

        @wraps(function)
        def _validate_return(*args, **kwargs):
            return _validate_type(function(*args, **kwargs))

    return _validate_return
