import threading
from concurrent.futures import Future
from typing import Callable, Set


class UserPollingManager:
    def __init__(self, thread_pool_executor):
        self.executor = thread_pool_executor
        self.active_users: Set[int] = set()
        self.user_futures: dict[int, Future] = {}
        self.lock = threading.Lock()

    def submit_job(
        self,
        user_id: int,
        callback: Callable[[int], None],
        args: tuple,
        kwargs: dict = None,
    ) -> Future:
        if kwargs is None:
            kwargs = {}
        with self.lock:
            if user_id in self.active_users:
                return None
            self.active_users.add(user_id)
            future = self.executor.submit(callback, *args, **kwargs)
            self.user_futures[user_id] = future
            future.add_done_callback(
                lambda f, uid=user_id: self._on_job_complete(uid, f)
            )
            return future

    def _on_job_complete(self, user_id: int, future: Future):
        with self.lock:
            self.active_users.discard(user_id)
            self.user_futures.pop(user_id, None)

    def get_active_users(self) -> Set[int]:
        with self.lock:
            return self.active_users.copy()

    def shutdown(self):
        with self.lock:
            for user_id, future in self.user_futures.items():
                if not future.done():
                    future.cancel()
            self.active_users.clear()
            self.user_futures.clear()
