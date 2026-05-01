from flask import Blueprint, request
from utils.helpers import success_response, error_response, validate_email, validate_required_fields
from services.auth_service import signup_user, login_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.", 400)

    err = validate_required_fields(data, ["name", "email", "password"])
    if err:
        return error_response(err, 400)

    if not validate_email(data["email"]):
        return error_response("Invalid email address format.", 400)

    if len(data["password"]) < 6:
        return error_response("Password must be at least 6 characters long.", 400)

    user, error = signup_user(data["name"], data["email"], data["password"])
    if error:
        return error_response(error, 409 if "already exists" in error else 500)

    return success_response("Account created successfully.", user.to_dict(), 201)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.", 400)

    err = validate_required_fields(data, ["email", "password"])
    if err:
        return error_response(err, 400)

    token, user_dict, error = login_user(data["email"], data["password"])
    if error:
        return error_response(error, 401)

    return success_response("Login successful.", {"token": token, "user": user_dict})
