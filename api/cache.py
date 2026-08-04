"""
---------------------------------------------------------
Trend Analyzer for the ASX

Simple API Cache

Caches API responses temporarily to reduce
duplicate requests and API rate limiting.

Author: Karan Attavar
---------------------------------------------------------
"""

import time
import threading


class APICache:
    """Store API results in memory until their configured expiry time."""

    def __init__(self):
        """Create an empty thread-safe cache."""

        self.cache = {}
        self._lock = threading.Lock()

    def get(self, key):
        """Return a cached value when present and unexpired, otherwise None."""

        with self._lock:
            if key not in self.cache:
                return None

            data, expiry = self.cache[key]

            if time.time() > expiry:

                del self.cache[key]

                return None

            return data

    def set(self, key, value, timeout):
        """Store a value under a key for the requested number of seconds."""

        with self._lock:
            self.cache[key] = (

                value,

                time.time() + timeout

            )

    def clear(self):
        """Remove every cached API response."""

        with self._lock:
            self.cache.clear()


api_cache = APICache()
