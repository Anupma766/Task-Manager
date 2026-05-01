from app import db
from models.models import Project, ProjectMember, User


def create_project(name: str, description: str, creator_id: int):
    """Create a project and auto-assign creator as Admin."""
    project = Project(name=name.strip(), description=description, created_by=creator_id)
    try:
        db.session.add(project)
        db.session.flush()  # Get project.id before commit

        # Auto-add creator as Admin
        membership = ProjectMember(
            user_id=creator_id, project_id=project.id, role="Admin"
        )
        db.session.add(membership)
        db.session.commit()
        return project, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def get_user_projects(user_id: int):
    """Get all projects the user is a member of."""
    memberships = ProjectMember.query.filter_by(user_id=user_id).all()
    projects = []
    for m in memberships:
        p = m.project.to_dict()
        p["my_role"] = m.role
        projects.append(p)
    return projects


def add_member(project_id: int, email: str, role: str = "Member"):
    """Add a user to a project by email. Returns (member, error)."""
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        return None, f"No user found with email '{email}'."

    existing = ProjectMember.query.filter_by(
        user_id=user.id, project_id=project_id
    ).first()
    if existing:
        return None, "This user is already a member of the project."

    membership = ProjectMember(user_id=user.id, project_id=project_id, role=role)
    try:
        db.session.add(membership)
        db.session.commit()
        return membership, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def remove_member(project_id: int, user_id_to_remove: int, requesting_user_id: int):
    """Remove a member from the project. Admin cannot remove themselves if sole admin."""
    if user_id_to_remove == requesting_user_id:
        # Check if there is another admin
        other_admins = ProjectMember.query.filter_by(
            project_id=project_id, role="Admin"
        ).filter(ProjectMember.user_id != requesting_user_id).count()
        if other_admins == 0:
            return False, "You cannot remove yourself as you are the only admin. Transfer admin rights first."

    membership = ProjectMember.query.filter_by(
        user_id=user_id_to_remove, project_id=project_id
    ).first()
    if not membership:
        return False, "This user is not a member of the project."

    try:
        db.session.delete(membership)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, f"Database error: {str(e)}"


def get_project_by_id(project_id: int):
    return Project.query.get(project_id)
