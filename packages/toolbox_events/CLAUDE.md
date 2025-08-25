# toolbox_events: Library Design Document

## General instructions

- Never use relative imports, always use absolute imports
- Use pydantic for models
- Use pydantic-settings for configuration
- No need to define **all** in any module

## 1. Project Goal

`toolbox_events` provides event-driven automation for the syft-toolbox ecosystem. It enables:

- MCP servers to emit events to a central daemon
- Trigger scripts to consume batched events from the daemon
- Scripts to send notifications to users (planned)
- Extensible backends for transport and notification delivery

## 2. Core Architecture

### Current Implementation

Two main components are currently implemented:

1. **EventSink**: For sending events (used by MCP servers)

   - Memory sink for testing/development
   - HTTP sink for daemon communication

2. **EventSource**: For receiving events (used by trigger scripts)
   - Memory source for testing/development
   - Stdin source for JSON event consumption

### Planned Components

3. **Notifier**: For sending notifications to users (used by trigger scripts) - **TO BE IMPLEMENTED**

Each component has its own `from_config()` factory method, can be used independently, and has a corresponding top-level convenience function.

### a. Events Module (`events/`)

#### EventSink (`sinks.py`)

- Abstract base class with `from_config()` factory method
- `send(name, data, source)` method for emitting events
- Implementations:
  - **MemorySink**: In-memory storage for testing
  - **HttpSink**: Posts events to daemon via HTTP

#### EventSource (`sources.py`)

- Abstract base class with `from_config()` factory method
- `get_events()` method returning list of events
- Implementations:
  - **MemorySource**: Reads from in-memory sink (can be linked for testing)
  - **StdinSource**: Reads JSON events from stdin

#### Event Model (`models.py`)

- **Event**: Pydantic model with name, data, timestamp, and source fields
- Automatic UTC timestamp generation
- `full_name` property combining source and name

### b. Notifications Module (`notifications/`) - **PLANNED**

- **Notifier**: Interface for sending human-readable messages

  - `from_config(config)` factory method
  - `notify(topic, message, level)` method
  - Example implementations might include:
    - Console output
    - Push notification services (e.g., ntfy.sh)
    - In-memory storage for testing

- **models.py**: Notification level, message, metadata

### c. Settings (`settings.py`)

- **EventSinkSettings**: Pydantic settings for sink configuration

  - Environment prefix: `TOOLBOX_EVENTS_SINK_`
  - Settings: kind, source_name, daemon_url, timeout, headers

- **EventSourceSettings**: Pydantic settings for source configuration
  - Environment prefix: `TOOLBOX_EVENTS_SOURCE_`
  - Settings: kind

### d. Daemon Client (`daemon_client.py`)

- **DaemonClient**: Used internally by HttpSink
  - Methods: `health()`, `send_events()`
  - Uses httpx

## 3. Key Design Decisions

### Component Independence

- EventSink and EventSource are completely independent
- MCP servers only need EventSink
- Trigger scripts need EventSource and optionally Notifier (when implemented)

### Dependency Injection

- Factory methods (`from_config()`) handle construction based on configuration
- Top-level functions (`send_event()`, `get_events()`) delegate to lazily-initialized default instances

### Configuration System

- Uses pydantic-settings with environment prefixes
- Defaults to "memory" implementation for development/testing

### Data Flow

- Flow: `MCP → EventSink → Daemon → EventSource → Script → Notifier → Human`
- Each arrow represents a boundary where components can be swapped

## 4. Current Directory Structure

```
packages/toolbox_events/
├── src/toolbox_events/
│   ├── __init__.py          # Public API: send_event(), get_events()
│   ├── settings.py          # EventSinkSettings, EventSourceSettings
│   ├── daemon_client.py     # DaemonClient for HTTP communication
│   ├── events/
│   │   ├── __init__.py
│   │   ├── sinks.py         # EventSink ABC, MemorySink, HttpSink
│   │   ├── sources.py       # EventSource ABC, MemorySource, StdinSource
│   │   └── models.py        # Event model
│   └── notifications/       # TO BE IMPLEMENTED
│       ├── __init__.py
│       ├── notifiers/
│       │   ├── __init__.py
│       │   └── base.py      # Notifier ABC with from_config()
│       └── models.py        # Notification dataclasses
├── tests/
│   ├── test_settings.py
│   ├── test_http_sink.py
│   ├── test_memory.py
│   └── test_stdin.py
└── pyproject.toml
```

## 5. Usage Examples

### MCP Server (Using EventSink)

```python
# Simple: Use top-level function
from toolbox_events import send_event

send_event("file.created", {"path": "/vault/note.md", "size": 1024})

# Explicit: Configure sink directly
from toolbox_events.events.sinks import EventSink
from toolbox_events.settings import EventSinkSettings

config = EventSinkSettings(kind="http", source_name="my-mcp-server")
sink = EventSink.from_config(config)
sink.send("file.created", {"path": "/vault/note.md", "size": 1024})
```

### Trigger Script (Using EventSource)

```python
# Simple: Use top-level functions
from toolbox_events import get_events

events = get_events()  # Always returns list for batch compatibility

for event in events:
    if event.name == "file.created":
        process_file(event.data["path"])
        print(f"Processed {event.data['path']}")

# Explicit: Configure source directly
from toolbox_events.events.sources import EventSource
from toolbox_events.settings import EventSourceSettings

config = EventSourceSettings(kind="stdin")
source = EventSource.from_config(config)

events = source.get_events()
for event in events:
    process_file(event.data["path"])
```

### Testing with Memory Implementation

```python
from toolbox_events.events.sinks import MemorySink
from toolbox_events.events.sources import MemorySource

# Create linked sink and source for testing
sink = MemorySink(source_name="test-mcp")
source = MemorySource(sink=sink)

# Send events through sink
sink.send("test.event", {"value": 42})

# Retrieve events from source
events = source.get_events()
assert len(events) == 1
assert events[0].name == "test.event"
assert events[0].data["value"] == 42
```

### Testing with HTTP Sink

```python
from toolbox_events.events.sinks import HttpSink

# Configure HTTP sink to send to daemon
sink = HttpSink(
    daemon_url="http://localhost:8000",
    source_name="my-mcp-server"
)

# Send event to daemon
with sink:
    sink.send("file.created", {"path": "/vault/note.md"})
```

### Reading Events from Stdin

```python
# Script that receives events via stdin
from toolbox_events.events.sources import StdinSource

source = StdinSource()
events = source.get_events()

# Process all events
for event in events:
    print(f"Received {event.name} from {event.source}")
    print(f"Data: {event.data}")
```

### Environment Configuration

```bash
# Configure sink to use HTTP
export TOOLBOX_EVENTS_SINK_KIND=http
export TOOLBOX_EVENTS_SINK_DAEMON_URL=http://localhost:8000
export TOOLBOX_EVENTS_SINK_SOURCE_NAME=my-mcp-server

# Configure source to use stdin
export TOOLBOX_EVENTS_SOURCE_KIND=stdin
```

### Custom Implementation Example

```python
from toolbox_events.events.sinks import EventSink
from toolbox_events.events.models import Event
from typing import ClassVar

class FileSink(EventSink):
    kind: ClassVar[str] = "file"

    def __init__(self, file_path: str, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path

    def _send(self, event: Event) -> None:
        # Append event to file
        with open(self.file_path, "a") as f:
            f.write(event.model_dump_json() + "\n")
```

### Planned Notifier Usage (Future)

```python
# Future: Use top-level function for notifications
from toolbox_events import notify

notify("my-notifications", "Processing completed successfully", level="info")

# Future: Explicit notifier configuration
from toolbox_events.notifications import Notifier
from toolbox_events.settings import NotifierSettings

config = NotifierSettings(kind="ntfy", topic="my-notifications")
notifier = Notifier.from_config(config)
notifier.notify("my-notifications", "Task completed", level="success")
```
