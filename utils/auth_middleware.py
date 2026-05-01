from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.models import ProjectMember
from utils.helpers import error_response


def jwt_required_custom(fn):
    """Standard JWT authentication decorator."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return error_response("Invalid or expired token. Please login again.", 401)
        return fn(*args, **kwargs)
    return wrapper


def require_project_admin(fn):
    """
    Decorator that checks if the current user is an ADMIN of the given project.
    The route must have a `project_id` parameter (URL or body).
    Usage: apply AFTER @jwt_required_custom.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask import request
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())

            # Try to get project_id from URL kwargs first, then JSON body
            project_id = kwargs.get("project_id")
            if project_id is None:
                data = request.get_json(silent=True) or {}
                project_id = data.get("project_id")

            if not project_id:
                return error_response("project_id is required.", 400)

            membership = ProjectMember.query.filter_by(
                user_id=user_id, project_id=int(project_id)
            ).first()

            if not membership:
                return error_response("You are not a member of this project.", 403)

            if membership.role != "Admin":
                return error_response(
                    "Access denied. Only project admins can perform this action.", 403
                )

        except Exception as e:
            return error_response(f"Authorization error: {str(e)}", 401)

        return fn(*args, **kwargs)
    return wrapper


def require_project_member(fn):
    """
    Decorator that checks if the current user is a member (any role) of the project.
    project_id must be in URL kwargs or JSON body.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask import request
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())

            project_id = kwargs.get("project_id")
            if project_id is None:
                data = request.get_json(silent=True) or {}
                project_id = data.get("project_id")

            if not project_id:
                return error_response("project_id is required.", 400)

            membership = ProjectMember.query.filter_by(
                user_id=user_id, project_id=int(project_id)
            ).first()

            if not membership:
                return error_response(
                    "Access denied. You are not a member of this project.", 403
                )

        except Exception as e:
            return error_response(f"Authorization error: {str(e)}", 401)

        return fn(*args, **kwargs)
    return wrapper
