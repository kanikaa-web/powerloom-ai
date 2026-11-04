"""
auth.py
-------
Handles password hashing, login verification, session state,
role-based access, and forgot-password flow.
"""

import bcrypt
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    try:
        return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def verify_password(plain_password: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def login_user(username: str, password: str):
    """
    Validate credentials against the users table.
    Returns the user dict on success, else None.
    """
    from database.db import fetch_one

    user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if user and verify_password(password, user["password_hash"]):
        st.session_state["logged_in"] = True
        st.session_state["username"] = user["username"]
        st.session_state["role"] = user["role"]
        st.session_state["full_name"] = user["full_name"]
        logger.info(f"User '{username}' logged in as {user['role']}.")
        return user
    logger.warning(f"Failed login attempt for username '{username}'.")
    return None


def logout_user():
    """Clear all session state related to authentication."""
    for key in ["logged_in", "username", "role", "full_name"]:
        if key in st.session_state:
            del st.session_state[key]
    logger.info("User logged out.")


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def get_current_role() -> str:
    return st.session_state.get("role", "")


def require_login():
    """Stop page execution if user is not logged in."""
    if not is_logged_in():
        st.warning("⚠️ Please log in to access this page.")
        st.stop()


def require_role(allowed_roles: list):
    """Restrict page access to specific roles."""
    require_login()
    if get_current_role() not in allowed_roles:
        st.error("🚫 You do not have permission to access this page.")
        st.stop()


def reset_password(username: str, new_password: str) -> bool:
    """Reset a user's password (used in Forgot Password flow)."""
    from database.db import fetch_one, execute

    user = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if not user:
        return False
    new_hash = hash_password(new_password)
    execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
    logger.info(f"Password reset for user '{username}'.")
    return True


def update_profile(username: str, full_name: str = None, email: str = None) -> bool:
    """Update profile fields for a user."""
    from database.db import execute

    if full_name:
        execute("UPDATE users SET full_name = ? WHERE username = ?", (full_name, username))
    if email:
        execute("UPDATE users SET email = ? WHERE username = ?", (email, username))
    logger.info(f"Profile updated for user '{username}'.")
    return True
