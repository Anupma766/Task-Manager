from app import db, bcrypt
from models.models import User, Project, ProjectMember
from flask_jwt_extended import create_access_token


def signup_user(name: str, email: str, password: str):
    """Create a new user. Returns (user, error_message)."""
    # Check if email already exists
    existing = User.query.filter_by(email=email.lower()).first()
    if existing:
        return None, "An account with this email already exists."

    # Hash password and create user
    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(name=name.strip(), email=email.lower().strip(), password_hash=pw_hash)

    try:
        db.session.add(user)
        db.session.commit()
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, f"Database error: {str(e)}"


def login_user(email: str, password: str):
    """
    Authenticate a user.
    Returns (access_token, user_dict, error_message).
    """
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        return None, None, "Invalid email or password."

    if not bcrypt.check_password_hash(user.password_hash, password):
        return None, None, "Invalid email or password."

    token = create_access_token(identity=str(user.id))
    return token, user.to_dict(), None
