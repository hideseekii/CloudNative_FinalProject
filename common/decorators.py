# common/decorators.py
from django.core.exceptions import PermissionDenied
from functools import wraps

def staff_required(fn):
    """只允許 role == 'staff' 的使用者存取 function-based view"""
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.role != user.Role.STAFF:
            raise PermissionDenied
        return fn(request, *args, **kwargs)
    return wrapper
