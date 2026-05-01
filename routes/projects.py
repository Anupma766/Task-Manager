from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from utils.helpers import (
    success_response, error_response, validate_required_fields, validate_role
)
from utils.auth_middleware import jwt_required_custom, require_project_admin
from services.project_service import (
    create_project, get_user_projects, add_member, remove_member, get_project_by_id
)
from models.models import ProjectMember

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("", methods=["POST"])
@jwt_required_custom
def create_project_route():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.", 400)

    err = validate_required_fields(data, ["name"])
    if err:
        return error_response(err, 400)

    user_id = int(get_jwt_identity())
    project, error = create_project(
        name=data["name"],
        description=data.get("description", ""),
        creator_id=user_id,
    )
    if error:
        return error_response(error, 500)

    return success_response("Project created successfully.", project.to_dict(include_members=True), 201)


@projects_bp.route("", methods=["GET"])
@jwt_required_custom
def list_projects():
    user_id = int(get_jwt_identity())
    projects = get_user_projects(user_id)
    return success_response("Projects fetched successfully.", {"projects": projects})


@projects_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required_custom
def get_project(project_id):
    user_id = int(get_jwt_identity())
    membership = ProjectMember.query.filter_by(user_id=user_id, project_id=project_id).first()
    if not membership:
        return error_response("Access denied or project not found.", 403)

    project = get_project_by_id(project_id)
    if not project:
        return error_response("Project not found.", 404)

    data = project.to_dict(include_members=True)
    data["my_role"] = membership.role
    return success_response("Project fetched successfully.", data)


@projects_bp.route("/add-member", methods=["POST"])
@jwt_required_custom
def add_member_route():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.", 400)

    err = validate_required_fields(data, ["project_id", "email"])
    if err:
        return error_response(err, 400)

    user_id = int(get_jwt_identity())
    project_id = data["project_id"]

    # Verify requester is admin
    membership = ProjectMember.query.filter_by(user_id=user_id, project_id=project_id).first()
    if not membership or membership.role != "Admin":
        return error_response("Access denied. Only project admins can add members.", 403)

    role = data.get("role", "Member")
    if not validate_role(role):
        return error_response("Invalid role. Must be 'Admin' or 'Member'.", 400)

    member, error = add_member(project_id, data["email"], role)
    if error:
        return error_response(error, 400)

    return success_response("Member added successfully.", member.to_dict(), 201)


@projects_bp.route("/remove-member", methods=["DELETE"])
@jwt_required_custom
def remove_member_route():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.", 400)

    err = validate_required_fields(data, ["project_id", "user_id"])
    if err:
        return error_response(err, 400)

    requesting_user_id = int(get_jwt_identity())
    project_id = data["project_id"]

    # Verify requester is admin
    membership = ProjectMember.query.filter_by(
        user_id=requesting_user_id, project_id=project_id
    ).first()
    if not membership or membership.role != "Admin":
        return error_response("Access denied. Only project admins can remove members.", 403)

    success, error = remove_member(project_id, int(data["user_id"]), requesting_user_id)
    if not success:
        return error_response(error, 400)

    return success_response("Member removed successfully.")
