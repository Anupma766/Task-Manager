from datetime import datetime
from sqlalchemy import func
from app import db
from models.models import Task, ProjectMember, User, Project


def get_dashboard_data(user_id: int, project_id: int = None):
    """
    Build dashboard analytics for the requesting user.
    Admins see project-wide data; members see their own task data.
    """
    # Find all projects user is admin of
    admin_memberships = ProjectMember.query.filter_by(user_id=user_id, role="Admin").all()
    admin_project_ids = [m.project_id for m in admin_memberships]

    # Base task query scope
    if project_id:
        is_admin = project_id in admin_project_ids
        if is_admin:
            base_query = Task.query.filter_by(project_id=project_id)
        else:
            base_query = Task.query.filter_by(project_id=project_id, assigned_to=user_id)
    else:
        if admin_project_ids:
            base_query = Task.query.filter(
                (Task.project_id.in_(admin_project_ids)) | (Task.assigned_to == user_id)
            )
        else:
            base_query = Task.query.filter_by(assigned_to=user_id)

    all_tasks = base_query.all()
    now = datetime.utcnow()

    # Total count
    total_tasks = len(all_tasks)

    # Tasks by status
    status_counts = {"To Do": 0, "In Progress": 0, "Done": 0}
    for t in all_tasks:
        if t.status in status_counts:
            status_counts[t.status] += 1

    # Tasks by priority
    priority_counts = {"Low": 0, "Medium": 0, "High": 0}
    for t in all_tasks:
        if t.priority in priority_counts:
            priority_counts[t.priority] += 1

    # Overdue tasks (past due_date and not Done)
    overdue = [
        t.to_dict()
        for t in all_tasks
        if t.due_date and t.due_date < now and t.status != "Done"
    ]

    # Tasks per user (for admins)
    tasks_per_user = {}
    if admin_project_ids:
        for t in all_tasks:
            if t.assigned_to:
                name = t.assignee.name if t.assignee else f"User #{t.assigned_to}"
                tasks_per_user[name] = tasks_per_user.get(name, 0) + 1

    # Recent tasks (last 5)
    recent_tasks = sorted(all_tasks, key=lambda t: t.created_at, reverse=True)[:5]

    return {
        "total_tasks": total_tasks,
        "tasks_by_status": status_counts,
        "tasks_by_priority": priority_counts,
        "overdue_tasks": overdue,
        "overdue_count": len(overdue),
        "tasks_per_user": tasks_per_user,
        "recent_tasks": [t.to_dict() for t in recent_tasks],
    }
