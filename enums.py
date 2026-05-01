from enum import StrEnum


class ResMsg(StrEnum):
    task_not_found = "[ERROR] Task not found"
    task_already_exists = "[INFO] Task already exists"
    invalid_auth_credentials = "[ERROR] Invalid authentication credentials"
    invalid_username_or_password = "[ERROR] Invalid username or password"
