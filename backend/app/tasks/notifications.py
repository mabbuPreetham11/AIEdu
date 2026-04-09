from app.workers.celery_app import celery_app


@celery_app.task
def send_assignment_notification(course_id: int, assignment_id: int) -> dict:
    return {"course_id": course_id, "assignment_id": assignment_id, "status": "queued"}


@celery_app.task
def send_deadline_reminder(submission_id: int, hours_before: int) -> dict:
    return {"submission_id": submission_id, "hours_before": hours_before}

