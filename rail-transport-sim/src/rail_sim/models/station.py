from collections import deque
from typing import Dict, Deque, Set

class Station:
    """Station with passenger queues."""
    def __init__(self, station_id: str, transfer_time: float = 2.0):
        self.id = station_id
        self.transfer_time = transfer_time  # minutes to transfer between lines
        # Queue per line at this station
        self.queues: Dict[str, Deque[int]] = {}  # line_id -> deque of passenger_ids
        self.lines: Set[str] = set()  # which lines stop here

    def add_line(self, line_id: str):
        """Register a line that stops at this station."""
        self.lines.add(line_id)
        if line_id not in self.queues:
            self.queues[line_id] = deque()

    def add_passenger_to_queue(self, passenger_id: int, line_id: str):
        """Add passenger to queue for specific line."""
        if line_id not in self.queues:
            self.queues[line_id] = deque()
        self.queues[line_id].append(passenger_id)

    def pop_for_boarding(self, line_id: str, max_n: int) -> List[int]:
        """Pop up to max_n passengers FIFO from the queue for a line."""
        q = self.queues.get(line_id)
        if not q:
            return []
        out = []
        for _ in range(min(max_n, len(q))):
            out.append(q.popleft())
        return out

    def get_queue_length(self, line_id: str) -> int:
        """Get number of passengers waiting for a line."""
        q = self.queues.get(line_id)
        return len(q) if q is not None else 0

    def is_transfer_station(self) -> bool:
        """Check if this is a transfer point between lines."""
        return len(self.lines) > 1