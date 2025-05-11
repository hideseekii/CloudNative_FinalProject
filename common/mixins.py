# common/mixins.py
from django.core.exceptions import PermissionDenied

class StaffRequiredMixin:
    """只允許 role == 'staff' 的使用者存取 CBV"""
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.role != user.Role.STAFF:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
