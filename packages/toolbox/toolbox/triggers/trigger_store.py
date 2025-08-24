import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Self

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
from sqlalchemy.types import Boolean, TypeDecorator

from toolbox.db import TOOLBOX_DB_DIR
from toolbox.triggers.cron_utils import calculate_next_run_time, is_valid_cron

TRIGGER_DB_PATH = TOOLBOX_DB_DIR / "triggers.db"


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
    cron_schedule: Mapped[str | None] = mapped_column(String, nullable=True)
    script_path: Mapped[str] = mapped_column(String)
    event_names: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    event_sources: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTimeUTC(), index=True, nullable=True
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
    __tablename__ = "triggered_events"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_id: Mapped[int] = mapped_column(ForeignKey("triggers.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("trigger_executions.id"))


class TriggerStore:
    def __init__(self, engine: Engine, session_factory: sessionmaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: sessionmaker[Session] = session_factory

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
        event_names: list[str] | None = None,
        event_sources: list[str] | None = None,
    ) -> Trigger:
        if cron_schedule and not is_valid_cron(cron_schedule):
            raise ValueError(f"Invalid cron schedule: {cron_schedule}")

        next_run_at = None
        if cron_schedule and enabled:
            try:
                next_run_at = calculate_next_run_time(cron_schedule, utcnow())
            except ValueError:
                pass

        with self.session_factory() as session:
            with session.begin():
                if name is None:
                    temp_name = f"temp_{uuid.uuid4().hex[:8]}"
                    trigger = Trigger(
                        name=temp_name,
                        cron_schedule=cron_schedule,
                        script_path=str(script_path),
                        enabled=enabled,
                        next_run_at=next_run_at,
                        event_names=event_names,
                        event_sources=event_sources,
                    )
                    session.add(trigger)
                    session.flush()
                    new_name = f"trigger-{trigger.id}"
                    trigger.name = new_name
                    session.flush()
                else:
                    trigger = Trigger(
                        name=name,
                        cron_schedule=cron_schedule,
                        script_path=str(script_path),
                        enabled=enabled,
                        next_run_at=next_run_at,
                        event_names=event_names,
                        event_sources=event_sources,
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
        """Update trigger fields and recalculate next_run_at if needed.

        Returns:
            True if a row was updated, False if trigger not found.
        """
        if (
            cron_schedule is not _UNSET
            and cron_schedule is not None
            and not is_valid_cron(cron_schedule)
        ):
            raise ValueError(f"Invalid cron schedule: {cron_schedule}")

        with self.session_factory() as session:
            with session.begin():
                trigger = session.query(Trigger).filter(Trigger.id == id_).first()
                if not trigger:
                    return False

                recalc_next_run = False

                if enabled is not _UNSET:
                    trigger.enabled = enabled
                    recalc_next_run = True

                if cron_schedule is not _UNSET:
                    trigger.cron_schedule = cron_schedule
                    recalc_next_run = True

                if script_path is not _UNSET:
                    trigger.script_path = str(script_path)

                if recalc_next_run:
                    if trigger.enabled and trigger.cron_schedule:
                        try:
                            trigger.next_run_at = calculate_next_run_time(
                                trigger.cron_schedule, utcnow()
                            )
                        except ValueError:
                            trigger.next_run_at = None
                    else:
                        trigger.next_run_at = None

                return True

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

    def get_due_triggers(self, now: datetime) -> list[Trigger]:
        """Get all enabled triggers that are due to run now.

        This method efficiently queries triggers using the next_run_at index,
        avoiding expensive cron calculations in the scheduler loop.

        Args:
            now: Current UTC datetime to check against

        Returns:
            List of triggers that should run now
        """
        with self.session_factory() as session:
            return (
                session.query(Trigger)
                .filter(
                    Trigger.enabled,
                    Trigger.next_run_at.is_not(None),
                    Trigger.next_run_at <= now,
                )
                .order_by(Trigger.next_run_at.asc())
                .all()
            )

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

    def update_next_run_time(
        self, trigger_id: int, from_time: datetime | None = None
    ) -> bool:
        """Update the next_run_at time for a trigger based on its cron schedule.

        Args:
            trigger_id: ID of the trigger to update
            from_time: Time to calculate from (defaults to now)

        Returns:
            True if trigger was found and updated, False otherwise
        """
        if from_time is None:
            from_time = utcnow()

        with self.session_factory() as session:
            with session.begin():
                trigger = (
                    session.query(Trigger).filter(Trigger.id == trigger_id).first()
                )

                if not trigger:
                    return False

                # Only update if trigger has a cron schedule and is enabled
                if not trigger.cron_schedule or not trigger.enabled:
                    # Set to None for event-based or disabled triggers
                    trigger.next_run_at = None
                else:
                    try:
                        trigger.next_run_at = calculate_next_run_time(
                            trigger.cron_schedule, from_time
                        )
                    except ValueError:
                        # Invalid cron schedule - set to None
                        trigger.next_run_at = None

                return True


class EventStore:
    def __init__(self, engine: Engine, session_factory: sessionmaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: sessionmaker[Session] = session_factory

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
        name: str | list[str] | None = None,
        source: str | list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Event]:
        with self.session_factory() as session:
            query = session.query(Event)

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
        """Get events matching a trigger's criteria.

        Args:
            trigger: The trigger to get events for
            is_consumed: Filter by consumption status (None for all)
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of matching Event objects
        """
        with self.session_factory() as session:
            query = session.query(Event)

            name_filter = None
            source_filter = None

            if trigger.event_names:
                name_filter = Event.name.in_(trigger.event_names)

            if trigger.event_sources:
                source_filter = Event.source.in_(trigger.event_sources)

            if name_filter is not None:
                query = query.filter(name_filter)
            if source_filter is not None:
                query = query.filter(source_filter)

            query = query.filter(Event.timestamp >= trigger.created_at)

            if is_consumed is not None:
                consumed_event_ids = session.query(TriggeredEvent.event_id).filter(
                    TriggeredEvent.trigger_id == trigger.id
                )
                if is_consumed:
                    query = query.filter(Event.id.in_(consumed_event_ids))
                else:
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
    def __init__(self, engine: Engine, session_factory: sessionmaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: sessionmaker[Session] = session_factory

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
                            "completed_at": utcnow(),
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
    def __init__(self, engine: Engine, session_factory: sessionmaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: sessionmaker[Session] = session_factory

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
