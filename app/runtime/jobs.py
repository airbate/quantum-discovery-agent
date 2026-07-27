from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any


@dataclass
class JobRecord:
    job_id: str
    status: str
    result: Any = None
    error: str | None = None


class JobRunner:
    """Small process-local job boundary; can be replaced by Celery/RQ later."""

    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.records: dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def submit(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        with self._lock:
            self.records[job_id] = JobRecord(job_id, "queued")
        future = self.executor.submit(function, *args, **kwargs)
        self.records[job_id].status = "running"
        future.add_done_callback(lambda completed: self._finish(job_id, completed))
        return job_id

    def _finish(self, job_id: str, future: Future) -> None:
        try:
            result = future.result()
        except Exception as error:  # noqa: BLE001 - persisted as job failure
            self.records[job_id] = JobRecord(job_id, "failed", error=str(error))
        else:
            self.records[job_id] = JobRecord(job_id, "completed", result=result)

    def get(self, job_id: str) -> JobRecord | None:
        return self.records.get(job_id)
