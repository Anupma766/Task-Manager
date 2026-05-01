from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from utils.helpers import success_response, error_response
from utils.auth_middleware import jwt_required_custom
from services.dashboard_service import get_dashboard_data

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("", methods=["GET"])
@jwt_required_custom
def dashboard():
    user_id = int(get_jwt_identity())
    project_id = request.args.get("project_id", type=int)

    try:
        data = get_dashboard_data(user_id, project_id)
        return success_response("Dashboard data fetched successfully.", data)
    except Exception as e:
        return error_response(f"Failed to fetch dashboard data: {str(e)}", 500)
