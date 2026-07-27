"""Business Modules package.

Each business domain (e.g. students, stalls, bookings, payments, vendors,
admin) lives in its own subpackage here, following the frozen per-module
layout:

    modules/<module_name>/
        api/
        service/
        repository/
        models/
        schemas/
        dependencies/
        utils/

No modules are implemented in Milestone 1 (bootstrap only).
"""
# app/modules/users/__init__.py
from app.modules.users.models import Admin, Student, User, Vendor

__all__ = ["User", "Student", "Vendor", "Admin"]