from datetime import datetime
from app import db
from models.models import Task, ProjectMember


def create_task(title, description, due_date_str, priority, status,
                assigned_to, project_id, created_by):
    """Create a new task. Returns (task, error)."""
    # Validate assigned_to is a member of the project
    if assigned_to:
        membership = ProjectMember.query.filter_by(
            user_id=assigned_to, project_id=project_id
        ).first()
        if not membership:
            return None, "The assigned user is not a member of this project."

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            return None, "Invalid due_date format. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"

    task = Task(
        title=title.strip(),
        description=description,
        due_date=due_date,
        priority=priority,
        status=status,
        assigned_to=assigned_to,
        project_id=project_id,
        created_by=created_by,
    )
    try:
        db.session.add(task)
        db.session.commit()
        return task, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def get_tasks_for_user(user_id: int, project_id: int = None, role: str = None):
    """
    Admin sees all tasks in their projects.
    Member sees only their assigned tasks.
    """
    if role == "Admin":
        query = Task.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        else:
            # Get all project IDs where user is admin
            admin_projects = ProjectMember.query.filter_by(
                user_id=user_id, role="Admin"
            ).all()
            project_ids = [m.project_id for m in admin_projects]
            query = query.filter(Task.project_id.in_(project_ids))
    else:
        query = Task.query.filter_by(assigned_to=user_id)
        if project_id:
            query = query.filter_by(project_id=project_id)

    return query.order_by(Task.created_at.desc()).all()


def get_all_accessible_tasks(user_id: int, project_id: int = None):
    """
    Returns tasks based on user's highest role.
    If user is admin in any project, they see all tasks in those projects.
    Plus all tasks assigned to them.
    """
    # Find all projects where user is admin
    admin_memberships = ProjectMember.query.filter_by(user_id=user_id, role="Admin").all()
    admin_project_ids = [m.project_id for m in admin_memberships]

    query = Task.query
    if project_id:
        # Check if user is admin in this project
        is_admin = project_id in admin_project_ids
        query = query.filter_by(project_id=project_id)
        if not is_admin:
            query = query.filter_by(assigned_to=user_id)
    else:
        if admin_project_ids:
            query = query.filter(
                (Task.project_id.in_(admin_project_ids)) | (Task.assigned_to == user_id)
            )
        else:
            query = query.filter_by(assigned_to=user_id)

    return query.order_by(Task.created_at.desc()).all()


def update_task(task_id: int, user_id: int, data: dict):
    """
    Update a task.
    Admins can update all fields. Members can only update status.
    Returns (task, error).
    """
    task = Task.query.get(task_id)
    if not task:
        return None, "Task not found."

    # Get user's role in the task's project
    membership = ProjectMember.query.filter_by(
        user_id=user_id, project_id=task.project_id
    ).first()

    if not membership:
        return None, "Access denied. You are not a member of this project."

    is_admin = membership.role == "Admin"
    is_assignee = task.assigned_to == user_id

    if not is_admin and not is_assignee:
        return None, "Access denied. You can only update tasks assigned to you."

    if is_admin:
        # Admin can update all fields
        if "title" in data and data["title"]:
            task.title = data["title"].strip()
        if "description" in data:
            task.description = data["description"]
        if "due_date" in data:
            if data["due_date"]:
                try:
                    task.due_date = datetime.fromisoformat(data["due_date"])
                except ValueError:
                    return None, "Invalid due_date format."
            else:
                task.due_date = None
        if "priority" in data:
            from utils.helpers import validate_priority
            if not validate_priority(data["priority"]):
                return None, "Invalid priority. Must be Low, Medium, or High."
            task.priority = data["priority"]
        if "assigned_to" in data:
            if data["assigned_to"]:
                m = ProjectMember.query.filter_by(
                    user_id=data["assigned_to"], project_id=task.project_id
                ).first()
                if not m:
                    return None, "Assigned user is not a member of this project."
            task.assigned_to = data["assigned_to"]

    # Both admin and member can update status
    if "status" in data:
        from utils.helpers import validate_status
        if not validate_status(data["status"]):
            return None, "Invalid status. Must be 'To Do', 'In Progress', or 'Done'."
        task.status = data["status"]

    try:
        db.session.commit()
        return task, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def delete_task(task_id: int, user_id: int):
    """Only project admins can delete tasks. Returns (success, error)."""
    task = Task.query.get(task_id)
    if not task:
        return False, "Task not found."

    membership = ProjectMember.query.filter_by(
        user_id=user_id, project_id=task.project_id
    ).first()

    if not membership or membership.role != "Admin":
        return False, "Access denied. Only project admins can delete tasks."

    try:
        db.session.delete(task)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"
