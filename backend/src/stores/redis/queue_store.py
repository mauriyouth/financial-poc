"""
Redis queue store for job management.
"""

from enum import Enum

from redis import Redis
from rq import Queue
from rq.job import Job

from src.configurations.redis import settings as redis_settings


class JobStatus(str, Enum):
    """Job status enum."""

    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"


class QueueStore:
    """Store for Redis queue operations."""

    def __init__(self) -> None:
        self.redis_conn = Redis.from_url(redis_settings.redis_url)
        self.queue = Queue("default", connection=self.redis_conn)

    def enqueue_parsing(self, doc_id: str) -> str:
        """
        Enqueue a document parsing job.

        Args:
            doc_id: Document ID to parse

        Returns:
            Job ID
        """
        from src.modules.queue.worker import process_document_task

        job = self.queue.enqueue(process_document_task, doc_id)
        return job.id

    def enqueue_document_processing(self, document_id: str, file_path: str, file_type: str) -> str:
        """
        Enqueue document processing job (chunking + embedding + indexing).

        Args:
            document_id: Document ID
            file_path: Path to document file
            file_type: File extension (pdf, pptx, docx, xlsx)

        Returns:
            Job ID
        """
        from src.jobs.process_document_job import process_document_job

        job = self.queue.enqueue(
            process_document_job,
            document_id,
            file_path,
            file_type,
            job_timeout="15m",
        )
        return job.id

    def get_job_status(self, job_id: str) -> tuple[JobStatus, int, str | None]:
        """
        Get job status and progress.

        Args:
            job_id: Job ID to check

        Returns:
            Tuple of (status, progress_percent, error_message)
        """
        job = Job.fetch(job_id, connection=self.redis_conn)

        # Map RQ status to our JobStatus
        status_map = {
            "queued": JobStatus.QUEUED,
            "started": JobStatus.STARTED,
            "finished": JobStatus.FINISHED,
            "failed": JobStatus.FAILED,
        }

        status = status_map.get(job.get_status(), JobStatus.QUEUED)

        # Calculate progress (simple: 0% if queued, 50% if started, 100% if finished)
        progress = 0
        if status == JobStatus.STARTED:
            progress = 50
        elif status == JobStatus.FINISHED:
            progress = 100

        error_message = None
        if status == JobStatus.FAILED and job.exc_info:
            error_message = str(job.exc_info)

        return status, progress, error_message
