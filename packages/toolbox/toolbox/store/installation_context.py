from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from toolbox.store.callbacks.callback import Callback


class InstallationContext(BaseModel):
    callbacks: list[Callback]
    values: dict[str, Any]

    def __getattr__(self, item: str) -> Any:
        return self.values[item]

    def on_input(self):
        for callback in self.callbacks:
            callback.on_input(self)

    def on_install_init(self, json_body: dict):
        for callback in self.callbacks:
            callback.on_install_init(self, json_body)
