import logging
import queue
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Thread
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class ScraperJob:
    func: Callable
    args: tuple
    kwargs: dict
    submitted_at: datetime


@dataclass
class ScraperJobSchedule:
    next_run: datetime
    interval: float | tuple[float, float]  # seconds or (min_seconds, max_seconds)
    func: Callable
    args: tuple
    kwargs: dict


class DataFetcherJobQueue:
    def __init__(
        self,
        max_job_age: int = 300,
        max_queue_size: int | None = None,
        worker_delay: float | tuple[float, float] = 0,
    ) -> None:
        """Initialize the DataFetcherJobQueue.

        Args:
            max_job_age (int, optional):
                The maximum age of a job in seconds before it is considered stale.
                Stale jobs will not be executed. Defaults to 300.
            max_queue_size (int | None, optional):
                The maximum size of the job queue. Defaults to None (unlimited).
            worker_delay (float | tuple[float, float], optional): The delay for worker threads. Defaults to 0.
        """
        self.max_job_age = max_job_age
        self.worker_delay = worker_delay
        self.queue = queue.Queue(maxsize=max_queue_size or 0)
        self.job_schedules: list[ScraperJobSchedule] = []

        self.running: bool = True
        self.worker_thread = Thread(target=self._worker, daemon=True)
        self.scheduler_thread = Thread(target=self._scheduler, daemon=True)

    def start(self) -> None:
        logger.info("Starting DataFetcherJobQueue threads")
        self.worker_thread.start()
        self.scheduler_thread.start()

    def stop(self) -> None:
        logger.info("Stopping DataFetcherJobQueue")
        self.running = False

    def _job_is_stale(self, job: ScraperJob) -> bool:
        return (datetime.now() - job.submitted_at).total_seconds() > self.max_job_age

    def _apply_worker_delay(self) -> None:
        if isinstance(self.worker_delay, (tuple, list)):
            delay = random.uniform(self.worker_delay[0], self.worker_delay[1])
        elif self.worker_delay:
            delay = self.worker_delay
        else:
            return
        time.sleep(delay)

    def _worker(self) -> None:
        while self.running:
            try:
                job = self.queue.get(timeout=1)
                if self._job_is_stale(job):
                    logger.warning(
                        f"Skipping stale job submitted at {job.submitted_at}"
                    )
                    self.queue.task_done()
                    continue
                logger.debug(f"Executing job: {job.func.__name__}")
                job.func(*job.args, **job.kwargs)
                self.queue.task_done()
                self._apply_worker_delay()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error executing job: {e}", exc_info=True)
                self.queue.task_done()

    def _schedule_job(self, job_schedule: ScraperJobSchedule) -> None:
        now = datetime.now()
        if now >= job_schedule.next_run:
            # Queue the job
            self.add_job(
                job_schedule.func,
                job_schedule.args,
                job_schedule.kwargs,
                allow_duplicates=False,
            )

            # Schedule next run with potential randomization
            if isinstance(job_schedule.interval, tuple):
                interval_seconds = random.uniform(
                    job_schedule.interval[0], job_schedule.interval[1]
                )
            else:
                interval_seconds = job_schedule.interval

            job_schedule.next_run = now + timedelta(seconds=interval_seconds)

    def _scheduler(self) -> None:
        while self.running:
            for job_schedule in self.job_schedules:
                self._schedule_job(job_schedule)
            time.sleep(1)

    def add_job(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        allow_duplicates: bool = True,
    ) -> ScraperJob | None:
        """Add immediate job to queue. Returns Job if added, None if deduped.

        Args:
            func (Callable): The job function to execute.
            args (tuple, optional): Positional arguments for the job function. Defaults to ().
            kwargs (dict, optional): Keyword arguments for the job function. Defaults to None.
            allow_duplicates (bool, optional): Whether to allow duplicate jobs.
                A job is considered a duplicate if another job with the same function is already in the queue.
                Args or kwargs are not considered for deduplication.
                Defaults to True.

        Returns:
            ScraperJob | None: The created job or None if it was deduplicated.
        """
        if kwargs is None:
            kwargs = {}

        if not allow_duplicates:
            with self.queue.mutex:
                for job in list(self.queue.queue):
                    if job.func == func:
                        logger.debug(f"Skipping duplicate job: {func.__name__}")
                        return None

        job = ScraperJob(
            func=func, args=args, kwargs=kwargs, submitted_at=datetime.now()
        )
        self.queue.put(job)

        return job

    def add_schedule(
        self,
        func: Callable,
        interval: float | tuple[float, float],
        args: tuple = (),
        kwargs: dict = None,
        next_run: datetime = None,
    ) -> None:
        """Add a recurring job schedule.

        Args:
            func (Callable): The job function to execute.
            interval (float | tuple[float, float]): Time interval in seconds (fixed) or (min, max) for randomized interval.
            args (tuple, optional): Positional arguments for the job function. Defaults to ().
            kwargs (dict, optional): Keyword arguments for the job function. Defaults to None.
            next_run (datetime, optional): The next run time for the schedule. Defaults to None.
        """
        if kwargs is None:
            kwargs = {}

        # Calculate initial interval
        if isinstance(interval, (tuple, list)):
            if len(interval) != 2 or interval[0] >= interval[1]:
                raise ValueError(
                    "Interval tuple must be (min_seconds, max_seconds) with min < max"
                )
            interval = tuple(interval)
            initial_interval = random.uniform(interval[0], interval[1])
        elif isinstance(interval, (int, float)):
            if interval <= 0:
                raise ValueError("Interval must be a positive number")
            initial_interval = interval
        else:
            raise ValueError("Interval must be a float or a tuple of two floats")

        next_run_time = next_run or (
            datetime.now() + timedelta(seconds=initial_interval)
        )
        job_schedule = ScraperJobSchedule(
            next_run=next_run_time,
            interval=interval,
            func=func,
            args=args,
            kwargs=kwargs,
        )
        self.job_schedules.append(job_schedule)
