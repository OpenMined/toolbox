from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Self

import crontab
from sqlalchemy import DateTime, Integer, String, create_engine
from sqlalchemy.engine import Dialect, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
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


class TriggerStore:
    def __init__(self, engine: Engine, session_factory: SessionMaker[Session]) -> None:
        self.engine: Engine = engine
        self.session_factory: SessionMaker[Session] = session_factory

    @classmethod
    def from_url(cls, db_url: str) -> Self:
        engine = create_engine(db_url)
        session_factory = sessionmaker(bind=engine)
        return cls(engine, session_factory)

    def validate_cron_schedule(self, cron_schedule: str) -> bool:
        if not crontab.CronSlices.is_valid(cron_schedule):
            raise ValueError(f"Invalid cron schedule: {cron_schedule}")

    def create(
        self,
        name: str,
        cron_schedule: str | None,
        script_path: str | Path,
        enabled: bool = True,
    ) -> Trigger:
        trigger = Trigger(
            name=name,
            cron_schedule=cron_schedule,
            script_path=str(script_path),
            enabled=enabled,
        )

        with self.session_factory() as session:
            with session.begin():
                session.add(trigger)
                session.flush()  # Get the ID without committing
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
