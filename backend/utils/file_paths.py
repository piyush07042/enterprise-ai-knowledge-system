from pathlib import Path


PROFILE_PICTURE_BASE_FOLDER = Path("uploads") / "profile_pictures"
ALLOWED_PROFILE_PICTURE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_PROFILE_PICTURE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
}
MAX_PROFILE_PICTURE_SIZE = 2 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip()
    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("Invalid filename")
    return safe_name


def resolve_user_upload_path(base_folder: str, user_folder: str, filename: str) -> Path:
    base_path = Path(base_folder).resolve()
    safe_name = sanitize_filename(filename)
    target_path = (base_path / user_folder / safe_name).resolve()

    if base_path not in target_path.parents and target_path != base_path:
        raise ValueError("Invalid file path")

    return target_path


def get_profile_picture_folder(user_email: str) -> Path:
    return PROFILE_PICTURE_BASE_FOLDER / user_email


def get_profile_picture_path(user_email: str, filename: str) -> Path:
    safe_name = sanitize_filename(filename)
    return get_profile_picture_folder(user_email) / safe_name


def is_allowed_profile_picture(filename: str, content_type: str | None) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in ALLOWED_PROFILE_PICTURE_EXTENSIONS and (
        content_type in ALLOWED_PROFILE_PICTURE_CONTENT_TYPES
        if content_type is not None
        else True
    )