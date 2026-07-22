"""
---------------------------------------------------------
Trend Analyzer for the ASX

Simple API Cache

Caches API responses temporarily to reduce
duplicate requests and API rate limiting.
---------------------------------------------------------
"""

import time
import threading


class APICache:

    def __init__(self):

        self.cache = {}
        self._lock = threading.Lock()

    def get(self, key):

        with self._lock:
            if key not in self.cache:
                return None

            data, expiry = self.cache[key]

            if time.time() > expiry:

                del self.cache[key]

                return None

            return data

    def set(self, key, value, timeout):

        with self._lock:
            self.cache[key] = (

                value,

                time.time() + timeout

            )

    def clear(self):

        with self._lock:
            self.cache.clear()


api_cache = APICache()
