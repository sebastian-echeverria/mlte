"""
mlte/store/user/underlying/default_user.py

Default user.
"""

from __future__ import annotations

from mlte.user import passwords

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = passwords.get_password_hash("admin1234")
