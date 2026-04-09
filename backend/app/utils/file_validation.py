ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def is_allowed_content_type(content_type: str) -> bool:
    return content_type in ALLOWED_CONTENT_TYPES

