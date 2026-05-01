import re
from flask import jsonify


# ─── Standard Response Helpers ────────────────────────────────────────────────

def success_response(message="Success", data=None, status_code=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": data or {}
    }), status_code


def error_response(message="An error occurred", status_code=400):
    return jsonify({
        "success": False,
        "message": message,
        "data": {}
    }), status_code


# ─── Input Validators ─────────────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_required_fields(data: dict, required_fields: list) -> str | None:
    """Returns error message string if validation fails, else None."""
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return f"'{field}' is required and cannot be empty."
    return None


VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_STATUSES = {"To Do", "In Progress", "Done"}
VALID_ROLES = {"Admin", "Member"}


def validate_priority(priority: str) -> bool:
    return priority in VALID_PRIORITIES


def validate_status(status: str) -> bool:
    return status in VALID_STATUSES


def validate_role(role: str) -> bool:
    return role in VALID_ROLES
