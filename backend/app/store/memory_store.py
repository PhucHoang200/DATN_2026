from collections import deque
from typing import Any, Dict, List


class MemoryEventStore:
    def __init__(self, max_events: int = 5000):
        self.max_events = int(max_events)
        self.events = deque(maxlen=self.max_events)
        self.next_event_id = 1

    def add_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event["event_id"] = self.next_event_id
        self.next_event_id += 1
        self.events.appendleft(event)
        return event

    def list_events(self, limit: int = 200) -> List[Dict[str, Any]]:
        return list(self.events)[: int(limit)]

    def stats(self) -> Dict[str, Any]:
        total = len(self.events)
        attack_count = sum(1 for e in self.events if e.get("is_attack", False))
        benign_count = total - attack_count

        by_class = {}
        for e in self.events:
            cls = e.get("class_name", "Unknown")
            by_class[cls] = by_class.get(cls, 0) + 1

        return {
            "total": total,
            "attack_count": attack_count,
            "benign_count": benign_count,
            "by_class": by_class,
        }