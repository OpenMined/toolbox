from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Self

from croniter import croniter
from sqlalchemy import JSON, DateTime, Integer, String, create_engine
from sqlalchemy.engine import Dialect, Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.orm.properties import ForeignKey
from sqlalchemy.orm.session import sessionmaker as SessionMaker
from sqlalchemy.sql import func
from sqlalchemy.types import Boolean, TypeDecorator

from toolbox.db import TOOLBOX_DB_DIR

TRIGGER_DB_PATH = TOOLBOX_DB_DIR / "triggers.db"

__all__ = ("DateTimeUTC",)


class DateTimeUTC(TypeDecorator[datetime]):
    """Timezone Aware DateTime.

    Ensure UTC is stored in the database and that TZ aware dates are returned for all dialects.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    @property
    def python_type(self) -> type[datetime]:
        return datetime

    def process_bind_param(
        self, value: Optional[datetime], dialect: Dialect
    ) -> Optional[datetime]:
        if value is None:
            return value
        if not value.tzinfo:
            msg = "tzinfo is required"
            raise TypeError(msg)
        return value.astimezone(timezone.utc)

    def process_result_value(
        self, value: Optional[datetime], dialect: Dialect
    ) -> Optional[datetime]:
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    pass


# Sentinel for update methods to distinguish between "don't update" and "set to None"
_UNSET = object()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Trigger(Base):
    __tablename__ = "triggers"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeUTC(), index=True, default=utcnow
    )
    name: Mapped[str] = mapped_column(String, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cron_schedule: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # Nullable to allow for future event-based triggers
    script_path: Mapped[str] = mapped_column(String)
    event_names: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    event_sources: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    @property
    def is_event_based(self) -> bool:
        return bool(self.event_names or self.event_sources)


class TriggerExecution(Base):
    __tablename__ = "trigger_executions"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_id: Mapped[int] = mapped_column(ForeignKey("triggers.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTimeUTC(), index=True, default=utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTimeUTC(), nullable=True)
    logs: Mapped[str] = mapped_column(String, default="")
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    data: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(
        DateTimeUTC(), index=True, default=utcnow
    )


class TriggeredEvent(Base):
    # Link table to track which triggers consumed which events.
    __tablename__ = "triggered_events"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_id: Mapped[int] = mapped_column(ForeignKey("triggers.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("trigger_executions.id"))


class TriggerStore:
    def __init__(self, engine: Engine, session_factory: SessionMaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: SessionMaker[Session] = session_factory

    @classmethod
    def from_url(cls, db_url: str) -> Self:
        engine = create_engine(db_url)
        session_factory = sessionmaker(bind=engine)
        return cls(engine, session_factory)

    def create(
        self,
        name: str | None,
        cron_schedule: str | None,
        script_path: str | Path,
        enabled: bool = True,
    ) -> Trigger:
        if not croniter.is_valid(cron_schedule):
            raise ValueError(f"Invalid cron schedule: {cron_schedule}")

        with self.session_factory() as session:
            with session.begin():
                if name is None:
                    # Use the flush approach to get the actual ID and set the name.
                    import uuid

                    temp_name = f"temp_{uuid.uuid4().hex[:8]}"
                    trigger = Trigger(
                        name=temp_name,
                        cron_schedule=cron_schedule,
                        script_path=str(script_path),
                        enabled=enabled,
                    )
                    session.add(trigger)
                    session.flush()  # Get the actual ID

                    # Now set the real name using the actual ID
                    new_name = f"trigger-{trigger.id}"
                    trigger.name = new_name
                    # Force another flush to ensure the name update is persisted
                    session.flush()
                else:
                    trigger = Trigger(
                        name=name,
                        cron_schedule=cron_schedule,
                        script_path=str(script_path),
                        enabled=enabled,
                    )
                    session.add(trigger)
                    session.flush()

                session.refresh(trigger)
                session.expunge(trigger)
                return trigger

    def update(
        self,
        id_: int,
        *,
        enabled=_UNSET,
        cron_schedule=_UNSET,
        script_path=_UNSET,
    ) -> bool:
        """Update trigger fields. Use None to explicitly set nullable fields to None.
        Returns True if a row was updated, False if trigger not found."""
        updates = {}

        if enabled is not _UNSET:
            updates["enabled"] = enabled

        if cron_schedule is not _UNSET:
            updates["cron_schedule"] = cron_schedule

        if script_path is not _UNSET:
            updates["script_path"] = str(script_path)

        if not updates:
            return False  # No updates to perform

        with self.session_factory() as session:
            with session.begin():
                rows_updated = (
                    session.query(Trigger).filter(Trigger.id == id_).update(updates)
                )
                return rows_updated > 0

    def get(self, id_: int) -> Trigger | None:
        with self.session_factory() as session:
            return session.query(Trigger).filter(Trigger.id == id_).first()

    def get_by_name(self, name: str) -> Trigger | None:
        with self.session_factory() as session:
            return session.query(Trigger).filter(Trigger.name == name).first()

    def get_all(
        self,
        enabled: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
        has_schedule: bool | None = None,
    ) -> list[Trigger]:
        with self.session_factory() as session:
            query = session.query(Trigger)

            if enabled is not None:
                query = query.filter(Trigger.enabled == enabled)

            if has_schedule is not None:
                if has_schedule:
                    query = query.filter(Trigger.cron_schedule.is_not(None))
                else:
                    query = query.filter(Trigger.cron_schedule.is_(None))

            query = query.order_by(Trigger.created_at.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()

    def delete(self, id_: int) -> bool:
        with self.session_factory() as session:
            with session.begin():
                rows_deleted = session.query(Trigger).filter(Trigger.id == id_).delete()
                return rows_deleted > 0

    def delete_by_name(self, name: str) -> bool:
        with self.session_factory() as session:
            with session.begin():
                rows_deleted = (
                    session.query(Trigger).filter(Trigger.name == name).delete()
                )
                return rows_deleted > 0

    def delete_all(self) -> bool:
        with self.session_factory() as session:
            with session.begin():
                rows_deleted = session.query(Trigger).delete()
                return rows_deleted > 0


class EventStore:
    def __init__(self, engine: Engine, session_factory: SessionMaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: SessionMaker[Session] = session_factory

    def create(
        self, name: str, source: str | None, data: dict, timestamp: datetime
    ) -> Event:
        event = Event(name=name, source=source, data=data, timestamp=timestamp)
        with self.session_factory() as session:
            with session.begin():
                session.add(event)
                session.flush()
                session.refresh(event)
                session.expunge(event)
                return event

    def create_many(self, events: list[dict]) -> list[Event]:
        """Create multiple events in a single transaction"""
        db_events = [
            Event(
                name=event["name"],
                source=event.get("source"),
                data=event["data"],
                timestamp=event["timestamp"],
            )
            for event in events
        ]

        with self.session_factory() as session:
            with session.begin():
                session.add_all(db_events)
                session.flush()
                for event in db_events:
                    session.refresh(event)
                    session.expunge(event)
                return db_events

    def get(self, id_: int) -> Event | None:
        with self.session_factory() as session:
            return session.query(Event).filter(Event.id == id_).first()

    def get_all(
        self,
        is_consumed: bool | None = None,
        name: str | list[str] | None = None,
        source: str | list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Event]:
        with self.session_factory() as session:
            query = session.query(Event)

            if is_consumed is not None:
                if is_consumed:
                    query = query.filter(Event.consumed_at.is_not(None))
                else:
                    query = query.filter(Event.consumed_at.is_(None))

            if name:
                if isinstance(name, list):
                    query = query.filter(Event.name.in_(name))
                else:
                    query = query.filter(Event.name == name)

            if source:
                if isinstance(source, list):
                    query = query.filter(Event.source.in_(source))
                else:
                    query = query.filter(Event.source == source)

            query = query.order_by(Event.timestamp.asc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()

    def get_events_for_trigger(
        self,
        trigger: Trigger,
        is_consumed: bool | None = False,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Event]:
        """Get events matching a trigger's criteria that haven't been consumed by this trigger yet"""
        with self.session_factory() as session:
            query = session.query(Event)

            # Filter by trigger's event criteria
            name_filter = None
            source_filter = None

            if trigger.event_names:
                name_filter = Event.name.in_(trigger.event_names)

            if trigger.event_sources:
                source_filter = Event.source.in_(trigger.event_sources)

            # Apply name and source filters with AND logic if both exist
            if name_filter is not None:
                query = query.filter(name_filter)
            if source_filter is not None:
                query = query.filter(source_filter)

            # Filter by consumption status
            if is_consumed is not None:
                consumed_event_ids = (
                    session.query(TriggeredEvent.event_id)
                    .filter(TriggeredEvent.trigger_id == trigger.id)
                    .subquery()
                )
                if is_consumed:
                    # Only get events consumed by this trigger
                    query = query.filter(Event.id.in_(consumed_event_ids))
                else:
                    # Filter out events already consumed by this trigger
                    query = query.filter(Event.id.notin_(consumed_event_ids))

            query = query.order_by(Event.timestamp.asc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()

    def mark_events_triggered(
        self, trigger_id: int, event_ids: list[int], execution_id: int
    ) -> None:
        """Link events to trigger execution"""
        triggered_events = [
            TriggeredEvent(
                trigger_id=trigger_id, event_id=event_id, execution_id=execution_id
            )
            for event_id in event_ids
        ]
        with self.session_factory() as session:
            with session.begin():
                session.add_all(triggered_events)


class TriggerExecutionStore:
    def __init__(self, engine: Engine, session_factory: SessionMaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: SessionMaker[Session] = session_factory

    @classmethod
    def from_url(cls, db_url: str) -> Self:
        engine = create_engine(db_url)
        session_factory = sessionmaker(bind=engine)
        return cls(engine, session_factory)

    def create(self, trigger_id: int) -> TriggerExecution:
        trigger_execution = TriggerExecution(trigger_id=trigger_id)
        with self.session_factory() as session:
            with session.begin():
                session.add(trigger_execution)
                session.flush()
                session.refresh(trigger_execution)
                session.expunge(trigger_execution)
                return trigger_execution

    def set_completed(self, id_: int, exit_code: int, logs: str) -> bool:
        """Mark execution as completed. Returns True if execution was found and updated."""
        with self.session_factory() as session:
            with session.begin():
                rows_updated = (
                    session.query(TriggerExecution)
                    .filter(TriggerExecution.id == id_)
                    .update(
                        {
                            "completed_at": func.now(),
                            "exit_code": exit_code,
                            "logs": logs,
                        }
                    )
                )
                return rows_updated > 0

    def get(self, id_: int) -> TriggerExecution | None:
        with self.session_factory() as session:
            return (
                session.query(TriggerExecution)
                .filter(TriggerExecution.id == id_)
                .first()
            )

    def get_all(
        self,
        trigger_id: int | None = None,
        exit_code: int | None = None,
        completed: bool | None = None,  # None=all, True=completed, False=pending
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[TriggerExecution]:
        with self.session_factory() as session:
            query = session.query(TriggerExecution)

            if trigger_id:
                query = query.filter(TriggerExecution.trigger_id == trigger_id)

            if exit_code is not None:
                query = query.filter(TriggerExecution.exit_code == exit_code)

            if completed is not None:
                if completed:
                    query = query.filter(TriggerExecution.completed_at.is_not(None))
                else:
                    query = query.filter(TriggerExecution.completed_at.is_(None))

            query = query.order_by(TriggerExecution.created_at.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()


class TriggerDB:
    def __init__(self, engine: Engine, session_factory: SessionMaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: SessionMaker[Session] = session_factory

        # Stores
        self.triggers: TriggerStore = TriggerStore(engine, session_factory)
        self.events: EventStore = EventStore(engine, session_factory)
        self.executions: TriggerExecutionStore = TriggerExecutionStore(
            engine, session_factory
        )

        self._setup()

    def _setup(self) -> None:
        Base.metadata.create_all(self.engine)

    @classmethod
    def from_url(cls, db_url: str) -> Self:
        engine = create_engine(db_url)
        session_factory = sessionmaker(bind=engine)
        return cls(engine, session_factory)

    def close(self) -> None:
        self.engine.dispose()


def get_db() -> TriggerDB:
    return TriggerDB.from_url(f"sqlite:///{TRIGGER_DB_PATH}")


if __name__ == "__main__":
    # in memory sqlite db
    db = TriggerDB.from_url("sqlite://")
    db.triggers.create("test", "0 * * * *", "echo 'test'")
    db.executions.create(1)
    for execution in db.executions.get_all():
        # print all fields in the execution
        for field in execution.__dict__:
            if not field.startswith("_"):
                v = getattr(execution, field)
                # print(f"{field}: {v}, {type(v)}")
                # check if datetimes have a timezone
                if isinstance(v, datetime):
                    print(f"{field}: {v.tzinfo}")
                print(type(v), v)
