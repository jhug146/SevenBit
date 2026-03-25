import threading


class ImageStore:
    """Thread-safe per-SKU cache for image upload results.

    Ensures that concurrent callers for the same SKU only trigger one real upload.
    The double-checked lock prevents two threads that both saw a cache miss from
    both running the upload function.
    """

    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()

    def get(self, sku, upload_fn, *args):
        if sku in self._cache:
            return self._cache[sku]
        with self._lock:
            if sku in self._cache:   # re-check after acquiring lock
                return self._cache[sku]
            result = upload_fn(*args)
            self._cache[sku] = result
            return result

    def clear(self, sku):
        self._cache.pop(sku, None)
