# toolbox_events: Library Design Plan

**Note**: The specific implementations mentioned throughout this document (e.g., stdio, file, API, ntfy) are illustrative examples to demonstrate the architecture pattern. The actual implementations will be determined based on needs as the library evolves.

## General instructions

- Never use relative imports, always use absolute imports
- Use pydantic for models
- Use pydantic-settings for configuration
- No need to define **all** in any module

## 1. Project Goal

`toolbox_events` provides event-driven automation for the syft-toolbox ecosystem. It enables:

- MCP servers to emit events to a central daemon
- Trigger scripts to consume batched events from the daemon
- Scripts to send notifications to users
- Extensible backends for transport and notification delivery

## 2. Core Architecture

### Independent Components

Three separate, independently configurable components:

1. **EventSink**: For sending events (used by MCP servers)
2. **EventSource**: For receiving events (used by trigger scripts)
3. **Notifier**: For sending notifications to users (used by trigger scripts)

Each component:

- Has its own `from_config()` factory method
- Can be used independently without the others
- Has a corresponding top-level convenience function

### a. Events Module (`events/`)

**Purpose**: Machine-to-machine communication of structured event data.

- **EventSink**: Interface for sending events from MCP servers

  - `from_config(config)` factory method
  - `emit(event_type, data)` method
  - Example implementations might include:
    - POSTing to daemon endpoint
    - Appending to local queue file
    - Writing to stdout for chaining

- **EventSource**: Interface for receiving events in trigger scripts

  - `from_config(config)` factory method
  - `get_events()` method
  - Example implementations might include:
    - Reading JSON from stdin
    - Fetching from daemon via HTTP
    - Reading from environment variables
    - Reading from file paths

- **models.py**: Event dataclasses with type, source, data, timestamp

### b. Notifications Module (`notifications/`)

**Purpose**: Machine-to-human communication.

- **Notifier**: Interface for sending human-readable messages

  - `from_config(config)` factory method
  - `notify(message, level)` method
  - Example implementations might include:
    - Console output
    - Push notification services (e.g., ntfy.sh)
    - In-memory storage for testing

- **models.py**: Notification level, message, metadata

### c. Configuration Module (`config/`)

**Purpose**: Configure which adapters to use for sinks/sources/notifiers.

- **Config**: Configuration for the library
  - Factory methods to create configured sources, sinks, and notifiers
  - Could load from environment variables, config files, etc.
  - `from_env()`, `from_file()` class methods for different config sources

### d. Daemon Module (`daemon/`)

**Purpose**: HTTP client for daemon API.

- **DaemonClient**: Encapsulates daemon HTTP endpoints
  - Used internally by API-based sinks and sources
  - Handles event emission, retrieval, future trigger management

## 3. Key Design Decisions

### Component Independence

- **EventSink**, **EventSource**, and **Notifier** are completely independent
- MCP servers only need EventSink
- Trigger scripts typically need EventSource and optionally Notifier
- Each component can be tested in isolation

### Dependency Injection

- Each component uses constructor injection for its dependencies
- Factory methods (`from_config()`) handle construction
- Top-level functions (`emit()`, `get_events()`, `notify()`) delegate to default instances
- Full testability through explicit dependencies

### Data Flow

- Flow: `MCP → EventSink → Daemon → EventSource → Script → Notifier → Human`
- Each arrow represents a boundary where components can be swapped

## 4. Directory Structure (Illustrative)

**Note**: The specific sink/source/notifier implementations shown here are examples. Actual implementations will be added as needed.

```
packages/toolbox_events/
├── src/toolbox_events/
│   ├── __init__.py          # Public API: emit(), get_events(), notify()
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py          # Config ABC
│   │   └── ... (configuration implementations)
│   ├── daemon/
│   │   ├── __init__.py
│   │   └── client.py        # DaemonClient
│   ├── events/
│   │   ├── __init__.py
│   │   ├── sinks/
│   │   │   ├── __init__.py
│   │   │   ├── base.py      # EventSink ABC with from_config()
│   │   │   └── ... (various sink implementations)
│   │   ├── sources/
│   │   │   ├── __init__.py
│   │   │   ├── base.py      # EventSource ABC with from_config()
│   │   │   └── ... (various source implementations)
│   │   └── models.py        # Event dataclasses
│   └── notifications/
│       ├── __init__.py
│       ├── notifiers/
│       │   ├── __init__.py
│       │   ├── base.py      # Notifier ABC with from_config()
│       │   └── ... (various notifier implementations)
│       └── models.py        # Notification dataclasses
├── tests/
│   └── ...
└── pyproject.toml
```

## 5. Usage Examples

**Note**: These examples show the intended API patterns and usage. The specific implementations (MemorySink, KafkaSink, etc.) are illustrative - actual implementations will be created as needed.

### MCP Server (Only EventSink)

```python
# Simple: Use top-level function
from toolbox_events import emit

emit("file.created", {"path": "/vault/note.md", "size": 1024})

# Explicit: Configure sink directly
from toolbox_events.events.sinks import EventSink
from toolbox_events.config import Config

config = Config.from_env()
sink = EventSink.from_config(config)
sink.emit("file.created", {"path": "/vault/note.md", "size": 1024})
```

### Trigger Script (EventSource + Notifier)

```python
# Simple: Use top-level functions
from toolbox_events import get_events, notify

events = get_events()  # Always returns list for batch compatibility

for event in events:
    if event["type"] == "file.created":
        process_file(event["data"]["path"])
        notify(f"Processed {event['data']['path']}", level="info")

# Explicit: Configure components directly
from toolbox_events.events.sources import EventSource
from toolbox_events.notifications import Notifier
from toolbox_events.config import Config

config = Config.from_env()
source = EventSource.from_config(config)
notifier = Notifier.from_config(config)

events = source.get_events()
for event in events:
    process_file(event["data"]["path"])
    notifier.notify(f"Processed {event['data']['path']}")
```

### Testing MCP Server (Only Mock Sink)

```python
from toolbox_events.events.sinks import MemorySink

# Only need to mock the sink
sink = MemorySink()

# Run MCP server code with injected sink
run_mcp_server(sink=sink)

# Assert events were sent to sink
assert len(sink.emitted_events) == 1
assert sink.emitted_events[0]["type"] == "file.created"
```

### Testing Trigger Script (Mock Source + Notifier)

```python
from toolbox_events.events.sources import MemorySource
from toolbox_events.notifications import MemoryNotifier

# Only need what the trigger uses
source = MemorySource()
source.add_event({"type": "test.event", "data": {"value": 42}})

notifier = MemoryNotifier()

# Run trigger with injected dependencies
run_trigger(source=source, notifier=notifier)

# Assert on what was used
assert source.events_consumed == 1
assert len(notifier.messages) == 1
```

### Custom Implementation

```python
from toolbox_events.events.sinks import EventSink
from toolbox_events.events import Event

class CustomKafkaSink(EventSink):
    @classmethod
    def from_config(cls, config: Config) -> "CustomKafkaSink":
        return cls(brokers=config.get("kafka_brokers"))

    def emit(self, event_type: str, data: dict) -> None:
        # Kafka implementation
        pass

# Use in MCP server
sink = CustomKafkaSink.from_config(config)
sink.emit("custom.event", {"data": "value"})
```

### Top-level Implementation

```python
# In toolbox_events/__init__.py

_default_sink: EventSink | None = None
_default_source: EventSource | None = None
_default_notifier: Notifier | None = None

def emit(event_type: str, data: dict[str, Any]) -> None:
    global _default_sink
    if _default_sink is None:
        config = Config.from_env()
        _default_sink = EventSink.from_config(config)
    _default_sink.emit(event_type, data)

def get_events() -> list[Event]:
    global _default_source
    if _default_source is None:
        config = Config.from_env()
        _default_source = EventSource.from_config(config)
    return _default_source.get_events()

def notify(message: str, level: str = "info") -> None:
    global _default_notifier
    if _default_notifier is None:
        config = Config.from_env()
        _default_notifier = Notifier.from_config(config)
    _default_notifier.notify(message, level)
```
