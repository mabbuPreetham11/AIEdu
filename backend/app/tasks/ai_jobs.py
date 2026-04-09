from app.workers.celery_app import celery_app


@celery_app.task
def extract_syllabus_from_document(course_id: int, source_url: str) -> dict:
    return {"course_id": course_id, "source_url": source_url, "status": "queued"}


@celery_app.task
def grade_submission_async(submission_id: int) -> dict:
    return {"submission_id": submission_id, "status": "queued"}

