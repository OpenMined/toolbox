from abc import ABC, abstractmethod
from typing import Any, ClassVar, Optional

import httpx
from loguru import logger

from toolbox_events.notifications.models import Notification
from toolbox_events.settings import NotifierSettings


class Notifier(ABC):
    """Abstract base class for notification systems"""

    kind: ClassVar[str]

    def __init__(self, default_topic: str | None = None, **kwargs: Any):
        self.default_topic = default_topic

    @classmethod
    def from_config(cls, config: NotifierSettings, **kwargs: Any) -> "Notifier":
        """Factory method to create notifier from configuration"""
        notifier_map = {
            "memory": MemoryNotifier,
            "ntfy": NtfyNotifier,
        }

        notifier_cls = notifier_map.get(config.kind)
        if not notifier_cls:
            raise ValueError(f"Unknown notifier kind: {config.kind}")

        return notifier_cls(**config.model_dump(), **kwargs)

    def notify(
        self,
        message: str,
        title: Optional[str] = None,
        priority: int = 3,
        tags: Optional[list[str]] = None,
        topic: Optional[str] = None,
    ) -> None:
        """Send a notification"""
        try:
            final_topic = topic or self.default_topic
            if final_topic is None:
                logger.error("No topic specified and no default topic configured")
                return

            notification = Notification(
                message=message,
                title=title,
                priority=priority,
                tags=tags,
                topic=final_topic,
            )
            self._notify(notification)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    @abstractmethod
    def _notify(self, notification: Notification) -> None:
        """Internal method to send a notification"""
        pass


class MemoryNotifier(Notifier):
    """In-memory notifier for testing"""

    kind: ClassVar[str] = "memory"

    def __init__(self, default_topic: str | None = None, **kwargs: Any):
        super().__init__(default_topic=default_topic, **kwargs)
        self.notifications: list[Notification] = []

    def _notify(self, notification: Notification) -> None:
        """Store notification in memory"""
        self.notifications.append(notification)

    def clear(self) -> None:
        """Clear all stored notifications"""
        self.notifications.clear()


class NtfyNotifier(Notifier):
    """Notifier that sends notifications to ntfy.sh service"""

    kind: ClassVar[str] = "ntfy"

    def __init__(
        self,
        server_url: str = "https://ntfy.sh",
        timeout: float = 30.0,
        default_topic: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(default_topic=default_topic, **kwargs)
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout

    def _notify(self, notification: Notification) -> None:
        """Send notification to ntfy.sh service"""
        url = f"{self.server_url}/{notification.topic}"

        headers = {}
        if notification.title:
            headers["Title"] = notification.title

        # Map priority (1-5) to ntfy priority names
        priority_map = {
            1: "min",
            2: "low",
            3: "default",
            4: "high",
            5: "urgent",
        }
        headers["Priority"] = priority_map.get(notification.priority, "default")

        if notification.tags:
            headers["Tags"] = ",".join(notification.tags)

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                url,
                data=notification.message,
                headers=headers,
            )
            response.raise_for_status()
            logger.debug(f"Notification sent to ntfy: {notification.topic}")


if __name__ == "__main__":
    # Test notifications to ntfy
    notifier = NtfyNotifier(default_topic="tb-test-1")

    # Test 1: Simple notification with success
    notifier.notify(
        message="Test notification from toolbox_events working correctly",
        title="Test 1: Basic",
        priority=3,
        tags=["heavy_check_mark", "computer"],
    )

    # Test 2: Urgent notification with warning
    notifier.notify(
        message="This is an urgent test alert! Everything is actually fine.",
        title="Test 2: Urgent Alert",
        priority=5,
        tags=["warning", "rotating_light"],
    )

    # Test 3: Success notification
    notifier.notify(
        message="Background process completed successfully. No action needed.",
        title="Test 3: Success",
        priority=2,
        tags=["tada", "partying_face"],
    )

    print("Sent 3 test notifications to tb-test-1")
