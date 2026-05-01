from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from utils.helpers import (
    success_response, error_response, validate_required_fields,
    validate_priority, validate_status, VALID_PRIORITIES, VALID_STATUSES
)
from utils.auth_middleware import jwt_required_custom
from services.task_service import (
    create_task, get_all_accessible_tasks, update_task, delete_task
)
from models.models import ProjectMember, Task

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("", methods=["POST"])
@jwt_required_custom
def create_task_route():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.", 400)

    err = validate_required_fields(data, ["title", "project_id"])
    if err:
        return error_response(err, 400)

    user_id = int(get_jwt_identity())

    # Only admins can create tasks
    project_id = int(data["project_id"])
    membership = ProjectMember.query.filter_by(user_id=user_id, project_id=project_id).first()
    if not membership:
        return error_response("You are not a member of this project.", 403)
    if membership.role != "Admin":
        return error_response("Only project admins can create tasks.", 403)

    priority = data.get("priority", "Medium")
    if not validate_priority(priority):
        return error_response(f"Invalid priority. Choose from: {', '.join(VALID_PRIORITIES)}", 400)

    status = data.get("status", "To Do")
    if not validate_status(status):
        return error_response(f"Invalid status. Choose from: {', '.join(VALID_STATUSES)}", 400)

    task, error = create_task(
        title=data["title"],
        description=data.get("description", ""),
        due_date_str=data.get("due_date"),
        priority=priority,
        status=status,
        assigned_to=data.get("assigned_to"),
        project_id=project_id,
        created_by=user_id,
    )
    if error:
        return error_response(error, 400)

    return success_response("Task created successfully.", task.to_dict(), 201)


@tasks_bp.route("", methods=["GET"])
@jwt_required_custom
def list_tasks():
    user_id = int(get_jwt_identity())
    project_id = request.args.get("project_id", type=int)

    tasks = get_all_accessible_tasks(user_id, project_id)
    return success_response(
        "Tasks fetched successfully.",
        {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)},
    )


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required_custom
def get_task(task_id):
    user_id = int(get_jwt_identity())
    task = Task.query.get(task_id)
    if not task:
        return error_response("Task not found.", 404)

    # Check access
    membership = ProjectMember.query.filter_by(user_id=user_id, project_id=task.project_id).first()
    if not membership:
        return error_response("Access denied.", 403)
    if membership.role != "Admin" and task.assigned_to != user_id:
        return error_response("Access denied. You can only view your own tasks.", 403)

    return success_response("Task fetched successfully.", task.to_dict())


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required_custom
def update_task_route(task_id):
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.", 400)

    user_id = int(get_jwt_identity())
    task, error = update_task(task_id, user_id, data)
    if error:
        status_code = 404 if "not found" in error.lower() else 403 if "access" in error.lower() else 400
        return error_response(error, status_code)

    return success_response("Task updated successfully.", task.to_dict())


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required_custom
def delete_task_route(task_id):
    user_id = int(get_jwt_identity())
    success, error = delete_task(task_id, user_id)
    if not success:
        status_code = 404 if "not found" in error.lower() else 403
        return error_response(error, status_code)

    return success_response("Task deleted successfully.")
