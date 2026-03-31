import queue as _queue


class _AppState:
    def __init__(self):
        self.item_list = None
        self.upload = None
        self.upload_changer = None
        self.item_type = None
        self.get_items = None
        self.actions = None
        self.title = "SevenBit"
        self.outlined_items = []
        self.outlined_red = False
        self.sse_queue = _queue.Queue()
        self.upload_display = None


state = _AppState()
