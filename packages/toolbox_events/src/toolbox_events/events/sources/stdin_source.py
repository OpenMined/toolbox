import json
import sys
from typing import Any

from loguru import logger
from toolbox_events.events.models import Event
from toolbox_events.events.sources.base import EventSource


class StdinSource(EventSource):
    """Event source that reads events from stdin as JSON."""

    kind = "stdin"

    def __init__(self, **kwargs: Any):
        self._events: list[Event] | None = None

    def get_events(self) -> list[Event]:
        """
        Read events from stdin once and cache them.
        Expected stdin format: {"events": [{"name": "...", "data": {...}, "source": "..."}, ...]}
        """
        if self._events is None:
            logger.debug("Reading events from stdin")
            try:
                stdin_content = sys.stdin.read().strip()
                if not stdin_content:
                    logger.debug("No data available on stdin")
                    self._events = []
                else:
                    data = json.loads(stdin_content)
                    if isinstance(data, dict):
                        events_data = data.get("events", [])
                        self._events = [
                            Event(**event_data) for event_data in events_data
                        ]
                        logger.info(f"Loaded {len(self._events)} events from stdin")
                    else:
                        raise ValueError(
                            "Invalid stdin format: expected JSON object with 'events' key"
                        )
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse events from stdin: {e}") from e

        return self._events
