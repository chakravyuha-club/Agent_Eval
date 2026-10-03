"""
Login throttling (in-process, thread-safe).

NOTE: state is per process. With several uvicorn workers/containers, back this with Redis
(INCR + EXPIRE on the same key) - the interface here is deliberately tiny so that swap is trivial.
"""
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Tuple


class LoginThrottle:
    def __init__(self, max_failures: int = 5, window_seconds: int = 900, lockout_seconds: int = 900,
                 clock=time.monotonic):
        self.max_failures, self.window, self.lockout, self.clock = max_failures, window_seconds, lockout_seconds, clock
        self._fails: Dict[str, Deque[float]] = defaultdict(deque)
        self._locked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> Tuple[bool, int]:
        """(allowed, retry_after_seconds)"""
        now = self.clock()
        with self._lock:
            until = self._locked_until.get(key)
            if until and until > now:
                return False, int(until - now) + 1
            if until:
                del self._locked_until[key]
            return True, 0

    def record_failure(self, key: str) -> None:
        now = self.clock()
        with self._lock:
            q = self._fails[key]
            q.append(now)
            while q and q[0] < now - self.window:
                q.popleft()
            if len(q) >= self.max_failures:
                self._locked_until[key] = now + self.lockout
                q.clear()

    def record_success(self, key: str) -> None:
        with self._lock:
            self._fails.pop(key, None)
            self._locked_until.pop(key, None)


login_throttle = LoginThrottle()
