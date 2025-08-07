from datetime import datetime
from pathlib import Path

from sqlalchemy import JSON, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.orm.properties import ForeignKey
from sqlalchemy.schema import Index
from sqlalchemy.sql import func
from sqlalchemy.types import Boolean

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str]
    event_type: Mapped[str]
    data: Mapped[dict] = mapped_column(JSON, default_factory=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_handled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class Trigger(Base):
    __tablename__ = "triggers"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    sources: Mapped[list[str]] = mapped_column(JSON, default_factory=list)
    event_types: Mapped[list[str]] = mapped_column(JSON, default_factory=list)
    cron_schedule: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    script_path: Mapped[str]
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class TriggerExecution(Base):
    __tablename__ = "trigger_executions"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger_id: Mapped[int] = mapped_column(ForeignKey("triggers.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    logs: Mapped[str] = mapped_column(String, default="")
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (Index("ix_trigger_event", "trigger_id", "event_id"),)


class EventStore:
    def __init__(self, engine, session):
        self.engine = engine
        self.session = session

    @classmethod
    def from_url(cls, db_url: str):
        engine = create_engine(db_url)
        session = sessionmaker(bind=engine)
        return cls(engine, session)

    def create(self, source: str, event_type: str, data: dict | None = None):
        if data is None:
            data = {}
        event = Event(source=source, event_type=event_type, data=data)
        with self.session() as session:
            session.add(event)
            session.commit()
        return event

    def update(self, id_: int, **kwargs):
        with self.session() as session:
            session.query(Event).filter(Event.id == id_).update(kwargs)
            session.commit()

    def get(self, id_: int):
        with self.session() as session:
            return session.query(Event).filter(Event.id == id_).first()

    def get_all(
        self,
        source: str | None = None,
        event_type: str | None = None,
        is_handled: bool | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        with self.session() as session:
            query = session.query(Event)

            if source:
                query = query.filter(Event.source == source)

            if event_type:
                query = query.filter(Event.event_type == event_type)

            if is_handled is not None:
                query = query.filter(Event.is_handled == is_handled)

            if created_after:
                query = query.filter(Event.created_at >= created_after)

            if created_before:
                query = query.filter(Event.created_at <= created_before)

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.offset(offset)

            return query.all()


class TriggerStore:
    def __init__(self, engine, session):
        self.engine = engine
        self.session = session

    @classmethod
    def from_url(cls, db_url: str):
        engine = create_engine(db_url)
        session = sessionmaker(bind=engine)
        return cls(engine, session)

    def create(
        self,
        name: str,
        sources: list[str],
        event_types: list[str],
        script_path: str | Path,
        enabled: bool = True,
    ):
        trigger = Trigger(
            name=name,
            sources=sources,
            event_types=event_types,
            script_path=script_path,
            enabled=enabled,
        )

        with self.session() as session:
            session.add(trigger)
            session.commit()
        return trigger

    def update(self, id_: int, enabled: bool):
        with self.session() as session:
            session.query(Trigger).filter(Trigger.id == id_).update(
                {"enabled": enabled}
            )
            session.commit()

    def get(self, id_: int):
        with self.session() as session:
            return session.query(Trigger).filter(Trigger.id == id_).first()

    def get_all(
        self,
        source: str | None = None,
        event_type: str | None = None,
        enabled: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        with self.session() as session:
            query = session.query(Trigger)

            if source:
                query = query.filter(Trigger.sources.contains(source))

            if event_type:
                query = query.filter(Trigger.event_types.contains(event_type))

            if enabled is not None:
                query = query.filter(Trigger.enabled == enabled)

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.offset(offset)

            return query.all()

    def get_triggers_for_event(self, event: Event, enabled: bool | None = True):
        return self.get_all(
            source=event.source,
            event_type=event.event_type,
            enabled=enabled,
        )


class TriggerExecutionStore:
    def __init__(self, engine, session):
        self.engine = engine
        self.session = session

    @classmethod
    def from_url(cls, db_url: str):
        engine = create_engine(db_url)
        session = sessionmaker(bind=engine)
        return cls(engine, session)

    def create(self, trigger_id: int, event_id: int):
        trigger_execution = TriggerExecution(trigger_id=trigger_id, event_id=event_id)
        with self.session() as session:
            session.add(trigger_execution)
            session.commit()

    def set_completed(self, id_: int, exit_code: int, logs: str):
        with self.session() as session:
            session.query(TriggerExecution).filter(TriggerExecution.id == id_).update(
                {
                    "completed_at": func.now(),
                    "exit_code": exit_code,
                    "logs": logs,
                }
            )
            session.commit()

    def get_all(
        self,
        trigger_id: int | None = None,
        event_id: int | None = None,
        exit_code: int | None = None,
        created_before: datetime | None = None,
        created_after: datetime | None = None,
        completed_before: datetime | None = None,
        completed_after: datetime | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        with self.session() as session:
            query = session.query(TriggerExecution)

            if trigger_id:
                query = query.filter(TriggerExecution.trigger_id == trigger_id)

            if event_id:
                query = query.filter(TriggerExecution.event_id == event_id)

            if exit_code:
                query = query.filter(TriggerExecution.exit_code == exit_code)

            if created_before:
                query = query.filter(TriggerExecution.created_at <= created_before)

            if created_after:
                query = query.filter(TriggerExecution.created_at >= created_after)

            if completed_before:
                query = query.filter(TriggerExecution.completed_at <= completed_before)

            if completed_after:
                query = query.filter(TriggerExecution.completed_at >= completed_after)

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.offset(offset)

            return query.all()
