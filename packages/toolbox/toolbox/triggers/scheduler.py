import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from loguru import logger

from toolbox.mcp_installer.uv_utils import find_uv_path
from toolbox.settings import settings
from toolbox.triggers.models import Event, EventBatch
from toolbox.triggers.trigger_store import Trigger, TriggerDB

DEFAULT_TRIGGER_TIMEOUT = 300  # Default timeout for trigger execution in seconds
DEFAULT_SLEEP_INTERVAL = 1  # Sleep interval between scheduler loops in seconds


class Scheduler:
    def __init__(self, db: TriggerDB):
        self.db = db
        self.running = True

    def _process_triggers(self, executor: ThreadPoolExecutor) -> None:
        """Process all due triggers by submitting them to a thread pool"""

        now = datetime.now(timezone.utc)
        due_triggers = self.db.triggers.get_due_triggers(now)
        if not due_triggers:
            return

        logger.debug(f"Processing {len(due_triggers)} due triggers at {now}")
        for trigger in due_triggers:
            try:
                self._execute_from_scheduler(executor, trigger)
            except Exception as e:
                logger.error(f"Failed to schedule trigger {trigger.name}: {e}")
                continue

    def _execute_from_scheduler(
        self,
        executor: ThreadPoolExecutor,
        trigger: Trigger,
    ) -> None:
        """Submit trigger to executor, and schedule next run"""

        # Always schedule next run, even if trigger fails
        if trigger.cron_schedule and trigger.enabled:
            try:
                self.db.triggers.update_next_run_time(trigger.id)
            except Exception as e:
                logger.error(
                    f"Failed to update next_run_time for trigger {trigger.name}: {e}"
                )
                return

        executor.submit(self.execute_trigger, trigger)

    def _format_events_for_trigger(self, events: list[Event] | None) -> str | None:
        if not events:
            return None

        # Convert to pydantic EventBatch for consistent serialization
        event_dicts = [
            {
                "name": event.name,
                "source": event.source,
                "data": event.data,
                "timestamp": event.timestamp,
            }
            for event in events
        ]
        return EventBatch(events=event_dicts).model_dump_json()

    def create_trigger_env_vars(self, trigger: Trigger) -> dict[str, str]:
        env = os.environ.copy()
        env["TOOLBOX_EVENTS_SOURCE_KIND"] = "stdin"

        return env

    def execute_trigger(
        self,
        trigger: Trigger,
        events: list[Event] | None = None,
        show_output: bool = False,
    ) -> None:
        """
        Execute a trigger script using uv run

        Args:
            trigger (Trigger): Trigger to execute
            events (list[Event] | None, optional): Events to pass to the trigger.
                If not provided, events will be fetched from the database.
            show_output (bool, optional): Whether to show the output of the trigger.
                Defaults to False.
        """
        # Get events if not provided
        if trigger.is_event_based and events is None:
            try:
                events = self.db.events.get_events_for_trigger(
                    trigger, is_consumed=False
                )
                if len(events) == 0:
                    logger.debug(
                        f"No events found for trigger {trigger.name} - skipping"
                    )
                    return
            except Exception as e:
                logger.error(f"Failed to get events for trigger {trigger.name}: {e}")
                return

        # Create execution record
        try:
            execution = self.db.executions.create(trigger.id)
            if events:
                self.db.events.mark_events_triggered(
                    trigger_id=trigger.id,
                    event_ids=[e.id for e in events],
                    execution_id=execution.id,
                )
        except Exception as e:
            logger.error(
                f"Failed to create execution record for trigger {trigger.name}: {e}"
            )
            return

        # Execute trigger
        try:
            stdin_str = self._format_events_for_trigger(events)
            # Find UV path and run the script
            uv_path = find_uv_path()
            if uv_path is None:
                raise FileNotFoundError("UV not found in PATH or common locations")

            uv_cmd = str(uv_path)
            logger.info(
                f"Executing trigger {trigger.name} with {uv_cmd} run python {trigger.script_path}"
            )
            result = subprocess.run(
                [uv_cmd, "run", trigger.script_path],
                capture_output=True,
                text=True,
                timeout=DEFAULT_TRIGGER_TIMEOUT,
                input=stdin_str,
                env=self.create_trigger_env_vars(trigger),
            )

            # Store results
            logs = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            self._safe_set_completed(
                execution.id, result.returncode, logs, trigger.name
            )

            if show_output:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)

        except subprocess.TimeoutExpired:
            self._safe_set_completed(
                execution.id, -1, "Execution timed out", trigger.name
            )
        except Exception as e:
            self._safe_set_completed(
                execution.id, -2, f"Execution failed: {str(e)}", trigger.name
            )

    def _safe_set_completed(
        self, execution_id: int, exit_code: int, logs: str, trigger_name: str
    ) -> None:
        """Safely set execution completion, logging DB errors without raising"""
        try:
            self.db.executions.set_completed(execution_id, exit_code, logs)
        except Exception as e:
            logger.error(
                f"Failed to store execution result for trigger {trigger_name}: {e}"
            )

    def run(self):
        """Main scheduler loop"""
        logger.info("Scheduler thread started")

        try:
            with ThreadPoolExecutor(
                max_workers=settings.daemon.max_concurrent_triggers
            ) as executor:
                while self.running:
                    try:
                        self._process_triggers(executor)

                    except Exception as e:
                        logger.error(f"Scheduler error: {e}")
                    time.sleep(DEFAULT_SLEEP_INTERVAL)

        finally:
            logger.info("Scheduler thread shutting down...")
