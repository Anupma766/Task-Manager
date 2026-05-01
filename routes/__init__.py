from routes.auth import auth_bp
from routes.projects import projects_bp
from routes.tasks import tasks_bp
from routes.dashboard import dashboard_bp

__all__ = ["auth_bp", "projects_bp", "tasks_bp", "dashboard_bp"]
